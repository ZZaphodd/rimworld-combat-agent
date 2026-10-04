"""tools/gate.py on synthetic rows: the no-regression rule (WORKFLOW.md)."""
import importlib.util
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))                      # tools/_path
_spec = importlib.util.spec_from_file_location("gate", TOOLS / "gate.py")
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

THEMES = [f"theme_{i}" for i in range(7)]


def row(agent="amove", version=6, scenario="theme_0", deaths=0, lost_pts=500.0, **kw):
    r = {"agent": agent, "agent_raw": agent, "agent_version": version, "scenario": scenario,
         "cycle": "adaptive:30/120@40", "reflex": True, "reflex_version": 4,
         "deaths": deaths, "enemy_lost_points": lost_pts, "enemy_seen_points": 1000.0,
         "enemies_seen": 10, "options": {}}
    return r | kw


def cell(deaths, **kw):
    return [row(deaths=d, **kw) for d in deaths]


BASE = [0, 1, 2, 0, 1, 1, 0, 2, 1, 0]          # mean 0.8


class Metrics(unittest.TestCase):
    def test_trade_share(self):
        self.assertEqual(gate.run_metrics(row(deaths=0, lost_pts=0))["trade"], 0.5)
        self.assertEqual(gate.run_metrics(row(deaths=0))["trade"], 1.0)
        # 1 colonist = 4 x 100 points; 400 lost each way -> even trade
        self.assertAlmostEqual(gate.run_metrics(row(deaths=1, lost_pts=400))["trade"], 0.5)


class Gate(unittest.TestCase):
    def run_gate(self, base, branch, **kw):
        cells, agents, passed, _, _ = gate.gate(base, branch, **kw)
        return {c["scenario"]: c for c in cells}, agents, passed

    def test_identical_passes(self):
        rows = [r for s in THEMES for r in cell(BASE, scenario=s)]
        cells, agents, passed = self.run_gate(rows, rows)
        self.assertTrue(passed)
        self.assertTrue(all(c["verdict"] == "ok" for c in cells.values()))
        self.assertEqual(agents["amove"]["verdict"], "ok")

    def test_noise_level_difference_passes(self):
        base = [r for s in THEMES for r in cell(BASE, scenario=s)]
        worse = [1, 1, 2, 0, 1, 1, 1, 2, 1, 0]     # +0.2 per battle in one cell
        branch = [r for s in THEMES for r in cell(worse if s == "theme_3" else BASE, scenario=s)]
        cells, agents, passed = self.run_gate(base, branch)
        self.assertTrue(passed, cells["theme_3"])

    def test_large_cell_regression_fails(self):
        base = [r for s in THEMES for r in cell(BASE, scenario=s)]
        bad = [d + 3 for d in BASE]                 # +3 colonists per battle in one cell
        branch = [r for s in THEMES for r in cell(bad if s == "theme_2" else BASE, scenario=s)]
        cells, agents, passed = self.run_gate(base, branch)
        self.assertFalse(passed)
        self.assertTrue(cells["theme_2"]["verdict"].startswith("REGRESS"))
        self.assertIn("lost", cells["theme_2"]["verdict"])
        self.assertEqual(cells["theme_0"]["verdict"], "ok")

    def test_small_shift_everywhere_fails_at_agent_level(self):
        """+0.5 colonists per battle in every cell: no single cell is beyond
        noise, the pooled agent is."""
        base = [r for s in THEMES for r in cell(BASE, scenario=s)]
        shifted = [0, 1, 2, 1, 2, 1, 1, 2, 2, 1]   # mean 1.3
        branch = [r for s in THEMES for r in cell(shifted, scenario=s)]
        cells, agents, passed = self.run_gate(base, branch)
        self.assertFalse(any(c["verdict"].startswith("REGRESS") for c in cells.values()))
        self.assertTrue(agents["amove"]["verdict"].startswith("REGRESS"))
        self.assertFalse(passed)

    def test_better_is_not_a_regression(self):
        base = [r for s in THEMES for r in cell(BASE, scenario=s)]
        branch = [r for s in THEMES for r in cell([0] * 10, scenario=s)]
        self.assertTrue(self.run_gate(base, branch)[2])

    def test_trade_regression(self):
        base = [r for s in THEMES for r in cell([1] * 10, scenario=s, lost_pts=900)]
        branch = [r for s in THEMES for r in cell([1] * 10, scenario=s, lost_pts=900)
                  if s != "theme_1"] + cell([1] * 10, scenario="theme_1", lost_pts=100)
        cells, agents, passed = self.run_gate(base, branch)
        self.assertEqual(cells["theme_1"]["verdict"], "REGRESS trade")
        self.assertFalse(passed)

    def test_incomplete_cell_fails(self):
        base = cell(BASE)
        cells, _, passed = self.run_gate(base, cell(BASE[:3]))
        self.assertEqual(cells["theme_0"]["verdict"], "INCOMPLETE")
        self.assertFalse(passed)

    def test_versions_options_and_config(self):
        base = (cell([5] * 10, version=4) + cell(BASE, version=5)
                + cell([9] * 10, version=5, options={"rescue": "on"}, agent="doctrine")
                + cell(BASE, version=5, agent="doctrine", options={"rescue": "off"}))
        branch = (cell(BASE, version=6) + cell(BASE, version=6, agent="doctrine")
                  + cell([9] * 10, version=6, cycle="fixed:120"))
        with self.assertRaises(SystemExit):              # branch mixes configs
            self.run_gate(base, branch)
        branch = branch[:20]
        cells, agents, passed = self.run_gate(base, branch)
        self.assertTrue(passed)                          # v5 natural options, not v4 / rescue=on
        cells, agents, passed = self.run_gate(base, branch, agents=["amove"],
                                              base_version={"amove": 4})
        self.assertTrue(passed)                          # vs v4 (5 lost) the branch is better
        self.assertEqual(list(agents), ["amove"])


if __name__ == "__main__":
    unittest.main()
