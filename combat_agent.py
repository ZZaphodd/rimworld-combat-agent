"""Rule-based combat agent for RimWorld via RimMolt.

Loop: pause -> snapshot -> plan -> act -> advance a few ticks -> repeat.
Moment-to-moment shooting/cover is delegated to RimMolt's built-in
"Auto attack (AI)" order; this agent decides WHO fights, WHERE they muster,
WHOM they focus, and WHEN they pull out.

  python3 combat_agent.py              # dry run: print one plan, change nothing
  python3 combat_agent.py --live       # wait for a raid, then fight it
"""
import argparse
import math
import time
from dataclasses import dataclass, field

from battleground import weapon_range
from rimmolt_client import RimMolt, RimMoltError

MELEE_KEYWORDS = ("sword", "horn", "hammer", "mace", "spear", "knife", "axe",
                  "club", "gladius", "ikwa", "fist", "claw")


@dataclass
class Doctrine:
    # Where the colony is. None = median of colonist positions at battle start.
    anchor: tuple | None = None
    # Muster point for drafted fighters. None = anchor.
    rally: tuple | None = None
    engage_radius: float = 45.0   # engage once a hostile is this close to the anchor
    exposed_radius: float = 30.0  # pull back non-engaged colonists this close to a hostile
    retreat_hp: int = 45          # fighters below this health % leave the fight
    max_per_target: int = 4       # focus-fire cap per enemy
    retarget_ticks: int = 1200    # game ticks between full re-assignments (was 10 steps of 120)
    reissue_ticks: int = 120      # an idle pawn's order is re-issued at most this often
    step_ticks: int = 120         # game ticks per decision step (60 ticks = 1s at 1x)
    # Higher = shoot first. Keys are pawn kinds (defName) from list_things.
    ranged_priority: dict = field(default_factory=lambda: {
        "Mech_Lancer": 5, "Mech_Pikeman": 5, "Mech_Scyther": 4,
        "Mech_Centurion": 3, "Mech_CentipedeBlaster": 2, "Mech_Warqueen": 1,
    })
    # Melee fighters only go for these kinds (squishy/ranged); empty = anything.
    melee_targets: tuple = ("Mech_Lancer", "Mech_Pikeman", "Mech_Scyther")
    melee_fallback_radius: float = 20.0  # ...but anything this close is fair game
    rally_gap: int = 3            # cells between rally cells (2 packed the squad for one grenade)
    in_range_bonus: float = 15.0  # prefer targets a shooter can hit without walking
    announce: bool = True         # show decisions in RimWorld's on-screen panel


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def is_melee(weapon):
    return any(k in weapon.lower() for k in MELEE_KEYWORDS)


class CombatAgent:
    def __init__(self, rm: RimMolt, doctrine: Doctrine, live: bool):
        self.rm, self.d, self.live = rm, doctrine, live
        self.drafted: set[str] = set()
        self.assign: dict[str, str] = {}      # colonist id -> hostile id
        self.evacuees: set[str] = set()       # non-fighters drafted only to walk them home
        self.rescues: dict[str, str] = {}     # downed colonist id -> rescuer id
        self.weapons: dict[str, str | None] = {}  # colonist id -> weapon label (cached)
        self.step = 0
        # Set by the harness wrapper: episode tick, the previous step's tick, and the
        # pawns the reflex layer owns this step. Standalone runs count steps instead.
        self.now = self.prev_now = None
        self.dodging: set[str] = set()
        self.rx = None
        self.ordered_at: dict[str, int] = {}

    # ---------- observe ----------
    def snapshot(self):
        # One call for every position; weapons rarely change, so fetch once per pawn.
        pos = {t["id"]: (t["x"], t["z"]) for t in self.rm.call(
            "list_things", category="pawn", confirm=True, faction="player", verbose=True)["things"]}
        cols = []
        for c in self.rm.call("list_colonists")["colonists"]:
            if c.get("inCaravan") or c["id"] not in pos:
                continue
            if c["id"] not in self.weapons:
                self.weapons[c["id"]] = self.rm.call("get_pawn", id=c["id"]).get("weapon")
            cols.append({**c, "weapon": self.weapons[c["id"]], "pos": pos[c["id"]]})
        hostiles = [h for h in self.rm.call(
            "list_things", category="pawn", confirm=True, faction="hostile", verbose=True)["things"]
            if not h.get("dead") and not h.get("downed")]
        for h in hostiles:
            h["pos"] = (h["x"], h["z"])
        return cols, hostiles

    def can_fight(self, c):
        return (c.get("weapon") and "Violent" not in c.get("incapableOf", "")
                and not c.get("downed") and not c.get("mentalState"))

    # ---------- act ----------
    def act(self, desc, tool, **args):
        print(("  DO   " if self.live else "  PLAN ") + desc)
        if not self.live:
            return None
        try:
            return self.rm.call(tool, **args)
        except RimMoltError as e:
            print(f"       ! {e}")
            return None

    def order(self, pawn, desc, prefer, **target):
        """order_pawn with the first option whose label contains a `prefer` string."""
        if not self.live:
            return self.act(desc, "order_pawn")
        opts = self.rm.call("order_pawn", id=pawn, **target).get("options", [])
        labels = [o.get("label", "") if isinstance(o, dict) else str(o) for o in opts]
        for want in prefer:
            for i, lab in enumerate(labels):
                off = isinstance(opts[i], dict) and opts[i].get("disabled")
                if want in lab.lower() and not off:
                    return self.act(f"{desc} [{lab}]", "order_pawn",
                                    id=pawn, index=i, **target)
        print(f"  SKIP {desc}: no option among {labels}")

    def say(self, text):
        print(f"  SAY  {text}")
        if self.live and self.d.announce:
            try:
                self.rm.call("say", text=text)
            except RimMoltError:
                pass

    # ---------- decide ----------
    def plan_step(self, cols, hostiles):
        d = self.d
        anchor = d.anchor or self._median([c["pos"] for c in cols])
        d.anchor = anchor
        rally = d.rally or anchor
        near = min((dist(h["pos"], anchor) for h in hostiles), default=math.inf)
        engaging = near <= d.engage_radius
        print(f"[step {self.step}] hostiles={len(hostiles)} nearest-to-anchor={near:.0f} "
              f"{'ENGAGE' if engaging else 'HOLD'}")

        fighters = [c for c in cols if self.can_fight(c) and c["health"] >= d.retreat_hp]
        fighter_ids = {c["id"] for c in fighters}

        # 1. Wounded fighters pull out (undrafted pawns flee per hostility response).
        for c in cols:
            if c["id"] in self.drafted and c["id"] not in fighter_ids:
                self.act(f"retreat {c['name']} (hp {c['health']})",
                         "draft", action="undraft", ids=c["id"])
                self.drafted.discard(c["id"])
                self.assign.pop(c["id"], None)

        # 2. Draft fit fighters.
        new = [c for c in fighters if c["id"] not in self.drafted]
        if new:
            self.act("draft " + ", ".join(c["name"] for c in new), "draft",
                     action="draft", ids=",".join(c["id"] for c in new))
            self.drafted |= {c["id"] for c in new}
            if not engaging:
                for i, c in enumerate(new):
                    cell = self._spread(rally, i, d.rally_gap)
                    self.order(c["id"], f"{c['name']} -> rally {cell}",
                               ("go here", "go to", "move"), x=cell[0], z=cell[1])

        # 3. Pull back exposed non-fighters. Undrafted pawns get no "Go here" option,
        #    so draft them for the walk and keep them drafted (= parked) until the
        #    battle ends; releasing early just sends them back out to work.
        for c in cols:
            if c["id"] in fighter_ids or c.get("downed") or c.get("mentalState"):
                continue
            exposed = any(dist(c["pos"], h["pos"]) <= d.exposed_radius for h in hostiles)
            if exposed and c["id"] not in self.evacuees:
                self.act(f"draft {c['name']} to evacuate", "draft", action="draft", ids=c["id"])
                self.evacuees.add(c["id"])
                self.order(c["id"], f"{c['name']} exposed -> back to {anchor}",
                           ("go here", "go to", "move"), x=anchor[0], z=anchor[1])


        # 4. Rescue downed colonists: nearest fit fighter carries them to bed.
        downed = {c["id"]: c for c in cols if c.get("downed")}
        self.rescues = {v: r for v, r in self.rescues.items()
                        if v in downed and r in fighter_ids}
        busy = set(self.rescues.values())
        for vid, v in downed.items():
            if vid in self.rescues:
                continue
            free = [c for c in fighters if c["id"] not in busy and c["id"] not in self.dodging]
            if not free:
                break
            r = min(free, key=lambda c: dist(c["pos"], v["pos"]))
            self.rescues[vid] = r["id"]
            busy.add(r["id"])
            self.assign.pop(r["id"], None)
            self.order(r["id"], f"{r['name']} rescue {v['name']}", ("rescue",), targetId=vid)
        fighters = [c for c in fighters if c["id"] not in busy and c["id"] not in self.dodging]
        for cid in self.dodging:                # re-assigned once the reflex lets go
            self.assign.pop(cid, None)

        if not engaging:
            return

        # 5. Focus fire: (re)assign targets — only enemies that are actually closing in,
        #    so a split raid doesn't drag the squad to both map edges.
        hostiles = [h for h in hostiles if dist(h["pos"], anchor) <= d.engage_radius + 15]
        alive = {h["id"]: h for h in hostiles}
        now = self.now if self.now is not None else self.step * d.step_ticks
        prev = self.prev_now if self.prev_now is not None else now - d.step_ticks
        full = now == 0 or now // d.retarget_ticks != prev // d.retarget_ticks
        load: dict[str, int] = {}
        # A finished or broken attack job (target out of range/sight, AttackStatic
        # ended) leaves the pawn idle with a stale assignment: v1 never noticed.
        job = {c["id"]: (c.get("job") or "") for c in cols}
        for cid, hid in list(self.assign.items()):
            idle = (not job.get(cid, "").startswith(("attacking", "melee attacking", "moving"))
                    and now - self.ordered_at.get(cid, -math.inf) >= d.reissue_ticks)
            if hid not in alive or cid not in fighter_ids or full or idle:
                del self.assign[cid]
            else:
                load[hid] = load.get(hid, 0) + 1
        for c in fighters:
            if c["id"] in self.assign:
                continue
            target = self._pick(c, hostiles, load)
            if target is None:
                continue
            self.assign[c["id"]] = target["id"]
            load[target["id"]] = load.get(target["id"], 0) + 1
            # In range: "Fire at" = stand and shoot this one (Auto attack walks off to
            # find cover and stops shooting meanwhile). Out of range: Auto attack closes.
            if not is_melee(c["weapon"]) and dist(c["pos"], target["pos"]) <= weapon_range(c["weapon"]):
                prefer = ("fire at", "auto attack")
            else:
                prefer = ("auto attack", "attack", "fire at", "melee")
            self.order(c["id"], f"{c['name']} -> {target['label']} {target['pos']}",
                       prefer, targetId=target["id"])
            self.ordered_at[c["id"]] = now

    def _pick(self, c, hostiles, load):
        d = self.d
        melee = is_melee(c["weapon"])
        best, best_score = None, -math.inf
        for h in hostiles:
            if load.get(h["id"], 0) >= d.max_per_target:
                continue
            kind = h.get("kind", h.get("def", ""))
            gap = dist(c["pos"], h["pos"])
            if (melee and d.melee_targets and kind not in d.melee_targets
                    and gap > d.melee_fallback_radius):
                continue
            prio = d.ranged_priority.get(kind, 2)
            if self.rx and self.rx.enabled and h in self.rx.carriers:
                prio = 6                        # rocket carriers: their shots can't be dodged
            score = prio * 10 - gap * (2.0 if melee else 0.5)
            if not melee and gap <= weapon_range(c["weapon"]):
                score += d.in_range_bonus
            if score > best_score:
                best, best_score = h, score
        return best

    @staticmethod
    def _median(pts):
        xs, zs = sorted(p[0] for p in pts), sorted(p[1] for p in pts)
        return (xs[len(xs) // 2], zs[len(zs) // 2])

    @staticmethod
    def _spread(center, i, gap=2):
        # i-th cell of a square grid (`gap`-cell spacing) ordered by distance from center.
        cells = sorted(((dx, dz) for dx in range(-4, 5) for dz in range(-4, 5)),
                       key=lambda p: (p[0] ** 2 + p[1] ** 2, p))
        dx, dz = cells[i % len(cells)]
        return (center[0] + dx * gap, center[1] + dz * gap)

    # ---------- lifecycle ----------
    def battle(self):
        self.say("Combat agent taking command.")
        while True:
            cols, hostiles = self.snapshot()
            if not hostiles:
                break
            self.plan_step(cols, hostiles)
            if not self.live:
                return
            self.step += 1
            ev = self.rm.call("wait_for_event", _timeout=90, maxGameTicks=self.d.step_ticks,
                              maxSeconds=60, pause="always")
            if ev.get("cause") == "threatsCleared":
                break
        if self.drafted | self.evacuees:
            self.act("undraft everyone", "draft", action="undraft",
                     ids=",".join(self.drafted | self.evacuees))
        self.drafted.clear()
        self.evacuees.clear()
        self.assign.clear()
        self.say("Threat cleared. Back to work.")

    def run(self):
        if not self.rm.call("get_status").get("loaded"):
            raise SystemExit("No colony loaded.")
        while True:
            _, hostiles = self.snapshot()
            if hostiles:
                if self.live:
                    self.rm.call("set_speed", action="pause")
                self.battle()
                if not self.live:
                    return
            elif not self.live:
                print("No hostiles on the map; nothing to plan.")
                return
            else:
                print("Waiting for a threat...")
                self.rm.call("wait_for_event", _timeout=330, maxSeconds=300)
            time.sleep(0.1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="actually issue orders")
    ap.add_argument("--url", default="http://localhost:8787/mcp")
    ap.add_argument("--rally", type=int, nargs=2, metavar=("X", "Z"))
    ap.add_argument("--anchor", type=int, nargs=2, metavar=("X", "Z"))
    ap.add_argument("--engage-radius", type=float, default=Doctrine.engage_radius)
    a = ap.parse_args()
    doc = Doctrine(anchor=tuple(a.anchor) if a.anchor else None,
                   rally=tuple(a.rally) if a.rally else None,
                   engage_radius=a.engage_radius)
    CombatAgent(RimMolt(a.url), doc, a.live).run()
