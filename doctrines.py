"""Theme-specific doctrines: each one counters a single kind of raid.

  spread  anti-explosive: keep >= MIN_GAP cells between pawns, Auto attack individually.
  kite    anti-melee: stand and fire; only the shooter a melee raider is about to
          reach runs, through the squad; melee pawns intercept.
  close   anti-standoff: rush to short range from cover to cover, then Auto attack.

All three share the same observe/act plumbing as hold_agent and stay drafted
throughout (drafted pawns that stand still fire at will at anything in range).
Each step starts with the shared reflex layer (reflexes.py); pawns it owns are
left alone that step. With reflex v3, spread asks the threat map (rx.place)
before handing a pawn to Auto attack. Durations are game ticks (agent.now from the harness), so
they mean the same at any decision cycle.
"""
import math
import statistics

from battle_tracker import short_name
from battleground import Grid
from combat_agent import is_melee
from kpis import Tally, add_spacing, in_contact, nearest_ally
from raid_census import weapon_class, weapon_name
from reflexes import attach

MAP = 250


def _pos(t):
    return (t["x"], t["z"])


def _clip(c):
    return (min(MAP - 3, max(2, round(c[0]))), min(MAP - 3, max(2, round(c[1]))))


def _unit(dx, dz):
    n = math.hypot(dx, dz)
    return (dx / n, dz / n) if n else (0.0, 0.0)


class _Base:
    name = "_base"
    version = 1
    reflex = True
    step_ticks, now = 120, 0

    def reset(self, rm, manifest):
        self.rm = rm
        self.weapons, self.enemy_class, self.target = {}, {}, {}
        self.drafted = False
        self.tally, self.steps = Tally(), 0
        self.rx, self.busy = attach(self, rm, manifest), set()
        self.last_now, self.dt = 0, 0

    def kpis(self):
        return self.tally.summary() | self.rx.kpis()

    def _observe(self):
        rm = self.rm
        mine = rm.call("list_things", category="pawn", faction="player", confirm=True,
                       verbose=True)["things"]
        pos = {t["id"]: _pos(t) for t in mine}
        self.short = {t["id"]: short_name(t.get("label")) for t in mine}
        cols = []
        for c in rm.call("list_colonists")["colonists"]:
            if c["id"] not in pos:
                continue
            if c["id"] not in self.weapons:
                self.weapons[c["id"]] = rm.call("get_pawn", id=c["id"]).get("weapon")
            cols.append({**c, "pos": pos[c["id"]], "weapon": self.weapons[c["id"]]})
        fighters = [c for c in cols if c.get("weapon") and not c.get("downed")
                    and not c.get("mentalState") and "Violent" not in c.get("incapableOf", "")]
        hostiles = [t for t in rm.call("list_things", category="pawn", faction="hostile",
                                       confirm=True, verbose=True)["things"]
                    if not t.get("downed") and not t.get("dead")]
        if fighters and not self.drafted:
            rm.call("draft", action="draft", ids=",".join(c["id"] for c in fighters))
            self.drafted = True
        alive = {h["id"] for h in hostiles}
        self.target = {k: v for k, v in self.target.items() if v in alive}
        self.steps += 1
        self.dt, self.last_now = self.now - self.last_now, self.now
        self.contact = bool(fighters) and in_contact(fighters, hostiles)
        if self.contact:
            add_spacing(self.tally, fighters)
        self.busy = self.rx.step(fighters, hostiles, self.now, self.step_ticks) \
            if fighters and hostiles else set()
        for pid in self.busy:                   # its order is gone: re-issue once released
            self.target.pop(pid, None)
        return fighters, hostiles

    def _target(self, c, hostiles):
        """Nearest raider; shooters take a rocket carrier in reach first."""
        near = self._nearest(c["pos"], hostiles)
        return near if is_melee(c["weapon"]) else self.rx.priority_target(c["pos"], hostiles, near)

    def _class(self, h):
        """Weapon class of a raider (cached: one get_pawn per raider per episode)."""
        if h["id"] not in self.enemy_class:
            w = weapon_name(self.rm.call("get_pawn", id=h["id"]).get("weapon"))
            self.enemy_class[h["id"]] = weapon_class(w, h.get("kind") or h.get("def", ""))
        return self.enemy_class[h["id"]]

    def _modes(self, fighters):
        """Who positioned each pawn this step (KPI), and the map's step cost."""
        self.rx.count_modes(fighters, set(self.target), self.busy)

    def _auto_attack(self, pid, hostile):
        if self.target.get(pid) == hostile["id"]:
            return
        r = self.rm.call("do_thing_action", id=pid, label="Auto attack (AI)",
                         targetId=hostile["id"])
        if r.get("ok"):
            self.target[pid] = hostile["id"]

    def _goto(self, pid, cell):
        """Go here; on an unwalkable cell try the neighbours. Drops any attack order."""
        self.target.pop(pid, None)
        for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 2), (-2, -2)):
            x, z = _clip((cell[0] + dx, cell[1] + dz))
            try:
                r = self.rm.call("order_pawn", id=pid, x=x, z=z, command="Go here")
            except Exception:
                continue
            if r.get("ok", True) and "error" not in r:
                return True
        return False

    @staticmethod
    def _nearest(p, things):
        return min(things, key=lambda h: math.dist(_pos(h), p))


class Spread(_Base):
    """Anti-explosive. One grenade/rocket/inferno blast hits everyone within a few
    cells, and Auto attack happily stacks a squad behind the same rock. So:
    any pawn with a squadmate closer than MIN_GAP steps away (repulsion from
    its close neighbours) and holds there for HOLD_STEPS, firing at will;
    otherwise it Auto attacks the raider nearest to IT (no shared focus target,
    which would pull everybody onto the same line).
    v3 (reflex v3): the step-out cell is the map's best cell near the repulsion
    point; inside elevated-threat areas the map places the pawn instead of Auto
    attack (fallback: step back out of the throw zone, keeping it in range)."""
    name = "spread"
    version = 2               # v2: reflex layer, hold in ticks
    versions = {2: 2, 3: 4}   # 3: with reflex 3a, 4: with reflex 3b
    own_spacing = True        # the reflex layer's rocket-spacing nudge would fight MIN_GAP
    MIN_GAP = 5
    STEP_OUT = 5              # cells: enough to clear MIN_GAP from a stacked neighbour
    HOLD_TICKS = 600          # v1: the move step + 4 held steps of 120

    def reset(self, rm, manifest):
        super().reset(rm, manifest)
        self.hold = {}            # pid -> tick until which it stands on its spread cell

    def step(self, rm):
        fighters, hostiles = self._observe()
        if not hostiles or not fighters:
            return
        if self.contact:
            for c in fighters:
                self.tally.add("mean_gap", min(15, nearest_ally(c, fighters)))
        for i, c in enumerate(fighters):
            pid, p = c["id"], c["pos"]
            if pid in self.busy:
                continue
            close = [o["pos"] for o in fighters
                     if o["id"] != pid and math.dist(o["pos"], p) < self.MIN_GAP]
            holding = self.now < self.hold.get(pid, 0)
            if close and not holding:
                vx = sum(_unit(p[0] - q[0], p[1] - q[1])[0] for q in close)
                vz = sum(_unit(p[0] - q[0], p[1] - q[1])[1] for q in close)
                if math.hypot(vx, vz) < 0.3:        # stacked on one cell: fan out by index
                    a = i * 2.4
                    vx, vz = math.cos(a), math.sin(a)
                ux, uz = _unit(vx, vz)
                want = (p[0] + ux * self.STEP_OUT, p[1] + uz * self.STEP_OUT)
                if self.rx.version >= 3 and self.rx.enabled:
                    rx = self.rx
                    cell, _ = rx.map.best_cell_near(pid, p, 3 + self.STEP_OUT, origin=_clip(want),
                                                    rng=rx._range(c), forbid=rx.forbidden(pid),
                                                    taken=rx._taken(pid))
                    if cell and all(math.dist(cell, q) >= self.MIN_GAP - 1 for q in close):
                        want = cell
                        rx.map.reserved[pid] = cell
                self._goto(pid, want)
                self.hold[pid] = self.now + self.HOLD_TICKS
            elif not holding:
                target = self._target(c, hostiles)
                if self.rx.place(c, hostiles, target, self.now, "back"):
                    self.target.pop(pid, None)
                    continue
                self._auto_attack(pid, target)
        self._modes(fighters)


class Kite(_Base):
    """Anti-melee: a shooter in melee is a dead shooter, a raider still running
    at us is a free target. v2 (v1 sent everyone forward with Auto attack, then
    ran each threatened shooter straight away from its own threat: the squad met
    the raid halfway, scattered over 100 cells, and shooters spent their steps
    walking with a raider on their heels — adjacent 1/3 of the time):
      * while melee raiders are coming nobody advances; drafted pawns that stand
        still fire at will, so the raid crosses open ground under fire;
      * a shooter runs only if a melee raider that is after IT (the raider's
        own "attacking colonist <name>", else the nearest shooter) can reach it
        before our next decision (RAIDER_SPEED x step + MARGIN); everyone else
        keeps shooting (v2a ran everyone in reach: at 120 ticks that was the
        whole squad, and nobody fired);
      * the runner goes THROUGH the squad to its far side: the chaser is dragged
        past everyone else's guns and the squad stays together;
      * melee pawns intercept the melee raider closest to a shooter;
      * when no melee raider is pressing any more (dead, fled), Auto attack the rest."""
    name = "kite"
    version = 4                 # v4: reflex layer, calm in ticks
    RAIDER_SPEED = 0.08         # cells/tick: humanlike ~4.6 c/s at 60 ticks/s, some faster
    MARGIN = 3
    # REAR and PRESS are distances, not durations: they keep their meaning at any cycle.
    REAR = 5                    # cells behind the squad's centre a runner aims for
    PRESS = 40                  # a melee raider this close to a fighter is pressing us
    SCREEN_ENGAGE = 8
    CALM_TICKS = 360            # v3: 3 contact steps of 120 with no melee raider pressing

    def reset(self, rm, manifest):
        super().reset(rm, manifest)
        self.calm = 0           # contact ticks with no melee raider pressing

    def step(self, rm):
        fighters, hostiles = self._observe()
        if not hostiles or not fighters:
            return
        melee_raiders = [h for h in hostiles if self._class(h) == "melee"]
        ranged = [c for c in fighters if not is_melee(c["weapon"])]
        screens = [c for c in fighters if is_melee(c["weapon"])]
        pressing = [h for h in melee_raiders
                    if any(math.dist(_pos(h), c["pos"]) <= self.PRESS for c in fighters)]
        self.calm = 0 if pressing else self.calm + self.dt * self.contact
        sweep = not melee_raiders or self.calm >= self.CALM_TICKS
        reach = self.RAIDER_SPEED * self.step_ticks + self.MARGIN
        line = [c["pos"] for c in ranged] or [c["pos"] for c in fighters]
        cx, cz = statistics.mean(q[0] for q in line), statistics.mean(q[1] for q in line)
        hunted = self._hunted(ranged, melee_raiders, reach)
        for i, c in enumerate(ranged):
            pid, p = c["id"], c["pos"]
            threats = hunted.get(pid, [])
            self._measure(p, melee_raiders, bool(threats))
            if pid in self.busy:
                continue
            if threats:
                self._run(pid, p, threats, (cx, cz), i, reach)
            elif sweep:
                self._auto_attack(pid, self._target(c, hostiles))
            elif pid in self.target:              # was advancing: stop and shoot
                self._goto(pid, p)
        self._screen(screens, ranged, pressing or hostiles)
        self._modes(fighters)

    def _hunted(self, ranged, melee_raiders, reach):
        """shooter id -> melee raiders within `reach` that are after that shooter."""
        out = {}
        for h in melee_raiders:
            near = [c for c in ranged if math.dist(_pos(h), c["pos"]) <= reach]
            if not near:
                continue
            aim = (h.get("targeting") or "").lower()
            victim = next((c for c in near if self.short.get(c["id"]) and
                           aim.endswith(" " + self.short[c["id"]].lower())), None)
            victim = victim or min(near, key=lambda c: math.dist(_pos(h), c["pos"]))
            out.setdefault(victim["id"], []).append(h)
        return out

    def _run(self, pid, p, threats, centre, i, reach):
        """Away from the threats, through the squad's centre to REAR cells past it
        (at least `reach` cells), fanned out sideways so runners don't stack."""
        tx = statistics.mean(h["x"] for h in threats)
        tz = statistics.mean(h["z"] for h in threats)
        ux, uz = _unit(centre[0] - tx, centre[1] - tz)
        if (ux, uz) == (0.0, 0.0):
            ux, uz = _unit(p[0] - tx, p[1] - tz) if (p[0], p[1]) != (tx, tz) else (1.0, 0.0)
        ahead = (centre[0] - p[0]) * ux + (centre[1] - p[1]) * uz   # centre's distance along u
        go = max(reach, ahead + self.REAR)
        side = ((i % 5) - 2) * 3
        self._goto(pid, (p[0] + ux * go - uz * side, p[1] + uz * go + ux * side))

    def _screen(self, screens, ranged, foes):
        """Each melee pawn takes the raider nearest to any shooter (one each)."""
        taken = set()
        for c in screens:
            pid, p = c["id"], c["pos"]
            if pid in self.busy:
                continue
            free = [h for h in foes if h["id"] not in taken] or foes
            threat = min(free, key=lambda h: min(
                [math.dist(_pos(h), s["pos"]) for s in ranged] or [math.dist(_pos(h), p)]))
            taken.add(threat["id"])
            gap = min([math.dist(_pos(threat), s["pos"]) for s in ranged] or [math.inf])
            if math.dist(_pos(threat), p) <= self.SCREEN_ENGAGE or gap <= self.SCREEN_ENGAGE:
                self._auto_attack(pid, threat)

    def _measure(self, p, melee_raiders, retreating):
        """Per shooter and step, while a melee raider is within 30 cells: how far the
        nearest one is, whether it is touching, and whether we spent the step running."""
        d = min((math.dist(_pos(h), p) for h in melee_raiders), default=math.inf)
        if d > 30:
            return
        self.tally.add("shooter_melee_dist", d)
        self.tally.add("melee_adjacent_share", d <= 1.5)
        self.tally.add("retreat_share", retreating)


class Close(_Base):
    """Anti-standoff. Snipers and archers out-range most of the squad, so
    trading shots at their range loses; close the gap instead. Each step every
    pawn farther than CLOSE_DIST from its nearest raider bounds ADVANCE cells
    toward it, ending next to cover (trees, rocks, walls) when there is any;
    inside CLOSE_DIST it switches to Auto attack for good."""
    name = "close"
    version = 2                  # v2: reflex layer, one bound per ADVANCE_TICKS
    CLOSE_DIST = 14
    ADVANCE = 10                 # cells per bound, ~ what a pawn walks in 120 ticks
    ADVANCE_TICKS = 120          # a new bound at most this often (v1: one per 120-tick step)
    COVER = set("*#%")           # get_area ascii: tree, wall, natural rock (sandbags do not render)

    def reset(self, rm, manifest):
        super().reset(rm, manifest)
        self.grid = None
        self.engaged = set()
        self.closed_at = []          # tick each pawn first got inside CLOSE_DIST
        self.next_bound = {}

    def _cover_cell(self, want):
        """Free cell within 3 of `want` that has a cover cell next to it."""
        g = self.grid
        best, best_d = _clip(want), math.inf
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                c = (round(want[0]) + dx, round(want[1]) + dz)
                if not g.inside(*c) or not g.passable(*c) or g.cell(*c) in self.COVER:
                    continue
                if any(g.cell(c[0] + a, c[1] + b) in self.COVER
                       for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b):
                    d = math.hypot(dx, dz)
                    if d < best_d:
                        best, best_d = c, d
        return best

    def step(self, rm):
        fighters, hostiles = self._observe()
        if not hostiles or not fighters:
            return
        if self.grid is None:
            self.grid = Grid.from_rimmolt(rm, 0, 0, MAP - 1, MAP - 1)
        for c in fighters:
            pid, p = c["id"], c["pos"]
            if pid in self.busy:
                continue
            near = self._nearest(p, hostiles)
            d = math.dist(_pos(near), p)
            if pid not in self.engaged and d <= self.CLOSE_DIST:
                self.closed_at.append(self.now)
                self.tally.put("close_tick_mean", round(statistics.mean(self.closed_at)))
                self.tally.put("closed_n", len(self.closed_at))
            if pid in self.engaged or d <= self.CLOSE_DIST:
                self.engaged.add(pid)
                self._auto_attack(pid, self._target(c, hostiles))
                continue
            if self.now < self.next_bound.get(pid, 0):
                continue                         # still on the last bound
            self.next_bound[pid] = self.now + self.ADVANCE_TICKS
            ux, uz = _unit(near["x"] - p[0], near["z"] - p[1])
            hop = min(self.ADVANCE, d - self.CLOSE_DIST + 2)
            self._goto(pid, self._cover_cell((p[0] + ux * hop, p[1] + uz * hop)))
        self._modes(fighters)

