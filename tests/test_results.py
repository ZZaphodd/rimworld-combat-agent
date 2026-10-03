"""Resume keys and canonical names (LESSONS bug 8)."""
import json
import tempfile
import unittest
from pathlib import Path

from rca.eval.results import canonical, done_counts, read_rows, row_config


class Resume(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "r.jsonl"
        rows = [
            {"scenario": "s", "agent": "hold", "agent_version": 7, "cycle": "fixed:120"},
            {"scenario": "s", "agent": "turtle", "agent_version": 7, "cycle": "fixed:120"},
            {"scenario": "s", "agent": "turtle", "agent_version": 6, "cycle": "fixed:120"},
            {"scenario": "s", "agent": "b1", "agent_version": 5, "cycle": "fixed:120"},
            {"scenario": "s", "agent": "amove", "agent_version": 5, "cycle": "adaptive:30/120@40",
             "reflex": True, "reflex_version": 4},
        ]
        self.tmp.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    def test_aliases_count_under_canonical_name(self):
        rows = read_rows(self.tmp)
        versions = {"turtle": 7, "amove": 5}
        done = done_counts(rows, versions.get, ("fixed:120", False, None))
        # 'hold' and 'turtle' rows of v7 both count; the CLI may say either name
        self.assertEqual(done[("s", canonical("hold"))], 2)
        self.assertEqual(done[("s", canonical("turtle"))], 2)
        self.assertEqual(done[("s", canonical("b1"))], 1)

    def test_config_must_match(self):
        rows = read_rows(self.tmp)
        done = done_counts(rows, {"amove": 5}.get, ("adaptive:30/120@40", True, 4))
        self.assertEqual(done[("s", "amove")], 1)

    def test_legacy_defaults(self):
        self.assertEqual(row_config({"step_ticks": 120}), ("fixed:120", False, None))
        self.assertEqual(row_config({"cycle": "adaptive:30/120@40", "reflex": True}),
                         ("adaptive:30/120@40", True, 1))


if __name__ == "__main__":
    unittest.main()
