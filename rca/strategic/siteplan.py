"""Where the squad holds a problem: the strategic layer's pick, one entry per problem (the user,
2026-10-06: even turtle needs the strategic layer to mark where to turtle; rules are too hard for
now, so Claude picks by hand).

A plan file (results/base/plans/<set>_r<N>.json) is frozen once a row cites it; a change goes into
a new revision. Picks use only what is known at the start: the manifest (squad, raid spawn and
composition), the save's map (rca.game.savemap), sites.md and the cases.

    {"format": 1, "for": "scenarios_base2", "by": "claude", "made": "2026-10-06", "basis": "...",
     "problems": {"<problem id>": {
        "site": "Ithfunda east room",          # a name from results/cases/sites.md, or a new one
        "why": "...",                          # the reason, a sentence or two
        "anchor": [x, z],                      # anchor mode: turtle's own planner around it
        "cells": {"<pawn id>": {"cell": [x, z], "role": "front|gun|back", "fire": "will|hold",
                                "name": "...", "weapon": "..."}},   # cells mode: every squad pawn
        "room": [[x0, z0, x1, z1], ...],       # cells mode, optional: an enclosed hold
        "doors": [{"at": [x, z], "hold_open": true}],
        "rear": [[x, z], ...],                 # room: where wounded pawns go
        "notes": "..."}}}

`entry()` is what the agent reads; `validate()` is what tools/site_plan.py check reports.
"""
import hashlib
import json
import math
import statistics
from dataclasses import dataclass, field
from pathlib import Path

FORMAT = 1
ROLES = ("front", "gun", "back")
FIRE = ("will", "hold")
THROWN = ("grenade", "molotov", "incendiary", "emp")     # weapon labels a doorway fight should not throw


class PlanError(Exception):
    pass


@dataclass
class Site:
    pid: str
    site: str
    anchor: tuple
    cells: dict = field(default_factory=dict)     # pawn id -> (x, z)
    roles: dict = field(default_factory=dict)     # pawn id -> role
    hold_fire: set = field(default_factory=set)
    room: list = field(default_factory=list)      # [(x0, z0, x1, z1)]
    doors: list = field(default_factory=list)     # [((x, z), hold_open)]
    rear: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)
    sha: str = ""

    @property
    def mode(self):
        return "cells" if self.cells else "anchor"

    def in_room(self, p, margin=0):
        return any(x0 - margin <= p[0] <= x1 + margin and z0 - margin <= p[1] <= z1 + margin
                   for x0, z0, x1, z1 in self.room)

    def open_doors(self):
        return {c for c, held in self.doors if held}


def sha(entry):
    return hashlib.sha1(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:12]


def load(path):
    from .. import ROOT
    p = Path(path)
    p = p if p.is_absolute() else ROOT / p
    data = json.loads(p.read_text())
    if data.get("format") != FORMAT:
        raise PlanError(f"{path}: format {data.get('format')!r}, want {FORMAT}")
    return data


def _xy(v):
    return (int(v[0]), int(v[1]))


def build(pid, e):
    """A Site from one entry (structure only; validate() checks it against the problem)."""
    cells = {k: _xy(v["cell"]) for k, v in (e.get("cells") or {}).items()}
    anchor = _xy(e["anchor"]) if e.get("anchor") else \
        (round(statistics.median(c[0] for c in cells.values())),
         round(statistics.median(c[1] for c in cells.values()))) if cells else None
    if anchor is None:
        raise PlanError(f"{pid}: neither anchor nor cells")
    return Site(pid=pid, site=e.get("site", ""), anchor=anchor, cells=cells,
                roles={k: v.get("role", "gun") for k, v in (e.get("cells") or {}).items()},
                hold_fire={k for k, v in (e.get("cells") or {}).items() if v.get("fire") == "hold"},
                room=[tuple(r) for r in e.get("room") or []],
                doors=[(_xy(d["at"]), bool(d.get("hold_open"))) for d in e.get("doors") or []],
                rear=[_xy(c) for c in e.get("rear") or []], raw=e, sha=sha(e))


def entry(path, manifest):
    """The Site for this problem from plan file `path`; PlanError if it is missing or invalid."""
    data = load(path)
    pid = manifest["id"]
    e = (data.get("problems") or {}).get(pid)
    if e is None:
        raise PlanError(f"{path}: no entry for {pid}")
    errors, _ = validate(e, manifest)
    if errors:
        raise PlanError(f"{path} {pid}: " + "; ".join(errors))
    return build(pid, e)


def _thrower(weapon):
    return any(w in (weapon or "").lower() for w in THROWN)


def validate(e, manifest, smap=None):
    """(errors, warnings) for one entry. With smap (rca.game.savemap.SaveMap of the problem's
    save) the cells, doors and paths are checked on the map too."""
    errs, warns = [], []
    for k in ("site", "why"):
        if not e.get(k):
            errs.append(f"no {k}")
    try:
        s = build(manifest["id"], e)
    except (PlanError, KeyError, TypeError, ValueError) as x:
        return errs + [f"bad entry: {x}"], warns
    squad = {p["id"]: p for p in manifest["squad"]}
    if s.cells:
        if set(s.cells) != set(squad):
            errs.append(f"cells cover {sorted(set(s.cells) & set(squad))}, missing {sorted(set(squad) - set(s.cells))}, "
                        f"unknown {sorted(set(s.cells) - set(squad))}")
        if len(set(s.cells.values())) != len(s.cells):
            errs.append("two pawns on one cell")
        for k, v in e["cells"].items():
            if v.get("role", "gun") not in ROLES:
                errs.append(f"{k}: role {v.get('role')!r}")
            if v.get("fire", "will") not in FIRE:
                errs.append(f"{k}: fire {v.get('fire')!r}")
    elif e.get("room") or e.get("rear"):
        errs.append("room and rear need cells")
    if s.room:
        for k, c in list(s.cells.items()):
            if not s.in_room(c):
                errs.append(f"{k} cell {c} outside the room")
        for c in s.rear:
            if not s.in_room(c):
                warns.append(f"rear {c} outside the room")
    opened = s.open_doors()
    for k, c in s.cells.items():
        weapon = squad.get(k, {}).get("weapon", "")
        role = s.roles.get(k)
        near_open = any(max(abs(c[0] - d[0]), abs(c[1] - d[1])) <= 1 for d in opened)
        if role != "front" and near_open:
            warns.append(f"{k} ({role}) next to an open door: cannot fire at a raider in it ('Too close')")
        if role == "front" and not near_open and opened:
            warns.append(f"{k} is front but not next to an open door")
        if s.room and _thrower(weapon) and k not in s.hold_fire:
            warns.append(f"{k} throws ({weapon}) with fire at will inside the room")
    if smap is not None:
        from ..terrain import Terrain
        for k, c in list(s.cells.items()) + [("rear", c) for c in s.rear]:
            if not smap.standable(*c):
                errs.append(f"{k} cell {c} not standable on the map ({smap.cell(*c)!r}, {smap.on.get(c, [])})")
        for c, _ in s.doors:
            if smap.door_at(*c) is None:
                errs.append(f"no door at {c}")
        t = Terrain(fetch=smap.fetch, size=smap.size)
        start = (round(statistics.median(p["x"] for p in manifest["squad"])),
                 round(statistics.median(p["z"] for p in manifest["squad"])))
        dist = t.bfs(start, limit=400)
        far = [(k, c) for k, c in s.cells.items() if c not in dist]
        if far:
            errs.append(f"not reachable from the squad's start {start}: {far}")
        elif s.cells:
            warns.append(f"walk from the start: up to {max(dist[c] for c in s.cells.values())} cells")
        elif s.anchor not in dist:
            errs.append(f"anchor {s.anchor} not reachable from the squad's start {start}")
    return errs, warns


def describe(s):
    """One line for logs and rows."""
    return f"{s.site} ({s.mode}, anchor {s.anchor}, {len(s.cells)} cells, sha {s.sha})"


def chebyshev(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
