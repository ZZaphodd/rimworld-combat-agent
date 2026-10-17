"""Line of fire as the game decides it (rca/sight.py): the 4-connected line, leaning around a corner,
and the range rules. Expected cells worked out by hand from the rules in the module's docstring."""
import unittest

from rca import sight

# 6 wide (x 0-5), 8 tall (z 0-7), north row first: rock fills x 0-3, z 3-7; its south-east corner is (3, 3).
CORNER = ["%%%%..",
          "%%%%..",
          "%%%%..",
          "%%%%..",
          "%%%%..",
          "......",
          "......",
          "......"]


class LineTest(unittest.TestCase):
    def test_four_connected_walk_with_tie_break(self):
        self.assertEqual(sight.line_cells((0, 0), (3, 0)), [(1, 0), (2, 0)])
        self.assertEqual(sight.line_cells((0, 0), (2, 2)), [(1, 0), (1, 1), (2, 1)])
        self.assertEqual(sight.line_cells((2, 2), (0, 0)), [(2, 1), (1, 1), (1, 0)])
        self.assertEqual(sight.line_cells((4, 2), (0, 1)), [(3, 2), (2, 2), (2, 1), (1, 1)])
        self.assertEqual(sight.line_cells((5, 5), (5, 5)), [])

    def test_a_diagonal_gap_between_two_blocks_is_closed(self):
        g = sight.CharGrid(["#.",
                            ".#"])            # north row first: (0, 1) and (1, 0) block
        self.assertFalse(sight.line_of_sight(g, (0, 0), (1, 1)))

    def test_doors(self):
        rows = ["...", ".+.", "..."]
        self.assertFalse(sight.line_of_sight(sight.CharGrid(rows), (1, 0), (1, 2)))
        self.assertTrue(sight.line_of_sight(sight.CharGrid(rows, open_doors=True), (1, 0), (1, 2)))
        self.assertTrue(sight.line_of_sight(sight.CharGrid(["...", ".*.", "..."]), (1, 0), (1, 2)))  # trees


class LeanTest(unittest.TestCase):
    def test_angles(self):
        self.assertEqual([sight.angle_flat((0, 0), c) for c in ((0, 1), (1, 0), (0, -1), (-1, 0))],
                         [0.0, 90.0, 180.0, 270.0])

    def test_peeking_round_the_corner(self):
        g = sight.CharGrid(CORNER)
        self.assertFalse(sight.line_of_sight(g, (4, 3), (0, 1)))         # straight: through (3, 3)
        self.assertEqual(sight.lean_cells(g, (4, 3), (0, 1)), [(4, 2), (4, 3)])
        self.assertEqual(sight.shoot_line(g, (4, 3), (0, 1), 30), ((4, 2), (0, 1)))
        self.assertEqual(sight.shoot_line(g, (0, 1), (4, 3), 30), ((0, 1), (4, 2)))   # and back

    def test_no_lean_away_from_the_corner(self):
        g = sight.CharGrid(CORNER)
        self.assertEqual(sight.lean_cells(g, (4, 5), (0, 2)), [(4, 5)])
        self.assertIsNone(sight.shoot_line(g, (4, 5), (0, 2), 30))

    def test_cover_beside_the_shooter(self):
        g = sight.CharGrid(["....", ".c..", "...."])                     # c: a sandbag at (1, 1)
        self.assertIn((1, 1), sight.lean_cells(g, (1, 0), (1, 2)))       # north, toward the target
        self.assertNotIn((1, 1), sight.lean_cells(g, (1, 0), (3, 0)))    # east: not that side


class LeanBranchTest(unittest.TestCase):
    """Each of the eight lean branches on a 3x3 patch round (1, 1), isolated by blocking the other diagonal."""
    CASES = [  # rows north first (z 2, 1, 0), the other pawn's cell, the lean cell expected, one not expected
        (["##.", "...", "..."], (1, 9), (2, 1), (0, 1)),     # east, past a block to the north
        (["...", "...", "##."], (1, -9), (2, 1), (0, 1)),    # east, past a block to the south
        ([".##", "...", "..."], (1, 9), (0, 1), (2, 1)),     # west, past a block to the north
        (["...", "...", ".##"], (1, -9), (0, 1), (2, 1)),    # west, past a block to the south
        (["#..", "#..", "..."], (-9, 1), (1, 0), (1, 2)),    # south, past a block to the west
        (["..#", "..#", "..."], (9, 1), (1, 0), (1, 2)),     # south, past a block to the east
        (["...", "#..", "#.."], (-9, 1), (1, 2), (1, 0)),    # north, past a block to the west
        (["...", "..#", "..#"], (9, 1), (1, 2), (1, 0)),     # north, past a block to the east
    ]

    def test_each_branch(self):
        for rows, other, want, not_want in self.CASES:
            got = sight.lean_cells(sight.CharGrid(rows), (1, 1), other)
            self.assertIn(want, got, rows)
            self.assertNotIn(not_want, got, rows)
            self.assertIn((1, 1), got)

    def test_wrong_side_gives_no_lean(self):
        self.assertEqual(sight.lean_cells(sight.CharGrid(["##.", "...", "..."]), (1, 1), (1, -9)), [(1, 1)])


class DoorwayTest(unittest.TestCase):
    def test_a_pawn_in_a_doorway_holds_it_open(self):
        g = sight.CharGrid(["#####",
                            "....+",
                            "#####"])
        self.assertEqual(sight.shoot_line(g, (0, 1), (4, 1), 30), ((0, 1), (4, 1)))
        self.assertIsNone(sight.shoot_line(sight.CharGrid(["#####", "...+.", "#####"]), (0, 1), (4, 1), 30))


class ThingGridTest(unittest.TestCase):
    """Cells judged from the things on them (data/cover.json), as the game does."""

    def grid(self, things, open_doors=False):
        calls = []

        def fetch(x0, z0, x1, z1):
            calls.append((x0, z0, x1, z1))
            return [t for t in things if x0 <= t["x"] <= x1 and z0 <= t["z"] <= z1]
        g = sight.ThingGrid(fetch, size=(60, 60), open_doors=open_doors, tile=50)
        return g, calls

    def test_blocks_and_cover(self):
        g, calls = self.grid([{"def": "Wall", "x": 3, "z": 3}, {"def": "Sandstone", "x": 4, "z": 3},
                              {"def": "Plant_Bush", "x": 5, "z": 5}, {"def": "Urn", "x": 6, "z": 5},
                              {"def": "ChunkSandstone", "x": 7, "z": 5}, {"def": "Door", "x": 8, "z": 5},
                              {"def": "Plant_Grass", "x": 9, "z": 5}, {"def": "Human", "x": 10, "z": 5}])
        self.assertTrue(g.blocks(3, 3) and g.blocks(4, 3) and g.blocks(8, 5))
        for c in ((5, 5), (6, 5), (7, 5)):
            self.assertFalse(g.blocks(*c), c)
            self.assertTrue(g.cover(*c), c)
        self.assertFalse(g.cover(9, 5) or g.cover(10, 5) or g.cover(0, 0))
        self.assertTrue(g.door(8, 5))
        self.assertEqual(calls, [(0, 0, 49, 49)])                    # one tile fetched, once
        g.blocks(55, 55)
        self.assertEqual(calls[-1], (50, 50, 59, 59))

    def test_rotated_footprints(self):
        # a 2x6 ship beam turned east lies along x (seen in game: base2_caw, cells 150-155 x 131-132)
        self.assertEqual(sorted(sight.occupied(152, 132, [2, 6], "East")),
                         [(x, z) for x in range(150, 156) for z in (131, 132)])
        self.assertEqual(sorted(sight.occupied(152, 132, [2, 6], "West")),
                         [(x, z) for x in range(149, 155) for z in (132, 133)])
        self.assertEqual(sight.occupied(155, 130, [1, 2], "South"), [(155, 129), (155, 130)])
        self.assertEqual(sight.occupied(155, 130, [1, 2], "North"), [(155, 130), (155, 131)])
        self.assertEqual(sight.occupied(5, 5, [1, 1], "East"), [(5, 5)])

    def test_rotations_are_asked_once_per_def(self):
        asked = []

        def rotations(name):
            asked.append(name)
            return {(152, 132): "East"}
        g = sight.ThingGrid(lambda *box: [{"def": "Ship_Beam", "x": 152, "z": 132}], rotations=rotations)
        self.assertTrue(g.blocks(155, 131))
        self.assertFalse(g.blocks(152, 135))                          # where a north beam would be
        self.assertEqual(asked, ["Ship_Beam"])

    def test_a_bush_beside_the_shooter_is_a_lean_cell(self):
        g, _ = self.grid([{"def": "Wall", "x": 2, "z": 9}, {"def": "Plant_Bush", "x": 0, "z": 9}])
        self.assertIn((0, 9), sight.lean_cells(g, (0, 10), (21, 0)))


class RangeTest(unittest.TestCase):
    def test_range_and_adjacent(self):
        g = sight.CharGrid(["......"] * 3)
        self.assertTrue(sight.can_hit(g, (0, 0), (5, 0), 5))
        self.assertFalse(sight.can_hit(g, (0, 0), (5, 1), 5))            # 26 > 25
        self.assertFalse(sight.can_hit(g, (0, 0), (1, 1), 5))            # a standing hostile next to us
        self.assertTrue(sight.can_hit(g, (0, 0), (1, 1), 5, adjacent_ok=True))
        self.assertFalse(sight.can_hit(g, (0, 0), (2, 0), 30, min_range=3))

    def test_float32_ranges_and_touch(self):
        g = sight.CharGrid(["." * 40] * 12)
        self.assertFalse(sight.in_range((0, 0), (30, 10), 1000 ** 0.5))   # 1000 > float32(31.62...)^2
        self.assertTrue(sight.in_range((0, 0), (30, 10), 31.7))
        with self.assertRaises(ValueError):
            sight.shoot_line(g, (0, 0), (1, 0), 1.42)


if __name__ == "__main__":
    unittest.main()
