"""Doctrine preconditions: cheap checks the strategic layer runs before it
picks a doctrine (WORKFLOW layer contracts, GLOSSARY "precondition").

A doctrine lists its preconditions as data: {check name: params}. check()
evaluates them on a Context (terrain + squad + enemy composition) without
moving anybody: a few terrain tiles and arithmetic, no planner run. Each result
is {"ok": bool | None, "value": x, "need": threshold}; None = no data.

The thresholds are first guesses (UNVERIFIED): rows store the values, so they
can be calibrated against outcomes later. Runtime breaks (e.g. turtle's enemy
never comes) are raised by the doctrine itself as signals.
"""
import math
import statistics
from dataclasses import dataclass, field

# Classes that must close in to fight (DATA.md §4 classes): they come to us.
CLOSERS = {"melee", "short", "thrown"}


@dataclass
class Context:
    terrain: object = None
    anchor: tuple = (125, 125)
    squad: list = field(default_factory=list)      # [{pos, range, melee}]
    enemies: list = field(default_factory=list)    # [{pos, cls, range}]


def _share(items, pred):
    return round(sum(1 for i in items if pred(i)) / len(items), 3) if items else None


def _cells(c, r):
    x0, z0 = round(c[0]), round(c[1])
    for x in range(x0 - r, x0 + r + 1):
        for z in range(z0 - r, z0 + r + 1):
            if math.dist((x, z), (x0, z0)) <= r:
                yield x, z


def ranged_squad(ctx, min_share=0.5):
    return _share(ctx.squad, lambda p: not p["melee"]), min_share


def defensible_terrain(ctx, radius=14, min_cover=0.10):
    """Blocking cells (wall/rock) + half for trees within the planner's search
    radius: an open field has nothing to build a concave behind."""
    if ctx.terrain is None:
        return None, min_cover
    n = cover = 0
    for x, z in _cells(ctx.anchor, radius):
        n += 1
        c = ctx.terrain.cover(x, z)
        cover += 1 if c == "full" else 0.5 if c == "half" else 0
    return round(cover / max(1, n), 3), min_cover


def enemy_approaches(ctx, min_share=0.5):
    """Raiders that must close in to fight come to us; snipers, archers and
    gunners can trade from where they stand."""
    return _share(ctx.enemies, lambda e: e["cls"] in CLOSERS), min_share


def enemy_melee_heavy(ctx, min_share=0.4):
    return _share(ctx.enemies, lambda e: e["cls"] == "melee"), min_share


def room_to_spread(ctx, radius=10, min_passable=0.7):
    if ctx.terrain is None or not ctx.squad:
        return None, min_passable
    cx = statistics.mean(p["pos"][0] for p in ctx.squad)
    cz = statistics.mean(p["pos"][1] for p in ctx.squad)
    cells = list(_cells((cx, cz), radius))
    return _share(cells, lambda c: ctx.terrain.passable(*c)), min_passable


def enemy_outranges(ctx, min_share=0.4, margin=5):
    """Poke: raiders whose range beats our median range by `margin` cells."""
    ours = [p["range"] for p in ctx.squad if not p["melee"]]
    if not ours:
        return None, min_share
    ref = statistics.median(ours) + margin
    return _share(ctx.enemies, lambda e: (e["range"] or 0) >= ref), min_share


def approach_cover(ctx, band=2, min_cover=0.05):
    """Cover cells along the straight line from the squad to the raid centre:
    `close` bounds from cover to cover."""
    if ctx.terrain is None or not ctx.enemies:
        return None, min_cover
    ex = statistics.median(e["pos"][0] for e in ctx.enemies)
    ez = statistics.median(e["pos"][1] for e in ctx.enemies)
    ax, az = ctx.anchor
    d = math.dist((ax, az), (ex, ez))
    n = cover = 0
    for i in range(int(d) + 1):
        t = i / max(1.0, d)
        x, z = round(ax + (ex - ax) * t), round(az + (ez - az) * t)
        for dx in range(-band, band + 1):
            n += 1
            cover += ctx.terrain.cover(x + dx, z) is not None
    return round(cover / max(1, n), 3), min_cover


CHECKS = {f.__name__: f for f in (ranged_squad, defensible_terrain, enemy_approaches,
                                  enemy_melee_heavy, room_to_spread, enemy_outranges,
                                  approach_cover)}


def check(doctrine, ctx):
    """{name: {ok, value, need}} for a doctrine class or instance."""
    out = {}
    for name, params in doctrine.preconditions.items():
        value, need = CHECKS[name](ctx, **(params or {}))
        out[name] = {"ok": None if value is None else value >= need, "value": value, "need": need}
    return out


def all_ok(report):
    """False if any check failed; None-valued checks don't count."""
    return all(r["ok"] is not False for r in report.values())
