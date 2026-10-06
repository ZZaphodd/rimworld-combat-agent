"""turtle_at (turtle v9 at a picked site), the plan format and the offline save map."""
import json
import tempfile
import unittest
from pathlib import Path

from rca.eval.results import canonical
from rca.game.savemap import footprint
from rca.strategic import siteplan
from rca.tactical import make, options_of
from rca.tactical.turtle import Turtle
from rca.tactical.turtle_at import TurtleAt
from rca.terrain import Terrain
from tests.test_tactical import FakeGame


class RoomGame(FakeGame):
    """FakeGame plus doors, gizmo toggles and the float menu's Melee attack."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.door = {"id": "Door1", "x": 22, "z": 34, "def": "Door", "held": False}
        self.faw = {}

    def call(self, tool, _timeout=None, **a):
        if tool == "list_things" and a.get("category") == "building":
            d = self.door
            return {"things": [{"id": d["id"], "def": d["def"], "x": d["x"], "z": d["z"]}]
                    if (a.get("nearX"), a.get("nearZ")) == (d["x"], d["z"]) else []}
        if tool == "inspect_thing":
            if a["id"] == self.door["id"]:
                return {"actions": [{"label": "Hold open", "active": self.door["held"]}]}
            return {"actions": [{"label": "Fire at will", "active": self.faw.get(a["id"], True)}]}
        if tool == "do_thing_action" and a.get("label") == "Hold open":
            self.door["held"] = not self.door["held"]
        if tool == "do_thing_action" and a.get("label") == "Fire at will":
            self.faw[a["id"]] = not self.faw.get(a["id"], True)
        if tool == "order_pawn" and "targetId" in a and "command" not in a:
            self.orders.append((tool, a))
            if "index" in a:
                return {"executed": True}
            return {"options": [{"index": 0, "label": f"Melee attack {a['targetId']}", "disabled": False},
                                {"index": 1, "label": f"Melee attack {a['targetId']} to death", "disabled": False}]}
        return super().call(tool, _timeout, **a)


def manifest(game, pid="p1"):
    return {"id": pid, "squad": [{"id": i, "x": p["x"], "z": p["z"], "name": i, "weapon": p["weapon"]}
                                 for i, p in game.squad.items()]}


def plan_file(entry, pid="p1"):
    d = Path(tempfile.mkdtemp())
    p = d / "plan.json"
    p.write_text(json.dumps({"format": 1, "for": "x", "problems": {pid: entry}}))
    return str(p)


def room_entry(game):
    """A 6x3 room (20..25, 35..37) with its door at (22,34) on the south side, facing the raid."""
    ids = sorted(game.squad)
    cells = {ids[0]: {"cell": [22, 35], "role": "front"}}
    for i, pid in enumerate(ids[1:]):
        cells[pid] = {"cell": [20 + i % 5, 36 + i // 5]}
    cells[ids[-1]] = {"cell": [25, 37]}
    return {"site": "test room", "why": "test", "room": [[20, 35, 25, 37]], "cells": cells,
            "doors": [{"at": [22, 34], "hold_open": True}], "rear": [[25, 36]]}


def run_at(game, entry, steps=4, start=0, dt=30, agent=None):
    d = agent or make("turtle_at")
    d.terrain = Terrain(game, size=60, tile=30)
    d.options = {"plan": plan_file(entry)}
    d.reset(game, manifest(game))
    for k in range(steps):
        d.now, d.step_ticks = start + k * dt, dt
        d.step(game)
    return d


class PinTest(unittest.TestCase):
    def test_pinned_to_turtle_v9_and_never_merged(self):
        self.assertEqual(TurtleAt.BASE_VERSION, Turtle.version)
        self.assertEqual(Turtle.version, 9)
        self.assertEqual(canonical("turtle_at"), "turtle_at")
        self.assertEqual(TurtleAt().viscosity, Turtle().viscosity)

    def test_plan_is_in_the_options_without_reading_it(self):
        self.assertEqual(options_of("turtle_at", {"plan": "nowhere.json"})["plan"], "nowhere.json")

    def test_preflight_refuses_a_missing_plan_or_entry(self):
        g = FakeGame()
        a = make("turtle_at")
        with self.assertRaises(siteplan.PlanError):
            a.preflight(manifest(g))
        a.options = {"plan": plan_file({"site": "s", "why": "w", "anchor": [1, 1]}, pid="other")}
        with self.assertRaises(siteplan.PlanError):
            a.preflight(manifest(g))


class AnchorModeTest(unittest.TestCase):
    def test_anchor_at_the_spawn_orders_like_turtle(self):
        g1, g2 = FakeGame(), FakeGame()
        t = make("turtle")
        t.terrain = Terrain(g1, size=60, tile=30)
        t.options = {}
        t.reset(g1, manifest(g1))
        for k in range(4):
            t.now, t.step_ticks = k * 30, 30
            t.step(g1)
        d = run_at(g2, {"site": "spawn", "why": "same as turtle", "anchor": list(t.anchor)})
        self.assertEqual(g1.orders, g2.orders)
        self.assertEqual(d.kpis()["site"]["mode"], "anchor")


class RoomModeTest(unittest.TestCase):
    def test_walks_to_the_cells_and_sets_the_door(self):
        g = RoomGame(raid_x=48)
        d = run_at(g, room_entry(g))
        self.assertTrue(g.door["held"])
        self.assertEqual(d.doors, {"22,34": "set"})
        gos = {a["id"]: (a["x"], a["z"]) for t, a in g.orders if t == "order_pawn" and a.get("command") == "Go here"}
        want = {k: tuple(v["cell"]) for k, v in room_entry(g)["cells"].items()}
        for pid, cell in gos.items():
            if pid != "S1":                         # S1 is wounded (30%): to the rear cell
                self.assertEqual(cell, want[pid])
        self.assertEqual(gos.get("S1"), (25, 36))

    def test_no_attack_orders_on_raiders_outside_the_room(self):
        g = RoomGame(raid_x=27)                     # within 10 of the anchor and 7 of the swordsman
        run_at(g, room_entry(g), steps=6)
        bad = [a for t, a in g.orders if t == "do_thing_action" and a.get("label") == "Auto attack (AI)"
               or t == "order_pawn" and a.get("command") == "Fire at"]
        self.assertEqual(bad, [])

    def test_melee_on_an_adjacent_raider(self):
        g = RoomGame(raid_x=48)
        d = run_at(g, room_entry(g), steps=2)
        g.raid["R0"].update(x=22, z=34)             # in the doorway, next to the plug
        g.squad["S0"].update(x=22, z=35)
        d.now += 30
        d.step(g)
        melee = [a for t, a in g.orders if t == "order_pawn" and a.get("targetId") == "R0" and "index" in a]
        self.assertEqual([a["index"] for a in melee if a["id"] == "S0"], [0])   # never "to death"
        self.assertGreaterEqual(d.k["melee_orders"], 1)

    def test_no_sally_only_a_record(self):
        g = RoomGame(raid_x=58)                     # never within 30: turtle would sally at 4800
        d = run_at(g, room_entry(g), steps=50, dt=120)
        self.assertFalse(d.sally)
        self.assertEqual(d.tally.vals.get("sally_would_reason"), "idle")
        self.assertFalse([a for t, a in g.orders if t == "do_thing_action" and a.get("label") == "Auto attack (AI)"])

    def test_wounded_stay_on_the_rear_cells_through_a_breach(self):
        g = RoomGame(raid_x=48)
        d = run_at(g, room_entry(g), steps=2)
        g.squad["S1"].update(x=25, z=36)            # S1 (30%) on its rear cell
        g.raid["R0"].update(x=22, z=34)             # a raider in the doorway: a breach
        n = len(g.orders)
        for k in range(3):
            d.now += 30
            d.step(g)
        back = [a for t, a in g.orders[n:] if t == "order_pawn" and a.get("id") == "S1"
                and a.get("command") == "Go here" and (a["x"], a["z"]) != (25, 36)]
        self.assertEqual(back, [])

    def test_idle_still_raises_turtles_signal(self):
        g = RoomGame(raid_x=58)
        d = run_at(g, room_entry(g), steps=50, dt=120)
        self.assertEqual([s["reason"] for s in d.signals], ["precondition:enemy_approaches"])

    def test_melee_picks_the_named_raider(self):
        class Stacked(RoomGame):
            def call(self, tool, _timeout=None, **a):
                if tool == "order_pawn" and "targetId" in a and "command" not in a and "index" not in a:
                    self.orders.append((tool, a))
                    return {"options": [{"index": 0, "label": "Melee attack R1", "disabled": False},
                                        {"index": 1, "label": f"Melee attack {a['targetId']}", "disabled": False}]}
                return super().call(tool, _timeout, **a)
        g = Stacked(raid_x=48)
        d = run_at(g, room_entry(g), steps=2)
        g.raid["R0"].update(x=22, z=34)
        g.squad["S0"].update(x=22, z=35)
        d.now += 30
        d.step(g)
        idx = [a["index"] for t, a in g.orders if t == "order_pawn" and a.get("id") == "S0" and "index" in a]
        self.assertEqual(idx, [1])

    def test_fire_hold(self):
        g = RoomGame(raid_x=48)
        e = room_entry(g)
        e["cells"]["S2"]["fire"] = "hold"
        d = run_at(g, e)
        self.assertIs(g.faw.get("S2"), False)
        self.assertEqual(d.k["fire_hold_set"], 1)


class PlanFormatTest(unittest.TestCase):
    def test_validate(self):
        g = FakeGame()
        m = manifest(g)
        ok = room_entry(g)
        self.assertEqual(siteplan.validate(ok, m)[0], [])
        bad = json.loads(json.dumps(ok))
        bad["cells"].pop("S0")
        self.assertTrue(any("missing" in e for e in siteplan.validate(bad, m)[0]))
        bad = json.loads(json.dumps(ok))
        bad["cells"]["S2"]["cell"] = bad["cells"]["S3"]["cell"]
        self.assertTrue(any("one cell" in e for e in siteplan.validate(bad, m)[0]))
        bad = json.loads(json.dumps(ok))
        bad["cells"]["S2"]["cell"] = [40, 40]
        self.assertTrue(any("outside the room" in e for e in siteplan.validate(bad, m)[0]))
        warn = json.loads(json.dumps(ok))
        warn["cells"]["S2"]["cell"] = [21, 35]      # a gun next to the open door
        self.assertTrue(any("Too close" in w for w in siteplan.validate(warn, m)[1]))

    def test_anchor_defaults_to_the_cells(self):
        s = siteplan.build("p", {"cells": {"a": {"cell": [1, 1]}, "b": {"cell": [3, 5]}, "c": {"cell": [5, 3]}}})
        self.assertEqual(s.anchor, (3, 3))
        self.assertEqual(s.mode, "cells")


class ShortHashTest(unittest.TestCase):
    def test_values_seen_in_a_save(self):
        from rca.game.savemap import short_hash
        self.assertEqual(short_hash("ChunkMarble"), 45390)       # scenario_base2_ith_pirate_2x
        self.assertEqual(short_hash("Marble"), 64468)
        self.assertEqual(short_hash("MineableSteel") + 1, 27293)  # bumped: taken by an earlier def


class FootprintTest(unittest.TestCase):
    def test_rotations(self):
        self.assertEqual(footprint(5, 5, [1, 1], 0), [(5, 5)])
        self.assertEqual(sorted(footprint(5, 5, [1, 2], 0)), [(5, 5), (5, 6)])      # bed facing north
        self.assertEqual(sorted(footprint(5, 5, [1, 2], 2)), [(5, 4), (5, 5)])      # facing south
        self.assertEqual(sorted(footprint(5, 5, [1, 2], 1)), [(5, 5), (6, 5)])      # east
        self.assertEqual(sorted(footprint(5, 5, [1, 2], 3)), [(4, 5), (5, 5)])      # west
        self.assertEqual(len(footprint(5, 5, [3, 1], 0)), 3)
        self.assertEqual(sorted(footprint(5, 5, [2, 2], 0)), [(5, 5), (5, 6), (6, 5), (6, 6)])


if __name__ == "__main__":
    unittest.main()
