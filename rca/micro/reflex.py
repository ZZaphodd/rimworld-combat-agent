"""Reflex framework: hazards -> severity per pawn -> move iff severity reaches
the doctrine's viscosity, to a safe cell reachable in time; the reflex then
owns the pawn until the hazard is over.

Frag dodge (LESSONS §1, results/hazards.md, reflex_report.md):
  * Proj_GrenadeFrag rests ~90 ticks (88-91) and then blows. The fuse clock
    starts at the first sighting at the grenade's current cell minus half a step
    (a moving sighting has landed ~1 time in 3 at a 30-tick cycle; waiting for a
    second sighting leaves too little time to walk 3 cells).
  * Blast reach 1.9 (XML; 0/32 hit at d >= 2.2): severity 1.0 within 1.9, 0.3
    in the margin out to 2.5.
  * Safe cell: walkable, outside every hazard, not held or targeted by a
    squadmate, not forbidden to the pawn, reachable before the deadline
    (START + d / SPEED ticks), 8-step BFS; prefer cells not closer to the
    raiders, then the nearest. No reachable cell: `too_late` (a safe cell exists
    but not in time) or `trapped`.
Fire: only fire on the pawn's own cell (severity 0.9). Standing next to fire
does no damage, and moving for it broke Auto attack for nothing.

Ownership: the doctrine skips owned pawns and re-issues its order on release.
A pawn is owned until the hazard is gone (frag blown + 10 ticks, fire out) or
OWN_MAX ticks, whichever comes first, and at least until it can have arrived.
Hysteresis (re-entry): the hazard a pawn fled stays forbidden to it while the
hazard lives; doctrines ask cell_ok() before sending it somewhere, and a pawn
seen back inside counts as a re-entry (KPI) and is dodged again.
"""
import math
import re
from collections import deque

from ..rimmolt import things_of

MICRO_VERSION = 4        # stored as reflex_version; 1-3 are legacy/reflexes.py
FRAG_DEF, FIRE_DEF, BLAST_DEF = "Proj_GrenadeFrag", "Fire", "Explosion"
FUSE = 90
HIT_R, DANGER_R = 1.9, 2.5
SEV_BLAST, SEV_MARGIN, SEV_FIRE = 1.0, 0.3, 0.9
SPEED, START = 0.07, 15      # cells/tick walking among trees; ticks before a Go here moves
SEARCH = 8
OBSERVE_R = 30               # query projectiles only with a raider this close
OWN_MAX = 150
# Doctrine viscosity (severity needed to move); v2 values, LESSONS §1.
VISCOSITY = {"amove": 0.15, "close": 0.15, "spread": 0.3, "doctrine": 0.3, "kite": 0.3,
             "turtle": 0.8}
THROW_RE = re.compile(r"\b(launched|flung|threw|tossed|lobbed|hurled)\b")


def frag_damage_entries(rm, pid, name):
    """Battle-log entries in which a frag grenade hurt pawn `name` (the throw
    'X flung her frag grenade at Y' is not damage). Matched by short name, so
    the caller must check names are unique in the squad (LESSONS bug 11)."""
    out = []
    for e in rm.call("get_pawn", id=pid, tab="log").get("entries", []):
        text = e.get("text", "")
        m = re.search(r"frag grenades?\b(.*)", text)
        if m and not THROW_RE.search(text) and f"{name}'s" in m.group(1):
            out.append(e)
    return out


def severity(p, hz):
    d = math.dist(p, hz["c"])
    if hz["kind"] == "fire":
        return SEV_FIRE if d < 0.5 else 0.0
    if d <= HIT_R:
        return SEV_BLAST
    return SEV_MARGIN if d <= DANGER_R else 0.0


def in_hazard(cell, hz):
    """Cells a dodge must not end on: the full danger disc, or a burning cell."""
    return math.dist(cell, hz["c"]) < (0.5 if hz["kind"] == "fire" else DANGER_R + 1e-9)


class MicroLayer:
    def __init__(self, rm, terrain, threshold, enabled=True, log=print):
        self.rm, self.terrain, self.threshold, self.enabled = rm, terrain, threshold, enabled
        self.log = log
        self.nades = {}       # frag id -> {pos, here, first, half_step, blast_first, ...}
        self.fire = set()
        self.explosions = []
        self.until, self.dest, self.fled = {}, {}, {}   # pid -> tick / cell / [hazard ids]
        self.events = []      # one per exploded frag (drills read these)
        self.moves = []       # one per dodge order
        self.names, self.log0, self.hits = {}, {}, {}
        self._last_pos, self._reentered = {}, set()
        self.k = {k: 0 for k in (
            "observe_steps", "frags_seen", "frags_exploded", "in_zone_at_landing",
            "in_blast_at_landing", "escaped", "stayed_in_blast", "lost_track", "moves",
            "moves_frag", "moves_fire", "too_late", "trapped", "ignored_viscous", "reentries",
            "goto_failed", "threatened", "threatened_escaped")}

    # ------------------------------------------------------------ episode
    def start(self, squad):
        """squad: {pid: short name}. Remember old frag-damage entries (theme_base
        pawns fought before) so hits count only this episode."""
        self.names = dict(squad)
        for pid, name in self.names.items():
            self.log0[pid] = {(e.get("tick"), e["text"])
                              for e in frag_damage_entries(self.rm, pid, name)}

    def harvest(self, pid):
        """New frag-damage entries of one pawn; returns the set added now."""
        try:
            got = {(e.get("tick"), e["text"])
                   for e in frag_damage_entries(self.rm, pid, self.names[pid])}
        except Exception:
            return set()
        new = got - self.log0.get(pid, set()) - self.hits.get(pid, set())
        self.hits.setdefault(pid, set()).update(new)
        return new

    # ------------------------------------------------------------ hazards
    def hazards(self):
        out = [{"id": f, "kind": "frag", "c": r["pos"],
                "deadline": r["here"] - r["half_step"] + FUSE} for f, r in self.nades.items()]
        out += [{"id": ("fire", c), "kind": "fire", "c": c, "deadline": math.inf}
                for c in self.fire]
        return out

    def alive(self, hid):
        return hid in self.nades or (isinstance(hid, tuple) and hid[1] in self.fire)

    def forbidden(self, pid):
        return [h for h in self.hazards() if h["id"] in self.fled.get(pid, ())]

    def cell_ok(self, pid, cell):
        """May a doctrine send `pid` to `cell`? Not into a live frag zone or a
        burning cell (this covers every hazard the pawn fled)."""
        return not any(in_hazard(cell, h) for h in self.hazards())

    # ------------------------------------------------------------ observe
    def _observe(self, pos, now, step_ticks):
        self.k["observe_steps"] += 1
        cur = {t["id"]: (t["x"], t["z"]) for t in things_of(self.rm, FRAG_DEF)}
        self.fire = {(t["x"], t["z"]) for t in things_of(self.rm, FIRE_DEF)}
        self.explosions = [(t["x"], t["z"]) for t in things_of(self.rm, BLAST_DEF)]
        for fid, p in cur.items():
            rec = self.nades.get(fid)
            if rec is None or p != rec["pos"]:
                if rec is None:
                    self.k["frags_seen"] += 1
                    rec = self.nades[fid] = {"first": now, "pos_first": dict(pos)}
                rec.update(pos=p, here=now, blast_first=self._within(pos, p, HIT_R),
                           zone_first=self._within(pos, p, DANGER_R))
            rec["half_step"] = step_ticks / 2
            rec["last_seen"] = now
            rec["hit_last"] = self._within(pos, p, HIT_R)
            rec["present"] = set(pos)
        for fid in [f for f in self.nades if f not in cur]:
            self._exploded(fid, self.nades.pop(fid), pos, now)

    @staticmethod
    def _within(pos, c, r):
        return {pid for pid, p in pos.items() if math.dist(p, c) <= r}

    def _exploded(self, fid, rec, pos, now):
        """'Landing' = first sighting at the final cell; 'escaped' = inside the
        blast reach then, outside it at the last sighting before the blast."""
        self.k["frags_exploded"] += 1
        blast = rec["blast_first"]
        escaped = (blast & rec["present"]) - rec["hit_last"]
        stayed = blast & rec["hit_last"]
        lost = blast - rec["present"]
        # Mode-independent denominator: where pawns stood when the frag was first
        # seen (any cell) vs where it came to rest. A dodging squad leaves on
        # in-flight sightings, so 'in blast at landing' shrinks with the dodge.
        threatened = self._within(rec["pos_first"], rec["pos"], HIT_R)
        self.k["threatened"] += len(threatened)
        self.k["threatened_escaped"] += len((threatened & rec["present"]) - rec["hit_last"])
        self.k["in_zone_at_landing"] += len(rec["zone_first"])
        self.k["in_blast_at_landing"] += len(blast)
        self.k["escaped"] += len(escaped)
        self.k["stayed_in_blast"] += len(stayed)
        self.k["lost_track"] += len(lost)
        hit = {}
        for pid in self.names:
            p = pos.get(pid, self._last_pos.get(pid))
            if pid in blast or (p and math.dist(p, rec["pos"]) <= DANGER_R + 1):
                new = self.harvest(pid)
                if new:
                    hit[pid] = len(new)
        landing = rec["here"] - rec["half_step"]
        self.events.append({
            "frag": fid, "cell": list(rec["pos"]), "first_seen": rec["first"],
            "landed_seen": rec["here"], "landing_est": landing, "gone_seen": now,
            "in_blast": sorted(blast), "in_zone": sorted(rec["zone_first"]),
            "threatened": sorted(threatened),
            "threatened_escaped": sorted((threatened & rec["present"]) - rec["hit_last"]),
            "escaped": sorted(escaped), "stayed": sorted(stayed), "lost_track": sorted(lost),
            "hit": hit,
            "moves": [m for m in self.moves if m["hazard"] == fid]})

    # ------------------------------------------------------------ step
    def step(self, fighters, hostiles, now, step_ticks):
        """fighters: [{id, pos}], hostiles: live raiders. Returns the ids the
        micro layer owns this step; the doctrine leaves them alone."""
        pos = {c["id"]: (round(c["pos"][0]), round(c["pos"][1])) for c in fighters}
        close = any(math.dist(p, (h["x"], h["z"])) <= OBSERVE_R
                    for p in pos.values() for h in hostiles)
        if close or self.nades or self.fire:
            self._observe(pos, now, step_ticks)
        else:
            self.explosions = []
        if self.terrain is not None:
            self.terrain.update(now, fires=self.fire, explosions=self.explosions)
        hz = self.hazards()
        for pid in list(self.until):
            if pid not in pos or now >= self.until[pid] or not any(
                    self.alive(h) for h in self.fled.get(pid, ())):
                self.until.pop(pid)
                self.dest.pop(pid, None)
        for pid in list(self.fled):
            self.fled[pid] = [h for h in self.fled[pid] if self.alive(h)]
        for pid, p in pos.items():
            sev, top = 0.0, None
            for h in hz:
                s = severity(p, h)
                if s > sev:
                    sev, top = s, h
            if top is None:
                continue
            if (top["id"] in self.fled.get(pid, ()) and pid not in self.until
                    and (pid, top["id"]) not in self._reentered):
                self._reentered.add((pid, top["id"]))
                self.k["reentries"] += 1
            if sev < self.threshold:
                self.k["ignored_viscous"] += 1
                continue
            if pid in self.until and pid in self.dest and not any(
                    in_hazard(self.dest[pid], h) for h in hz):
                continue                                   # still walking to a safe cell
            if not self.enabled:
                continue
            deadline = min(h["deadline"] for h in hz if severity(p, h) > 0)
            cells, why = self.safe_cells(pid, p, pos, hz, hostiles, deadline - now)
            if not cells:
                self.k[why] += 1
                continue
            # A Go here can fail (cell taken or unwalkable for the pawn): try the next best.
            cell = next((c for c in cells[:3] if self._goto(pid, c)), None)
            if cell is None:
                self.k["goto_failed"] += 1
                continue
            walk = START + math.dist(cell, p) / SPEED
            end = deadline + 10 if top["kind"] == "frag" else now + walk + 30
            self.until[pid] = min(now + OWN_MAX, max(end, now + walk))
            self.dest[pid] = cell
            self.fled.setdefault(pid, []).append(top["id"])
            self.k["moves"] += 1
            self.k[f"moves_{top['kind']}"] += 1
            self.moves.append({"pid": pid, "tick": now, "hazard": top["id"], "kind": top["kind"],
                               "from": list(p), "to": list(cell), "sev": sev,
                               "left": round(deadline - now, 1) if deadline < math.inf else None})
        self._last_pos = pos
        return set(self.until)

    def safe_cells(self, pid, p, pos, hz, hostiles, budget):
        """Safe cells reachable in time, best first -> (cells, None) or ([], reason)."""
        taken = {q for o, q in pos.items() if o != pid} | {q for o, q in self.dest.items()
                                                           if o != pid}

        def enemy_d(c):
            return min((math.dist(c, (h["x"], h["z"])) for h in hostiles), default=99.0)
        here = enemy_d(p)
        found, any_safe = [], False
        seen, q = {p}, deque([(p, 0)])
        while q:
            c, n = q.popleft()
            if n and c not in taken and not any(in_hazard(c, h) for h in hz):
                any_safe = True
                if START + math.dist(c, p) / SPEED <= budget:
                    found.append(((enemy_d(c) < here - 0.5, math.dist(c, p), -enemy_d(c)), c))
            if n >= SEARCH:
                continue
            for nb in (self.terrain.neighbours(c) if self.terrain else ()):
                if nb not in seen:
                    seen.add(nb)
                    q.append((nb, n + 1))
        if found:
            return [c for _, c in sorted(found)], None
        return [], ("too_late" if any_safe else "trapped")

    def _goto(self, pid, cell):
        try:
            r = self.rm.call("order_pawn", id=pid, x=cell[0], z=cell[1], command="Go here")
        except Exception as e:
            r = {"error": repr(e)}
        ok = r.get("ok", True) and "error" not in r
        if not ok:
            self.goto_errors = (getattr(self, "goto_errors", []) + [str(r.get("error"))[:100]])[-5:]
        return ok

    # ------------------------------------------------------------ KPIs
    def kpis(self):
        for pid in self.names:
            self.harvest(pid)
        return ({f"rx_{k}": v for k, v in self.k.items()}
                | {"rx_version": MICRO_VERSION, "rx_enabled": self.enabled,
                   "rx_threshold": self.threshold,
                   "rx_goto_errors": getattr(self, "goto_errors", []),
                   "rx_frag_hit_pawns": sum(bool(v) for v in self.hits.values()),
                   "rx_frag_hit_entries": sum(len(v) for v in self.hits.values())})
