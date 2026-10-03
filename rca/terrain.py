"""One terrain model for every layer: get_area ascii in 50x50 tiles, one legend,
LOS and BFS. Replaces battleground.Grid, reflexes.TiledGrid and threatmap.Terrain
(LESSONS bug 1: they disagreed on what " " means).

Legend (verified in game 2026-10-03, GAME_FACTS §9): get_area's own legend is
  # wall/impassable building, % natural rock, + door, * tree, ~ water/marsh,
  . open ground, V steam geyser, ? fogged/unknown.
" " never occurs in a fetched grid (0 of 62,500 cells on a whole forest map);
it was the old code's fill for cells it had not fetched. Here every cell is
fetched on first use, so " " cannot appear; out-of-map cells read as "#".

Cache (LESSONS §4 item 2, decided design): one Terrain per episode, never shared
across episodes. Tiles are marked stale and re-fetched lazily on next use when
  * an Explosion thing is seen (tiles within EXPLOSION_R),
  * wait_for_event's _delta reports newBuildings/removedBuildings (no cells are
    given, so every fetched tile with a structure char is marked),
  * a fire burns in the tile and the tile is older than REFRESH ticks,
  * we are in contact and the tile lies within CONTACT_R of the squad and is
    older than REFRESH ticks (catches what the events miss).
Burned trees do not appear in _delta and still render "*" (BurnedTree stump,
verified), so fire mostly costs nothing here.
"""
from collections import deque

LEGEND = {"#": "wall", "%": "rock", "+": "door", "*": "tree", "~": "water", ".": "open",
          "V": "geyser", "?": "fog"}
IMPASSABLE = set("#%~")      # ~ also covers marsh (slow, not blocked): conservative, UNVERIFIED
BLOCKS_LOS = set("#%+")      # closed doors block LOS; open ones don't (UNVERIFIED which we see)
FULL_COVER = set("#%")
HALF_COVER = set("*")        # trees: fillPercent 0.25 (burned stump 0.20)
STRUCTURE = set("#%+")       # what a building delta can change
TILE, MAP = 50, 250
REFRESH = 600                # ticks
CONTACT_R = 30
EXPLOSION_R = 6


class Terrain:
    def __init__(self, rm=None, size=MAP, tile=TILE, fetch=None):
        """fetch(x0, z0, x1, z1) -> rows north (max z) first; defaults to get_area."""
        self.rm, self.size, self.tile = rm, size, tile
        self.fetch = fetch or self._get_area
        self.tiles = {}          # (tx, tz) -> {"rows": [z][x] south-first, "pre", "at", "stale"}
        self.now = 0
        self.stats = {"fetches": 0, "refetches": 0, "stale_explosion": 0, "stale_building": 0,
                      "stale_fire": 0, "stale_contact": 0, "unknown_chars": 0}

    def _get_area(self, x0, z0, x1, z1):
        return self.rm.call("get_area", minX=x0, minZ=z0, maxX=x1, maxZ=z1, render="ascii")["grid"]

    # ------------------------------------------------------------ tiles
    def _bounds(self, key):
        x0, z0 = key[0] * self.tile, key[1] * self.tile
        return x0, z0, min(x0 + self.tile, self.size) - 1, min(z0 + self.tile, self.size) - 1

    def _tile(self, key):
        t = self.tiles.get(key)
        if t is None or t["stale"]:
            x0, z0, x1, z1 = self._bounds(key)
            grid = self.fetch(x0, z0, x1, z1)
            rows = [grid[z1 - z] for z in range(z0, z1 + 1)]        # south-first
            self.stats["refetches" if t else "fetches"] += 1
            self.stats["unknown_chars"] += sum(ch not in LEGEND for r in rows for ch in r)
            w = x1 - x0 + 1
            pre = [[0] * (w + 1) for _ in range(len(rows) + 1)]
            for z, row in enumerate(rows):
                acc = 0
                for x in range(w):
                    acc += row[x] in BLOCKS_LOS
                    pre[z + 1][x + 1] = pre[z][x + 1] + acc
            t = self.tiles[key] = {"rows": rows, "pre": pre, "at": self.now, "stale": False,
                                   "structure": any(ch in STRUCTURE for r in rows for ch in r)}
        return t

    def inside(self, x, z):
        return 0 <= x < self.size and 0 <= z < self.size

    def cell(self, x, z):
        if not self.inside(x, z):
            return "#"
        t = self._tile((x // self.tile, z // self.tile))
        return t["rows"][z % self.tile][x % self.tile]

    def passable(self, x, z):
        return self.cell(x, z) not in IMPASSABLE

    def blocks_los(self, x, z):
        return self.cell(x, z) in BLOCKS_LOS

    def cover(self, x, z):
        ch = self.cell(x, z)
        return "full" if ch in FULL_COVER else "half" if ch in HALF_COVER else None

    # ------------------------------------------------------------ queries
    def _any_blocker(self, x0, z0, x1, z1):
        """Any LOS blocker in the box? Per-tile prefix sums, so open ground is O(tiles)."""
        x0, x1 = max(0, min(x0, x1)), min(self.size - 1, max(x0, x1))
        z0, z1 = max(0, min(z0, z1)), min(self.size - 1, max(z0, z1))
        for tx in range(x0 // self.tile, x1 // self.tile + 1):
            for tz in range(z0 // self.tile, z1 // self.tile + 1):
                bx0, bz0, bx1, bz1 = self._bounds((tx, tz))
                a, b = max(x0, bx0) - bx0, max(z0, bz0) - bz0
                c, d = min(x1, bx1) - bx0, min(z1, bz1) - bz0
                p = self._tile((tx, tz))["pre"]
                if p[d + 1][c + 1] - p[b][c + 1] - p[d + 1][a] + p[b][a]:
                    return True
        return False

    def los(self, a, b):
        """Bresenham line of sight; the endpoints themselves never block."""
        (x0, z0), (x1, z1) = (round(a[0]), round(a[1])), (round(b[0]), round(b[1]))
        if not self._any_blocker(x0, z0, x1, z1):
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
            if (x, z) != (x1, z1) and self.blocks_los(x, z):
                return False
        return True

    def neighbours(self, c, diagonal=True):
        """Walkable neighbours; a diagonal step needs both orthogonal cells free
        (no corner cutting)."""
        x, z = c
        out = [n for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1))
               if self.inside(*n) and self.passable(*n)]
        if diagonal:
            for dx in (-1, 1):
                for dz in (-1, 1):
                    n = (x + dx, z + dz)
                    if (self.inside(*n) and self.passable(*n) and self.passable(x + dx, z)
                            and self.passable(x, z + dz)):
                        out.append(n)
        return out

    def bfs(self, start, limit=None, diagonal=True):
        """Steps from start over walkable cells (start itself always counts)."""
        start = (round(start[0]), round(start[1]))
        dist = {start: 0}
        q = deque([start])
        while q:
            c = q.popleft()
            if limit is not None and dist[c] >= limit:
                continue
            for n in self.neighbours(c, diagonal):
                if n not in dist:
                    dist[n] = dist[c] + 1
                    q.append(n)
        return dist

    # ------------------------------------------------------------ invalidation
    def _keys_near(self, c, r):
        x, z = c
        return {(tx, tz) for tx in range(max(0, int(x - r)) // self.tile,
                                         min(self.size - 1, int(x + r)) // self.tile + 1)
                for tz in range(max(0, int(z - r)) // self.tile,
                                min(self.size - 1, int(z + r)) // self.tile + 1)}

    def _stale(self, keys, why, min_age=0):
        for k in keys:
            t = self.tiles.get(k)
            if t and not t["stale"] and self.now - t["at"] >= min_age:
                t["stale"] = True
                self.stats[f"stale_{why}"] += 1

    def update(self, now, fires=(), explosions=(), delta=None, squad=(), contact=False):
        """Feed one step's events (see module docstring). Costs no calls itself:
        stale tiles are re-fetched only when something reads them."""
        self.now = now
        for e in explosions:
            self._stale(self._keys_near(e, EXPLOSION_R), "explosion")
        if delta and (delta.get("newBuildings") or delta.get("removedBuildings")):
            self._stale([k for k, t in self.tiles.items() if t["structure"]], "building")
        self._stale({(round(x) // self.tile, round(z) // self.tile) for x, z in fires
                     if self.inside(round(x), round(z))}, "fire", REFRESH)
        if contact:
            keys = set()
            for p in squad:
                keys |= self._keys_near(p, CONTACT_R)
            self._stale(keys, "contact", REFRESH)

    def summary(self):
        return {f"terrain_{k}": v for k, v in self.stats.items()}
