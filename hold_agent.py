"""'turtle' (formerly 'hold'): pick the battleground, man the firing line, let raiders come.

Ranged pawns take the cells battleground.plan_positions() picks and stay there
drafted (drafted pawns fire at will at anything in range). Melee pawns stand
just behind the line and only charge raiders that get close. The line breaks
into Auto attack only when raiders are inside our area or never show up.
The plan is redone when the raid's bearing swings (it went around the walls,
or a second group showed up elsewhere): a line facing the wrong way is useless.

v6 (with reflex v3): slots respect the threat map. A slot that is dangerous
(hazard >= HIGH) or that this pawn fled (hysteresis) is swapped for a clearly
safer cell within 4, and a pawn that dodged only goes back to a slot that is
safe again. Line pawns on their slot Fire at the nearest grenade thrower or
rocket carrier in reach (rifles out-range a 13-cell throw). When the line
engages (sally / raid inside), the map places shooters in elevated-threat
areas instead of Auto attack.
"""
import math
import statistics

from battleground import Grid, plan_positions, weapon_range
from combat_agent import is_melee
from kpis import Tally, add_spacing, in_contact
from reflexes import attach

GRID_MARGIN = 60          # map rectangle around the anchor we analyse
MELEE_TRIGGER = 7         # melee pawns charge raiders this close to the line
INSIDE_RADIUS = 10        # raiders this close to the anchor = fight is inside, everyone engages
# Durations in game ticks (v4 counted 120-tick steps: 40, 12 and 10 steps).
IDLE_SALLY_TICKS = 4800   # no raider ever comes within range for this long -> go get them
STALL_SALLY_TICKS = 1440  # in contact but no raider lost for this long -> go get them
RETREAT_HP = 45
REPLAN_ANGLE = 45         # degrees the raid's bearing from the anchor may swing before re-planning
REPLAN_COOLDOWN = 1200    # ticks between plans, so a split raid can't make the line dance


def _pos(t):
    return (t["x"], t["z"])


class HoldAgent:
    name = "turtle"
    version = 5              # v3 planner + stall sally (v4) + reflex layer, timers in ticks (v5)
    versions = {2: 5, 3: 7}  # reflex version -> agent version (v6: map-aware slots, reflex 3a;
                             # v7: same with reflex 3b)
    reflex = True
    step_ticks, now = 120, 0

    def reset(self, rm, manifest):
        self.rm = rm
        sq = manifest["squad"]
        self.anchor = (round(statistics.median(p["x"] for p in sq)),
                       round(statistics.median(p["z"] for p in sq)))
        self.weapons, self.slots, self.target = {}, {}, {}
        self.plan = None
        self.grid = None
        self.bearing = None
        self.planned_at = 0
        self.steps = 0
        self.idle = 0
        self.sally = False
        self.tally, self.n_hostiles, self.stall = Tally(), None, 0     # stall/idle in ticks
        self.last_now, self.dt = 0, self.step_ticks
        self.rx, self.displaced = attach(self, rm, manifest), set()

    # ---------------------------------------------------------- observe
    def _observe(self):
        rm = self.rm
        pos = {t["id"]: _pos(t) for t in rm.call(
            "list_things", category="pawn", confirm=True, faction="player", verbose=True)["things"]}
        cols = []
        for c in rm.call("list_colonists")["colonists"]:
            if c["id"] not in pos:
                continue
            if c["id"] not in self.weapons:
                self.weapons[c["id"]] = rm.call("get_pawn", id=c["id"]).get("weapon")
            cols.append({**c, "pos": pos[c["id"]], "weapon": self.weapons[c["id"]]})
        hostiles = [t for t in rm.call("list_things", category="pawn", confirm=True, faction="hostile",
                                       verbose=True)["things"]
                    if not t.get("downed") and not t.get("dead")]
        return cols, hostiles

    def _fighters(self, cols):
        return [c for c in cols if c.get("weapon") and not c.get("downed")
                and not c.get("mentalState") and "Violent" not in c.get("incapableOf", "")]

    # ---------------------------------------------------------- plan once
    def _enemy_center(self, hostiles):
        return (statistics.median(h["x"] for h in hostiles),
                statistics.median(h["z"] for h in hostiles))

    def _bearing(self, center):
        return math.degrees(math.atan2(center[1] - self.anchor[1], center[0] - self.anchor[0]))

    def _make_plan(self, fighters, hostiles):
        ax, az = self.anchor
        if self.grid is None:                 # terrain doesn't change mid-fight
            self.grid = Grid.from_rimmolt(
                self.rm, max(0, ax - GRID_MARGIN), max(0, az - GRID_MARGIN),
                min(249, ax + GRID_MARGIN), min(249, az + GRID_MARGIN))
        grid = self.grid
        enemy_center = self._enemy_center(hostiles)
        self.bearing = self._bearing(enemy_center)
        self.planned_at = self.now
        self.slots = {}
        ranged = [c for c in fighters if not is_melee(c["weapon"])]
        melee = [c for c in fighters if is_melee(c["weapon"])]
        cells, report = plan_positions(grid, self.anchor, enemy_center, len(ranged))
        self.plan = report
        if report.get("no_approach"):
            self.sally = True              # raid landed on us: nothing to hold, fight
            print("   hold plan: raid already inside the search radius -> fight")
            return
        # Nearest free firing cell per shooter (greedy is fine at squad sizes).
        free = list(cells)
        for c in sorted(ranged, key=lambda c: math.dist(c["pos"], report["exit"])):
            if not free:
                break
            cell = min(free, key=lambda f: math.dist(f, c["pos"]))
            free.remove(cell)
            self.slots[c["id"]] = cell
        # Melee: a step behind the line, between it and the anchor.
        line = [self.slots[c["id"]] for c in ranged if c["id"] in self.slots] or [self.anchor]
        lx = statistics.median(p[0] for p in line)
        lz = statistics.median(p[1] for p in line)
        bx, bz = (lx + self.anchor[0]) / 2, (lz + self.anchor[1]) / 2
        for i, c in enumerate(melee):
            self.slots[c["id"]] = (round(bx) + (i % 3) - 1, round(bz) + (i // 3) - 1)
        print(f"   hold plan: exit={report['exit']} center={report.get('center')} "
              f"window={report.get('window', 0):.0f} exposure_frac={report['exposure_frac']:.2f} "
              f"shooters={len(cells)}/{len(ranged)} melee={len(melee)}")

    # ---------------------------------------------------------- act
    def _goto(self, pid, cell):
        self.rm.call("order_pawn", id=pid, x=cell[0], z=cell[1], command="Go here")

    def _safe_slot(self, c):
        """The pawn's slot, unless the map says it is dangerous or the pawn fled it:
        then a clearly safer cell within 4 (which becomes its slot), else None."""
        pid = c["id"]
        slot = self.slots.get(pid)
        if slot is None or self.rx.slot_ok(pid, slot):
            return slot
        new = self.rx.better_slot(c, slot, {s for o, s in self.slots.items() if o != pid})
        if new:
            self.slots[pid] = new
        return new

    def _auto_attack(self, pid, hostile):
        if self.target.get(pid) == hostile["id"]:
            return
        r = self.rm.call("do_thing_action", id=pid, label="Auto attack (AI)",
                         targetId=hostile["id"])
        if r.get("ok"):
            self.target[pid] = hostile["id"]

    def step(self, rm):
        self.steps += 1
        self.dt, self.last_now = self.now - self.last_now, self.now
        cols, hostiles = self._observe()
        fighters = self._fighters(cols)
        if not hostiles or not fighters:
            return
        if self.plan is None:
            rm.call("draft", action="draft", ids=",".join(c["id"] for c in fighters))
            self._make_plan(fighters, hostiles)
            busy = self.rx.step(fighters, hostiles, self.now, self.step_ticks)
            for c in fighters:
                if c["id"] in self.slots and c["id"] not in busy:
                    slot = self._safe_slot(c)          # v2: always the planned slot
                    if slot:
                        self._goto(c["id"], slot)
            return
        busy = self.rx.step(fighters, hostiles, self.now, self.step_ticks)
        self.displaced |= busy

        inside = any(math.dist(_pos(h), self.anchor) <= INSIDE_RADIUS for h in hostiles)
        if not inside and not self.sally and self.now - self.planned_at >= REPLAN_COOLDOWN:
            swing = abs((self._bearing(self._enemy_center(hostiles)) - self.bearing + 180) % 360 - 180)
            if swing > REPLAN_ANGLE:
                print(f"   hold: raid bearing swung {swing:.0f} deg -> re-plan")
                self._make_plan(fighters, hostiles)
                self.target = {}
                for c in fighters:
                    if c["id"] in self.slots and c["id"] not in busy:
                        slot = self._safe_slot(c)
                        if slot:
                            self._goto(c["id"], slot)
                return
        self._measure(fighters, hostiles, inside)
        in_range = any(math.dist(_pos(h), c["pos"]) <= 30 for h in hostiles for c in fighters)
        self.idle = 0 if in_range else self.idle + self.dt
        # v3 only had the idle rule, and a raider parked 13-28 cells out of sight
        # (mechs) counts as "in range": the line sat 40+ steps being picked off.
        stalled = self.stall >= STALL_SALLY_TICKS
        if (self.idle >= IDLE_SALLY_TICKS or stalled) and not self.sally:
            self.sally = True              # not coming / not dying where we can hit them: go
            self.tally.once("sally_tick", self.now)
            self.tally.once("sally_reason", "stall" if stalled else "idle")
        alive = {h["id"] for h in hostiles}
        for c in fighters:
            pid = c["id"]
            if pid in busy:                            # the reflex has it this step
                self.target.pop(pid, None)
                continue
            if pid in self.displaced:                  # dodged: back to the line
                self.displaced.discard(pid)
                if pid in self.slots and not (self.sally or inside):
                    slot = self._safe_slot(c)
                    if slot:
                        self._goto(pid, slot)
                    continue
            if self.target.get(pid) not in alive:
                self.target.pop(pid, None)
            if c["health"] < RETREAT_HP and not inside:
                self._goto(pid, self.anchor)           # stay drafted, step off the line
                self.target.pop(pid, None)
                continue
            near = min(hostiles, key=lambda h: math.dist(_pos(h), c["pos"]))
            d = math.dist(_pos(near), c["pos"])
            melee = is_melee(c["weapon"])
            if self.sally or inside or (melee and d <= MELEE_TRIGGER):
                tgt = near if melee else self.rx.priority_target(c["pos"], hostiles, near)
                if not melee and self.rx.place(c, hostiles, tgt, self.now, "kill"):
                    self.target.pop(pid, None)         # v6: the map places it
                    continue
                self._auto_attack(pid, tgt)
            elif pid in self.target:
                # Raider left melee reach / fight moved outside: back to the slot.
                self.target.pop(pid, None)
                slot = self._safe_slot(c)
                if slot:
                    self._goto(pid, slot)
            elif pid in self.slots and self.rx.version >= 3:
                slot = self.slots[pid]
                safe = self._safe_slot(c)
                if safe and safe != slot:
                    self._goto(pid, safe)
                elif not melee and math.dist(c["pos"], slot) <= 1.5:
                    self.rx.focus_danger(c, hostiles)
        self.rx.count_modes(fighters, set(self.target), busy)

    # ---------------------------------------------------------- KPIs
    def _measure(self, fighters, hostiles, inside):
        """Line discipline while holding, time to the line's first shot, and the
        stall counter the sally rule reads (contact steps without a raider lost)."""
        t = self.tally
        if self.n_hostiles is not None and len(hostiles) < self.n_hostiles:
            self.stall = 0
        elif in_contact(fighters, hostiles):
            self.stall += self.dt
            t.put("longest_stall_ticks", max(t.vals.get("longest_stall_ticks", 0), self.stall))
        self.n_hostiles = len(hostiles)
        if not in_contact(fighters, hostiles):
            return
        add_spacing(t, fighters)
        line = [c for c in fighters if c["id"] in self.slots and not is_melee(c["weapon"])]
        on = [c for c in line if math.dist(c["pos"], self.slots[c["id"]]) <= 1.5]
        if line and not (self.sally or inside):
            t.add("on_slot_share", len(on) / len(line))
        if any(math.dist(c["pos"], _pos(h)) <= weapon_range(c["weapon"])
               for c in on for h in hostiles):
            t.once("first_shot_tick", self.now)

    def kpis(self):
        return self.tally.summary() | self.rx.kpis()
