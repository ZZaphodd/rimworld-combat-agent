"""Shared plumbing for the ported doctrines: observe, draft, casualties,
positioning vs throwers, targeting helpers.

Casualties (LESSONS §4 bugs 5 and 6):
  * Wounded fighters are never undrafted (an undrafted pawn follows the
    hostility response and flees, possibly into the raid). Below RETREAT_HP
    they stay drafted and walk to a fallback cell behind the squad, where they
    still fire at will. Off (None) for doctrines that never had the rule.
  * Rescue: the arenas have no beds, so "Rescue" is disabled ("Cannot rescue:
    No reachable ... bed"). rescue_choice() reads the float menu and only
    reserves a rescuer for an *enabled* option: Rescue if a bed exists, else
    "Carry <name>" (verified 2026-10-03: the drafted carrier keeps the downed
    pawn while it walks under Go here, and the "Drop <name>" gizmo puts it
    down). The carried pawn is walked to a safe cell behind the squad and
    dropped. No enabled option -> nobody is reserved (count rescue_unavailable).
  * Both take shooters out of the fight and are not shown to pay (LESSONS §2
    phase-2 smoke), so they are options: `rescue` (doctrine agent) and
    `wounded_pullback` (doctrine agent, turtle), each on|off, natural = on;
    off = the pawn keeps fighting where it is (wounded) / nobody is sent to
    a downed squadmate. Recorded in rows and the resume key.
Positioning vs throwers (TODO phase-2 requirement 3) is an explicit option
`vs_throwers` on doctrines that list it in option_choices:
  accept_dodge  stay where the doctrine puts the pawn; micro dodges frags;
  stand_off     a shooter within throw range (12.9) + 1.5 of a frag/molotov
                carrier steps back to 15.5 cells from it (still in range for
                guns >= 16) and holds there OVERRIDE_TICKS;
  close_in      a shooter within 25 cells of a thrower Auto-attacks it.
The first choice in option_choices is the doctrine's natural behaviour.
"""
import math
import statistics

from ..eval.kpis import CONTACT, Tally, add_spacing, in_contact
from ..game.weapons import (CARRIER_WORDS, THROWER_WORDS, is_melee, weapon_class,
                            weapon_name, weapon_range)
from ..rimmolt import hostiles as list_hostiles, player_pawns
from .doctrine import Doctrine
from .preconditions import Context, check

MAP = 250
THROW_R = 12.9                # frag/molotov verb range (XML)
STANDOFF_R = 15.5
CLOSE_IN_R = 25
OVERRIDE_TICKS = 300
CARRIER_R = 35                # rocket carriers first within this range (doctrine agent priority 6)
RESCUE_R = 30
CARRY_TICKS = 1500            # give up a carry that takes longer
PICKUP_SPEED = 0.06          # cells/tick walking to the victim (GAME_FACTS §4: ~0.07)
MAX_RESCUE_TRIES = 2
FALLBACK_R = 10
REISSUE_TICKS = 600


def able(c):
    return (not c.get("downed") and not c.get("mentalState")
            and "Violent" not in (c.get("incapableOf") or ""))


def unit(dx, dz):
    n = math.hypot(dx, dz)
    return (dx / n, dz / n) if n else (0.0, 0.0)


def clip(c):
    return (min(MAP - 3, max(2, round(c[0]))), min(MAP - 3, max(2, round(c[1]))))


def pos(t):
    return (t["x"], t["z"])


def rescue_choice(options):
    """Float menu on a downed squadmate -> ("rescue"|"carry", index, name) or
    None. Disabled options ("Cannot rescue: ...") are never chosen (legacy v1
    matched 'rescue' inside them and clicked 41 times)."""
    opts = [o for o in options if isinstance(o, dict) and not o.get("disabled")]
    for kind, prefix in (("rescue", "Rescue "), ("carry", "Carry ")):
        o = next((o for o in opts if o.get("label", "").startswith(prefix)), None)
        if o:
            return kind, o["index"], o["label"][len(prefix):].strip()
    return None


class SquadDoctrine(Doctrine):
    RETREAT_HP = None            # pull wounded back below this health % (None: never)
    RESCUE = False               # carry downed squadmates to a safe cell

    def reset(self, rm, manifest):
        super().reset(rm, manifest)
        self.rm = rm
        sq = manifest["squad"]
        self.squad_ids = {p["id"] for p in sq}
        self.anchor = (round(statistics.median(p["x"] for p in sq)),
                       round(statistics.median(p["z"] for p in sq)))
        self.weapons, self.enemy = {}, {}
        self.drafted, self.target, self.override = set(), {}, {}
        self.rescues, self.dropped, self.wounded, self.tries = {}, set(), {}, {}
        self.errors = []
        self.tally, self.contact, self.short = Tally(), False, {}
        self.owned, self.all_fighters, self.downed = set(), [], {}
        self.k = {k: 0 for k in ("rescue_started", "rescue_carried", "rescue_unavailable",
                                 "rescue_failed", "wounded_pullbacks", "thrower_moves",
                                 "thrower_attacks", "orders_failed", "redrafts",
                                 "redraft_on_error")}
        self.lapsed = set()
        self.pre = self.precheck(rm)

    # ------------------------------------------------------------ observe
    def enemy_info(self, h):
        """Weapon label, class, range, thrower/carrier of a raider: one get_pawn
        per raider per episode."""
        e = self.enemy.get(h["id"])
        if e is None:
            label = self.rm.call("get_pawn", id=h["id"]).get("weapon") or ""
            kind = h.get("kind") or h.get("def", "")
            low = label.lower()
            e = self.enemy[h["id"]] = {
                "weapon": weapon_name(label), "cls": weapon_class(label, kind),
                "range": weapon_range(label, kind),
                "thrower": any(w in low for w in THROWER_WORDS),
                "carrier": any(w in low for w in CARRIER_WORDS)}
        return e

    def enemy_reach(self, h):
        e = self.enemy_info(h)
        return e["range"], e["thrower"]

    def precheck(self, rm):
        """Preconditions on the starting position (stored in kpis as pre_*)."""
        if not self.preconditions:
            return {}
        try:
            hs = list_hostiles(rm)
            sq = {t["id"]: pos(t) for t in player_pawns(rm) if t["id"] in self.squad_ids}
            squad = []
            for pid, p in sq.items():
                w = self._weapon(pid)
                squad.append({"pos": p, "range": weapon_range(w), "melee": is_melee(w)})
            enemies = [{"pos": pos(h), "cls": self.enemy_info(h)["cls"],
                        "range": self.enemy_info(h)["range"]} for h in hs]
            return check(self, Context(self.terrain, self.anchor, squad, enemies))
        except Exception as e:                  # a check must never cost the episode
            return {"error": repr(e)[:100]}

    def _weapon(self, pid):
        if pid not in self.weapons:
            self.weapons[pid] = self.rm.call("get_pawn", id=pid).get("weapon")
        return self.weapons[pid]

    def observe(self, rm):
        """-> (free fighters, live hostiles). Drafts new fighters (never
        undrafts), runs micro, progress, casualties and the thrower option.
        Fighters: {id, pos, weapon, range, melee, health, job, name}."""
        cols = [c for c in rm.call("list_colonists")["colonists"] if c["id"] in self.squad_ids]
        mine = {t["id"]: t for t in player_pawns(rm)}
        self.short = {i: t.get("label", "").split(",")[0].split("<")[0].strip()
                      for i, t in mine.items()}
        self.downed = {c["id"]: pos(mine[c["id"]]) for c in cols
                       if c.get("downed") and c["id"] in mine}
        sq = {c["id"]: {"pos": pos(mine[c["id"]]) if c["id"] in mine else None,
                        "health": c.get("health", 100), "downed": bool(c.get("downed"))}
              for c in cols}
        fighters = []
        for c in cols:
            if c["id"] not in mine or not able(c):
                continue
            w = self._weapon(c["id"])
            if not w:
                continue
            fighters.append({"id": c["id"], "pos": pos(mine[c["id"]]), "weapon": w,
                             "range": weapon_range(w), "melee": is_melee(w),
                             "health": c.get("health", 100), "job": (c.get("job") or "").lower(),
                             "name": self.short.get(c["id"], "")})
        hs = list_hostiles(rm)
        for h in hs:
            h["pos"] = pos(h)
        # The game undrafts a pawn when it goes down (or breaks); when it stands
        # up again it is undrafted and has no "Go here" (verified 2026-10-03,
        # LESSONS §4 "Turtle Go here failures"). Forget it, so it is re-drafted.
        lapsed = {c["id"] for c in cols if not able(c)} & self.drafted
        self.drafted -= lapsed
        self.k["redrafts"] += len({c["id"] for c in fighters} & self.lapsed)
        self.lapsed = (self.lapsed | lapsed) - {c["id"] for c in fighters}
        new = [c["id"] for c in fighters if c["id"] not in self.drafted]
        if new and hs:
            rm.call("draft", action="draft", ids=",".join(new))
            self.drafted |= set(new)
        self.all_fighters = fighters
        if not hs or not fighters:
            self.note_progress(hs, False, sq)
            return [], hs
        owned = self.micro.step(fighters, hs, self.now, self.step_ticks)
        for pid in owned:
            self.target.pop(pid, None)              # its order is gone: re-issue once released
        self.contact = in_contact(fighters, hs)
        if self.contact:
            add_spacing(self.tally, fighters)
        self.note_progress(hs, self.contact, sq)
        busy = set(owned)
        busy |= self.rescue_step(fighters, hs, busy)
        busy |= self.wounded_step(fighters, hs, busy)
        free = [c for c in fighters if c["id"] not in busy]
        busy |= self.thrower_step(free, hs)
        self.owned = owned
        return [c for c in fighters if c["id"] not in busy], hs

    # ------------------------------------------------------------ orders
    def goto(self, pid, cell):
        """Go here; on an error try the neighbours. Drops any attack order.
        "No order matched 'Go here'" means the pawn is undrafted (an occupied
        or impassable cell still succeeds: the game picks a cell nearby;
        verified 2026-10-03): draft it and retry once instead."""
        self.target.pop(pid, None)
        r, redrafted = None, False
        cells = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (2, 0), (0, 2))
        i = 0
        while i < len(cells):
            dx, dz = cells[i]
            i += 1
            x, z = clip((cell[0] + dx, cell[1] + dz))
            if self.terrain is not None and not self.terrain.passable(x, z):
                continue
            try:
                r = self.rm.call("order_pawn", id=pid, x=x, z=z, command="Go here")
            except Exception as e:
                r = {"error": repr(e)}
                continue
            if r.get("ok", True) and "error" not in r:
                return (x, z)
            if "No order matched" in str(r.get("error")):
                if redrafted:
                    break                        # still no Go here: not a cell problem
                self.rm.call("draft", action="draft", ids=pid)
                self.drafted.add(pid)
                self.k["redraft_on_error"] += 1
                redrafted, i = True, i - 1       # same cell again
        self.fail("goto", r)
        return None

    def fail(self, what, r):
        self.k["orders_failed"] += 1
        self.errors = (self.errors + [f"{what}: {str((r or {}).get('error', r))[:80]}"])[-6:]

    def auto_attack(self, pid, h, force=False):
        if self.target.get(pid) == h["id"] and not force:
            return True
        r = self.rm.call("do_thing_action", id=pid, label="Auto attack (AI)", targetId=h["id"])
        if r.get("ok"):
            self.target[pid] = h["id"]
            return True
        self.fail("auto_attack", r)
        return False

    def fire_at(self, pid, h):
        """Stand and shoot (Auto attack walks off to find cover and stops
        shooting; LESSONS §2). Falls back to Auto attack."""
        try:
            r = self.rm.call("order_pawn", id=pid, targetId=h["id"], command="Fire at")
        except Exception as e:
            r = {"error": repr(e)}
        if r.get("ok", True) and "error" not in r:
            self.target[pid] = h["id"]
            return True
        return self.auto_attack(pid, h, force=True)

    @staticmethod
    def nearest(p, things):
        return min(things, key=lambda h: math.dist(pos(h), p))

    def priority_target(self, p, hs, near):
        """Rocket carriers within CARRIER_R first: their shots can't be dodged."""
        carriers = [h for h in hs if self.enemy_info(h)["carrier"]
                    and math.dist(pos(h), p) <= CARRIER_R]
        return self.nearest(p, carriers) if carriers else near

    def target_for(self, c, hs):
        near = self.nearest(c["pos"], hs)
        return near if c["melee"] else self.priority_target(c["pos"], hs, near)

    # ------------------------------------------------------------ safe cells
    def fallback_cell(self, hs, origin=None, dist=FALLBACK_R, taken=()):
        """A walkable cell `dist` behind the squad centre, away from the raid."""
        pts = [c["pos"] for c in self.all_fighters] or [self.anchor]
        cx, cz = statistics.mean(p[0] for p in pts), statistics.mean(p[1] for p in pts)
        ex = statistics.mean(h["x"] for h in hs)
        ez = statistics.mean(h["z"] for h in hs)
        ux, uz = unit(cx - ex, cz - ez)
        want = clip((cx + ux * dist, cz + uz * dist))
        if self.terrain is None:
            return want
        for c, _ in sorted(self.terrain.bfs(want, limit=5).items(), key=lambda kv: kv[1]):
            if c not in taken and self.micro.cell_ok(None, c):
                return c
        return want

    # ------------------------------------------------------------ casualties
    def rescue_on(self):
        """RESCUE class flag and the `rescue` option (doctrine agent; on/off)."""
        return self.RESCUE and self.opt.get("rescue", "on") == "on"

    def pullback_on(self):
        """RETREAT_HP class value and the `wounded_pullback` option (on/off)."""
        return self.RETREAT_HP is not None and self.opt.get("wounded_pullback", "on") == "on"

    def rescue_step(self, fighters, hs, busy):
        """Carry downed squadmates out (see module docstring). Returns rescuers."""
        if not self.rescue_on():
            return set()
        byid = {c["id"]: c for c in fighters}
        out = set()
        for vid in list(self.rescues):
            r = self.rescues[vid]
            rid = r["by"]
            if vid not in self.downed or rid not in byid:
                self.rescues.pop(vid)
                continue
            if r["state"] == "pickup":
                job = (self.rm.call("get_pawn", id=vid).get("job") or "").lower()
                if job.startswith("being carried"):
                    r["dest"] = self.fallback_cell(hs)
                    self.goto(rid, r["dest"])
                    r.update(state="carry", at=self.now)
                    self.k["rescue_carried"] += 1
                elif self.now - r["at"] > r["pickup_ticks"]:
                    self.rescues.pop(vid)
                    self.k["rescue_failed"] += 1
                    continue
            elif r["state"] == "carry":
                here = byid[rid]["pos"]
                if math.dist(here, r["dest"]) <= 1.5 or self.now - r["at"] > CARRY_TICKS:
                    self.rm.call("do_thing_action", id=rid, label=f"Drop {r['name']}")
                    self.dropped.add(vid)
                    self.rescues.pop(vid)
                    continue
            elif r["state"] == "rescue" and self.now - r["at"] > CARRY_TICKS:
                self.rescues.pop(vid)
                continue
            out.add(rid)
        for vid, vpos in self.downed.items():
            if vid in self.rescues or vid in self.dropped \
                    or self.tries.get(vid, 0) >= MAX_RESCUE_TRIES:
                continue
            if any(math.dist(pos(h), vpos) <= 2 for h in hs):
                continue                         # still in melee: dragging it out costs two
            free = [c for c in fighters if c["id"] not in busy and c["id"] not in out
                    and math.dist(c["pos"], vpos) <= RESCUE_R]
            if not free:
                continue
            rc = min(free, key=lambda c: math.dist(c["pos"], vpos))
            opts = self.rm.call("order_pawn", id=rc["id"], targetId=vid).get("options", [])
            choice = rescue_choice(opts)
            if choice is None:
                self.k["rescue_unavailable"] += 1
                self.dropped.add(vid)            # don't ask again every step
                continue
            kind, idx, name = choice
            r = self.rm.call("order_pawn", id=rc["id"], targetId=vid, index=idx)
            if not r.get("ok", True) or "error" in r:
                self.fail("rescue", r)
                continue
            self.target.pop(rc["id"], None)
            self.tries[vid] = self.tries.get(vid, 0) + 1
            self.rescues[vid] = {"by": rc["id"], "state": "pickup" if kind == "carry" else "rescue",
                                 "name": name, "at": self.now,
                                 "pickup_ticks": 60 + math.dist(rc["pos"], vpos) / PICKUP_SPEED}
            self.k["rescue_started"] += 1
            out.add(rc["id"])
        return out

    def keep_wounded_fighting(self, c, hs):
        """Hook: True = this wounded pawn keeps its post (e.g. the fight is inside)."""
        return False

    def wounded_step(self, fighters, hs, busy):
        """Bug 6: stay drafted, walk to a fallback cell, fire at will from there."""
        if not self.pullback_on():
            return set()
        out = set()
        for c in fighters:
            pid = c["id"]
            if pid in busy or c["health"] >= self.RETREAT_HP or self.keep_wounded_fighting(c, hs):
                continue
            last = self.wounded.get(pid)
            if last is None or (self.now - last["at"] >= REISSUE_TICKS
                                and math.dist(c["pos"], last["dest"]) > 2):
                dest = self.fallback_cell(hs)
                if self.goto(pid, dest):
                    self.wounded[pid] = {"at": self.now, "dest": dest}
                    self.k["wounded_pullbacks"] += last is None
            out.add(pid)
        return out

    # ------------------------------------------------------------ vs throwers
    def thrower_step(self, free, hs):
        mode = self.opt.get("vs_throwers")
        if mode in (None, "accept_dodge"):
            return set()
        throwers = [h for h in hs if self.enemy_info(h)["thrower"]]
        out = set()
        for c in free:
            pid = c["id"]
            if self.now < self.override.get(pid, -1):
                out.add(pid)
                continue
            if c["melee"] or not throwers:
                continue
            t = self.nearest(c["pos"], throwers)
            d = math.dist(pos(t), c["pos"])
            if mode == "stand_off" and d <= THROW_R + 1.5:
                ux, uz = unit(c["pos"][0] - t["x"], c["pos"][1] - t["z"])
                want = (t["x"] + ux * STANDOFF_R, t["z"] + uz * STANDOFF_R)
                if self.goto(pid, want):
                    self.override[pid] = self.now + OVERRIDE_TICKS
                    self.k["thrower_moves"] += 1
                    out.add(pid)
            elif mode == "close_in" and d <= CLOSE_IN_R:
                if self.auto_attack(pid, t):
                    self.override[pid] = self.now + OVERRIDE_TICKS
                    self.k["thrower_attacks"] += 1
                    out.add(pid)
        return out

    def kpis(self):
        pre = {f"pre_{k}": v for k, v in (self.pre or {}).items()}
        return (super().kpis() | self.tally.summary() | dict(self.k) | pre
                | {"no_progress_ticks": self.no_progress_ticks, "order_errors": self.errors})
