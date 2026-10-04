"""Squad down no longer ends an episode (harness.watch_after_down): record it, watch on."""
import unittest

from rca.eval import harness


class Tracker:
    squad = {"a": {"fate": None, "downed": True}, "b": {"fate": "pending", "downed": True}}
    enemy = {"x": {"fate": None, "downed": False}, "y": {"fate": "killed"}, "z": {"fate": None, "downed": True}}


class SquadDownTest(unittest.TestCase):
    def test_records_the_first_moment_and_stops_only_after_the_window(self):
        quiet = lambda s: None                      # noqa: E731
        down, stop = harness.watch_after_down([{"downed": False}], Tracker, [], 100, None, quiet)
        self.assertEqual((down, stop), (None, False))
        down, stop = harness.watch_after_down([{"downed": True}], Tracker, [{"id": "x"}], 200, None, quiet)
        self.assertEqual(down, {"tick": 200, "missing": 1, "downed": 1, "enemies_standing": 1,
                                "enemies_out": 2})
        self.assertFalse(stop)
        again, stop = harness.watch_after_down([{"downed": True}], Tracker, [], 300, down, quiet)
        self.assertIs(again, down)                  # the first moment is kept
        self.assertFalse(stop)
        _, stop = harness.watch_after_down([{"downed": True}], Tracker, [], 200 + harness.AFTER_DOWN_TICKS,
                                           down, quiet)
        self.assertTrue(stop)


if __name__ == "__main__":
    unittest.main()
