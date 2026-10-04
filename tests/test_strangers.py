"""Man-in-black rule (harness.remove_strangers): destroy him, never a squad pawn's cell."""
import unittest

from rca.eval import harness


class FakeRm:
    def __init__(self, pawns):
        self.pawns, self.calls = pawns, []

    def call(self, tool, **kw):
        self.calls.append((tool, kw))
        if tool == "list_things":
            return {"things": self.pawns}
        return {"ok": True}


SQUAD = {"label": "Trev", "id": "H1", "x": 10, "z": 10, "kind": "Colonist"}
HOWARD = {"label": "Howard", "id": "H9", "x": 134, "z": 5, "kind": "StrangerInBlack"}


class StrangerTest(unittest.TestCase):
    def test_man_in_black_is_destroyed_with_dev_mode_only_for_it(self):
        rm = FakeRm([SQUAD, HOWARD])
        gone = harness.remove_strangers(rm, {"H1"}, log=lambda s: None)
        self.assertEqual(gone, [("Howard", "StrangerInBlack")])
        tools = [t for t, _ in rm.calls]
        self.assertEqual(tools[1], "dev_mode")
        self.assertEqual(rm.calls[-1], ("dev_mode", {"devMode": False, "godMode": False}))
        self.assertIn(("debug_menu", {"action": "click", "x": 134, "z": 5}), rm.calls)

    def test_never_on_a_squad_cell_and_nothing_else_touched(self):
        on_squad = dict(HOWARD, x=10, z=10)
        rm = FakeRm([SQUAD, on_squad, dict(SQUAD, id="H2", label="Wanderer", kind="Villager")])
        self.assertEqual(harness.remove_strangers(rm, {"H1"}, log=lambda s: None), [])
        self.assertNotIn("dev_mode", [t for t, _ in rm.calls])

    def test_cheap_check_only_acts_on_a_colonist_outside_the_squad(self):
        rm, removed = FakeRm([SQUAD, HOWARD]), []
        harness.check_strangers(rm, {"H1"}, [{"id": "H1"}], 100, removed, log=lambda s: None)
        self.assertEqual((rm.calls, removed), ([], []))
        harness.check_strangers(rm, {"H1"}, [{"id": "H1"}, {"id": "H9"}], 120, removed,
                                log=lambda s: None)
        self.assertEqual(removed, [{"tick": 120, "name": "Howard", "kind": "StrangerInBlack"}])


if __name__ == "__main__":
    unittest.main()
