"""Battleground planner v4 for turtle (LESSONS §2 "Battleground planner").

Square law: a side's strength ~ (shooters actually engaged)^2. We can't change
the raid's size, but we can change how many raiders get to shoot at once. Per
candidate cell: the firing window (approach-path cells it can shoot at) and the
exposure (enemy-side cells that can shoot back).

Kept from v1-v3 (each fixed a measured failure):
  * pack the squad around the single best cell (v1's crossfire split lost one
    half at a time: mutual support);
  * only cells with window >= 0.6 x the best window compete on
    window / (1 + exposure) (v2: a corner seeing ONE approach cell won;
    hiding is not holding);
  * widen the pack radius by 2 until every shooter has a cell (v2 left 8/18
    shooters without one);
  * an approach shorter than 3 cells = the raid is inside: no plan, fight;
  * cells closer than `standoff` (8) to the funnel exit are excluded, so
    raiders cross open ground under fire (v3).
New in v4: the rca terrain (one legend, 8-neighbour paths), per-pawn ranges
from the XML (LESSONS bug 3): the site is chosen with the shooters' median
range, exposure with the raid's median range, and each shooter gets the free
cell with the largest window for ITS range (short guns forward). Exposure is
sampled on every 2nd enemy-ground cell (cost; a relative measure anyway).
"""
import math
import statistics

SEARCH_RADIUS, EXIT_DEPTH, CLUSTER_RADIUS, STANDOFF, MIN_WINDOW_FRAC = 14, 8, 5, 8, 0.6
DEFAULT_RANGE = 25
GAP = 1.5                    # 1-cell gaps: tight but not stacked


def approach_path(terrain, enemy_center, anchor, limit=200):
    """Shortest walkable path from the enemy toward the anchor (cells, enemy first)."""
    anchor = (round(anchor[0]), round(anchor[1]))
    dist = terrain.bfs(anchor, limit=limit)
    cur = min(dist, key=lambda c: (math.dist(c, enemy_center), dist[c]))
    path = [cur]
    while dist[cur] > 0:
        cur = min(terrain.neighbours(cur), key=lambda n: dist.get(n, math.inf))
        path.append(cur)
    return path


def plan(terrain, anchor, enemy_center, ranges, enemy_range=DEFAULT_RANGE,
         search_radius=SEARCH_RADIUS, exit_depth=EXIT_DEPTH, cluster_radius=CLUSTER_RADIUS,
         standoff=STANDOFF, min_window_frac=MIN_WINDOW_FRAC, sample=2):
    """-> (cells, slots, report). ranges: one per shooter. slots[i] = cell for
    shooter i (or None); cells = the packed set."""
    rng = statistics.median(ranges) if ranges else DEFAULT_RANGE
    far = max(ranges) if ranges else DEFAULT_RANGE
    path = approach_path(terrain, enemy_center, anchor)
    enter = next((i for i, c in enumerate(path) if math.dist(c, anchor) <= search_radius),
                 len(path) - 1)
    exit_cells = path[max(0, enter - exit_depth):enter + 1]
    approach = path[:enter + 1]
    ex, ez = exit_cells[-1]
    er = int(enemy_range)
    enemy_ground = [(x, z) for x in range(ex - er, ex + er + 1, sample)
                    for z in range(ez - er, ez + er + 1, sample)
                    if terrain.inside(x, z) and terrain.passable(x, z)
                    and math.dist((x, z), anchor) > search_radius]
    base = {"exit": list(exit_cells[-1]), "exit_cells": len(exit_cells), "range": rng,
            "enemy_range": enemy_range, "enemy_ground": len(enemy_ground)}
    if len(approach) < 3:
        return [], [None] * len(ranges), base | {"no_approach": True, "window": 0,
                                                  "exposure_frac": 1.0, "best_window": 0}
    reach = terrain.bfs(anchor, limit=search_radius)
    seen, scored = {}, {}
    for c in reach:
        if (math.dist(c, anchor) > search_radius or c in exit_cells
                or math.dist(c, (ex, ez)) < standoff):
            continue
        ds = sorted(math.dist(c, p) for p in approach
                    if math.dist(c, p) <= far and terrain.los(c, p))
        window = sum(d <= rng for d in ds)
        if not ds:
            continue
        exposed = sum(1 for g in enemy_ground
                      if math.dist(c, g) <= enemy_range and terrain.los(g, c))
        seen[c] = ds
        scored[c] = (window / (1 + exposed), window, exposed)
    scored = {c: v for c, v in scored.items() if v[1] > 0} or scored
    if not scored:
        return [], [None] * len(ranges), base | {"window": 0, "exposure_frac": 1.0,
                                                  "best_window": 0}
    best_window = max(v[1] for v in scored.values())
    good = {c: v for c, v in scored.items() if v[1] >= min_window_frac * best_window}
    best = max(good, key=lambda c: good[c][0])
    picked, radius = [], cluster_radius
    while len(picked) < len(ranges):
        pool = good if radius <= 2 * search_radius else scored
        near = sorted((c for c in pool if math.dist(c, best) <= radius and c not in picked),
                      key=lambda c: (-pool[c][0], math.dist(c, best)))
        for c in near:
            if len(picked) >= len(ranges):
                break
            if all(math.dist(c, p) >= GAP for p in picked):
                picked.append(c)
        if radius > 4 * search_radius:
            break
        radius += 2
    slots = assign(picked, seen, ranges)
    n = max(1, len(picked))
    return picked, slots, base | {
        "center": list(best), "best_window": best_window, "radius": radius,
        "window": round(sum(scored[c][1] for c in picked) / n, 1),
        "mean_exposure": round(sum(scored[c][2] for c in picked) / n, 1),
        # 1.0 = every enemy-side cell sees us (open field); lower = we found an edge
        "exposure_frac": round(sum(scored[c][2] for c in picked) / max(1, n * len(enemy_ground)), 3),
        "shooters_placed": sum(s is not None for s in slots), "shooters": len(ranges)}


def assign(cells, seen, ranges):
    """Shortest range first: each shooter takes the free cell with the largest
    window for its own range (ties: the cell nearest the approach)."""
    free, slots = list(cells), [None] * len(ranges)
    for i in sorted(range(len(ranges)), key=lambda i: ranges[i]):
        if not free:
            break
        r = ranges[i]
        cell = max(free, key=lambda c: (sum(d <= r for d in seen.get(c, ())),
                                        -min(seen.get(c, (math.inf,)))))
        free.remove(cell)
        slots[i] = cell
    return slots

