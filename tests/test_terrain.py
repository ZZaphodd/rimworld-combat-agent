"""LOS, BFS, legend and cache invalidation on synthetic grids."""
import unittest

from rca.terrain import Terrain


def synthetic(rows_south_first, size=None):
    """fetch() over a fixed map given south-first rows; counts calls."""
    size = size or len(rows_south_first)
    calls = []

    def fetch(x0, z0, x1, z1):
        calls.append((x0, z0, x1, z1))
        return [rows_south_first[z][x0:x1 + 1] for z in range(z1, z0 - 1, -1)]   # north first
    return Terrain(size=size, tile=5, fetch=fetch), calls


OPEN = ["." * 10] * 10


class Legend(unittest.TestCase):
    def test_chars(self):
        rows = ["#%~*+.V?.." ] + ["." * 10] * 9
        t, _ = synthetic(rows)
        self.assertFalse(t.passable(0, 0))      # wall
        self.assertFalse(t.passable(1, 0))      # rock
        self.assertFalse(t.passable(2, 0))      # water/marsh (conservative)
        self.assertTrue(t.passable(3, 0))       # tree
        self.assertTrue(t.passable(4, 0))       # door
        self.assertTrue(t.passable(6, 0))       # geyser
        self.assertTrue(t.passable(7, 0))       # fog
        self.assertTrue(t.blocks_los(4, 0))
        self.assertFalse(t.blocks_los(3, 0))
        self.assertEqual(t.cover(3, 0), "half")
        self.assertEqual(t.cover(0, 0), "full")
        self.assertEqual(t.cell(-1, 3), "#")    # outside the map
        self.assertEqual(t.stats["unknown_chars"], 0)

    def test_orientation_north_first(self):
        rows = ["." * 10 for _ in range(10)]
        rows[7] = "...#......"                  # z = 7
        t, _ = synthetic(rows)
        self.assertEqual(t.cell(3, 7), "#")
        self.assertEqual(t.cell(3, 2), ".")


class Los(unittest.TestCase):
    def test_wall_blocks_and_endpoints_never_block(self):
        rows = ["." * 10 for _ in range(10)]
        rows[5] = "....#....."
        t, _ = synthetic(rows)
        self.assertFalse(t.los((0, 5), (9, 5)))
        self.assertTrue(t.los((0, 0), (9, 0)))
        self.assertTrue(t.los((4, 5), (9, 5)))  # standing in the wall cell
        self.assertTrue(t.los((0, 5), (4, 5)))

    def test_trees_do_not_block(self):
        rows = ["*" * 10 for _ in range(10)]
        t, _ = synthetic(rows)
        self.assertTrue(t.los((0, 0), (9, 9)))


class Bfs(unittest.TestCase):
    def test_wall_with_gap(self):
        rows = ["." * 10 for _ in range(10)]
        for z in range(10):
            if z != 8:
                rows[z] = rows[z][:5] + "#" + rows[z][6:]
        t, _ = synthetic(rows)
        d = t.bfs((0, 0))
        self.assertIn((9, 0), d)
        self.assertGreater(d[(9, 0)], 9)        # has to go round through z = 8
        d4 = t.bfs((0, 0), diagonal=False)
        self.assertGreaterEqual(d4[(9, 0)], d[(9, 0)])

    def test_no_corner_cutting(self):
        rows = ["." * 10 for _ in range(10)]
        rows[1] = "#........."
        rows[0] = ".#........"
        t, _ = synthetic(rows)
        self.assertNotIn((1, 1), t.neighbours((0, 0)))

    def test_limit(self):
        t, _ = synthetic(OPEN)
        d = t.bfs((5, 5), limit=2)
        self.assertEqual(max(d.values()), 2)


class Cache(unittest.TestCase):
    def test_lazy_tiles_and_explosion_invalidation(self):
        t, calls = synthetic(OPEN)
        t.cell(1, 1)
        self.assertEqual(len(calls), 1)         # one 5x5 tile only
        t.cell(2, 2)
        self.assertEqual(len(calls), 1)
        t.update(10, explosions=[(2, 2)])
        self.assertEqual(len(calls), 1)         # lazy: nothing fetched yet
        t.cell(2, 2)
        self.assertEqual(len(calls), 2)
        self.assertEqual(t.stats["refetches"], 1)

    def test_fire_refresh_respects_age(self):
        t, calls = synthetic(OPEN)
        t.cell(1, 1)
        t.update(100, fires=[(1, 1)])           # tile is 100 ticks old: keep
        t.cell(1, 1)
        self.assertEqual(len(calls), 1)
        t.update(700, fires=[(1, 1)])
        t.cell(1, 1)
        self.assertEqual(len(calls), 2)

    def test_building_delta_marks_structure_tiles_only(self):
        rows = ["." * 10 for _ in range(10)]
        rows[0] = "#........."
        t, calls = synthetic(rows)
        t.cell(0, 0)
        t.cell(7, 7)
        t.update(5, delta={"removedBuildings": [{"def": "Wall", "count": 1}]})
        self.assertEqual(t.stats["stale_building"], 1)

    def test_contact_refresh_near_squad(self):
        t, calls = synthetic(OPEN)
        t.cell(1, 1)
        t.update(600, squad=[(1, 1)], contact=True)
        self.assertEqual(t.stats["stale_contact"], 1)

    def test_episodes_do_not_share(self):
        a, _ = synthetic(OPEN)
        b, _ = synthetic(OPEN)
        a.cell(1, 1)
        self.assertEqual(b.tiles, {})


if __name__ == "__main__":
    unittest.main()
