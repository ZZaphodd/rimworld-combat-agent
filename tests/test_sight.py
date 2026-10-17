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
