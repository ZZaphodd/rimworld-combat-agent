"""Line of fire as RimWorld 1.6 decides it: can a pawn standing here shoot a pawn standing there.

Our own implementation of the rules read in the game's code (2026-10-17, decompiled with the user's OK;
only member names are cited here, no code text). It differs from rca.terrain's `los()` (an 8-connected
Bresenham line, kept unchanged for the frozen agents) in two ways that showed at rock corners:

* **The line** (GenSight.LineOfSight, the cell form): a 4-connected walk of 1 + |dx| + |dz| cells, each
  step moving in x or in z; the error term starts at 2|dx| - 2|dz| and a tie steps in x when the line
  runs toward +x, or (x equal) toward +z. The first cell is skipped (skipFirstCell) and the last one is
  never checked. A cell blocks when its edifice is full-fill and not an open door
  (GenGrid.CanBeSeenOver): natural rock, walls, closed doors; trees and sandbags do not block. A door
  with a pawn in it is held open.
* **Leaning** (ShootLeanUtility.LeanShootingSourcesFromTo): besides its own cell (when that cell can be
  seen over), a pawn uses a cardinal neighbour when the cell beside it on the other axis blocks and the
  diagonal past that block is open, on the side facing the other pawn; and a cardinal neighbour on that
  side that holds cover (CoverGrid: any thing with a fill percent). The side comes from the angle to the
  other pawn (IntVec3.AngleFlat: 0 north, 90 east, 180 south, 270 west; "north" is above 270 or below
  90, "south" between 90 and 270, "west" above 180, "east" below 180, all strict).
* **The shot** (Verb.TryFindShootLineFromTo for a pawn shooting a pawn with a projectile verb): range
  first, by the squared distance between the two cells in float32 (Verb.OutOfRange; a projectile
  verb's minimum range is at least 1.421 against a standing hostile pawn, so it never fires at an
  adjacent one: VerbProperties.EffectiveMinRange, VerbUtility.AllowAdjacentShot); then from the
  shooter's cell, then from each of its lean cells toward the target, to any of the target's lean
  cells toward that source cell (ShootLeanUtility.CalcShootableCellsOf).

The two checks by fuzzing against a literal transliteration of the decompiled code (2026-10-17,
kept out of this repo): 450,107 random cases and 88,596 pairs on hand-made corner maps, 0 differences.
Open in game: whether Unity's AngleFlat is exactly 90/180/270 for pawns on one row or column (the side
flags are strict, so a float error there changes which lean cells count).

Not modelled: the weather's range cap (pass the range the weather leaves: VerbProperties.AdjustedRange),
an effective range of 1.42 or less (the game then asks for touch reachability, not a line), verbs
without requireLineOfSight, targets wider than one cell, shooters that are not pawns (turrets use their
footprint and no leaning), apparel that prevents shooting, psychic invisibility, and the melee lock
(GAME_FACTS §8: a raider swung at in melee cannot shoot at all while that pawn is next to it; our
drafted pawns on fire at will melee an adjacent enemy instead of shooting).
"""
import math
import struct

ADJACENT = ((0, 1), (1, 0), (0, -1), (-1, 0), (1, -1), (1, 1), (-1, 1), (-1, -1))   # GenAdj.AdjacentCells
N, E, S, W, SE, NE, NW, SW = range(8)
ADJACENT_MIN_RANGE = 1.421
TOUCH_RANGE = 1.42


def f32(v):
    """v rounded to a float32, as the game stores ranges."""
    return struct.unpack("f", struct.pack("f", v))[0]


class TerrainGrid:
    """rca.terrain.Terrain (get_area's legend) as the questions the rules ask. '#' (wall or impassable
    building) and '%' (rock) block, and so does '?' (fogged: the game ignores fog, but fogged cells are
    mostly unopened rock); doors block unless open_doors. Cover is anything blocking plus trees.
    What the legend cannot say: impassable buildings that are not full-fill (they do not block in the
    game and are cover), full-fill buildings that render as open, and partial fillers that render as
    '.' (sandbags, chunks, furniture, fences: cover the leaning rule would use)."""

    def __init__(self, terrain, open_doors=False):
        self.t, self.open_doors = terrain, open_doors

    def inside(self, x, z):
        return self.t.inside(x, z)

    def door(self, x, z):
        return self.t.cell(x, z) == "+"

    def blocks(self, x, z):
        ch = self.t.cell(x, z)
        return ch in "#%?" or (ch == "+" and not self.open_doors)

    def cover(self, x, z):
        return self.t.cell(x, z) in "#%?*+"


class CharGrid:
    """A grid from rows of characters, north row first as get_area gives it: '#' or '%' blocks, '+' is a
    door (closed unless open_doors), '*' and 'c' are cover that does not block, anything else is open."""

    def __init__(self, rows, open_doors=False):
        self.rows, self.h, self.w, self.open_doors = rows, len(rows), len(rows[0]), open_doors

    def ch(self, x, z):
        return self.rows[self.h - 1 - z][x]

    def inside(self, x, z):
        return 0 <= x < self.w and 0 <= z < self.h

    def door(self, x, z):
        return self.ch(x, z) == "+"

    def blocks(self, x, z):
        ch = self.ch(x, z)
        return ch in "#%" or (ch == "+" and not self.open_doors)

    def cover(self, x, z):
        return self.ch(x, z) in "#%*+c"


class HeldOpen:
    """A grid with the doors under the given cells held open (a pawn standing in a doorway)."""

    def __init__(self, grid, cells):
        self.g, self.cells = grid, {c for c in cells if grid.inside(*c) and grid.door(*c)}

    def inside(self, x, z):
        return self.g.inside(x, z)

    def door(self, x, z):
        return self.g.door(x, z)

    def blocks(self, x, z):
        return (x, z) not in self.cells and self.g.blocks(x, z)

    def cover(self, x, z):
        return self.g.cover(x, z)


def _seen_over(grid, x, z):
    return grid.inside(x, z) and not grid.blocks(x, z)


def line_cells(a, b):
    """The cells the game checks on the line from a to b (a and b excluded), in walk order."""
    (x, z), (x1, z1) = a, b
    dx, dz = abs(x1 - x), abs(z1 - z)
    toward = (x < x1) if x != x1 else (z < z1)
    sx, sz = (1 if x1 > x else -1), (1 if z1 > z else -1)
    err = 2 * dx - 2 * dz
    cells = []
    for i in range(dx + dz):
        if i:
            cells.append((x, z))
        if err > 0 or (err == 0 and toward):
            x += sx
            err -= 4 * dz
        else:
            z += sz
            err += 4 * dx
    return cells


def line_of_sight(grid, a, b):
    """GenSight.LineOfSight(a, b, skipFirstCell: true): no blocking cell strictly between."""
    if not (grid.inside(*a) and grid.inside(*b)):
        return False
    return not any(grid.blocks(x, z) for x, z in line_cells(a, b))


def angle_flat(a, b):
    """Degrees from a toward b: 0 north (+z), 90 east (+x), 180 south, 270 west."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    return 0.0 if dx == 0 and dz == 0 else math.degrees(math.atan2(dx, dz)) % 360.0


def lean_cells(grid, at, toward):
    """The cells a pawn at `at` can shoot from or be shot at, facing `toward`, in the game's order."""
    ang = angle_flat(at, toward)
    north, south = ang > 270 or ang < 90, 90 < ang < 270
    west, east = ang > 180, ang < 180
    x, z = at
    blocked = [not _seen_over(grid, x + dx, z + dz) for dx, dz in ADJACENT]
    out = []
    if not blocked[E] and ((blocked[N] and not blocked[NE] and north) or (blocked[S] and not blocked[SE] and south)):
        out.append((x + 1, z))
    if not blocked[W] and ((blocked[N] and not blocked[NW] and north) or (blocked[S] and not blocked[SW] and south)):
        out.append((x - 1, z))
    if not blocked[S] and ((blocked[W] and not blocked[SW] and west) or (blocked[E] and not blocked[SE] and east)):
        out.append((x, z - 1))
    if not blocked[N] and ((blocked[W] and not blocked[NW] and west) or (blocked[E] and not blocked[NE] and east)):
        out.append((x, z + 1))
    if _seen_over(grid, x, z):
        out.append((x, z))
    for j, side in ((N, north), (E, east), (S, south), (W, west)):
        cx, cz = x + ADJACENT[j][0], z + ADJACENT[j][1]
        if not blocked[j] and side and grid.inside(cx, cz) and grid.cover(cx, cz):
            out.append((cx, cz))
    return out


def in_range(shooter, target, range_, min_range=0.0, adjacent_ok=False):
    """Verb.OutOfRange, inverted, in float32. adjacent_ok: the target is not a standing hostile pawn (a
    downed one, a friend, a thing) or the verb launches no projectile (beam, spray, spew fire), so the
    1.421 minimum does not apply."""
    d2 = (shooter[0] - target[0]) ** 2 + (shooter[1] - target[1]) ** 2
    low = f32(min_range) if adjacent_ok else max(f32(min_range), f32(ADJACENT_MIN_RANGE))
    return not (d2 > f32(f32(range_) * f32(range_)) or d2 < f32(low * low))


def shoot_line(grid, shooter, target, range_, min_range=0.0, adjacent_ok=False, held_open=()):
    """(source cell, target cell) of the shot the game would take, or None when it cannot hit.
    held_open: other cells holding pawns (their doors are open); the shooter's and target's are added."""
    if range_ <= TOUCH_RANGE:
        raise ValueError(f"range {range_} <= {TOUCH_RANGE}: the game uses touch reachability, not a line")
    if not in_range(shooter, target, range_, min_range, adjacent_ok):
        return None
    grid = HeldOpen(grid, set(held_open) | {shooter, target})
    for src in [shooter] + lean_cells(grid, shooter, target):
        for dst in lean_cells(grid, target, src):
            if line_of_sight(grid, src, dst):
                return src, dst
    return None


def can_hit(grid, shooter, target, range_, min_range=0.0, adjacent_ok=False, held_open=()):
    return shoot_line(grid, shooter, target, range_, min_range, adjacent_ok, held_open) is not None
