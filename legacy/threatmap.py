"""Shared threat heatmap: one per-cell danger estimate that reflexes and doctrine
positioning both consult, so a pawn that left a dangerous cell is not sent (or
walked by Auto attack) straight back into it.

Reflex v2 was a set of one-shot rules: step out of the fire, nudge apart for
rockets. Whatever got the pawn back (the doctrine, or RimMolt's Auto attack AI,
which picks its own cover cell and cannot see our data) re-chose the same cell
(results/reflex_report.md). Here danger is a field with memory instead.

threat(cell) = hazard + exposure + cover, in rough "how bad is standing here"
units (HIGH = 3 is a cell nobody should stand on by choice):

  hazard (what reflexes flee; remembered with decay, see below)
    frag         W_FRAG inside a resting frag's blast (d <= 1.9), W_FRAG_MARGIN out
                 to 2.5, until it blows (it is not remembered: its end is exact)
    throw zone   W_THROW within 12.9 + THROW_APPROACH cells (then a THROW_TAPER taper) of a live raider
                 carrying frags/molotovs; x THROW_NO_LOS without line of sight
                 (the verb needs LOS: see threatmap_report.md)
    rockets      W_ROCKET within 36 cells of a doomsday/triple-rocket carrier, plus
                 W_CLUMP per squadmate within CLUMP_R of the cell (per pawn): one
                 rocket hits everyone there, so spacing falls out of the field
    fire         W_FIRE on a burning cell, W_FIRE_ADJ next to one
  exposure       W_EXPOSE per live raider that has the cell in weapon range and LOS
  cover          W_COVER_FULL (wall/rock) or W_COVER_TREE next to the cell on the
                 side facing the raiders (sandbags do not render in get_area ascii)

Memory: the pawn-independent hazard of every queried cell is remembered and
decays with a half-life of HALF_LIFE ticks; threat uses max(now, remembered). A
fire that just went out or a grenadier who moved on keeps the cell dangerous
for a few hundred ticks, which is what the hysteresis in reflexes v3 reads.

Cells are evaluated lazily and memoised per step: only cells somebody asks about
(pawn cells, search discs around pawns) cost anything. Terrain comes from one
get_area pass over the squad's neighbourhood and is cached per save for the
whole process (terrain only changes when something burns or blows up).
"""
import math
import time
from collections import deque

from battleground import IMPASSABLE, weapon_range

# ------------------------------------------------------------------ weights
W_FRAG = 10.0             # inside the measured blast reach: very high
W_FRAG_MARGIN = 5.0       # 1.9 < d <= 2.5: our safety margin
FRAG_HIT_R, FRAG_R = 1.9, 2.5
W_THROW = 3.0             # inside a thrower's reach = at the HIGH watermark on its own
THROW_R = 12.9            # Weapon_GrenadeFrag / Molotov verb range (XML)
THROW_APPROACH = 2.0      # full weight this far past 12.9: he walks ~2.4 cells per 30-tick step
THROW_TAPER = 3.0         # then down to 0 over 3 more cells
THROW_NO_LOS = 0.3        # no LOS now; he can step around the obstacle
W_ROCKET = 0.5            # low: rockets can't be dodged, only spread out against
ROCKET_R = 36.0
W_CLUMP = 0.6             # per squadmate within CLUMP_R while a carrier is in reach
CLUMP_R = 3.0
W_FIRE = 6.0
W_FIRE_ADJ = 1.5
W_EXPOSE = 0.35           # per raider that can shoot the cell
W_COVER_FULL = -0.8
W_COVER_TREE = -0.3
COVER_DOT = 0.6           # cover cell must lie within ~53 deg of the threat bearing
FIRE_W = 0.5              # positioning: value per raider we can shoot from the cell
FIRE_CAP = 3
MUST_SEE_BONUS = 1.0
DIST_COST = 0.08          # per cell walked, in threat units
HALF_LIFE = 240           # ticks
HIGH, LOW = 3.0, 1.0      # watermarks: "dangerous" / "safe again"
ELEVATED = 1.5            # doctrines stop handing pawns to Auto attack above this

THROWER_WORDS = ("frag grenade", "molotov")
CARRIER_WORDS = ("doomsday", "rocket launcher")
BLOCKS_LOS = set("#%")
FULL_COVER = set("#%")
TREE = "*"
TILE = 50
MAP = 250

_TERRAIN = {}             # save name -> Terrain, shared by every episode of a process


def hostile_range(label):
    lab = (label or "").lower()
    if any(w in lab for w in THROWER_WORDS):
        return THROW_R
    if any(w in lab for w in CARRIER_WORDS):
        return ROCKET_R
    return weapon_range(label)


class Terrain:
    """ascii terrain fetched in TILE x TILE get_area tiles on demand, with a
    blocker prefix sum so most LOS checks (open ground) are O(1)."""

    def __init__(self, rm, size=MAP):
        self.rm, self.size, self.tiles = rm, size, {}
        self.rows = [[" "] * size for _ in range(size)]      # rows[z][x]
        self.pre = None
        self.calls = 0

    def ensure(self, x0, z0, x1, z1):
        """Fetch every tile overlapping the box; rebuild the prefix sum if any was new."""
        new = False
        for tx in range(max(0, x0) // TILE, min(self.size - 1, x1) // TILE + 1):
            for tz in range(max(0, z0) // TILE, min(self.size - 1, z1) // TILE + 1):
                if (tx, tz) in self.tiles:
                    continue
                ax, az = tx * TILE, tz * TILE
                bx, bz = min(ax + TILE, self.size) - 1, min(az + TILE, self.size) - 1
                grid = self.rm.call("get_area", minX=ax, minZ=az, maxX=bx, maxZ=bz,
                                    render="ascii")["grid"]
                self.calls += 1
                for i, row in enumerate(grid):                # north (max z) first
                    for j, ch in enumerate(row):
                        self.rows[bz - i][ax + j] = ch
                self.tiles[(tx, tz)] = True
                new = True
        if new or self.pre is None:
            n = self.size
            pre = [[0] * (n + 1) for _ in range(n + 1)]
            for z in range(n):
                acc, row, up, cur = 0, self.rows[z], pre[z], pre[z + 1]
                for x in range(n):
                    acc += row[x] in BLOCKS_LOS
                    cur[x + 1] = up[x + 1] + acc
            self.pre = pre

    def cell(self, x, z):
        if not (0 <= x < self.size and 0 <= z < self.size):
            return "#"
        return self.rows[z][x]

    def passable(self, x, z):
        ch = self.cell(x, z)
        return ch != " " and ch not in IMPASSABLE

    def _blockers(self, x0, z0, x1, z1):
        x0, x1 = sorted((max(0, x0), min(self.size - 1, x1)))
        z0, z1 = sorted((max(0, z0), min(self.size - 1, z1)))
        p = self.pre
        return p[z1 + 1][x1 + 1] - p[z0][x1 + 1] - p[z1 + 1][x0] + p[z0][x0]

    def los(self, a, b):
        """Bresenham like battleground.Grid.los (endpoints never block), skipped
        when the bounding box holds no wall or rock at all."""
        (x0, z0), (x1, z1) = a, b
        if not self._blockers(min(x0, x1), min(z0, z1), max(x0, x1), max(z0, z1)):
            return True
        dx, dz = abs(x1 - x0), -abs(z1 - z0)
        sx, sz = (1 if x0 < x1 else -1), (1 if z0 < z1 else -1)
        err, x, z = dx + dz, x0, z0
        while (x, z) != (x1, z1):
            e2 = 2 * err
            if e2 >= dz:
                err += dz
                x += sx
            if e2 <= dx:
                err += dx
                z += sz
            if (x, z) != (x1, z1) and self.rows[z][x] in BLOCKS_LOS:
                return False
        return True


def _timed(f):
    """Count the time spent in map code only (outermost call; nested calls and the
    doctrine's game calls between queries are not counted)."""
    def g(self, *a, **kw):
        if self._depth:
            return f(self, *a, **kw)
        self._depth = 1
        t0 = time.perf_counter()
        try:
            return f(self, *a, **kw)
        finally:
            self._depth = 0
            self._acc += time.perf_counter() - t0
    g.__name__, g.__doc__ = f.__name__, f.__doc__
    return g


def terrain_for(rm, save):
    """One Terrain per save per process: episodes reload the same arena."""
    if save not in _TERRAIN:
        _TERRAIN[save] = Terrain(rm)
    t = _TERRAIN[save]
    t.rm = rm
    return t


class ThreatMap:
    BOX_MARGIN = 12        # cells around the squad's bounding box that we evaluate
    BOX_MAX = 90           # cap on the box side (a scattered squad)

    def __init__(self, terrain):
        self.t = terrain
        self.mem = {}          # cell -> (hazard, tick): remembered pawn-independent hazard
        self.now = 0
        self.pos, self.hostiles, self.frags, self.fire = {}, [], [], set()
        self.fire_adj = set()
        self.reserved = {}     # pid -> cell it is heading for (counts for clumping)
        self.box = (0, 0, MAP - 1, MAP - 1)
        self.cost = {"steps": 0, "ms": 0.0, "cells": 0, "max_ms": 0.0}
        self._depth, self._acc = 0, 0.0      # map seconds since the last update

    # -------------------------------------------------------------- update
    @_timed
    def update(self, pos, hostiles, weapons, now, frags=(), fire=()):
        """pos: pid -> cell; hostiles: live raiders (id/x/z); weapons: raider id ->
        weapon label (lower case); frags: [(cell, deadline_tick)]; fire: cells."""
        self._book()
        self.now, self.pos = now, {k: (round(v[0]), round(v[1])) for k, v in pos.items()}
        self.frags = [(c, d) for c, d in frags if d > now - 5]
        self.fire = {(round(x), round(z)) for x, z in fire}
        self.fire_adj = {(x + dx, z + dz) for x, z in self.fire
                         for dx in (-1, 0, 1) for dz in (-1, 0, 1)} - self.fire
        hs = []
        for h in hostiles:
            w = weapons.get(h["id"], "")
            hs.append({"id": h["id"], "c": (h["x"], h["z"]), "range": hostile_range(w),
                       "thrower": any(k in w for k in THROWER_WORDS),
                       "carrier": any(k in w for k in CARRIER_WORDS)})
        self.hostiles = hs
        self.throwers = [h for h in hs if h["thrower"]]
        self.carriers = [h for h in hs if h["carrier"]]
        xs = [c[0] for c in self.pos.values()] or [MAP // 2]
        zs = [c[1] for c in self.pos.values()] or [MAP // 2]
        m = self.BOX_MARGIN
        x0, x1, z0, z1 = min(xs) - m, max(xs) + m, min(zs) - m, max(zs) + m
        if x1 - x0 > self.BOX_MAX:
            cx = sorted(xs)[len(xs) // 2]
            x0, x1 = cx - self.BOX_MAX // 2, cx + self.BOX_MAX // 2
        if z1 - z0 > self.BOX_MAX:
            cz = sorted(zs)[len(zs) // 2]
            z0, z1 = cz - self.BOX_MAX // 2, cz + self.BOX_MAX // 2
        self.box = (max(0, x0), max(0, z0), min(MAP - 1, x1), min(MAP - 1, z1))
        # LOS from raiders up to ~36 cells outside the box crosses terrain beyond it.
        self.t.ensure(self.box[0] - 40, self.box[1] - 40, self.box[2] + 40, self.box[3] + 40)
        self._hz, self._ex, self._fv = {}, {}, {}
        self.reserved = {k: v for k, v in self.reserved.items() if k in self.pos}
        if len(self.mem) > 20000:                       # forget what has decayed away
            self.mem = {c: v for c, v in self.mem.items() if self._decayed(v) >= 0.2}
        self.cost["steps"] += 1

    def _book(self):
        """Book the previous step's map time (its update + every query since). The
        update that calls this is timed into the new step."""
        if self.cost["steps"]:
            ms = self._acc * 1000
            self.cost["ms"] += ms
            self.cost["max_ms"] = max(self.cost["max_ms"], ms)
            self.cost["cells"] += len(self._hz)
        self._acc = 0.0

    def in_box(self, c):
        x0, z0, x1, z1 = self.box
        return x0 <= c[0] <= x1 and z0 <= c[1] <= z1

    # -------------------------------------------------------------- parts
    def _decayed(self, v):
        val, tick = v
        return val * 0.5 ** ((self.now - tick) / HALF_LIFE)

    @_timed
    def frag(self, c):
        best = 0.0
        for g, _ in self.frags:
            d = math.dist(c, g)
            if d <= FRAG_HIT_R:
                return W_FRAG
            if d <= FRAG_R:
                best = W_FRAG_MARGIN
        return best

    @_timed
    def frag_deadline(self, c):
        """Earliest blast tick among frags whose danger zone covers c (inf if none)."""
        return min((d for g, d in self.frags if math.dist(c, g) <= FRAG_R), default=math.inf)

    def _hazard_now(self, c):
        """Pawn-independent hazard except frags: throw zones, rockets, fire."""
        v = 0.0
        for h in self.throwers:
            d = math.dist(c, h["c"])
            full = THROW_R + THROW_APPROACH
            if d > full + THROW_TAPER:
                continue
            w = W_THROW if d <= full else W_THROW * (full + THROW_TAPER - d) / THROW_TAPER
            v = max(v, w if self.t.los(h["c"], c) else w * THROW_NO_LOS)
        if any(math.dist(c, h["c"]) <= ROCKET_R for h in self.carriers):
            v += W_ROCKET
        if c in self.fire:
            v += W_FIRE
        elif c in self.fire_adj:
            v += W_FIRE_ADJ
        return v

    @_timed
    def base_hazard(self, c):
        """Remembered hazard (no frag, no clumping): max(now, decayed memory)."""
        if c in self._hz:
            return self._hz[c]
        now = self._hazard_now(c)
        old = self.mem.get(c)
        val = max(now, self._decayed(old)) if old else now
        if now >= 0.2 and (not old or now >= self._decayed(old)):
            self.mem[c] = (now, self.now)
        self._hz[c] = val
        return val

    @_timed
    def clump(self, c, pid=None):
        if not any(math.dist(c, h["c"]) <= ROCKET_R for h in self.carriers):
            return 0.0
        mates = {q for o, q in self.pos.items() if o != pid}
        mates |= {q for o, q in self.reserved.items() if o != pid}
        return W_CLUMP * sum(1 for q in mates if q != c and math.dist(q, c) <= CLUMP_R)

    @_timed
    def hazard(self, c, pid=None):
        """What reflexes flee and the watermarks read: frag + remembered hazard,
        plus clumping when asked for a particular pawn."""
        c = (round(c[0]), round(c[1]))
        return self.frag(c) + self.base_hazard(c) + (self.clump(c, pid) if pid else 0.0)

    @_timed
    def exposure(self, c):
        if c in self._ex:
            return self._ex[c]
        n = sum(1 for h in self.hostiles
                if math.dist(c, h["c"]) <= h["range"] and self.t.los(h["c"], c))
        v = W_EXPOSE * n + self.cover(c)
        self._ex[c] = v
        return v

    @_timed
    def cover(self, c):
        """Best cover next to c on the side facing the nearest raiders."""
        near = sorted(self.hostiles, key=lambda h: math.dist(c, h["c"]))[:3]
        if not near:
            return 0.0
        vx = sum(h["c"][0] - c[0] for h in near)
        vz = sum(h["c"][1] - c[1] for h in near)
        n = math.hypot(vx, vz)
        if not n:
            return 0.0
        vx, vz = vx / n, vz / n
        best = 0.0
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if not (dx or dz) or (dx * vx + dz * vz) / math.hypot(dx, dz) < COVER_DOT:
                    continue
                ch = self.t.cell(c[0] + dx, c[1] + dz)
                if ch in FULL_COVER:
                    best = min(best, W_COVER_FULL)
                elif ch == TREE:
                    best = min(best, W_COVER_TREE)
        return best

    @_timed
    def threat(self, c, pid=None):
        c = (round(c[0]), round(c[1]))
        return self.hazard(c, pid) + self.exposure(c)

    @_timed
    def fire_value(self, c, rng, target=None):
        """Raiders we can shoot from c (capped); -inf if `target` is given and can't be."""
        key = (c, rng, target["id"] if target else None)
        if key in self._fv:
            return self._fv[key]
        if target is not None:
            tc = (target["x"], target["z"])
            if math.dist(c, tc) > rng or not self.t.los(c, tc):
                self._fv[key] = -math.inf
                return -math.inf
        n = sum(1 for h in self.hostiles
                if math.dist(c, h["c"]) <= rng and self.t.los(c, h["c"]))
        v = FIRE_W * min(FIRE_CAP, n) + (MUST_SEE_BONUS if target is not None else 0.0)
        self._fv[key] = v
        return v

    @_timed
    def dominant(self, c, pid=None):
        """Which hazard component dominates at c (for KPIs and the frag deadline)."""
        c = (round(c[0]), round(c[1]))
        parts = {"frag": self.frag(c), "fire": W_FIRE if c in self.fire else
                 (W_FIRE_ADJ if c in self.fire_adj else 0.0),
                 "rocket": self.clump(c, pid) + (W_ROCKET if self.carriers and any(
                     math.dist(c, h["c"]) <= ROCKET_R for h in self.carriers) else 0.0)}
        parts["throw"] = max(0.0, self.base_hazard(c) - parts["fire"] - (
            W_ROCKET if parts["rocket"] else 0.0))
        k = max(parts, key=parts.get)
        return k if parts[k] > 0 else None

    # -------------------------------------------------------------- search
    @_timed
    def reachable(self, start, radius, blocked=()):
        """8-neighbour BFS over passable cells within `radius` steps -> cell: steps."""
        start = (round(start[0]), round(start[1]))
        dist, q = {start: 0}, deque([start])
        while q:
            c = q.popleft()
            if dist[c] >= radius:
                continue
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    nb = (c[0] + dx, c[1] + dz)
                    if nb not in dist and nb not in blocked and self.t.passable(*nb):
                        dist[nb] = dist[c] + 1
                        q.append(nb)
        return dist

    @_timed
    def best_cell_near(self, pid, p, radius, must_see=None, rng=25, forbid=(), taken=(),
                       budget=math.inf, speed=0.07, start=15, origin=None):
        """Cell within `radius` steps of `origin` (default p) maximising
        -threat + fire value - DIST_COST x walk, skipping forbidden and taken cells
        and cells p can't reach within `budget` ticks. must_see: a raider that must
        be in range and LOS from the cell. -> (cell, info) or (None, None)."""
        origin = (round(origin[0]), round(origin[1])) if origin else (round(p[0]), round(p[1]))
        best, best_s, best_info = None, -math.inf, None
        for c, steps in self.reachable(origin, radius).items():
            if c in forbid or (c in taken and c != (round(p[0]), round(p[1]))):
                continue
            walk = math.dist(c, p)
            if start + walk / speed > budget and walk > 0.5:
                continue
            fv = self.fire_value(c, rng, must_see)
            if fv == -math.inf:
                continue
            th = self.threat(c, pid)
            s = -th + fv - DIST_COST * walk
            if s > best_s:
                best, best_s = c, s
                best_info = {"threat": th, "hazard": self.hazard(c, pid), "fire": fv,
                             "score": s, "walk": walk}
        return best, best_info

    @_timed
    def rocket_base(self, c):
        return W_ROCKET if any(math.dist(c, h["c"]) <= ROCKET_R for h in self.carriers) else 0.0

    @_timed
    def local_hazard(self, p, pid=None, r=4, minus_rocket=False):
        """Max hazard on p and 8 cells r away: where Auto attack might walk it.
        minus_rocket drops the uniform rocket base (nothing nearby is better)."""
        p = (round(p[0]), round(p[1]))
        pts = [p] + [(p[0] + dx * r, p[1] + dz * r)
                     for dx in (-1, 0, 1) for dz in (-1, 0, 1) if dx or dz]
        return max(self.hazard(c, pid) - (self.rocket_base(c) if minus_rocket else 0.0)
                   for c in pts)

    def summary(self):
        self._book()
        s = max(1, self.cost["steps"])
        return {"tm_ms_per_step": round(self.cost["ms"] / s, 2),
                "tm_max_ms": round(self.cost["max_ms"], 1),
                "tm_cells_per_step": round(self.cost["cells"] / s, 1),
                "tm_steps": self.cost["steps"], "tm_terrain_calls": self.t.calls}


class DangerKPI:
    """Per-pawn bookkeeping for 'returns to danger' and time in high threat,
    the same for every reflex version (it only reads the map).

      fled cell     the pawn stood on a cell with hazard >= HIGH and is >= 2 cells
                    from it a step later;
      return        it is back within 1 cell of a fled cell within RETURN_TICKS while
                    that cell's hazard is still >= LOW (danger that has gone, e.g. a
                    frag that blew, does not count);
      known entry   it moved onto a cell whose hazard was already >= HIGH (and above
                    its old cell's) on the previous step's map, i.e. the danger was
                    known when the move was decided;
      high entry    the same judged on the current map (also counts a zone that
                    moved onto the pawn's new cell while it walked: reported, not
                    part of returns_to_danger);
      high time     pawn-ticks spent on cells with hazard >= HIGH (rockets' clumping
                    included; exposure/cover are not hazard)."""
    RETURN_TICKS = 600

    def __init__(self):
        self.prev = {}         # pid -> (cell, hazard)
        self.fled = {}         # pid -> {cell: tick}
        self.known = {}        # pid -> new cell's hazard on the previous step's map
        self.events = []       # this step's (pid, 'fled' | 'known') returns, for attribution
        self.k = {"returns_fled": 0, "entries_known": 0, "entries_high": 0,
                  "high_pawn_ticks": 0, "pawn_ticks": 0, "fled_cells": 0}

    def pre(self, tm, pos):
        """Before the map is updated: how dangerous did the old map say each pawn's
        new cell was?"""
        self.known = {}
        for pid, p in pos.items():
            c = (round(p[0]), round(p[1]))
            old = self.prev.get(pid)
            if old and old[0] != c:
                self.known[pid] = tm.hazard(c, pid)

    def observe(self, tm, pos, now, dt):
        self.events = []
        for pid, p in pos.items():
            c = (round(p[0]), round(p[1]))
            hz = tm.hazard(c, pid)
            self.k["pawn_ticks"] += dt
            if hz >= HIGH:
                self.k["high_pawn_ticks"] += dt
            fled = self.fled.setdefault(pid, {})
            for cell, t in list(fled.items()):
                if now - t > self.RETURN_TICKS:
                    fled.pop(cell)
                elif math.dist(cell, c) <= 1.5 and tm.hazard(cell) >= LOW:
                    self.k["returns_fled"] += 1
                    self.events.append((pid, "fled"))
                    fled.pop(cell)
            old = self.prev.get(pid)
            if old:
                oc, ohz = old
                if oc != c and hz >= HIGH and hz > ohz:
                    self.k["entries_high"] += 1
                if self.known.get(pid, 0) >= HIGH and self.known[pid] > ohz:
                    self.k["entries_known"] += 1
                    self.events.append((pid, "known"))
                if ohz >= HIGH and math.dist(oc, c) >= 2:
                    fled[oc] = now
                    self.k["fled_cells"] += 1
            self.prev[pid] = (c, hz)

    def summary(self):
        k = dict(self.k)
        k["returns_to_danger"] = k["returns_fled"] + k["entries_known"]
        k["high_share"] = round(k["high_pawn_ticks"] / max(1, k["pawn_ticks"]), 4)
        return {f"tm_{a}": b for a, b in k.items()}
