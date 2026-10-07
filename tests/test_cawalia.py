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

    def test_floor_and_ids(self):
        h = [{"mult": 0.5, "win": False, "grade": "defeat"}]
        self.assertEqual(cawalia.next_step(h)[0], 0.5)
        self.assertEqual(cawalia.pid("pirate", 2.5), "base2_caw_pirate_2p5x")
        self.assertEqual(cawalia.pid("tribe", 3.0), "base2_caw_tribe_3x")


if __name__ == "__main__":
    unittest.main()
