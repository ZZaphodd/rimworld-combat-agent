"""Battleground selection: pick firing positions that create a local Lanchester edge.

Square law: a side's strength ~ (shooters actually engaged)^2. A defender can't
change the raid's size, but it can change how many raiders get to shoot at once.
For each candidate cell we ask two questions:
  * does it see the enemy's approach (the funnel exit)?  -> it gets to shoot
  * from how much enemy-accessible ground can it be seen? -> how many shoot back
A cell deep inside a walled compound that sees out only through the gate scores
well; any cell in an open field scores the same as any other (no edge to take).
"""
import math
from collections import deque

BLOCKS_LOS = set("#%")          # walls, natural rock
IMPASSABLE = set("#%~")         # + deep water / marsh treated as blocked
DEFAULT_RANGE = 25


def weapon_range(label):
    lab = (label or "").lower()
    for key, r in (("sniper", 44), ("charge lance", 30), ("bolt", 30), ("assault", 31),
                   ("charge rifle", 27), ("rifle", 35), ("lmg", 26), ("minigun", 30),
                   ("heavy smg", 23), ("smg", 23), ("machine pistol", 19),
                   ("chain shotgun", 15), ("shotgun", 16), ("autopistol", 26),
                   ("revolver", 26), ("pistol", 26), ("bow", 25), ("launcher", 23)):
        if key in lab:
            return r
    return DEFAULT_RANGE


class Grid:
    """Character grid for a map rectangle. cell(x, z) -> char, in map coordinates."""

    def __init__(self, rows, min_x, min_z, north_up=True):
        self.rows, self.min_x, self.min_z, self.north_up = rows, min_x, min_z, north_up
        self.w, self.h = len(rows[0]), len(rows)

    @classmethod
    def from_rimmolt(cls, rm, min_x, min_z, max_x, max_z, tile=50):
        """Stitch fine-grained ascii tiles (the tool caps one call at ~55x55)."""
        w, h = max_x - min_x + 1, max_z - min_z + 1
        canvas = [[" "] * w for _ in range(h)]       # canvas[z - min_z][x - min_x]
        for tz in range(min_z, max_z + 1, tile):
            for tx in range(min_x, max_x + 1, tile):
                bx, bz = min(tx + tile - 1, max_x), min(tz + tile - 1, max_z)
                r = rm.call("get_area", minX=tx, minZ=tz, maxX=bx, maxZ=bz, render="ascii")
                rows = r["grid"]
                for i, row in enumerate(rows):       # rows come north (max z) first
                    z = bz - i
                    for j, ch in enumerate(row):
                        canvas[z - min_z][tx + j - min_x] = ch
        return cls(["".join(r) for r in canvas], min_x, min_z, north_up=False)

    def inside(self, x, z):
        return 0 <= x - self.min_x < self.w and 0 <= z - self.min_z < self.h

    def cell(self, x, z):
        if not self.inside(x, z):
            return "#"
        return self.rows[z - self.min_z][x - self.min_x]

    def passable(self, x, z):
        return self.cell(x, z) not in IMPASSABLE

    def los(self, a, b):
        """Bresenham line of sight; endpoints themselves never block."""
        (x0, z0), (x1, z1) = a, b
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
            if (x, z) != (x1, z1) and self.cell(x, z) in BLOCKS_LOS:
                return False
        return True

    def bfs(self, start, goal_set=None, limit=None):
        """Distances from start over passable cells (4-neighbour)."""
        dist = {start: 0}
        q = deque([start])
        while q:
            c = q.popleft()
            if limit and dist[c] >= limit:
                continue
            x, z = c
            for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
                if n not in dist and self.inside(*n) and self.passable(*n):
                    dist[n] = dist[c] + 1
                    q.append(n)
        return dist


def approach_path(grid, enemy_center, anchor):
    """Shortest walkable path from the enemy toward the anchor (cells, enemy first)."""
    dist = grid.bfs(anchor)
    cur = min(dist, key=lambda c: math.dist(c, enemy_center))  # nearest reachable cell
    path = [cur]
    while dist[cur] > 0:
        x, z = cur
        cur = min(((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)),
                  key=lambda n: dist.get(n, math.inf))
        path.append(cur)
    return path


def plan_positions(grid, anchor, enemy_center, n_shooters, rng=DEFAULT_RANGE,
                   search_radius=14, exit_depth=8, cluster_radius=5, standoff=8,
                   min_window_frac=0.6):
    """Return (cells, report): n_shooters firing cells, packed together.

    Score per cell = approach-path cells it can shoot at (the firing window)
                     / (1 + enemy-side cells that can shoot back at it),
    but only among cells whose window is >= min_window_frac of the best window.
    (v2 ranked by the ratio alone, and a corner seeing ONE approach cell with no
    exposure beat every real firing position: hiding is not holding.)
    Cells closer than `standoff` to the funnel exit are excluded: raiders that
    come through must still cross open ground under fire before contact.
    Then the squad is packed around the single best cell: splitting it into a
    crossfire lets raiders that get inside fight each half alone (v1 lost
    exactly that way), which is the square law working against us. The pack
    widens until every shooter has a cell (v2 capped at cluster_radius and left
    8 of 18 shooters without one).
    """
    path = approach_path(grid, enemy_center, anchor)
    enter = next((i for i, c in enumerate(path) if math.dist(c, anchor) <= search_radius),
                 len(path) - 1)
    exit_cells = path[max(0, enter - exit_depth):enter + 1]
    approach = path[:enter + 1]
    ex, ez = exit_cells[-1]
    enemy_ground = [(x, z) for x in range(ex - rng, ex + rng + 1)
                    for z in range(ez - rng, ez + rng + 1)
                    if grid.inside(x, z) and grid.passable(x, z)
                    and math.dist((x, z), anchor) > search_radius]
    if len(approach) < 3:
        # Raid is already on top of us (drop pods inside the walls): there is no
        # approach to cover, and every cell "sees" it equally badly (v2 chose a
        # corner with window=1 here). Report it; the caller should just fight.
        return [], {"exit": exit_cells[-1], "exposure_frac": 1.0, "window": 0,
                    "enemy_ground": len(enemy_ground), "mean_exposure": 0,
                    "exit_cells": len(exit_cells), "best_window": 0, "no_approach": True}
    reach = grid.bfs(anchor, limit=search_radius)
    scored = {}
    for c in reach:
        if (math.dist(c, anchor) > search_radius or c in exit_cells
                or math.dist(c, (ex, ez)) < standoff):
            continue
        window = sum(1 for p in approach if math.dist(c, p) <= rng and grid.los(c, p))
        if not window:
            continue
        exposed = sum(1 for g in enemy_ground if math.dist(c, g) <= rng and grid.los(g, c))
        scored[c] = (window / (1 + exposed), window, exposed)
    if not scored:
        return [], {"exit": exit_cells[-1], "exposure_frac": 1.0, "window": 0,
                    "enemy_ground": len(enemy_ground), "mean_exposure": 0,
                    "exit_cells": len(exit_cells), "best_window": 0}
    best_window = max(v[1] for v in scored.values())
    good = {c: v for c, v in scored.items() if v[1] >= min_window_frac * best_window}
    best = max(good, key=lambda c: good[c][0])
    picked, radius = [], cluster_radius
    while len(picked) < n_shooters:
        # Best ratio first inside the radius; once every good cell is in reach,
        # fall back to the remaining scored cells nearest the pack.
        pool = good if radius <= 2 * search_radius else scored
        near = sorted((c for c in pool if math.dist(c, best) <= radius and c not in picked),
                      key=lambda c: (-pool[c][0], math.dist(c, best)))
        for c in near:                              # 1-cell gaps: tight but not stacked
            if len(picked) >= n_shooters:
                break
            if all(math.dist(c, p) >= 1.5 for p in picked):
                picked.append(c)
        if radius > 4 * search_radius:
            break                                   # every reachable cell considered
        radius += 2
    open_ref = len(enemy_ground)
    report = {
        "exit": exit_cells[-1], "exit_cells": len(exit_cells), "center": best,
        "enemy_ground": open_ref, "best_window": best_window,
        "radius": radius,
        "window": sum(scored[c][1] for c in picked) / max(1, len(picked)),
        "mean_exposure": sum(scored[c][2] for c in picked) / max(1, len(picked)),
        # 1.0 = every enemy-side cell can shoot us (open field); lower = we found an edge.
        "exposure_frac": sum(scored[c][2] for c in picked) / max(1, len(picked) * open_ref),
    }
    return picked, report
