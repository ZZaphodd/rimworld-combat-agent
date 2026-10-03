"""The `doctrine` agent (focus fire), v4 — port of legacy combat_agent v1-v3.

Win condition: concentrate fire. Each enemy is shot by at most MAX_PER_TARGET
guns, in kill-priority order (rocket carriers, then lancers/pikemen, ...), so
raiders drop one at a time and their fire shrinks faster than ours
(Lanchester square law); no overkill.
Preconditions: a mostly ranged squad (ranged_squad >= 0.5).
Phases:
  setup   draft, take rally cells RALLY_GAP apart around the anchor;
  hold    on the rally cells (drafted, fire at will) while no raider is within
          ENGAGE_R of the anchor;
  commit  a raider within ENGAGE_R: focus-fire assignments; Fire at when the
          target is in the pawn's XML range (stand and shoot), Auto attack to
          close otherwise; only raiders within ENGAGE_R + 15 are assigned
          (split-raid rule); full re-assignment every RETARGET_TICKS, idle
          pawns re-ordered after REISSUE_TICKS;
  reset   no raider within ENGAGE_R + 15 for RESET_TICKS while raiders
          remain: back to the rally cells (hold).
Casualties: wounded (< 45%) stay drafted and fall back (v1-v3 undrafted them:
they fled, LESSONS bug 6); downed squadmates are carried to a safe cell when
"Carry" is enabled, never reserved for a disabled "Rescue" (bug 5). Both are
options: rescue=on|off, wounded_pullback=on|off (natural on; to be compared in
the baseline).
vs_throwers: accept_dodge (natural) / stand_off / close_in.
Signal: no_progress after NO_PROGRESS_TICKS of contested time (we take damage or
are in a raider's reach) without enemy points lost (EVAL_SPEC §2).
Evidence (LESSONS §2): v2 tied amove on its home themes; guns per target
barely moved (2.6 -> 2.7); catastrophic vs grenadiers (5.2 lost).
"""
import math

from .squad import SquadDoctrine, pos

RANGED_PRIORITY = {"Mech_Lancer": 5, "Mech_Pikeman": 5, "Mech_Scyther": 4,
                   "Mech_Centurion": 3, "Mech_CentipedeBlaster": 2, "Mech_Warqueen": 1}
CARRIER_PRIORITY = 6
MELEE_TARGETS = ("Mech_Lancer", "Mech_Pikeman", "Mech_Scyther")
MELEE_FALLBACK_R = 20


class Focus(SquadDoctrine):
    name = "doctrine"
    version = 4                  # legacy v1-v3 (combat_agent)
    win_condition = "focus fire: kill raiders one at a time, <= 4 guns each, by priority"
    preconditions = {"ranged_squad": {"min_share": 0.5}}
    phases_spec = {"setup": "rally", "hold": "rally cells, fire at will",
                   "commit": "raider within 45 of the anchor: focus fire",
                   "reset": "no raider within 60 for 1200 ticks: back to rally"}
    option_choices = {"vs_throwers": ("accept_dodge", "stand_off", "close_in"),
                      "rescue": ("on", "off"), "wounded_pullback": ("on", "off")}
    RETREAT_HP = 45
    RESCUE = True
    ENGAGE_R, SPLIT_R = 45, 15
    MAX_PER_TARGET = 4
    RETARGET_TICKS, REISSUE_TICKS, RESET_TICKS = 1200, 120, 1200
    RALLY_GAP = 3                # 2 packed the squad for one grenade
    IN_RANGE_BONUS = 15

    def reset(self, rm, manifest):
        super().reset(rm, manifest)
        self.assign, self.ordered_at, self.rallied = {}, {}, set()
        self.far_since = None
        self.last_full = -1

    def rally_cell(self, i):
        cells = sorted(((dx, dz) for dx in range(-4, 5) for dz in range(-4, 5)),
                       key=lambda p: (p[0] ** 2 + p[1] ** 2, p))
        dx, dz = cells[i % len(cells)]
        return (self.anchor[0] + dx * self.RALLY_GAP, self.anchor[1] + dz * self.RALLY_GAP)

    def step(self, rm):
        fighters, hs = self.observe(rm)
        if not hs or not fighters:
            return
        near = min(math.dist(pos(h), self.anchor) for h in hs)
        engaging = near <= self.ENGAGE_R
        in_area = [h for h in hs if math.dist(pos(h), self.anchor) <= self.ENGAGE_R + self.SPLIT_R]
        if self.phase == "commit" and not in_area:
            self.far_since = self.now if self.far_since is None else self.far_since
            if self.now - self.far_since >= self.RESET_TICKS:
                self.set_phase("reset")
                self.rallied.clear()
                self.assign.clear()
        else:
            self.far_since = None
        if not engaging and self.phase != "commit":
            self.set_phase("setup" if self.phase is None else "hold")
            for i, c in enumerate(sorted(fighters, key=lambda c: c["id"])):
                if c["id"] not in self.rallied:
                    self.goto(c["id"], self.rally_cell(i))
                    self.rallied.add(c["id"])
            return
        if engaging:
            self.set_phase("commit")
        self.focus(fighters, in_area or hs)

    def focus(self, fighters, hs):
        alive = {h["id"]: h for h in hs}
        free = {c["id"] for c in fighters}
        full = self.now // self.RETARGET_TICKS != self.last_full
        self.last_full = self.now // self.RETARGET_TICKS
        load = {}
        for cid, hid in list(self.assign.items()):
            c = next((f for f in fighters if f["id"] == cid), None)
            idle = c is not None and (not c["job"].startswith(("attacking", "melee attacking", "moving"))
                                      and self.now - self.ordered_at.get(cid, -math.inf)
                                      >= self.REISSUE_TICKS)
            if hid not in alive or cid not in free or full or idle:
                del self.assign[cid]
            else:
                load[hid] = load.get(hid, 0) + 1
        for c in fighters:
            if c["id"] in self.assign:
                continue
            t = self.pick(c, hs, load)
            if t is None:
                continue
            self.assign[c["id"]] = t["id"]
            load[t["id"]] = load.get(t["id"], 0) + 1
            if not c["melee"] and math.dist(c["pos"], pos(t)) <= c["range"]:
                self.fire_at(c["id"], t)
            else:
                self.auto_attack(c["id"], t, force=True)
            self.ordered_at[c["id"]] = self.now
        if self.contact:
            targets = [h for h in self.assign.values()]
            if targets:
                self.tally.add("targets_per_step", len(set(targets)))
                self.tally.add("guns_per_target", len(targets) / len(set(targets)))
            self.tally.add("assigned_share", len(self.assign) / max(1, len(fighters)))
            self.tally.add("attacking_share", sum(c["job"].startswith(("attacking", "melee"))
                                                  for c in fighters) / len(fighters))

    def pick(self, c, hs, load):
        best, best_score = None, -math.inf
        for h in hs:
            if load.get(h["id"], 0) >= self.MAX_PER_TARGET:
                continue
            kind = h.get("kind") or h.get("def", "")
            gap = math.dist(c["pos"], pos(h))
            if c["melee"] and kind not in MELEE_TARGETS and gap > MELEE_FALLBACK_R:
                continue
            prio = CARRIER_PRIORITY if self.enemy_info(h)["carrier"] else RANGED_PRIORITY.get(kind, 2)
            score = prio * 10 - gap * (2.0 if c["melee"] else 0.5)
            if not c["melee"] and gap <= c["range"]:
                score += self.IN_RANGE_BONUS
            if score > best_score:
                best, best_score = h, score
        return best
