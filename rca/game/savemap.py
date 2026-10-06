"""A map read from a save file without the game (base positions, the user, 2026-10-06).

The strategic layer picks where the squad holds a base problem before the battle; the game may be
busy (the user's own colony, another session), so the map comes from the .rws file:
  * the compressed thing grid (<compressedThingMapDeflate>: base64, raw deflate, one
    little-endian uint16 per cell, index z * size + x): each nonzero value is the short hash of a
    save-compressible def, natural rock or a stone chunk (short_hash, as the game's ShortHashGiver
    makes it; an unknown value counts as rock);
  * things: every <thing> whose def is in data/buildings.json (rca.game.defs): buildings on their
    footprint (size and rotation as GenAdj.OccupiedRect places it; smoothed rock walls are saved
    as explicit things too), trees and chunks a pawn cannot stand on, and building frames
    (Frame_<def>, on that def's footprint: not standable). Blueprints are ignored.
The grid uses rca.terrain's legend: % rock, # impassable or full-fill building, + door, * tree,
. the rest (water and marsh are not read: the live terrain is checked again at the battle);
standable() also looks at the things on a cell. `fetch` plugs into rca.terrain.Terrain for line
of sight and BFS offline.
"""
import base64
import math
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

from . import defs

FULL = 0.99                     # the game's FillCategory.Full


def short_hash(name):
    """A def's short hash: GenText.StableStringHash(defName) % 65535 as a ushort (C# int
    arithmetic). The game bumps a hash already taken by an earlier def by one (MineableSteel is
    saved as its hash + 1): SaveMap looks one to three below an unknown value."""
    n = 23
    for ch in name:
        n = (n * 31 + ord(ch)) & 0xFFFFFFFF
    n -= (n >> 31) << 32                          # back to a signed int
    return (int(math.fmod(n, 65535)) & 0xFFFF) or 1


def footprint(x, z, size, rot):
    """Cells a building of `size` [x, z] at (x, z) with rotation 0-3 covers (GenAdj.OccupiedRect)."""
    sx, sz = size
    if sx == 1 and sz == 1:
        return [(x, z)]
    if rot in (1, 3):
        sx, sz = sz, sx
    if rot == 1 and sz % 2 == 0:
        z -= 1
    elif rot == 2:
        x -= sx % 2 == 0
        z -= sz % 2 == 0
    elif rot == 3 and sx % 2 == 0:
        x -= 1
    x0, z0 = x - (sx - 1) // 2, z - (sz - 1) // 2
    return [(i, j) for i in range(x0, x0 + sx) for j in range(z0, z0 + sz)]


def _cell(text):
    x, _, z = (int(v) for v in text.strip("() ").split(","))
    return x, z


class SaveMap:
    """One map of a save: grid (rows south-first), doors, traps, turrets and the building defs on
    each cell."""

    def __init__(self, path, map_index=0):
        root = ET.parse(path).getroot()
        maps = root.find("game/maps")
        m = list(maps)[map_index]
        self.size = int(m.findtext("mapInfo/size").strip("() ").split(",")[0])
        n = self.size
        raw = zlib.decompress(base64.b64decode(m.findtext("compressedThingMapDeflate")), -15)
        packed = memoryview(raw).cast("H")
        by_hash = {short_hash(k): k for k, v in defs.buildings().items() if v.get("packed")}
        self.rows = [["." for _ in range(n)] for _ in range(n)]
        self.on = {}                   # (x, z) -> [defs of the things there]
        self.doors, self.traps, self.turrets, self.unknown = [], [], [], set()
        self.unknown_packed = 0
        for z in range(n):
            for x in range(n):
                v = packed[z * n + x]
                if not v:
                    continue
                d = by_hash.get(v) or next((by_hash[v - k] for k in (1, 2, 3) if v - k in by_hash), None)
                if d is None or defs.building(d)["rock"]:
                    self.rows[z][x] = "%"
                    self.unknown_packed += d is None
                else:
                    self.on.setdefault((x, z), []).append(d)      # a chunk: passable, not standable
        for t in m.find("things"):
            d = t.findtext("def") or ""
            b = defs.building(d)
            frame = d.startswith("Frame_") and defs.building(d[len("Frame_"):])
            if b is None and not frame:
                if t.get("Class", "").startswith("Building") and not d.startswith("Blueprint_"):
                    self.unknown.add(d)        # a modded building: not on the grid
                continue
            x, z = _cell(t.findtext("pos"))
            if frame or b["kind"] != "building":
                size = frame["size"] if frame else [1, 1]
                for c in footprint(x, z, size, int(t.findtext("rot") or 0)):
                    if 0 <= c[0] < n and 0 <= c[1] < n:
                        self.on.setdefault(c, []).append(d)        # Frame_* is not in the table: not standable
                        if b and b["kind"] == "plant" and self.rows[c[1]][c[0]] == ".":
                            self.rows[c[1]][c[0]] = "*"
                continue
            cells = footprint(x, z, b["size"], int(t.findtext("rot") or 0))
            info = {"id": t.findtext("id"), "def": d, "cell": (x, z), "faction": t.findtext("faction")}
            if b["door"]:
                self.doors.append(info | {"hold_open": (t.findtext("holdOpen") or "").lower() == "true"})
            elif d.startswith("Trap"):
                self.traps.append(info)
            elif d.startswith("Turret"):
                self.turrets.append(info)
            ch = "+" if b["door"] else "%" if b["rock"] else \
                "#" if b["pass"] == "Impassable" or b["fill"] >= FULL else None
            for (cx, cz) in cells:
                if not (0 <= cx < n and 0 <= cz < n):
                    continue
                self.on.setdefault((cx, cz), []).append(d)
                if ch and self.rows[cz][cx] != "%":
                    self.rows[cz][cx] = ch

    def cell(self, x, z):
        return self.rows[z][x] if 0 <= x < self.size and 0 <= z < self.size else "#"

    def standable(self, x, z):
        """A pawn can stop here: not rock, wall, door or tree, and nothing that only lets pawns pass
        (bed, table, barricade, chunk, a building frame)."""
        if self.cell(x, z) != ".":
            return False
        return all((defs.building(d) or {}).get("pass") == "Standable" for d in self.on.get((x, z), []))

    def fetch(self, x0, z0, x1, z1):
        """rca.terrain.Terrain fetch: rows north (max z) first."""
        return ["".join(self.rows[z][x0:x1 + 1]) for z in range(z1, z0 - 1, -1)]

    def door_at(self, x, z):
        return next((d for d in self.doors if d["cell"] == (x, z)), None)


_maps = {}


def load(save, saves=None):
    """The map of save `save` (a name in the Saves folder or a path), cached per process."""
    from .builders.base import SAVES
    p = Path(save) if str(save).endswith(".rws") else Path(saves or SAVES) / f"{save}.rws"
    key = (str(p), p.stat().st_mtime)
    if key not in _maps:
        _maps[key] = SaveMap(p)
    return _maps[key]
