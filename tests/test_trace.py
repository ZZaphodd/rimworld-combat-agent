"""Human-play trace (rca/eval/trace.py): pawn entries, poll lines, failed polls, end line."""
import tempfile
import unittest
from pathlib import Path

from rca.eval import trace

MANIFEST = {"id": "rand_000", "save": "scenario_rand_000",
            "squad": [{"id": "H1", "name": "Pogub 'Butters' Moilluoik", "weapon": "Frag grenades"}]}
PAWNS = [
    {"id": "H1", "label": "Butters<color=#999999FF>, Quack</color>", "x": 10, "z": 20,
     "faction": "New Arrivals", "hostile": False, "downed": False, "drafted": True},
    {"id": "H2", "label": "Mushinto", "x": 30, "z": 5, "hostile": True, "downed": True},
    {"id": "H3", "label": "Corpse", "x": 1, "z": 1, "hostile": True, "dead": True},
    {"id": "A1", "label": "Rat", "x": 2, "z": 2, "hostile": False},
]
SUMMARY = {"H1": {"health": 18, "weapon": "Machine pistol (normal)", "job": "standing."},
           "H2": {"health": 40, "weapon": "Pump shotgun (normal)", "job": "downed, unconscious."}}


class FakeRm:
    def __init__(self, fail=False):
        self.fail = fail

    def call(self, tool, **kw):
        if self.fail:
            raise RuntimeError("loading")
        if tool == "get_pawn":
            return SUMMARY[kw["id"]]
        if kw.get("category") == "pawn":
            return {"things": PAWNS}
        if kw.get("defName") == "Fire":
            return {"things": [{"x": 11, "z": 21}]}
        if kw.get("defName") == "Proj_GrenadeFrag":
            return {"things": [{"x": 25, "z": 8}]}
        return {"things": []}


class TraceTest(unittest.TestCase):
    def test_pawn_entry_flags_only_when_set(self):
        e = trace.pawn_entry(PAWNS[0], SUMMARY["H1"])
        self.assertEqual(e, {"id": "H1", "n": "Butters", "x": 10, "z": 20, "hp": 18,
                             "w": "Machine pistol (normal)", "j": "standing.", "dr": 1})
        self.assertEqual(trace.pawn_entry(PAWNS[1], SUMMARY["H2"])["d"], 1)

    def test_episode_lines(self):
        path = Path(tempfile.mkdtemp()) / "t" / "rand_000_human.jsonl.gz"
        t = trace.Trace(path, MANIFEST, "human")
        t.poll(FakeRm(), 120, ["Outlanders are fleeing."])
        t.poll(FakeRm(fail=True), 180)
        t.end({"outcome": "enemies_cleared", "ticks": 200, "grade": "decisive"})
        head, poll, failed, end = trace.read(path)
        self.assertEqual(head["scenario"], "rand_000")
        self.assertEqual(head["squad"][0]["w"], "Frag grenades")
        self.assertEqual([p["n"] for p in poll["ours"]], ["Butters"])
        self.assertEqual([p["n"] for p in poll["them"]], ["Mushinto"])   # no corpse, no rat
        self.assertEqual(poll["fires"], [[11, 21]])
        self.assertEqual(poll["proj"], [["frag", 25, 8]])
        self.assertEqual(poll["msg"], ["Outlanders are fleeing."])
        self.assertEqual(failed["t"], 180)
        self.assertIn("RuntimeError", failed["err"])
        self.assertEqual((end["end"], end["t"], end["grade"]), ("enemies_cleared", 200, "decisive"))


class LightRm(FakeRm):
    """get_pawn allowed only while `paused` (a light trace's load-time read)."""
    paused = True

    def call(self, tool, **kw):
        if tool == "get_pawn" and not self.paused:
            raise AssertionError("per-pawn read while the game runs")
        if tool == "list_colonists":
            return {"colonists": [{"id": "H1", "health": 55, "job": "melee attacking Mushinto."}]}
        return super().call(tool, **kw)


class LightTraceTest(unittest.TestCase):
    def test_weapons_once_then_bulk_reads_only(self):
        path = Path(tempfile.mkdtemp()) / "light.jsonl.gz"
        rm = LightRm()
        t = trace.Trace(path, MANIFEST, "human", light=True)
        t.ready(rm)
        rm.paused = False
        PAWNS[1]["targeting"] = "attacking colonist Butters"
        try:
            t.poll(rm, 60)
        finally:
            PAWNS[1].pop("targeting")
        t.end({"outcome": "x"})
        head, weapons, poll, _ = trace.read(path)
        self.assertTrue(head["light"])
        self.assertEqual(weapons["weapons"], {"H1": "Machine pistol (normal)", "H2": "Pump shotgun (normal)"})
        self.assertEqual((poll["ours"][0]["hp"], poll["ours"][0]["j"], poll["ours"][0]["w"]),
                         (55, "melee attacking Mushinto.", "Machine pistol (normal)"))
        self.assertEqual((poll["them"][0]["hp"], poll["them"][0]["j"], poll["them"][0]["w"]),
                         (None, "attacking colonist Butters", "Pump shotgun (normal)"))

    def test_full_trace_has_no_weapons_line(self):
        path = Path(tempfile.mkdtemp()) / "full.jsonl.gz"
        t = trace.Trace(path, MANIFEST, "human")
        t.ready(FakeRm())
        t.end({"outcome": "x"})
        self.assertEqual([("header" in x, "end" in x) for x in trace.read(path)], [(True, False), (False, True)])


class TruncatedTest(unittest.TestCase):
    def test_killed_writer_is_still_readable(self):
        tmp = Path(tempfile.mkdtemp())
        t = trace.Trace(tmp / "t.jsonl.gz", MANIFEST, "human")
        t.poll(FakeRm(), 120)
        killed = tmp / "killed.jsonl.gz"              # the bytes on disk before any close:
        killed.write_bytes((tmp / "t.jsonl.gz").read_bytes())   # no trailer, no end line
        t.end({"outcome": "x"})
        lines = trace.read(killed)
        self.assertEqual([("header" in x, x.get("t")) for x in lines], [(True, None), (False, 120)])


if __name__ == "__main__":
    unittest.main()
