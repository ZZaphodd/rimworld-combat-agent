"""Fate classification on synthetic observation sequences (fake RimMolt)."""
import unittest

from rca.eval.tracker import BattleTracker, enemy_fate


class FakeRM:
    """Plays back frames: each frame = {hostiles: [...], player: [...],
    jobs: {id: job}, logs: {id: [text]}}; the tracker advances one per observe."""

    def __init__(self, frames):
        self.frames, self.i = frames, 0

    def frame(self):
        return self.frames[max(0, min(self.i, len(self.frames)) - 1)]

    def call(self, tool, _timeout=None, **a):
        f = self.frame()
        if tool == "list_things":
            if a.get("faction") == "hostile":
                self.i += 1                           # observe() starts with hostiles
                return {"things": self.frames[self.i - 1]["hostiles"]}
            return {"things": self.frames[self.i - 1]["player"]}
        if tool == "get_pawn":
            if a.get("tab") == "log":
                return {"entries": [{"text": t} for t in f.get("logs", {}).get(a["id"], [])]}
            if a.get("tab") == "records":
                return {"records": [{"record": "Kills", "value": 0}]}
            return {"job": f.get("jobs", {}).get(a["id"], "")}
        raise AssertionError(tool)


def h(i, x, z, label="Raider", kind="Mercenary_Gunner", downed=False, defn="Human"):
    return {"id": i, "label": f"{label}, Pirate", "def": defn, "kind": kind, "x": x, "z": z,
            "downed": downed}


def us(i, x, z, label="Ally", downed=False):
    return {"id": i, "label": f"{label}, Colonist", "x": x, "z": z, "downed": downed}


class Fates(unittest.TestCase):
    def test_pure_rules(self):
        e = {"mech": False, "name": "A", "downed": False, "job": "", "x": 100, "z": 100}
        self.assertEqual(enemy_fate({**e, "mech": True}, set(), 5), "destroyed")
        self.assertEqual(enemy_fate(e, {"A"}, 5), "killed")
        self.assertEqual(enemy_fate({**e, "downed": True}, set(), 5), "killed_inferred")
        self.assertEqual(enemy_fate({**e, "job": "fleeing."}, set(), 5), "escaped")
        self.assertEqual(enemy_fate({**e, "x": 3}, set(), 5), "escaped")
        self.assertEqual(enemy_fate(e, set(), 5), "killed_inferred")

    def test_sequence(self):
        squad = [us("c1", 120, 120, "Ann"), us("c2", 122, 120, "Bob")]
        frames = [
            {"hostiles": [h("r1", 140, 120, "Rex"), h("r2", 150, 120, "Sid"),
                          h("r3", 160, 120, "Tom"), h("m1", 170, 120, "Mech", "Mech_Scyther",
                                                     defn="Mech_Scyther")],
             "player": squad},
            # r1 downed, r2 walks to the edge, Bob downed
            {"hostiles": [h("r1", 140, 120, "Rex", downed=True), h("r2", 2, 120, "Sid"),
                          h("r3", 123, 121, "Tom"), h("m1", 170, 120, "Mech", "Mech_Scyther",
                                                     defn="Mech_Scyther")],
             "player": [squad[0], us("c2", 122, 120, "Bob", downed=True)],
             "jobs": {"r3": "kidnapping Bob.", "r2": "exiting map."}},
            # r1 gone (log: killed), r2 gone near edge (escaped), mech gone
            # (destroyed), r3 gone with a kidnapping job (escaped) and Bob with him
            {"hostiles": [], "player": [squad[0]],
             "logs": {"c1": ["Rex perished."]}},
        ]
        rm = FakeRM(frames)
        t = BattleTracker(rm, ["c1", "c2"], harvest_ticks=10 ** 9)
        for now in (0, 120, 240):
            t.observe(now)
        f = t.finish()
        self.assertEqual(f["enemies_seen"], 4)
        self.assertEqual(f["enemies_killed"], 2)          # Rex by log, mech destroyed
        self.assertEqual(f["enemies_escaped"], 2)         # Sid at the edge, Tom kidnapping
        self.assertEqual(f["enemies_killed_inferred"], 0)
        self.assertEqual(f["squad_kidnapped"], 1)
        self.assertEqual(f["squad_dead"], 0)
        self.assertEqual(f["enemy_seen_points"], 85 * 3 + 150)
        self.assertEqual(f["enemy_lost_points"], 85 + 150)
        self.assertEqual(f["enemy_escaped_points"], 170)

    def test_ambiguous_kidnap_flagged(self):
        squad = [us("c1", 120, 120, "Ann"), us("c2", 122, 120, "Ann", downed=True)]
        frames = [{"hostiles": [h("r1", 122, 121)], "player": squad,
                   "jobs": {"r1": "kidnapping Ann."}},
                  {"hostiles": [], "player": [squad[0]]}]
        t = BattleTracker(FakeRM(frames), ["c1", "c2"], harvest_ticks=10 ** 9)
        t.observe(0)
        t.observe(30)
        self.assertEqual(t.finish()["debug_kidnap_ambiguous"], ["ann"])


if __name__ == "__main__":
    unittest.main()
