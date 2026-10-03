"""turtle (formerly hold) v8: pick the battleground, man a concave, let them come.

Win condition: raiders come through our choke/approach into a packed concave
and die crossing open ground under the fire of every shooter at once
(engagement surface ours > theirs).
Preconditions: defensible terrain near the anchor (defensible_terrain) and an
enemy that comes to us (enemy_approaches). The "turtle + grenade" stalemate
(LESSONS §0) was a turtle without either.
Phases:
  setup   plan (rca/tactical/planner.py v4, per-pawn XML ranges), draft, walk
          to the slots; melee pawns a step behind the line;
  hold    on the line, drafted, fire at will; melee pawns charge raiders within
          MELEE_TRIGGER; re-plan when the raid's bearing swings > 45 deg
          (cooldown 1200 ticks, so a split raid can't make the line dance);
  commit  (a) inside: a raider within INSIDE_RADIUS of the anchor -> everyone
          engages locally; (b) sally (permanent): nobody within 30 cells for
          IDLE_SALLY_TICKS (4800), or in contact with no raider lost for
          STALL_SALLY_TICKS (1440; v4: mechs parked 13-28 cells out);
  reset   the inside fight is over (no raider within INSIDE_RADIUS): back to
          the slots; a pawn released by micro walks back only to a slot that
          is not inside a live hazard (cell_ok).
Signals: precondition:no_approach (raid already inside at planning: nothing to
hold), precondition:enemy_approaches (the idle sally fired: they don't come),
no_progress (NO_PROGRESS_TICKS of contested time without enemy points lost,
also after a sally; EVAL_SPEC §2).
Casualties: < 45% health steps off the line to a fallback cell, drafted
(unless the fight is inside); option wounded_pullback=on|off (natural on).
vs_throwers: accept_dodge (natural; micro dodges, viscosity 0.8) / stand_off /
close_in.
Dropped from legacy v6/v7: threat-map slot swaps and map placement (micro v4
has no threat map; LESSONS §1: untested as a tactical option).
"""
import math
import statistics

from . import planner
from .squad import SquadDoctrine, pos

MELEE_TRIGGER = 7
INSIDE_RADIUS = 10
IDLE_R = 30
IDLE_SALLY_TICKS = 4800
STALL_SALLY_TICKS = 1440
REPLAN_ANGLE, REPLAN_COOLDOWN = 45, 1200
SLOT_REISSUE_TICKS = 600


class Turtle(SquadDoctrine):
    name = "turtle"
    version = 8                  # legacy hold/turtle v1-v7
    win_condition = "they come through our approach into a packed concave and die crossing open ground"
    preconditions = {"defensible_terrain": {"radius": 14, "min_cover": 0.10},
                     "enemy_approaches": {"min_share": 0.5}}
    phases_spec = {"setup": "plan + walk to slots", "hold": "line, fire at will",
                   "commit": "inside (local) or sally (idle 4800 / stall 1440 ticks)",
                   "reset": "inside fight over: back to the slots"}
    option_choices = {"vs_throwers": ("accept_dodge", "stand_off", "close_in"),
                      "wounded_pullback": ("on", "off")}
    RETREAT_HP = 45

    def reset(self, rm, manifest):
        super().reset(rm, manifest)
        self.plan, self.slots, self.bearing = None, {}, None
        self.planned_at, self.replans = 0, 0
        self.idle = self.stall = 0
        self.n_hostiles, self.sally, self.inside = None, False, False
        self.last_now, self.slot_order = 0, {}

    # ------------------------------------------------------------ plan
    def _center(self, hs):
        return (statistics.median(h["x"] for h in hs), statistics.median(h["z"] for h in hs))

    def _bearing(self, c):
        return math.degrees(math.atan2(c[1] - self.anchor[1], c[0] - self.anchor[0]))

    def make_plan(self, fighters, hs):
        center = self._center(hs)
        self.bearing, self.planned_at = self._bearing(center), self.now
        ranged = [c for c in fighters if not c["melee"]]
        melee = [c for c in fighters if c["melee"]]
        er = [self.enemy_info(h)["range"] for h in hs]
        enemy_range = min(45, statistics.median(er)) if er else planner.DEFAULT_RANGE
        _, slots, report = planner.plan(self.terrain, self.anchor, center,
                                        [c["range"] for c in ranged], enemy_range)
        self.plan, self.slots = report, {}
        if report.get("no_approach"):
            self.sally = True              # raid landed on us: nothing to hold, fight
            self.tally.once("sally_tick", self.now)
            self.tally.once("sally_reason", "no_approach")
            self.raise_signal("precondition:no_approach")
            return
        for c, cell in zip(ranged, slots):
            if cell is not None:
                self.slots[c["id"]] = cell
        line = list(self.slots.values()) or [self.anchor]
        lx = statistics.median(p[0] for p in line)
        lz = statistics.median(p[1] for p in line)
        bx, bz = (lx + self.anchor[0]) / 2, (lz + self.anchor[1]) / 2
        for i, c in enumerate(melee):
            self.slots[c["id"]] = (round(bx) + (i % 3) - 1, round(bz) + (i // 3) - 1)
        self.tally.put("plan", {k: report.get(k) for k in (
            "exit", "center", "window", "best_window", "exposure_frac", "shooters_placed",
            "shooters", "range", "enemy_range")})

    def to_slot(self, c, force=False):
        pid, slot = c["id"], self.slots.get(c["id"])
        if slot is None or not self.micro.cell_ok(pid, slot):
            return                         # never walk back into a live hazard
        if math.dist(c["pos"], slot) <= 1.5:
            return
        if force or self.now - self.slot_order.get(pid, -math.inf) >= SLOT_REISSUE_TICKS:
            self.goto(pid, slot)
            self.slot_order[pid] = self.now

    def keep_wounded_fighting(self, c, hs):
        return self.inside

    # ------------------------------------------------------------ step
    def step(self, rm):
        fighters, hs = self.observe(rm)
        dt, self.last_now = self.now - self.last_now, self.now
        if not hs or not self.all_fighters:
            return
        self.inside = any(math.dist(pos(h), self.anchor) <= INSIDE_RADIUS for h in hs)
        if self.plan is None:
            self.set_phase("setup")
            self.make_plan(self.all_fighters, hs)
            for c in fighters:
                self.to_slot(c, force=True)
            return
        if not self.inside and not self.sally and self.now - self.planned_at >= REPLAN_COOLDOWN:
            swing = abs((self._bearing(self._center(hs)) - self.bearing + 180) % 360 - 180)
            if swing > REPLAN_ANGLE:
                self.replans += 1
                self.set_phase("setup")
                self.make_plan(self.all_fighters, hs)
                self.target = {}
                for c in fighters:
                    self.to_slot(c, force=True)
                return
        self.measure(hs)
        near30 = any(math.dist(pos(h), c["pos"]) <= IDLE_R for h in hs for c in self.all_fighters)
        self.idle = 0 if near30 else self.idle + dt
        if not self.sally and (self.idle >= IDLE_SALLY_TICKS or self.stall >= STALL_SALLY_TICKS):
            self.sally = True              # not coming / not dying where we can hit them: go
            why = "stall" if self.stall >= STALL_SALLY_TICKS else "idle"
            self.tally.once("sally_tick", self.now)
            self.tally.once("sally_reason", why)
            if why == "idle":
                self.raise_signal("precondition:enemy_approaches")
        was_inside = self.phase == "commit" and not self.sally
        self.set_phase("commit" if self.sally or self.inside else
                       "reset" if was_inside else
                       "hold" if self.phase in ("hold", "reset") or self.on_line(fighters) else "setup")
        for c in fighters:
            pid = c["id"]
            near = self.nearest(c["pos"], hs)
            d = math.dist(pos(near), c["pos"])
            if self.sally or self.inside or (c["melee"] and d <= MELEE_TRIGGER):
                t = self.target_for(c, hs)
                if not c["melee"] and math.dist(pos(t), c["pos"]) <= c["range"] and not self.sally:
                    if self.target.get(pid) != t["id"]:
                        self.fire_at(pid, t)
                else:
                    self.auto_attack(pid, t)
            elif pid in self.target:       # raider left melee reach / fight moved out: back
                self.target.pop(pid, None)
                self.to_slot(c, force=True)
            else:
                self.to_slot(c, force=pid in self.owned_before)
        self.owned_before = set(self.owned)

    owned_before = frozenset()

    def on_line(self, fighters):
        line = [c for c in fighters if c["id"] in self.slots and not c["melee"]]
        return bool(line) and sum(math.dist(c["pos"], self.slots[c["id"]]) <= 1.5
                                  for c in line) >= 0.8 * len(line)

    def measure(self, hs):
        """Line discipline while holding, the line's first shot, and the stall
        counter the sally rule reads (contact ticks without a raider lost)."""
        t, dt = self.tally, self.now - getattr(self, "_mlast", self.now)
        self._mlast = self.now
        if self.n_hostiles is not None and len(hs) < self.n_hostiles:
            self.stall = 0
        elif self.contact:
            self.stall += dt
            t.put("longest_stall_ticks", max(t.vals.get("longest_stall_ticks", 0), self.stall))
        self.n_hostiles = len(hs)
        if not self.contact:
            return
        line = [c for c in self.all_fighters if c["id"] in self.slots and not c["melee"]]
        on = [c for c in line if math.dist(c["pos"], self.slots[c["id"]]) <= 1.5]
        if line and not (self.sally or self.inside):
            t.add("on_slot_share", len(on) / len(line))
        if any(math.dist(c["pos"], pos(h)) <= c["range"] for c in on for h in hs):
            t.once("first_shot_tick", self.now)

    def kpis(self):
        return super().kpis() | {"replans": self.replans}
