"""Offline tests of the probe formatters (rca/probe.py, tools/rm.py)."""
import unittest

from rca import probe


class TrimTest(unittest.TestCase):
    def test_noise_color_float_and_cuts(self):
        t = probe.trim({"loaded": True, "bundled": {"x": 1}, "_paused": True,
                        "label": "Mausi<color=#999999FF>, Ranger</color>", "v": 1.7999999523,
                        "xs": list(range(5)), "s": "abcdef"}, max_list=3, max_str=4)
        self.assertEqual(t, {"label": "Maus...(+9)", "v": 1.8, "xs": [0, 1, 2, "...(+2)"],
                             "s": "abcd...(+2)"})

    def test_loaded_false_is_kept(self):
        self.assertEqual(probe.trim({"loaded": False}), {"loaded": False})

    def test_generic_one_line_per_key(self):
        self.assertEqual(probe.generic({"a": 1, "b": [1, 2], "hint": "x"}), "a: 1\nb: [1,2]")


class ArgsTest(unittest.TestCase):
    def test_parse_kv(self):
        self.assertEqual(probe.parse_kv(["x=3", "f=0.5", "confirm=true", "ids=a,b", "j=[1]"]),
                         {"x": 3, "f": 0.5, "confirm": True, "ids": "a,b", "j": [1]})

    def test_pawn_ref(self):
        self.assertEqual(probe.pawn_ref("Human51228"), {"id": "Human51228"})
        self.assertEqual(probe.pawn_ref("Mausi"), {"name": "Mausi"})
        self.assertEqual(probe.pawn_ref("Sabrina Janacki"), {"name": "Sabrina Janacki"})


class LinesTest(unittest.TestCase):
    def test_pawn_line(self):
        line = probe.pawn_line({"id": "Human1", "label": "Opa<color=#999999FF>, Raider</color>",
                                "kind": "Mercenary_Gunner", "x": 3, "z": 4, "downed": True,
                                "targeting": "attacking colonist Mausi", "distance": 2.0})
        self.assertTrue(line.startswith("Opa "))
        for part in ("Human1", "Mercenary_Gunner", "3,4", "d=2.0", "downed",
                     "-> attacking colonist Mausi"):
            self.assertIn(part, line)

    def test_area_lines_label_rows_by_z(self):
        r = {"bounds": {"minX": 118, "minZ": 9, "maxX": 122, "maxZ": 10},
             "grid": ["..*..", "#...."]}
        out = probe.area_lines(r)
        self.assertEqual(out[1:], ["  10 |..*..", "   9 |#...."])
        self.assertEqual(out[0].split()[0], "2")      # x = 120 marked by its tens digit

    def test_wait_lines(self):
        w = {"cause": "timeout", "ticksWaited": 120, "pausedAfter": True,
             "_notifications": [{"kind": "message", "text": "Pirates are fleeing."}],
             "_delta": {"pawnDamage": [{"name": "Mausi", "hpBefore": 100, "hpAfter": 80,
                                         "newInjuries": ["Gunshot (LMG) (torso)"]}],
                        "removedBuildings": [{"def": "Wall", "count": 2}]}}
        self.assertEqual(probe.wait_lines(w, 1695), [
            "cause timeout waited 120 -> tick 1695 paused=True",
            "  [message] Pirates are fleeing.",
            "  dmg Mausi 100->80 Gunshot (LMG) (torso)",
            "  -Wall x2"])

    def test_debug_and_records(self):
        r = {"ok": True, "optionList": {"options": ["Pirate gang (Pirate)", "x [NO]"]},
             "log": [{"text": "empty collection"}]}
        self.assertEqual(probe.debug_lines(r), ["ok", "  > Pirate gang (Pirate)", "  > x [NO]",
                                                "  log: empty collection"])
        self.assertEqual(probe.debug_lines({"ok": False, "error": "nope"}), ["error: nope"])
        self.assertEqual(probe.records_line({"records": [{"record": "Kills", "value": 3},
                                                         {"record": "Shots fired", "value": 0}]}),
                         "Kills=3")

    def test_health_lines(self):
        h = {"overallHealthPercent": 80, "painPercent": 10, "state": "Mobile",
             "capacities": [{"capacity": "moving", "percent": 70},
                            {"capacity": "sight", "percent": 100}],
             "hediffs": [{"label": "Gunshot", "part": "left leg", "permanent": False}]}
        self.assertEqual(probe.health_lines(h), ["hp 80% pain 10% Mobile | low: moving 70%",
                                                 "  Gunshot (left leg)"])


if __name__ == "__main__":
    unittest.main()
