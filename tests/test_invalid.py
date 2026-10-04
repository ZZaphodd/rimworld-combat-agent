"""Strive to Survive guards (EVAL_SPEC §3): invalid episodes and the difficulty key."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rca.eval import harness
from rca.eval.results import done_counts, read_rows, row_difficulty


def write(rows):
    p = Path(tempfile.mkdtemp()) / "r.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return p


class Rows(unittest.TestCase):
    def test_invalid_rows_are_skipped_unless_asked(self):
        p = write([{"scenario": "s", "agent": "amove", "outcome": "invalid"},
                   {"scenario": "s", "agent": "amove", "outcome": "enemies_cleared"}])
        self.assertEqual([r["outcome"] for r in read_rows(p)], ["enemies_cleared"])
        self.assertEqual(len(read_rows(p, invalid=True)), 2)

    def test_difficulty_default_and_resume_key(self):
        self.assertEqual(row_difficulty({}), "peaceful")
        self.assertEqual(row_difficulty({"difficulty": "Strive to survive"}), "strive to survive")
        base = {"scenario": "s", "agent": "amove", "agent_version": 6, "cycle": "fixed:120"}
        rows = [dict(base), dict(base, difficulty="strive to survive")]
        cfg = ("fixed:120", False, None)
        self.assertEqual(done_counts(rows, {"amove": 6}.get, cfg)[("s", "amove")], 2)
        self.assertEqual(done_counts(rows, {"amove": 6}.get, cfg,
                                     difficulty="strive to survive")[("s", "amove")], 1)


class Guard(unittest.TestCase):
    def test_unexpected_hostiles(self):
        enemies = {"a": {"kind": "Mercenary_Gunner"}, "b": {"kind": "Tribal_Warrior"}}
        self.assertEqual(harness.unexpected_hostiles({"a", "b"}, enemies), {})
        self.assertEqual(list(harness.unexpected_hostiles({"a"}, enemies)), ["b"])

    def _batch(self, outcomes):
        """run_batch with run_episode replaced by a script of outcomes."""
        p = Path(tempfile.mkdtemp()) / "r.jsonl"
        script = iter(outcomes)

        def fake(rm, m, agent, *a, **k):
            o = next(script)
            if isinstance(o, Exception):
                raise o
            return {"scenario": m["id"], "agent": agent.name, "agent_version": agent.version,
                    "outcome": o, "difficulty": "strive to survive", "grade": None, "ler": None,
                    **{k_: 0 for k_ in ("deaths", "downed_at_end", "enemies_seen",
                                        "enemies_killed", "enemies_killed_inferred",
                                        "enemies_downed_end", "enemies_escaped",
                                        "enemies_active_end", "trade_enemy_points", "ticks",
                                        "wall_s", "progress_rate", "longest_no_progress_ticks",
                                        "fire_share", "enemy_fire_share")},
                    "unattainable_reason": None, "kpis": {}}
        with mock.patch.object(harness, "run_episode", fake), \
                mock.patch.object(harness.time, "sleep", lambda s: None):
            harness.run_batch(None, [{"id": "s"}], ["amove"], 1, p, harness.Cycle(),
                              log=lambda s: None)
        return p

    def test_invalid_episode_is_written_and_rerun(self):
        p = self._batch(["invalid", "invalid", "enemies_cleared"])
        self.assertEqual([r["outcome"] for r in read_rows(p, invalid=True)],
                         ["invalid", "invalid", "enemies_cleared"])
        self.assertEqual(len(read_rows(p)), 1)

    def test_gives_up_after_three_invalid_tries(self):
        p = self._batch(["invalid"] * 3)
        self.assertEqual(len(read_rows(p, invalid=True)), 3)
        self.assertEqual(read_rows(p), [])

    def test_wrong_difficulty_stops_the_batch(self):
        with self.assertRaises(harness.WrongDifficulty):
            self._batch([harness.WrongDifficulty("peaceful")])


if __name__ == "__main__":
    unittest.main()
