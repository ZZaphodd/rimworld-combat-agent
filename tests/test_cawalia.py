"""Cawalia's raid-size staircase (tools/cawalia.py): +0.5x after a win, -0.5x after a loss,
floor 0.5x; unresolved rows do not move it; the kind rotates over counted battles."""
import sys
import unittest

sys.path.insert(0, "tools")
import cawalia  # noqa: E402


class StaircaseTest(unittest.TestCase):
    def test_steps(self):
        self.assertEqual(cawalia.next_step([]), (2.0, "tribe"))
        h = [{"mult": 2.0, "win": True, "grade": "repelled"}]
        self.assertEqual(cawalia.next_step(h), (2.5, "pirate"))
        h.append({"mult": 2.5, "win": False, "grade": "defeat"})
        self.assertEqual(cawalia.next_step(h), (2.0, "mech"))
        h.append({"mult": 2.0, "win": False, "grade": "unresolved"})     # does not count
        self.assertEqual(cawalia.next_step(h), (2.0, "mech"))

    def test_window_from_battle_14(self):
        res = [True] * 11 + [False]                       # battles 1-11 won, 14 lost (12-13 unresolved)
        h = [{"n": i + 1, "mult": 2.0 + 0.5 * i, "win": w, "grade": "repelled" if w else "conceded"}
             for i, w in enumerate(res[:11])]
        h += [{"n": 12, "mult": 7.5, "win": False, "grade": "unresolved"},
              {"n": 13, "mult": 7.5, "win": False, "grade": "unresolved"},
              {"n": 14, "mult": 7.5, "win": False, "grade": "conceded"}]
        self.assertEqual(cawalia.next_step(h), (8.0, "tribe"))   # 5 of the last 6 won: up
        h += [{"n": 15, "mult": 8.0, "win": False, "grade": "defeat"},
              {"n": 16, "mult": 8.5 - 1.0, "win": False, "grade": "defeat"}]
        self.assertEqual(cawalia.next_step(h)[0], 7.5)            # 3 won, 3 lost: hold
        h.append({"n": 17, "mult": 7.5, "win": False, "grade": "defeat"})
        self.assertEqual(cawalia.next_step(h)[0], 7.0)            # 2 won, 4 lost: down

    def test_floor_and_ids(self):
        h = [{"mult": 0.5, "win": False, "grade": "defeat"}]
        self.assertEqual(cawalia.next_step(h)[0], 0.5)
        self.assertEqual(cawalia.pid("pirate", 2.5), "base2_caw_pirate_2p5x")
        self.assertEqual(cawalia.pid("tribe", 3.0), "base2_caw_tribe_3x")


if __name__ == "__main__":
    unittest.main()
