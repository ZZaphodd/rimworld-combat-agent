"""Mixed hands (tools/hands_rc.py): st()'s pawn line and wait_safe's stop rule, from snapshot rows.
Runs only where the frozen rimcockpit client is (a clone in ~/.cache/rimcockpit or RIMCOCKPIT_CLIENT)."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, "tools")
CLIENT = Path(os.environ.get("RIMCOCKPIT_CLIENT")
              or Path.home() / ".cache/rimcockpit/clients/python/releases/0.2.0")


def row(i, side, x, z, downed=False, dead=False, **kw):
    return {"id": f"Human{i}", "shortName": f"P{i}", "side": side, "x": x, "z": z, "downed": downed,
            "dead": dead, "summaryHealth": 0.5, "jobDef": "Wait_Combat", **kw}


@unittest.skipUnless((CLIENT / "rimcockpit").is_dir(), "needs the frozen rimcockpit 0.2.0 client")
class HandsRcTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import hands_rc
        cls.h = hands_rc

    def test_row_line(self):
        p = row(1, "player", 10, 20, weapon={"def": "Gun_Autopistol"},
                job={"jobText": "Moving.", "pather": {"moving": True, "destination": {"cell": {"x": 12, "z": 22}}}})
        self.assertEqual(self.h.row_line(p), "P1@10,20 50% Autopistol | Moving. ->12,22  [Human1]")
        self.assertIn(" DOWN ", self.h.row_line(row(2, "player", 0, 0, downed=True)))

    def test_alarm_reason(self):
        ours = [row(1, "player", 0, 0), row(2, "player", 50, 50)]
        self.assertIsNone(self.h.alarm_reason(ours + [row(3, "hostile", 30, 0)], 25))
        self.assertEqual(self.h.alarm_reason(ours + [row(3, "hostile", 20, 0)], 25), "near: P3 20.0 from P1")
        self.assertIsNone(self.h.alarm_reason(ours + [row(3, "hostile", 20, 0, downed=True)], 25))
        self.assertEqual(self.h.alarm_reason([row(1, "player", 0, 0, downed=True)], 25), "down: P1")

    def test_weapons_and_names(self):
        rifle = self.h.weapon_of({"weapon": {"def": "Gun_BoltActionRifle"}})
        self.assertEqual(rifle[0], 36.9)
        self.assertTrue(rifle[2])                                     # a projectile: no adjacent shot
        self.assertFalse(self.h.weapon_of({"weapon": {"def": "Gun_BeamGraser"}})[2])          # a beam: adjacent shots allowed
        self.assertIsNone(self.h.weapon_of({"weapon": {"def": "MeleeWeapon_Knife"}}))
        self.assertIsNone(self.h.weapon_of({"weapon": None}))
        rows = [row(1, "player", 0, 0), {**row(2, "hostile", 5, 5), "shortName": "centipede#k3z9"}]
        self.assertEqual(self.h._pick(rows, "Human1")["id"], "Human1")
        self.assertEqual(self.h._pick(rows, "Centipede")["id"], "Human2")
        with self.assertRaises(KeyError):
            self.h._pick(rows + [{**row(3, "hostile", 9, 9), "shortName": "centipede#a1b2"}], "centipede")

    def test_melee_note(self):
        me = row(1, "player", 5, 5)
        rows = [me, row(2, "hostile", 6, 6), row(3, "hostile", 7, 5), row(4, "hostile", 4, 5, downed=True)]
        self.assertEqual(self.h._melee_note(rows, me), "  [melee: P2 adjacent]")
        self.assertEqual(self.h._melee_note([me, row(3, "hostile", 7, 5)], me), "")

    def test_time_goes_through_rimcockpit(self):
        import hands
        self.assertIs(hands.wait, self.h.wait)
        self.assertIs(hands.skip, self.h.skip)
        self.assertIs(hands.wait_safe, self.h.wait_safe)


if __name__ == "__main__":
    unittest.main()
