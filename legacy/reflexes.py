"""Shared reflex layer: step out of what is about to blow up, whatever the doctrine.

Every doctrine calls Reflexes.step() right after observing and before deciding;
the pawns it returns belong to the reflex this step and the doctrine leaves them
alone. What it reacts to (see results/hazards.md for the measured windows):

  * frag grenades (ground-fused): a grenade seen at the same cell twice is at
    rest and blows ~FUSE ticks after it landed. A grenade seen for the first time
    may already be at rest, so it is treated as one. Pawns within DANGER_R walk
    to the nearest safe cell, if they can get there before the fuse runs out.
  * grenades/molotovs in flight: thrown AT a pawn, so the squad pawn nearest the
    forward ray of two sightings is the predicted landing spot. v1 moved pawns
    on it; it was right for only ~1 frag in 4 (reflex_report.md), so v2 only
    scores the prediction (KPI) and does not act on it. Molotovs therefore get
    no reflex before impact; their fire does.
  * fire: pawns on a burning cell step out; next to one only at low viscosity.
  * rocket carriers (doomsday / triple rocket launcher, not dodgeable once fired):
    clumped pawns are nudged apart (not for doctrines that space themselves),
    and priority_target() lets a doctrine shoot the carriers first.

Viscosity: each doctrine has a threshold; a reflex fires only when the threat's
severity for that pawn reaches it. Severity is 1.0 inside a resting grenade's
blast (d <= 1.5), 0.3 in the safety margin out to DANGER_R; x0.6 while the
threat is only predicted (in flight); fire 0.9 on the cell, 0.2 next to it;
rocket spacing 0.3. So a turtle (0.8) leaves its line only for a grenade at its
feet or fire under it, while close/aggressive (0.15) react to anything.

With enabled=False the layer still observes and counts (baseline KPIs) but
never moves anybody and never changes target choice.

v3 (HeatReflexes, below) replaces these fixed rules with the shared threat
heatmap (threatmap.py). Both versions feed the map every step, so v2 rows get
the same danger KPIs (returns to danger, time in high threat) as v3 rows.
"""
import math
import re
from collections import deque

from battle_tracker import short_name
from battleground import IMPASSABLE, weapon_range
from combat_agent import is_melee
import threatmap as tmap
from threatmap import HIGH, LOW, ThreatMap, DangerKPI, terrain_for

REFLEX_VERSION = 2       # v2: no moves on in-flight predictions, adjacent fire 0.2,
                         # nudges every 600 ticks and none for self-spacing doctrines
FRAG_DEFS = ("Proj_GrenadeFrag",)            # rest on the ground, then explode
IMPACT_DEFS = ("Proj_GrenadeMolotov",)       # burst where they land
FUSE = 90                                    # ticks at rest, measured 88-91
# measure_blast.py: hit 6/7 pawns at d <= 1.5, 0/2 at 2.2, 0/10 at 3.2 (XML radius 1.9).
DANGER_R = 2.5                               # frag danger radius we keep clear of
HIT_R = 1.9                                  # blast reach used to score escapes
FIRE_R = 1.5
SPEED = 0.07                                 # cells/tick, a walking colonist minus trees
START = 15                                   # ticks before a fresh Go here gets moving
OBSERVE_R = 30                               # look for projectiles only if a raider is this close
SEARCH = 8                                   # cells searched for a safe spot
CARRIER_WORDS = ("doomsday", "rocket launcher")
CARRIER_R = 45                               # carriers this close to the squad: keep spacing
SPACING = 4.5
NUDGE = 3
NUDGE_EVERY = 600                            # ticks between nudges of one pawn
SPACING_SEV = 0.3
PREDICTED = 0.6
PREDICT_MOVES = False                        # act on in-flight landing predictions
# Doctrine viscosity: minimum severity that makes the reflex move a pawn.
VISCOSITY = {"b1": 0.15, "close": 0.15, "spread": 0.3, "doctrine": 0.3, "kite": 0.3,
             "turtle": 0.8}
THROW_RE = re.compile(r"\b(launched|flung|threw|tossed|lobbed|hurled)\b")


def frag_damage_entries(rm, pid, name):
    """Battle-log entries in which a frag grenade hurt pawn `name` (the throw
    itself, 'X flung her frag grenade at Y', is not damage)."""
    out = []
    for e in rm.call("get_pawn", id=pid, tab="log").get("entries", []):
        text = e.get("text", "")
        m = re.search(r"frag grenades?\b(.*)", text)
        if m and not THROW_RE.search(text) and f"{name}'s" in m.group(1):
            out.append(e)
    return out


class TiledGrid:
    """Passability from get_area ascii, fetched in 50x50 tiles only when needed."""
    TILE = 50

    def __init__(self, rm, size=250):
        self.rm, self.size, self.tiles = rm, size, {}

    def passable(self, x, z):
        if not (0 <= x < self.size and 0 <= z < self.size):
            return False
        key = (x // self.TILE, z // self.TILE)
        if key not in self.tiles:
            tx, tz = key[0] * self.TILE, key[1] * self.TILE
            bx, bz = min(tx + self.TILE, self.size) - 1, min(tz + self.TILE, self.size) - 1
            rows = self.rm.call("get_area", minX=tx, minZ=tz, maxX=bx, maxZ=bz,
                                render="ascii")["grid"]
            self.tiles[key] = (tx, bz, rows)                 # rows come north (max z) first
        tx, bz, rows = self.tiles[key]
        return rows[bz - z][x - tx] not in IMPASSABLE


class Reflexes:
    version = REFLEX_VERSION

    def __init__(self, rm, threshold, enabled=True, spacing=True, terrain=None):
        self.rm, self.threshold, self.enabled, self.spacing = rm, threshold, enabled, spacing
        self.map = ThreatMap(terrain or tmap.Terrain(rm))
        self.danger = DangerKPI()
        self.mapped = set()        # pids the map positioned this step (v3 doctrines)
        self.modes = {"auto": 0, "map": 0, "reflex": 0, "other": 0}
        self.last_mode = {}        # pid -> who positioned it last step (return attribution)
        self.rx_last = None
        self.grid = TiledGrid(rm)
        self.nades = {}            # projectile id -> track
        self.until = {}            # pid -> tick until which the reflex owns the pawn
        self.dest = {}             # pid -> safe cell it was sent to
        self.nudged = {}           # pid -> tick of last spacing nudge
        self.weapon = {}           # hostile id -> weapon label (cached)
        self.fire = []
        self.carriers = []
        self.k = {k: 0 for k in ("frags_seen", "molotovs_seen", "frags_exploded",
                                 "in_zone_at_landing", "in_blast_at_landing", "escaped",
                                 "stayed_in_blast", "lost_track",
                                 "moves", "moves_frag", "moves_predicted", "moves_fire",
                                 "nudges", "trapped", "too_late", "ignored_viscous",
                                 "predictions", "predictions_right", "observe_steps",
                                 "prediction_sightings")}
        self.names, self.log0, self.hits, self.last_pos = {}, {}, {}, {}

    # ------------------------------------------------------------ episode
    def start(self, squad_ids):
        """Remember each squad pawn's old frag-damage log entries (theme_base pawns
        fought before) so kpis() counts only this episode's hits."""
        for t in self.rm.call("list_things", category="pawn", faction="player", confirm=True,
                              verbose=True)["things"]:
            if t["id"] in squad_ids:
                self.names[t["id"]] = short_name(t.get("label"))
        for pid, name in self.names.items():
            self.log0[pid] = {(e["tick"], e["text"])
                              for e in frag_damage_entries(self.rm, pid, name)}

    def _harvest(self, pid):
        """Collect new frag-damage entries of one squad pawn. Done right after each
        nearby blast too: a pawn that dies later has no log to read at the end."""
        try:
            got = {(e["tick"], e["text"])
                   for e in frag_damage_entries(self.rm, pid, self.names[pid])}
        except Exception:
            return
        self.hits.setdefault(pid, set()).update(got - self.log0.get(pid, set()))

    def kpis(self):
        for pid in self.names:
            self._harvest(pid)
        hit_pawns = sum(bool(v) for v in self.hits.values())
        hit_entries = sum(len(v) for v in self.hits.values())
        return {f"rx_{k}": v for k, v in self.k.items()} | {
            "rx_version": self.version, "rx_revision": getattr(self, "revision", None),
            "rx_enabled": self.enabled, "rx_threshold": self.threshold,
            "rx_frag_hit_pawns": hit_pawns, "rx_frag_hit_entries": hit_entries} \
            | self.map.summary() | self.danger.summary() \
            | {f"steps_{m}": n for m, n in self.modes.items()}

    # ------------------------------------------------------------ heatmap
    def _map_update(self, pos, hostiles, now):
        """Feed the threat map (both versions) and the danger KPIs."""
        frags = [(rec["pos"], rec["here"] - rec["half_step"] + FUSE)
                 for rec in self.nades.values() if rec["frag"]]
        if self.map.cost["steps"]:
            self.danger.pre(self.map, pos)           # judged on last step's map
        self.map.update(pos, hostiles, self.weapon, now, frags, self.fire)
        dt = now - self.rx_last if self.rx_last is not None else 0
        self.rx_last = now
        self.danger.observe(self.map, pos, now, dt)
        # Attribute this step's returns to whoever positioned the pawn last step.
        for pid, kind in self.danger.events:
            mode = self.last_mode.get(pid, "other")
            key = f"returns_{mode}"
            self.k[key] = self.k.get(key, 0) + 1

    def count_modes(self, fighters, auto_ids, owned=()):
        """Per pawn-step in contact: who positioned it - the reflex, the map,
        RimMolt's Auto attack, or nothing (standing / walking a doctrine order)."""
        hs = self.map.hostiles
        for c in fighters:
            p = tuple(c["pos"])
            pid = c["id"]
            m = ("reflex" if pid in owned or pid in self.until else "map" if pid in self.mapped
                 else "auto" if pid in auto_ids else "other")
            self.last_mode[pid] = m
            if not any(math.dist(p, h["c"]) <= 30 for h in hs):
                continue
            self.modes[m] += 1

    def forbidden(self, pid):
        """v2 has no hysteresis."""
        return set()

    def place(self, c, hostiles, target, now, fallback="kill"):
        """v2 has no map positioning: the doctrine keeps the pawn."""
        return False

    def slot_ok(self, pid, cell):
        return True

    def better_slot(self, c, slot, taken):
        return None

    def focus_danger(self, c, hostiles):
        return False

    # ------------------------------------------------------------ rockets
    def _update_carriers(self, hostiles):
        for h in hostiles:
            if h["id"] not in self.weapon:
                self.weapon[h["id"]] = (self.rm.call("get_pawn", id=h["id"]).get("weapon")
                                        or "").lower()
        self.carriers = [h for h in hostiles
                         if any(w in self.weapon[h["id"]] for w in CARRIER_WORDS)]

    def priority_target(self, p, hostiles, fallback, reach=35):
        """Rocket carriers first (their shots can't be dodged): the nearest carrier
        within `reach` of p, else `fallback`. Off when the layer is disabled."""
        if not self.enabled:
            return fallback
        near = [h for h in self.carriers if math.dist(p, (h["x"], h["z"])) <= reach]
        return min(near, key=lambda h: math.dist(p, (h["x"], h["z"]))) if near else fallback

    # ------------------------------------------------------------ main
    def step(self, fighters, hostiles, now, step_ticks):
        """fighters: dicts with id/pos; hostiles: live raiders with id/x/z.
        Returns the ids the reflex owns this step (moved now or still dodging)."""
        pos = {c["id"]: tuple(c["pos"]) for c in fighters}
        self._update_carriers(hostiles)
        close = any(math.dist(p, (h["x"], h["z"])) <= OBSERVE_R
                    for p in pos.values() for h in hostiles)
        if close or self.nades or self.fire:
            self.k["observe_steps"] += 1
            self._observe(pos, now, step_ticks)
        self.mapped = set()
        self._map_update(pos, hostiles, now)
        zones = self._zones(pos, now, step_ticks)
        for pid in [p for p, t in self.until.items() if t <= now or p not in pos]:
            self.until.pop(pid)
            self.dest.pop(pid, None)
        moved = set()
        for pid, p in pos.items():
            sev, deadline, kind = 0.0, math.inf, None
            for z in zones:
                s = self._severity(p, z)
                if s > 0:
                    deadline = min(deadline, z["deadline"])
                if s > sev:
                    sev, kind = s, z["kind"]
            if sev <= 0:
                continue
            if sev < self.threshold:
                self.k["ignored_viscous"] += 1
                continue
            if pid in self.dest and self._safe(self.dest[pid], zones):
                continue                        # already on its way to a safe cell
            if not self.enabled:
                continue
            cell, why = self._safe_cell(p, pos, zones, hostiles, deadline - now)
            if cell is None:
                self.k[why] += 1                # 'trapped' (no safe cell) or 'too_late'
                print(f"   rx t={now}: {pid} {kind} sev {sev:.2f} {why}, {deadline - now:.0f} ticks left")
                continue
            if self._goto(pid, cell):
                moved.add(pid)
                self.dest[pid] = cell
                self.until[pid] = min(deadline + 10, now + 120)
                self.k["moves"] += 1
                self.k[f"moves_{kind}"] += 1
        if self.enabled and self.spacing and self.carriers and SPACING_SEV >= self.threshold:
            moved |= self._spread_out(pos, hostiles, now)
        return moved | set(self.until)

    # ------------------------------------------------------------ observe
    def _observe(self, pos, now, step_ticks):
        cur = {}
        for d in FRAG_DEFS + IMPACT_DEFS:
            for t in self.rm.call("list_things", category="all", defName=d, confirm=True,
                                  verbose=True)["things"]:
                cur[t["id"]] = (d, (t["x"], t["z"]))
        # confirm=True: a big fire (molotovs on forest) makes the list "largeOutput"
        # with no 'things' key, which cost 37 agent steps in 2 v3b grenadier episodes.
        self.fire = [(t["x"], t["z"]) for t in self.rm.call(
            "list_things", category="all", defName="Fire", confirm=True,
            verbose=True)["things"]]
        for tid, (d, p) in cur.items():
            rec = self.nades.get(tid)
            frag = d in FRAG_DEFS
            if rec is None:
                rec = self.nades[tid] = {"frag": frag, "pos": p, "here": now,
                                         "moving": None, "heading": None, "pred": None}
                self.k["frags_seen" if frag else "molotovs_seen"] += 1
                rec["zone_first"] = self._in(pos, p, DANGER_R)
                rec["blast_first"] = self._in(pos, p, HIT_R)
            elif p != rec["pos"]:
                rec.update(heading=(p[0] - rec["pos"][0], p[1] - rec["pos"][1]),
                           pos=p, here=now, moving=True)
                rec["zone_first"] = self._in(pos, p, DANGER_R)
                rec["blast_first"] = self._in(pos, p, HIT_R)
                rec["pred"] = self._predict(rec, pos)
                self.k["prediction_sightings"] += bool(rec["pred"])
            else:
                rec["moving"] = False
            rec["half_step"] = step_ticks / 2
            rec["hit_last"] = self._in(pos, p, HIT_R)
            rec["present"] = set(pos)
        self.last_pos = dict(pos)
        for tid in [t for t in self.nades if t not in cur]:
            rec = self.nades.pop(tid)
            if rec.get("pred_final"):           # scored per projectile, at its last cell
                self.k["predictions"] += 1
                self.k["predictions_right"] += math.dist(rec["pred_final"], rec["pos"]) <= DANGER_R
            if not rec["frag"]:
                continue
            self.k["frags_exploded"] += 1
            # 'Landing' = first sighting at its final cell; 'escaped' = was inside the
            # blast reach then, outside it at the last sighting before the explosion.
            blast = rec["blast_first"]
            self.k["in_zone_at_landing"] += len(rec["zone_first"])
            self.k["in_blast_at_landing"] += len(blast)
            self.k["escaped"] += len((blast & rec["present"]) - rec["hit_last"])
            self.k["stayed_in_blast"] += len(blast & rec["hit_last"])
            self.k["lost_track"] += len(blast - rec["present"])
            near = [pid for pid in rec["present"] if pid in self.names
                    and math.dist(self.last_pos.get(pid, (-99, -99)), rec["pos"]) <= DANGER_R + 1]
            for pid in near:
                self._harvest(pid)
            if blast:
                print(f"   rx t={now}: frag at {rec['pos']} blew: in blast at landing "
                      f"{len(blast)}, still in at last sight {len(blast & rec['hit_last'])}")
        for rec in self.nades.values():                     # last prediction before landing
            if rec["pred"]:
                rec["pred_final"] = rec["pred"]

    @staticmethod
    def _in(pos, c, r):
        return {pid for pid, p in pos.items() if math.dist(p, c) <= r}

    @staticmethod
    def _predict(rec, pos):
        """Squad pawn closest to the forward ray of the last two sightings (within
        2 cells sideways, ahead of the projectile): thrown grenades aim at a pawn."""
        hx, hz = rec["heading"]
        n = math.hypot(hx, hz)
        if not n:
            return None
        ux, uz = hx / n, hz / n
        best, best_off = None, 2.0
        for p in pos.values():
            ax, az = p[0] - rec["pos"][0], p[1] - rec["pos"][1]
            along = ax * ux + az * uz
            off = abs(ax * uz - az * ux)
            if along > 0 and off <= best_off:
                best, best_off = p, off
        return best

    def _zones(self, pos, now, step_ticks):
        zones = []
        for rec in self.nades.values():
            if rec["frag"]:
                # Wherever a frag is now it may already be at rest: a sighting that
                # moved since the last one has landed by now about 1 time in 3 at a
                # 30-tick cycle, and waiting for a second sighting at the same cell
                # leaves ~45 ticks, too little to walk 3 cells. So the fuse runs from
                # the first sighting at this cell (minus half a step, the mean lag).
                zones.append({"c": rec["pos"], "r": DANGER_R, "mult": 1.0,
                              "deadline": rec["here"] - rec["half_step"] + FUSE,
                              "kind": "frag"})
            if PREDICT_MOVES and rec["pred"] and rec["moving"]:
                # Molotovs burst on landing; after two sightings in flight (>= 30
                # ticks of a 90-105 tick flight) ~60 ticks remain on average.
                zones.append({"c": rec["pred"], "r": DANGER_R, "mult": PREDICTED,
                              "deadline": now + (FUSE if rec["frag"] else 60),
                              "kind": "predicted"})
        for f in self.fire:
            zones.append({"c": f, "r": FIRE_R, "mult": 1.0, "deadline": math.inf,
                          "kind": "fire"})
        return zones

    @staticmethod
    def _severity(p, z):
        d = math.dist(p, z["c"])
        if d > z["r"]:
            return 0.0
        if z["kind"] == "fire":
            return 0.9 if d < 0.5 else 0.2
        return (1.0 if d <= 1.5 else 0.3) * z["mult"]

    @staticmethod
    def _safe(cell, zones):
        return all(math.dist(cell, z["c"]) > z["r"] for z in zones)

    # ------------------------------------------------------------ act
    def _safe_cell(self, p, pos, zones, hostiles, budget):
        """Walkable cell outside every zone, not taken by a squadmate, reachable
        within `budget` ticks; among those, one not closer to the raiders if
        possible, then the nearest. -> (cell, None) or (None, reason)."""
        taken = set(pos.values()) | set(self.dest.values())

        def enemy_d(c):
            return min((math.dist(c, (h["x"], h["z"])) for h in hostiles), default=99)
        here = enemy_d(p)
        start = (round(p[0]), round(p[1]))
        seen, q, best, best_key, any_safe = {start}, deque([(start, 0)]), None, None, False
        while q:
            c, n = q.popleft()
            if n and c not in taken and self._safe(c, zones):
                any_safe = True
                if START + math.dist(c, p) / SPEED <= budget:
                    key = (enemy_d(c) < here - 0.5, math.dist(c, p), -enemy_d(c))
                    if best_key is None or key < best_key:
                        best, best_key = c, key
            if n >= SEARCH:
                continue
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    nb = (c[0] + dx, c[1] + dz)
                    if nb not in seen and self.grid.passable(*nb):
                        seen.add(nb)
                        q.append((nb, n + 1))
        if best:
            return best, None
        return None, ("too_late" if any_safe else "trapped")

    def _goto(self, pid, cell):
        try:
            r = self.rm.call("order_pawn", id=pid, x=cell[0], z=cell[1], command="Go here")
        except Exception:
            return False
        return r.get("ok", True) and "error" not in r

    def _spread_out(self, pos, hostiles, now):
        """Rocket carriers about: nudge pawns with a squadmate closer than SPACING
        NUDGE cells away from their close neighbours (at most every NUDGE_EVERY)."""
        if not any(math.dist(p, (h["x"], h["z"])) <= CARRIER_R
                   for p in pos.values() for h in self.carriers):
            return set()
        moved = set()
        for pid, p in pos.items():
            if pid in self.until or now - self.nudged.get(pid, -NUDGE_EVERY) < NUDGE_EVERY:
                continue
            near = [q for o, q in pos.items() if o != pid and math.dist(p, q) < SPACING]
            if not near:
                continue
            vx = sum(p[0] - q[0] for q in near)
            vz = sum(p[1] - q[1] for q in near)
            n = math.hypot(vx, vz) or 1.0
            if math.hypot(vx, vz) < 0.3:          # stacked: any direction
                vx, vz, n = 1.0, 0.0, 1.0
            want = (round(p[0] + vx / n * NUDGE), round(p[1] + vz / n * NUDGE))
            cell = next((c for c in _ring(want, 2) if self.grid.passable(*c)
                         and c not in pos.values()), None)
            if cell and self._goto(pid, cell):
                self.nudged[pid] = now
                self.k["nudges"] += 1
                moved.add(pid)
        return moved


def _ring(c, r):
    """Cells within r of c, nearest first."""
    cells = [(c[0] + dx, c[1] + dz) for dx in range(-r, r + 1) for dz in range(-r, r + 1)]
    return sorted(cells, key=lambda x: math.dist(x, c))


# ---------------------------------------------------------------- reflex v3
# Doctrine viscosity in threat units (threatmap.py): a pawn moves when the best
# reachable cell beats its own by more than threshold + move cost. Turtle (3.0)
# leaves its line for a frag (5-10) or fire under it (6), not for a throw zone (3),
# adjacent fire (1.5) or some clumping: its slots handle those. Aggressive and
# close (0.5) take any clearly better nearby cell; spread, focus and kite sit
# between (1.0).
VISCOSITY_V3 = {"b1": 0.5, "close": 0.5, "spread": 1.0, "doctrine": 1.0, "kite": 1.0,
                "turtle": 3.0}
MOVE_BASE = 0.5       # any move: a fresh Go here costs ~15 ticks before it walks, no aimed shots
SHOOT_COST = 0.5      # the pawn is shooting now: moving breaks its line of fire
POS_R = 6             # doctrine positioning: steps searched around the pawn
BACK_R = 12           # fallback: how far a pawn may step back out of a throw zone
REPLAN_TICKS = 150    # a pawn walking to a map cell is left alone this long


class HeatReflexes(Reflexes):
    """Reflex v3: one rule over the threat map instead of per-hazard rules.

    A pawn moves iff threat(here) - threat(best reachable cell) > threshold +
    move_cost, where move_cost = MOVE_BASE + SHOOT_COST if it is shooting + the
    fire value it gives up (raiders it could shoot from here but not there). Only
    cells it reaches before the dominant threat lands count: with a resting frag
    over its cell, START + walk / SPEED must fit in the remaining fuse.

    Hysteresis: the cell a pawn fled and its 8 neighbours (d <= 1.5, the same
    neighbourhood the returns_to_danger KPI uses) are forbidden to that pawn, in
    our searches and the doctrines' slot choice, until the fled cell's
    (remembered, decaying) hazard falls below the LOW watermark. (v3a forbade the
    exact cell plus neighbours that were >= LOW at flight time and released each
    cell on its own hazard, so a pawn could settle next to a still-hot fled cell.)

    No rocket nudges: spacing comes from the map's clumping term, which scores
    candidate cells but never triggers a move by itself (v3b). Doctrines ask
    place() before handing a pawn to Auto attack (see place)."""
    version = 3
    revision = "3b"   # 3a: exact-cell hysteresis, clumping in the move gate (rows of
                      # agent versions b1 3 / spread 3 / turtle 6 in threatmap_check.jsonl)

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.forbid = {}        # pid -> cells it fled (hysteresis centres)
        self.pdest = {}         # pid -> (cell, tick): doctrine map destination
        self.firing = {}        # pid -> raider id under a Fire at order
        self.ranges = {}        # pid -> our weapon range (0 = melee)
        self.k.update({k: 0 for k in (
            "moves_throw", "moves_rocket", "stays", "map_moves", "fire_at", "fallback_kill",
            "fallback_back", "fallback_none", "forbidden_cells", "reslots")})

    def _range(self, c):
        pid = c["id"]
        if pid not in self.ranges:
            w = c.get("weapon")
            if w is None:
                w = self.rm.call("get_pawn", id=pid).get("weapon")
            self.ranges[pid] = 0 if not w or is_melee(w) else weapon_range(w)
        return self.ranges[pid]

    def _taken(self, pid):
        m = self.map
        return ({q for o, q in m.pos.items() if o != pid}
                | {q for o, q in m.reserved.items() if o != pid}
                | {q for o, q in self.dest.items() if o != pid})

    def _dangerous(self, h):
        w = self.weapon.get(h["id"], "")
        return any(k in w for k in tmap.THROWER_WORDS + CARRIER_WORDS)

    def threat_target(self, p, hostiles, fallback, reach):
        """Shared target helper: the nearest grenade/molotov thrower we can shoot
        (in reach, LOS), else the nearest rocket carrier in reach, else fallback."""
        def near(ws):
            hs = [h for h in hostiles if any(k in self.weapon.get(h["id"], "") for k in ws)
                  and math.dist(p, (h["x"], h["z"])) <= reach]
            return min(hs, key=lambda h: math.dist(p, (h["x"], h["z"]))) if hs else None
        hs = [h for h in hostiles if any(k in self.weapon.get(h["id"], "") for k in tmap.THROWER_WORDS)
              and math.dist(p, (h["x"], h["z"])) <= reach
              and self.map.t.los((round(p[0]), round(p[1])), (h["x"], h["z"]))]
        if hs:
            return min(hs, key=lambda h: math.dist(p, (h["x"], h["z"])))
        return near(CARRIER_WORDS) or fallback

    def priority_target(self, p, hostiles, fallback, reach=35):
        if not self.enabled:
            return fallback
        return self.threat_target(p, hostiles, fallback, reach)

    # ------------------------------------------------------------ main
    def step(self, fighters, hostiles, now, step_ticks):
        pos = {c["id"]: tuple(c["pos"]) for c in fighters}
        info = {c["id"]: c for c in fighters}
        self._update_carriers(hostiles)
        close = any(math.dist(p, (h["x"], h["z"])) <= OBSERVE_R
                    for p in pos.values() for h in hostiles)
        if close or self.nades or self.fire:
            self.k["observe_steps"] += 1
            self._observe(pos, now, step_ticks)
        self.mapped = set()
        self._map_update(pos, hostiles, now)
        m = self.map
        alive = {h["id"] for h in hostiles}
        self.firing = {k: v for k, v in self.firing.items() if v in alive and k in pos}
        for pid in [p for p, t in self.until.items() if t <= now or p not in pos]:
            self.until.pop(pid)
            self.dest.pop(pid, None)
        for cells in self.forbid.values():           # hysteresis: release below LOW
            cells -= {c for c in cells if m.hazard(c) < LOW}
        moved = set()
        for pid, p in pos.items():
            cur = (round(p[0]), round(p[1]))
            if pid in self.until:
                dest = self.dest[pid]
                if m.hazard(dest, pid) < HIGH and not (m.frag(cur) and math.dist(cur, dest) < 1.5):
                    continue                          # still walking somewhere safe
                self.until.pop(pid)
                self.dest.pop(pid, None)
            # v3b: the gate ignores rockets (base and clumping): they can't be dodged,
            # and v3a's clump-driven moves (100/episode for aggressive on the grenadier
            # theme) were the v2 nudges again. Clumping only shapes WHERE pawns go.
            gate = m.hazard(cur) - m.rocket_base(cur)
            if gate <= 0:
                continue
            if gate < self.threshold:
                self.k["ignored_viscous"] += 1
                continue
            if not self.enabled:
                continue
            budget = m.frag_deadline(cur) - now
            rng = self._range(info[pid])
            best, bi = m.best_cell_near(pid, p, SEARCH, rng=rng, forbid=self.forbidden(pid),
                                        taken=self._taken(pid), budget=budget, speed=SPEED,
                                        start=START)
            if m.frag(cur) and (best is None or m.frag(best)):
                free = any(not m.frag(c) for c in m.reachable(cur, SEARCH))
                why = "too_late" if free else "trapped"
                self.k[why] += 1
                print(f"   rx3 t={now}: {pid} frag {why}, {budget:.0f} ticks left")
            if best is None:
                continue
            shooting = (info[pid].get("job") or "").startswith("attacking")
            cost = (MOVE_BASE + SHOOT_COST * shooting
                    + max(0.0, m.fire_value(cur, rng) - bi["fire"]))
            th = m.threat(cur, pid)
            if best == cur or th - bi["threat"] <= self.threshold + cost:
                self.k["stays"] += 1
                if m.frag(cur) >= tmap.W_FRAG:
                    print(f"   rx3 t={now}: {pid} stays in frag blast: gain "
                          f"{th - bi['threat']:.1f} <= {self.threshold} + {cost:.1f}")
                continue
            kind = m.dominant(cur, pid) or "throw"
            if not self._goto(pid, best):
                continue
            moved.add(pid)
            self.dest[pid] = m.reserved[pid] = best
            hold = min(START + bi["walk"] / SPEED + 15, 150)
            if budget < math.inf:
                hold = max(hold, min(budget + 10, 150))     # stay out until it blows
            self.until[pid] = now + hold
            fl = self.forbid.setdefault(pid, set())
            self.k["forbidden_cells"] += cur not in fl
            fl.add(cur)
            self.k["moves"] += 1
            self.k[f"moves_{kind}"] += 1
            self.pdest.pop(pid, None)
            self.firing.pop(pid, None)
        return moved | set(self.until)

    # ------------------------------------------------------------ doctrine positioning
    def forbidden(self, pid):
        """Cells this pawn may not pick: within 1.5 of a fled cell still >= LOW."""
        return {(f[0] + dx, f[1] + dz) for f in self.forbid.get(pid, ())
                for dx in (-1, 0, 1) for dz in (-1, 0, 1)}

    def _elevated(self, pid, p):
        m = self.map
        if m.local_hazard(p, pid, minus_rocket=True) >= tmap.ELEVATED:
            return True
        return any(math.dist(p, c) <= 6 for c in self.forbid.get(pid, ()))

    def place(self, c, hostiles, target, now, fallback="kill"):
        """Doctrine hook, asked before a pawn is handed to Auto attack (which picks
        its own cover cell and can't see the map). Inside an elevated-threat area
        (hazard >= ELEVATED within 4 cells, or a cell it fled nearby) the map picks
        the cell (Go here) within POS_R that maximises -threat + fire value while
        seeing the target, and the pawn fires from there (fire at will, or Fire at
        a thrower/carrier in reach). If no such cell is below HIGH, `fallback`:
        'kill' = Fire at the nearest thrower/carrier we can hit, else step back;
        'back' = step back out of the zone (BACK_R) keeping it in weapon range,
        else shoot it. Returns True if the map handled the pawn this step."""
        if not self.enabled:
            return False
        rng = self._range(c)
        pid, m = c["id"], self.map
        p = (round(c["pos"][0]), round(c["pos"][1]))
        if not rng or not self._elevated(pid, p):
            self.pdest.pop(pid, None)
            self.firing.pop(pid, None)
            return False
        self.mapped.add(pid)
        d = self.pdest.get(pid)
        if d and d[0] != p and now - d[1] < REPLAN_TICKS and m.hazard(d[0], pid) < HIGH:
            return True                               # still walking to its map cell
        tgt = self.threat_target(p, hostiles, target, rng)
        seen = tgt if tgt and math.dist(p, (tgt["x"], tgt["z"])) <= rng + POS_R else None
        forbid, taken = self.forbidden(pid), self._taken(pid)
        best, bi = m.best_cell_near(pid, p, POS_R, must_see=seen, rng=rng, forbid=forbid,
                                    taken=taken)
        if best is None and seen:
            best, bi = m.best_cell_near(pid, p, POS_R, rng=rng, forbid=forbid, taken=taken)
        if best is None or bi["hazard"] >= HIGH:
            return self._fallback(c, p, hostiles, tgt, rng, fallback, now)
        here = -m.threat(p, pid) + m.fire_value(p, rng, seen)
        if best != p and bi["score"] - here > self.threshold + MOVE_BASE:
            self._move(pid, best, now)
        else:
            self._fire_at(pid, p, tgt, rng)
        return True

    def _fallback(self, c, p, hostiles, tgt, rng, how, now):
        m, pid = self.map, c["id"]
        danger = [h for h in hostiles if self._dangerous(h)]
        src = min(danger, key=lambda h: math.dist(p, (h["x"], h["z"]))) if danger else tgt
        for step in (("kill", "back") if how == "kill" else ("back", "kill")):
            if step == "kill" and src and self._can_hit(p, src, rng):
                self.k["fallback_kill"] += 1
                self._fire_at(pid, p, src, rng)
                return True
            if step == "back":
                see = src if src and math.dist(p, (src["x"], src["z"])) <= rng + BACK_R else None
                best, bi = m.best_cell_near(pid, p, BACK_R, must_see=see, rng=rng,
                                            forbid=self.forbidden(pid), taken=self._taken(pid))
                if best and best != p and bi["hazard"] < HIGH:
                    self.k["fallback_back"] += 1
                    self._move(pid, best, now)
                    return True
        self.k["fallback_none"] += 1
        return True

    def _can_hit(self, p, h, rng):
        hc = (h["x"], h["z"])
        return math.dist(p, hc) <= rng and self.map.t.los(p, hc)

    def _move(self, pid, cell, now):
        if self._goto(pid, cell):
            self.pdest[pid] = (cell, now)
            self.map.reserved[pid] = cell
            self.firing.pop(pid, None)
            self.k["map_moves"] += 1

    def _fire_at(self, pid, p, h, rng):
        """Fire at a raider in reach (once per target); otherwise fire at will."""
        if h is None or self.firing.get(pid) == h["id"] or not self._can_hit(p, h, rng):
            return
        try:
            r = self.rm.call("order_pawn", id=pid, targetId=h["id"], command="Fire at")
        except Exception:
            return
        if r.get("ok"):
            self.firing[pid] = h["id"]
            self.k["fire_at"] += 1

    def focus_danger(self, c, hostiles):
        """A pawn holding a cell: Fire at the nearest thrower/carrier it can hit."""
        if not self.enabled:
            return False
        rng = self._range(c)
        p = (round(c["pos"][0]), round(c["pos"][1]))
        h = self.threat_target(p, hostiles, None, rng) if rng else None
        if h is None or not self._can_hit(p, h, rng):
            return False
        self._fire_at(c["id"], p, h, rng)
        return True

    # ------------------------------------------------------------ turtle slots
    def slot_ok(self, pid, cell):
        return (not self.enabled or tuple(cell) not in self.forbidden(pid)
                and self.map.hazard(cell, pid) < HIGH)

    def better_slot(self, c, slot, taken):
        """A cell within 4 of `slot` that is clearly safer (hazard at least 1 lower,
        below HIGH, not forbidden), or None."""
        if not self.enabled:
            return None
        m, pid = self.map, c["id"]
        best, bi = m.best_cell_near(pid, c["pos"], 4, rng=self._range(c), origin=slot,
                                    forbid=self.forbidden(pid), taken=taken)
        if best and bi["hazard"] < HIGH and bi["hazard"] <= m.hazard(slot, pid) - 1:
            self.k["reslots"] += 1
            return best
        return None


LATEST_VERSION = HeatReflexes.version


def attach(agent, rm, manifest):
    """Give an agent its reflex layer (threshold by doctrine name). The harness
    sets agent.reflex (on/off) and agent.rx_version (2 or 3) before reset."""
    terrain = terrain_for(rm, manifest["save"])
    if getattr(agent, "rx_version", LATEST_VERSION) >= 3:
        rx = HeatReflexes(rm, VISCOSITY_V3.get(agent.name, 1.0), getattr(agent, "reflex", True),
                          spacing=False, terrain=terrain)
    else:
        rx = Reflexes(rm, VISCOSITY.get(agent.name, 0.3), getattr(agent, "reflex", True),
                      spacing=not getattr(agent, "own_spacing", False), terrain=terrain)
    rx.start({p["id"] for p in manifest["squad"]})
    return rx
