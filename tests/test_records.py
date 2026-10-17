"""Combat records read during a battle (rca/eval/records.py): baseline, last read kept for a pawn
that is gone, reads every few polls, row totals."""
import unittest

from rca.eval import records

SQUAD = [{"id": "H1", "name": "Pogub 'Butters' Moilluoik"}, {"id": "H2", "name": "Taras Levy"}]


def reply(dealt, shots=0, kills=0, taken=0):
    rows = [{"record": "Damage dealt", "value": dealt}, {"record": "Shots fired", "value": shots},
            {"record": "Kills", "value": kills}, {"record": "Prisoners recruited", "value": 2}]
    if taken:
        rows.append({"record": "Damage taken", "value": taken})
    return {"tab": "records", "records": rows}


class FakeRm:
    """state[id]: the reply get_pawn gives now; None = 'Pawn not found' (dead or taken)."""

    def __init__(self, state):
        self.state, self.calls = state, 0

    def call(self, tool, **kw):
        if tool == "list_things":
            return {"things": [{"id": "H1", "label": "Butters<color=#999999FF>, Quack</color>"},
                               {"id": "H2", "label": "Levy, Hunter"}, {"id": "X9", "label": "Rat"}]}
        self.calls += 1
        assert tool == "get_pawn" and kw["tab"] == "records"
        v = self.state[kw["id"]]
        return v if v is not None else {"error": "Pawn not found."}


class RecordsTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(records.parse(reply(10, 3, 1, 7)),
                         {"dealt": 10, "shots": 3, "kills": 1, "taken": 7})
        self.assertIsNone(records.parse({"error": "Pawn not found."}))

    def test_baseline_dead_pawn_keeps_last_read_and_totals(self):
        rm = FakeRm({"H1": reply(5, 2), "H2": reply(0)})
        r = records.SquadRecords(rm, SQUAD, every=2)
        r.start()
        rm.state = {"H1": reply(40, 9, 1), "H2": reply(30, 0, 0, 12)}
        self.assertIsNone(r.poll(100))                       # 1st poll: skipped
        got = r.poll(200)                                    # 2nd poll: read
        self.assertEqual(got["Butters"], [35, 7, 1, 0, 0])
        rm.state = {"H1": reply(90, 20, 2), "H2": None}      # Levy died
        r.poll(300)
        got = r.poll(400)
        self.assertEqual(list(got), ["Butters"])
        row = r.poll(450, final=True) and r.row()
        self.assertEqual(row["squad_records"]["Levy"], {"dealt": 30, "shots": 0, "kills": 0,
                                                        "taken": 12, "headshots": 0, "tick": 200})
        self.assertEqual(row["squad_records"]["Butters"]["dealt"], 85)
        self.assertEqual(row["squad_records"]["Butters"]["tick"], 450)
        self.assertEqual((row["damage_dealt"], row["damage_taken"]), (115, 12))

    def test_light_reads_only_start_and_end(self):
        rm = FakeRm({"H1": reply(0), "H2": reply(0)})
        r = records.SquadRecords(rm, SQUAD, every=None)
        r.start()
        for t in range(1, 30):
            self.assertIsNone(r.poll(t))
        self.assertEqual(rm.calls, 2)
        r.poll(30, final=True)
        self.assertEqual(rm.calls, 4)

    def test_failed_call_keeps_going(self):
        class Broken(FakeRm):
            def call(self, tool, **kw):
                raise RuntimeError("loading")
        r = records.SquadRecords(Broken({}), SQUAD, every=1)
        r.start()
        self.assertEqual(r.poll(10), {})
        self.assertEqual(r.row()["damage_dealt"], 0)


if __name__ == "__main__":
    unittest.main()
