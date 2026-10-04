"""Replay agent helpers (rca/tactical/replay.py): timelines, cells, loadout targets."""
import unittest

from rca.tactical import replay

POLLS = [
    {"t": 0, "ours": [{"id": "A", "x": 1, "z": 1, "w": "Pila (poor)"},
                      {"id": "B", "x": 5, "z": 5, "w": "Steel ikwa (poor)"}]},
    {"t": 100, "ours": [{"id": "A", "x": 2, "z": 2, "w": "Steel ikwa (poor)", "dr": 1},
                        {"id": "B", "x": 6, "z": 6, "w": "Pila (poor)", "dr": 1}]},
    {"t": 200, "ours": [{"id": "A", "x": 9, "z": 9, "w": "Steel ikwa (poor)", "dr": 1, "d": 1},
                        {"id": "B", "x": 7, "z": 7, "w": "Pila (poor)", "dr": 1}]},
]


class ReplayTest(unittest.TestCase):
    def test_cells_follow_the_human_and_hold_once_down(self):
        lines = replay.timelines(POLLS)
        self.assertEqual(replay.cell_at(lines["A"], -50), (1, 1))      # before the first poll
        self.assertEqual(replay.cell_at(lines["A"], 150), (2, 2))
        self.assertEqual(replay.cell_at(lines["A"], 999), (2, 2))      # down at 200: hold
        self.assertEqual(replay.cell_at(lines["B"], 999), (7, 7))

    def test_loadout_is_the_weapon_when_first_drafted(self):
        self.assertEqual(replay.target_weapons(POLLS),
                         {"A": "Steel ikwa (poor)", "B": "Pila (poor)"})


if __name__ == "__main__":
    unittest.main()
