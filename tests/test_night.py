"""Failure-mining helpers (roadmap 3): badness ranking and the router briefing."""
import unittest

from rca.eval.ranking import badness, worst
from rca.strategic.briefing import features, text


def row(**k):
    base = {"deaths": 0, "squad_kidnapped": 0, "downed_at_end": 0, "new_permanent_injuries": 0,
            "hp_lost_pct": 0, "grade": "decisive"}
    return {**base, **k}


class Ranking(unittest.TestCase):
    def test_components(self):
        score, parts = badness(row(deaths=1, squad_kidnapped=1, downed_at_end=2,
                                   new_permanent_injuries=3, hp_lost_pct=100, grade="defeat"))
        self.assertEqual(parts, {"lost": 20.0, "downed": 6.0, "permanent": 6.0, "hp": 4.0,
                                 "grade": 10.0})
        self.assertEqual(score, 46.0)

    def test_clean_win_is_zero_and_sorts_last(self):
        rows = [row(grade="decisive"), row(deaths=1, grade="repelled"), row(downed_at_end=4)]
        self.assertEqual(badness(rows[0])[0], 0.0)
        self.assertEqual([r["deaths"] for r in worst(rows, 2)], [0, 1])   # 12 downed pts > 10 lost
        self.assertEqual(worst(rows)[0]["downed_at_end"], 4)


class Briefing(unittest.TestCase):
    M = {"id": "rand_001", "spec": {"arena": "arena_open", "squad": {"faction": "Pirate"},
                                    "enemy": {"faction": "TribeRough"}},
         "squad": [{"name": "A B", "weapon": "Assault rifle (good)", "class": "medium", "x": 0, "z": 0},
                   {"name": "C D", "weapon": "Longsword (normal)", "class": "melee", "x": 2, "z": 0}],
         "enemy": [{"def": "Tribal_Warrior", "weapon": "Club", "class": "melee", "x": 40, "z": 0},
                   {"def": "Tribal_Archer", "weapon": "Short bow", "class": "bow", "x": 42, "z": 0},
                   {"def": "Tribal_Warrior", "weapon": "Spear", "class": "melee", "x": 41, "z": 2}]}

    def test_features(self):
        f = features(self.M)
        self.assertEqual((f["squad_n"], f["enemy_n"], f["squad_melee"]), (2, 3, 1))
        self.assertEqual(f["enemy_melee_share"], 0.67)
        self.assertEqual(f["enemy_closer_share"], 0.67)
        self.assertFalse(f["mech"])
        self.assertAlmostEqual(f["distance"], 40.0, places=1)

    def test_text_mentions_both_sides(self):
        t = text(self.M, features(self.M))
        self.assertIn("our Pirate x2 vs TribeRough x3", t)
        self.assertIn("Tribal_Warrior/Club", t)


if __name__ == "__main__":
    unittest.main()
