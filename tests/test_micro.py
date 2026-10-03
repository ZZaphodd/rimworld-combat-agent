"""Frag dodge logic offline: severity, safe cell, ownership, re-entry."""
import unittest

from rca.micro.reflex import DANGER_R, MicroLayer, severity
from rca.terrain import Terrain


class FakeRM:
    def __init__(self):
        self.frags, self.fire, self.orders = {}, set(), []

    def call(self, tool, _timeout=None, **a):
        if tool == "list_things":
            d = a.get("defName")
            if d == "Proj_GrenadeFrag":
                return {"things": [{"id": k, "x": x, "z": z} for k, (x, z) in self.frags.items()]}
            if d == "Fire":
                return {"things": [{"id": f"f{x}_{z}", "x": x, "z": z} for x, z in self.fire]}
            return {"things": []}
        if tool == "order_pawn":
            self.orders.append((a["id"], a["x"], a["z"]))
            return {"ok": True}
        if tool == "get_pawn":
            return {"entries": []}
        raise AssertionError(tool)


def open_terrain():
    return Terrain(size=60, tile=30, fetch=lambda x0, z0, x1, z1: ["." * (x1 - x0 + 1)] * (z1 - z0 + 1))


RAIDER = [{"id": "r", "x": 40, "z": 20}]


class Frag(unittest.TestCase):
    def test_severity(self):
        hz = {"kind": "frag", "c": (10, 10)}
        self.assertEqual(severity((11, 11), hz), 1.0)
        self.assertEqual(severity((12, 10), hz), 0.3)
        self.assertEqual(severity((13, 10), hz), 0.0)
        self.assertEqual(severity((10, 10), {"kind": "fire", "c": (10, 10)}), 0.9)
        self.assertEqual(severity((11, 10), {"kind": "fire", "c": (10, 10)}), 0.0)

    def test_dodge_moves_out_and_away(self):
        rm = FakeRM()
        m = MicroLayer(rm, open_terrain(), threshold=0.15)
        rm.frags["g"] = (20, 20)
        owned = m.step([{"id": "a", "pos": (20, 21)}], RAIDER, 0, 30)
        self.assertEqual(owned, {"a"})
        pid, x, z = rm.orders[0]
        self.assertGreater(((x - 20) ** 2 + (z - 20) ** 2) ** 0.5, DANGER_R)
        self.assertLessEqual(x, 20)                 # not closer to the raider (east)
        self.assertEqual(m.k["moves_frag"], 1)

    def test_viscous_doctrine_ignores_margin(self):
        rm = FakeRM()
        m = MicroLayer(rm, open_terrain(), threshold=0.8)
        rm.frags["g"] = (20, 20)
        owned = m.step([{"id": "a", "pos": (22, 20)}], RAIDER, 0, 30)
        self.assertEqual(owned, set())
        self.assertEqual(m.k["ignored_viscous"], 1)

    def test_disabled_counts_only(self):
        rm = FakeRM()
        m = MicroLayer(rm, open_terrain(), threshold=0.15, enabled=False)
        rm.frags["g"] = (20, 20)
        m.step([{"id": "a", "pos": (20, 20)}], RAIDER, 0, 30)
        rm.frags.clear()
        m.step([{"id": "a", "pos": (20, 20)}], RAIDER, 30, 30)
        self.assertEqual(rm.orders, [])
        self.assertEqual(m.k["in_blast_at_landing"], 1)
        self.assertEqual(m.k["stayed_in_blast"], 1)
        self.assertEqual(len(m.events), 1)

    def test_too_late(self):
        rm = FakeRM()
        m = MicroLayer(rm, open_terrain(), threshold=0.15)
        rm.frags["g"] = (20, 20)
        m.step([{"id": "a", "pos": (20, 20)}], RAIDER, 0, 30)     # first seen at t=0
        rm.orders.clear()
        m.until.clear()
        m.dest.clear()
        m.step([{"id": "a", "pos": (20, 20)}], RAIDER, 75, 30)    # 0 - 15 + 90 = 75: no time left
        self.assertEqual(rm.orders, [])
        self.assertEqual(m.k["too_late"], 1)

    def test_escape_counted_and_ownership_released(self):
        rm = FakeRM()
        m = MicroLayer(rm, open_terrain(), threshold=0.15)
        rm.frags["g"] = (20, 20)
        m.step([{"id": "a", "pos": (20, 20)}], RAIDER, 0, 30)
        dest = m.dest["a"]
        m.step([{"id": "a", "pos": dest}], RAIDER, 30, 30)
        rm.frags.clear()
        owned = m.step([{"id": "a", "pos": dest}], RAIDER, 90, 30)
        self.assertEqual(m.k["escaped"], 1)
        self.assertEqual(owned, set())              # hazard gone -> released
        self.assertTrue(m.cell_ok("a", (20, 20)))

    def test_cell_ok_blocks_live_zone(self):
        rm = FakeRM()
        m = MicroLayer(rm, open_terrain(), threshold=0.15)
        rm.frags["g"] = (20, 20)
        m.step([{"id": "a", "pos": (20, 21)}], RAIDER, 0, 30)
        self.assertFalse(m.cell_ok("a", (21, 21)))
        self.assertTrue(m.cell_ok("a", (25, 25)))

    def test_fire_under_pawn_only(self):
        rm = FakeRM()
        m = MicroLayer(rm, open_terrain(), threshold=0.15)
        rm.fire = {(20, 20)}
        owned = m.step([{"id": "a", "pos": (20, 20)}, {"id": "b", "pos": (21, 20)}], RAIDER, 0, 30)
        self.assertEqual(owned, {"a"})
        self.assertNotIn(tuple(rm.orders[0][1:]), rm.fire)


if __name__ == "__main__":
    unittest.main()
