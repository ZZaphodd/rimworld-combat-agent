"""Grade, trade ratio and superiority on fixture rows (no game)."""
import math
import unittest

from rca.eval import report, scoring


def row(**kw):
    r = {"squad_size": 14, "deaths": 0, "downed_at_end": 0, "squad_kidnapped": 0,
         "enemies_seen": 10, "enemies_active_end": 0, "enemies_downed_end": 0,
         "enemies_killed": 10, "enemies_killed_inferred": 0, "enemies_escaped": 0,
         "enemy_neutralized_frac": 1.0, "hp_lost_pct": 0, "new_permanent_injuries": 0,
         "raid_fled_tick": None, "raid_satisfied_tick": None}
    r.update(kw)
    return r


class Grade(unittest.TestCase):
    def test_clean_sweep_is_decisive(self):
        self.assertEqual(scoring.grade(row()), "decisive")

    def test_sweep_at_heavy_cost_is_pyrrhic(self):
        # 8 of 14 lost: v1 called this decisive (EVAL_SPEC known gap)
        r = row(deaths=8)
        self.assertEqual(scoring.grade_v1(r), "decisive")
        self.assertEqual(scoring.grade(r), "pyrrhic")

    def test_standing_exactly_half_stays_decisive(self):
        self.assertEqual(scoring.grade(row(deaths=7)), "decisive")

    def test_kidnap_and_satisfied_are_defeats(self):
        self.assertEqual(scoring.grade(row(squad_kidnapped=1, deaths=1)), "defeat")
        self.assertEqual(scoring.grade(row(raid_satisfied_tick=900)), "defeat")

    def test_active_enemies_unresolved(self):
        self.assertEqual(scoring.grade(row(enemies_active_end=2, enemies_killed=8)), "unresolved")

    def test_fallback_without_message(self):
        r = row(enemies_killed=3, enemies_escaped=7)
        self.assertEqual(scoring.grade(r), "defeat")          # broken 0.3 < 0.5
        r = row(enemies_killed=6, enemies_escaped=4)
        self.assertEqual(scoring.grade(r), "repelled")
        r = row(enemies_killed=3, enemies_escaped=7, raid_fled_tick=500)
        self.assertEqual(scoring.grade(r), "repelled")        # the game said they fled

    def test_pre_tracker_rows_use_stored_win(self):
        self.assertEqual(scoring.grade({"win": True, "squad_size": 5, "deaths": 0}), "decisive")


class Trade(unittest.TestCase):
    def test_point_weighted(self):
        r = row(deaths=1, enemy_seen_points=1000, enemy_lost_points=600)
        t = scoring.trade(r)
        # colonist = 4 x mean raider (100) = 400
        self.assertEqual(t["our_lost_points"], 400)
        self.assertAlmostEqual(t["ler"], 1.5)
        self.assertEqual(t["ler_basis"], "points")

    def test_count_rows_use_scenario_mean(self):
        r = row(deaths=2, enemies_killed=4, enemies_escaped=6)
        t = scoring.trade(r, mean_points=50)
        self.assertEqual(t["enemy_lost_points"], 200)
        self.assertEqual(t["our_lost_points"], 400)
        self.assertAlmostEqual(t["ler"], 0.5)
        self.assertEqual(t["ler_basis"], "count_x_mean")

    def test_colonist_value_parameter(self):
        r = row(deaths=1, enemies_killed=4)
        self.assertAlmostEqual(scoring.trade(r, 10, colonist_enemies=2)["ler"], 2.0)

    def test_clean_and_empty_trades(self):
        self.assertEqual(scoring.trade(row())["ler"], math.inf)
        t = scoring.trade(row(enemies_killed=0, enemies_escaped=10))
        self.assertIsNone(t["ler"])
        self.assertEqual(scoring.ler_key(t), (1.0, 0))

    def test_pre_tracker_count_from_fraction(self):
        r = {"deaths": 1, "enemies_seen": 8, "enemy_neutralized_frac": 0.5, "squad_size": 10}
        self.assertEqual(scoring.trade(r, 100)["enemy_lost_points"], 400)

    def test_pooled(self):
        ts = [scoring.trade(row(deaths=1, enemies_killed=4), 10),
              scoring.trade(row(enemies_killed=2), 10)]
        self.assertAlmostEqual(scoring.pooled_ler(ts), 60 / 40)
        self.assertEqual(scoring.pooled_ler(ts[1:]), math.inf)


class Superiority(unittest.TestCase):
    def test_ties_half(self):
        self.assertEqual(report.superiority([1, 2], [1, 2]), 0.5)
        self.assertEqual(report.superiority([3], [1, 2]), 1.0)

    def test_inf_keys_tiebreak_on_points(self):
        a = scoring.ler_key(scoring.trade(row(enemies_killed=10)))
        b = scoring.ler_key(scoring.trade(row(enemies_killed=5, enemies_escaped=5)))
        self.assertEqual(report.superiority([a], [b]), 1.0)

    def test_summary_separates_configs_and_compares_with_amove(self):
        rows = []
        for agent, deaths in (("b1", 2), ("turtle", 0)):
            for cyc in ("fixed:120", "adaptive:30/120@40"):
                rows.append(row(scenario="s", agent=agent, deaths=deaths, cycle=cyc,
                                agent_version=1))
        for r in rows:
            r["agent"] = {"b1": "amove"}.get(r["agent"], r["agent"])
        s = report.summarize(rows, {"s": 100})
        self.assertEqual(set(s), {"fixed:120", "adaptive:30/120@40"})
        cell = s["fixed:120"]["cells"][("s", "turtle@v1")]
        self.assertEqual(cell["p_ler"], 1.0)
        self.assertIsNone(s["fixed:120"]["cells"][("s", "amove@v1")]["p_ler"])


if __name__ == "__main__":
    unittest.main()
