"""Tactical layer offline: planner, preconditions, progress/signal, weapon
ranges, rescue decision, firelog, options, and a fake-game smoke of every
doctrine (no exceptions, orders issued)."""
import math
import unittest

from rca.eval import firelog
from rca.eval.progress import ProgressMeter, lost_points, pressure
from rca.eval.results import done_counts
from rca.game.weapons import range_source, weapon_range
from rca.tactical import AGENTS, Doctrine, make, options_of, planner
from rca.tactical.preconditions import Context, all_ok, check
from rca.tactical.squad import rescue_choice
from rca.terrain import Terrain


def grid_terrain(rows_south_first, size=60, tile=30):
    """rows[z][x]; anything outside the given rows is open ground."""
    def fetch(x0, z0, x1, z1):
        out = []
        for z in range(z1, z0 - 1, -1):                 # north first
            out.append("".join(rows_south_first[z][x] if z < len(rows_south_first)
                               and x < len(rows_south_first[z]) else "."
                               for x in range(x0, x1 + 1)))
        return out
    return Terrain(size=size, tile=tile, fetch=fetch)


def open_terrain(size=60):
    return grid_terrain([], size)


def wall_with_gap(size=60, wx=40, gap=(28, 31)):
    """A wall at x=wx with a 3-cell gap: the raid (east) must come through it."""
    rows = [["."] * size for _ in range(size)]
    for z in range(size):
        if not gap[0] <= z < gap[1]:
            rows[z][wx] = "#"
    return grid_terrain(["".join(r) for r in rows], size)


class WeaponRanges(unittest.TestCase):
    def test_xml_ranges(self):
        self.assertEqual(range_source("Chain shotgun (normal)"), (12.9, "label"))
        self.assertEqual(weapon_range("Biocoded heavy SMG (good 80%)"), 22.9)
        self.assertEqual(weapon_range("Doomsday rocket launcher"), 35.9)   # guess said 23
        self.assertEqual(weapon_range("Frag grenades"), 12.9)

    def test_mechs_by_kind(self):
        self.assertEqual(range_source("", "Mech_Pikeman"), (44.9, "mech"))
        self.assertEqual(range_source("", "Mech_Lancer"), (32.9, "mech"))
        self.assertEqual(range_source("", "Mech_Termite"), (24.9, "mech"))  # race -> kind
        self.assertEqual(range_source("", "Mech_Scyther")[1], "melee")

    def test_melee_and_unknown(self):
        self.assertEqual(range_source("Steel longsword (normal)")[1], "melee")
        self.assertEqual(range_source("Plasma whatsit")[1], "default")


class Rescue(unittest.TestCase):
    def test_disabled_rescue_falls_back_to_carry(self):
        opts = [{"index": 0, "label": "Try to arrest Xevion (100% chance)", "disabled": False},
                {"index": 1, "label": "Carry Xevion", "disabled": False},
                {"index": 4, "label": "Cannot rescue: No reachable, un-reserved non-prisoner "
                                      "bed in safe temperature.", "disabled": True}]
        self.assertEqual(rescue_choice(opts), ("carry", 1, "Xevion"))

    def test_enabled_rescue_wins(self):
        opts = [{"index": 0, "label": "Carry Kip", "disabled": False},
                {"index": 1, "label": "Rescue Kip", "disabled": False}]
        self.assertEqual(rescue_choice(opts)[0], "rescue")

    def test_nothing_enabled_reserves_nobody(self):
        opts = [{"index": 0, "label": "Cannot rescue: no bed", "disabled": True},
                {"index": 1, "label": "Carry Kip", "disabled": True}]
        self.assertIsNone(rescue_choice(opts))


class Planner(unittest.TestCase):
    def test_choke_plan_places_everyone_with_standoff(self):
        t = wall_with_gap()
        ranges = [12.9, 22.9, 22.9, 25.9, 25.9, 30.9, 19.9, 22.9]
        cells, slots, rep = planner.plan(t, (25, 30), (55, 30), ranges)
        self.assertEqual(rep["shooters_placed"], len(ranges))
        self.assertTrue(all(s is not None for s in slots))
        self.assertEqual(len(set(slots)), len(slots))
        exit_ = tuple(rep["exit"])
        for s in slots:
            self.assertGreaterEqual(math.dist(s, exit_), planner.STANDOFF)
            self.assertLess(s[0], 40)                  # our side of the wall
        for a in slots:                                 # packed with gaps, not stacked
            self.assertTrue(all(a == b or math.dist(a, b) >= planner.GAP for b in slots))

    def test_short_gun_gets_a_window(self):
        t = wall_with_gap()
        ranges = [12.9, 30.9, 30.9, 30.9]
        _, slots, _ = planner.plan(t, (25, 30), (55, 30), ranges)
        path = planner.approach_path(t, (55, 30), (25, 30))
        self.assertTrue(any(math.dist(slots[0], p) <= 12.9 and t.los(slots[0], p) for p in path))

    def test_raid_inside_means_no_approach(self):
        _, slots, rep = planner.plan(open_terrain(), (30, 30), (30, 31), [25, 25])
        self.assertTrue(rep.get("no_approach"))
        self.assertEqual(slots, [None, None])


class Preconditions(unittest.TestCase):
    def ctx(self, terrain, enemy_cls, squad_melee=0):
        squad = [{"pos": (30, 30 + i), "range": 22.9, "melee": i < squad_melee} for i in range(10)]
        enemies = [{"pos": (50, 30), "cls": c, "range": 44.9 if c == "long" else 12.9}
                   for c in enemy_cls]
        return Context(terrain, (30, 30), squad, enemies)

    def test_turtle_open_field_vs_snipers_fails(self):
        rep = check(AGENTS["turtle"], self.ctx(open_terrain(), ["long"] * 8))
        self.assertFalse(rep["defensible_terrain"]["ok"])
        self.assertFalse(rep["enemy_approaches"]["ok"])
        self.assertFalse(all_ok(rep))

    def test_turtle_walls_vs_melee_passes(self):
        rows = ["".join("%" if (x + z) % 3 == 0 else "." for x in range(60)) for z in range(60)]
        rep = check(AGENTS["turtle"], self.ctx(grid_terrain(rows), ["melee"] * 6 + ["short"] * 2))
        self.assertTrue(all_ok(rep), rep)

    def test_kite_and_close(self):
        self.assertTrue(check(AGENTS["kite"], self.ctx(open_terrain(), ["melee"] * 5))
                        ["enemy_melee_heavy"]["ok"])
        rep = check(AGENTS["close"], self.ctx(open_terrain(), ["long"] * 5))
        self.assertTrue(rep["enemy_outranges"]["ok"])
        self.assertFalse(rep["approach_cover"]["ok"])           # open field: no cover
        self.assertEqual(check(AGENTS["amove"], self.ctx(open_terrain(), [])), {})


class Progress(unittest.TestCase):
    def test_rate_and_longest_stretch(self):
        m = ProgressMeter()
        m.update(0, 0, False)
        m.update(500, 0, True)          # first contact
        m.update(1000, 100, True)
        m.update(3500, 100, False)      # parked out of contact: still a stalemate
        m.update(4500, 300, True)
        self.assertEqual(m.first_contact, 500)
        self.assertEqual(m.longest, 3500)
        self.assertEqual(m.rate(), 75.0)            # 300 points / 4000 ticks x 1000
        self.assertEqual(m.stretch(), 0)

    def test_no_contact_no_clock(self):
        m = ProgressMeter()
        m.update(5000, 0, False)
        self.assertIsNone(m.rate())
        self.assertEqual(m.stretch(), 0)

    def test_edge_escape_is_not_progress(self):
        d = AGENTS["amove"]()
        d.init_tactical()
        d.now = 0
        d.note_progress([{"id": "r1", "kind": "Mercenary_Gunner", "x": 2, "z": 100}], True)
        d.now = 30
        d.note_progress([], True)
        self.assertEqual(d.meter.points, 0)

    def test_lost_points_doctrine_view(self):
        self.assertEqual(lost_points({"a": 85, "b": 110, "c": None}, {"b"}), 85)

    @staticmethod
    def doctrine(reach=25.0):
        d = Doctrine()
        d.init_tactical()
        d.enemy_reach = lambda h: (reach, False)
        return d

    SQ = {"s1": {"pos": (90, 100), "health": 100, "downed": False}}      # 10 cells from r1/r2

    def test_signal_rearms_after_progress(self):
        d = self.doctrine()
        d.no_progress_ticks = 1000
        h = [{"id": "r1", "kind": "Mercenary_Gunner", "x": 100, "z": 100},
             {"id": "r2", "kind": "Mercenary_Gunner", "x": 100, "z": 100}]
        for now, hs in ((0, h), (600, h), (1200, h), (1500, h[1:]), (2700, h[1:])):
            d.now = now
            d.note_progress(hs, True, self.SQ)               # in their range: under threat
        self.assertEqual([(s["tick"], s["reason"]) for s in d.signals],
                         [(1200, "no_progress"), (2700, "no_progress")])
        self.assertEqual((d.signals[0]["pause"], d.signals[0]["contested"]), (1200, 1200))

    def test_quiet_pause_is_not_a_stalemate(self):
        """Smoke case: raiders out of reach (fleeing / far), nobody hurt -> no signal."""
        d = self.doctrine(reach=25.0)
        h = [{"id": "r1", "kind": "Tribal_Warrior", "x": 150, "z": 100}]   # 60 cells away
        for now in range(0, 6001, 120):
            d.now = now
            d.note_progress(h, True, self.SQ)
        self.assertEqual(d.signals, [])
        k = d.kpis()
        self.assertEqual((k["longest_pause_ticks"], k["longest_contested_ticks"]), (6000, 0))
        self.assertEqual(k["no_progress_rule"], 2)

    def test_contested_time_counts_only_pressed_steps(self):
        """Threat every other 1000-tick block: 3000 contested ticks need 5000 of pause."""
        d = self.doctrine(reach=12.0)
        near = [{"id": "r1", "kind": "Mercenary_Gunner", "x": 100, "z": 100}]   # 10 cells
        far = [{"id": "r1", "kind": "Mercenary_Gunner", "x": 130, "z": 100}]    # 40 cells
        for now in range(0, 6001, 100):
            d.now = now
            d.note_progress(near if (now - 1) // 1000 % 2 == 0 else far, True, self.SQ)
        self.assertEqual([s["tick"] for s in d.signals], [5000])
        self.assertEqual(d.signals[0]["pause"], 5000)
        self.assertGreaterEqual(d.signals[0]["contested"], 3000)

    def test_no_squad_no_signal(self):
        d = self.doctrine()
        for now in (0, 5000):
            d.now = now
            d.note_progress([{"id": "r1", "kind": "x", "x": 100, "z": 100}], True)
        self.assertEqual(d.signals, [])

    def test_meter_contested_resets_on_progress(self):
        m = ProgressMeter()
        m.update(0, 0, True, (False, True))
        m.update(1000, 0, True, (True, False))
        m.update(2000, 50, True, (False, False))       # progress: contested -> 0
        m.update(2500, 50, True, (False, True))
        self.assertEqual((m.contested, m.longest_contested, m.longest), (500, 1000, 2000))
        self.assertEqual(m.pressure_ticks, {"cost": 1000, "threat": 500, "either": 1500,
                                            "total": 2500})


class Pressure(unittest.TestCase):
    def sq(self, **kw):
        return {"a": {"pos": (0, 0), "health": 100, "downed": False, **kw}}

    def test_cost(self):
        self.assertEqual(pressure(self.sq(health=90), self.sq(), []), (True, False))
        self.assertEqual(pressure(self.sq(downed=True), self.sq(), []), (True, False))
        self.assertEqual(pressure({}, self.sq(), []), (True, False))         # dead / carried off
        self.assertEqual(pressure(self.sq(health=99.8), self.sq(), []), (False, False))
        self.assertEqual(pressure(self.sq(), None, []), (False, False))      # first observation

    def test_threat_by_weapon_range(self):
        gun = {"pos": (20, 0), "range": 24.9, "thrower": False}
        self.assertEqual(pressure(self.sq(), self.sq(), [gun]), (False, True))
        self.assertEqual(pressure(self.sq(), self.sq(), [{**gun, "range": 19.9}]), (False, False))
        club = {"pos": (1, 1), "range": 1.5, "thrower": False}
        self.assertTrue(pressure(self.sq(), None, [club])[1])                 # adjacent melee
        self.assertFalse(pressure(self.sq(), None, [{**club, "pos": (3, 0)}])[1])

    def test_throw_zone_and_downed_pawns(self):
        frag = {"pos": (14, 0), "range": 12.9, "thrower": True}             # 12.9 + 1.9 blast
        self.assertTrue(pressure(self.sq(), None, [frag])[1])
        self.assertFalse(pressure(self.sq(), None, [{**frag, "pos": (15, 0)}])[1])
        self.assertTrue(pressure(self.sq(downed=True), None, [{**frag, "pos": (5, 0)}])[1])
        self.assertFalse(pressure({"a": {"pos": None, "health": 50, "downed": True}}, None,
                                  [frag])[1])                                # carried: no position


class FireLog(unittest.TestCase):
    NAMES = {"Osborn", "Mausi", "Opa", "Xevion", "Minoru", "Bellerose", "Rakool", "Hamster",
             "Mitch", "Pikeman", "Termite"}

    def test_attackers(self):
        cases = {
            "Osborn tried to shoot at Mausi with her assault rifle.": "Osborn",
            "Opa's machine pistol bullet shot Xevion's left leg.": "Opa",
            "Xevion's torso was damaged by Opa's shot.": "Opa",
            "The blast of Minoru's doomsday rocket damaged Xevion's torso and left foot horribly.":
                "Minoru",
            "Bellerose, using her left fist aptly, beat Xevion in the right shoulder.": "Bellerose",
            "Rakool missed while trying to beat Hamster.": "Rakool",
            "Opa's shot narrowly missed Xevion and hit Mitch.": "Opa",
            "Burn in the right shoulder made Xevion drop.": None,
            "Xevion was downed.": None,
            "The pikeman's needle gun bullet hit Mitch.": "Pikeman",
            "Mitch's shot damaged the termite's head.": "Mitch",
            "The blast of the termite's thump cannon damaged Mitch's torso.": "Termite",
        }
        for text, who in cases.items():
            self.assertEqual(firelog.attacker(text, self.NAMES), who, text)

    def test_share_and_surface(self):
        fired = {"a": {0, 1}, "b": {1}}
        avail = {"a": {0, 1, 2}, "b": {1, 2}}
        self.assertEqual(firelog.share(fired, avail), (0.6, 1.0))   # 3/5; (1+2+0)/3


class Options(unittest.TestCase):
    def test_effective_options_and_resume(self):
        nat = {"vs_throwers": "accept_dodge", "wounded_pullback": "on"}
        self.assertEqual(options_of("hold"), nat)
        self.assertEqual(options_of("turtle", {"vs_throwers": "stand_off"}),
                         nat | {"vs_throwers": "stand_off"})
        self.assertEqual(options_of("turtle", {"vs_throwers": "bogus"}), nat)
        self.assertEqual(options_of("kite", {"vs_throwers": "stand_off"}), {})
        cfg = ("adaptive:30/120@40", True, 4)
        rows = [{"scenario": "s", "agent": "turtle", "agent_version": 8, "cycle": cfg[0],
                 "reflex": True, "reflex_version": 4, "options": {"vs_throwers": o}}
                for o in ("accept_dodge", "stand_off", "stand_off")]
        n = done_counts(rows, lambda a: 8, cfg, lambda a: options_of(a, {"vs_throwers": "stand_off"}),
                        lambda a: options_of(a))
        self.assertEqual(n[("s", "turtle")], 2)

    def test_rescue_and_pullback_options(self):
        self.assertEqual(options_of("doctrine"), {"vs_throwers": "accept_dodge", "rescue": "off",
                                                  "wounded_pullback": "on"})
        self.assertEqual(options_of("turtle", {"rescue": "off"}),
                         {"vs_throwers": "accept_dodge", "wounded_pullback": "on"})
        # rows written before an option existed read as what agents did then (rescue on),
        # not as today's natural value (doctrine v5: rescue off)
        cfg = ("adaptive:30/120@40", True, 4)
        old = {"scenario": "s", "agent": "doctrine", "agent_version": 4, "cycle": cfg[0],
               "reflex": True, "reflex_version": 4, "options": {"vs_throwers": "accept_dodge"}}
        off = {**old, "options": {**options_of("doctrine"), "rescue": "off"}}
        for req, want in (({}, 1), ({"rescue": "off"}, 1), ({"wounded_pullback": "off"}, 0)):
            n = done_counts([old, off], lambda a: 4, cfg, lambda a: options_of(a, req),
                            lambda a: options_of(a))
            self.assertEqual(n[("s", "doctrine")], want, req)
        from rca.eval.report import option_tag
        self.assertEqual(option_tag(old, options_of), "[rescue=on]")   # differs from v5's natural off
        self.assertEqual(option_tag(off, options_of), "")


# ------------------------------------------------------------------ fake game
class FakeGame:
    """Just enough RimMolt for one doctrine to observe and order."""

    def __init__(self, n_squad=6, n_raid=4, raid_x=48, weapon="Heavy SMG (normal)",
                 raid_weapon="Frag grenades (normal)", downed=()):
        self.squad = {f"S{i}": {"x": 20 + (i % 3) * 2, "z": 28 + (i // 3) * 2, "downed": i in downed,
                                "weapon": "Steel longsword" if i == n_squad - 1 else weapon}
                      for i in range(n_squad)}
        self.raid = {f"R{i}": {"x": raid_x, "z": 26 + 2 * i, "weapon": raid_weapon,
                               "kind": "Grenadier_Destructive"} for i in range(n_raid)}
        self.orders, self.carried = [], set()

    def call(self, tool, _timeout=None, **a):
        if tool == "list_colonists":
            return {"colonists": [{"id": i, "name": f"Pawn {i}", "downed": p["downed"],
                                   "health": 30 if i == "S1" else 100, "job": "watching for targets."}
                                  for i, p in self.squad.items()]}
        if tool == "list_things":
            if a.get("defName"):
                return {"things": []}
            if a.get("faction") == "player":
                return {"things": [{"id": i, "label": f"{i}, Pawn", "x": p["x"], "z": p["z"],
                                    "downed": p["downed"]} for i, p in self.squad.items()]}
            return {"things": [{"id": i, "label": f"{i}, raider", "kind": r["kind"], "def": "Human",
                                "x": r["x"], "z": r["z"], "targeting": "attacking colonist S0"}
                               for i, r in self.raid.items()]}
        if tool == "get_pawn":
            p = self.squad.get(a["id"]) or self.raid.get(a["id"])
            if a.get("tab") == "log":
                return {"entries": []}
            job = "being carried by S0." if a["id"] in self.carried else "downed."
            return {"weapon": p["weapon"], "job": job}
        if tool == "get_area":
            return {"grid": ["." * (a["maxX"] - a["minX"] + 1)] * (a["maxZ"] - a["minZ"] + 1)}
        if tool == "order_pawn":
            self.orders.append((tool, a))
            if "targetId" in a and "command" not in a and "index" not in a:
                return {"options": [{"index": 0, "label": "Cannot rescue: no bed", "disabled": True},
                                    {"index": 1, "label": f"Carry {a['targetId']}", "disabled": False}]}
            if "index" in a:
                self.carried.add(a["targetId"])
            return {"ok": True}
        if tool in ("draft", "do_thing_action"):
            self.orders.append((tool, a))
            return {"ok": True}
        raise AssertionError(tool)


class DraftingGame(FakeGame):
    """FakeGame that tracks draft state like the game: Go here needs a drafted
    pawn ("No order matched 'Go here'." otherwise) and downing undrafts."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.drafted = set()

    def down(self, pid):
        self.squad[pid]["downed"] = True
        self.drafted.discard(pid)

    def call(self, tool, _timeout=None, **a):
        if tool == "draft":
            ids = set(a["ids"].split(","))
            self.drafted = self.drafted | ids if a["action"] == "draft" else self.drafted - ids
        if tool == "order_pawn" and a.get("command") == "Go here" and a["id"] not in self.drafted:
            self.orders.append((tool, a))
            return {"ok": False, "error": "No order matched 'Go here'.", "available": []}
        return super().call(tool, _timeout, **a)


def run(name, game, steps=4, options=None):
    d = make(name)
    d.terrain = Terrain(game, size=60, tile=30)
    d.options = options or {}
    manifest = {"squad": [{"id": i, "x": p["x"], "z": p["z"]} for i, p in game.squad.items()]}
    d.reset(game, manifest)
    for k in range(steps):
        d.now, d.step_ticks = k * 30, 30
        d.step(game)
    return d


class DoctrineSmoke(unittest.TestCase):
    def test_every_doctrine_steps_and_orders(self):
        for name in ("doctrine", "turtle", "spread", "kite", "close"):
            g = FakeGame()
            d = run(name, g)
            self.assertTrue(any(t == "draft" for t, _ in g.orders), name)
            self.assertGreater(len(g.orders), 1, name)
            self.assertIsInstance(d.kpis(), dict)
            self.assertTrue(d.phase_log, name)

    def test_wounded_stay_drafted(self):
        g = FakeGame()
        run("doctrine", g)
        self.assertFalse(any(t == "draft" and a.get("action") == "undraft" for t, a in g.orders))
        moves = [a for t, a in g.orders if t == "order_pawn" and a.get("id") == "S1"
                 and a.get("command") == "Go here"]
        self.assertTrue(moves)
        self.assertTrue(all(m["x"] < 22 for m in moves))           # away from the raid (east)

    def test_downed_pawn_is_carried_not_rescued(self):
        g = FakeGame(downed=(2,))
        d = run("doctrine", g, steps=3, options={"rescue": "on"})   # default is off since v5
        idx = [a for t, a in g.orders if t == "order_pawn" and a.get("targetId") == "S2"
               and "index" in a]
        self.assertEqual([a["index"] for a in idx], [1])            # Carry, never the disabled one
        self.assertEqual(d.k["rescue_carried"], 1)

    def test_rescue_off_sends_nobody(self):
        g = FakeGame(downed=(2,))
        d = run("doctrine", g, steps=3, options={"rescue": "off"})
        self.assertFalse([a for t, a in g.orders if t == "order_pawn" and a.get("targetId") == "S2"])
        self.assertEqual(d.k["rescue_started"], 0)

    def test_pullback_off_keeps_the_wounded_fighting(self):
        for name in ("doctrine", "turtle"):
            g = FakeGame()
            d = run(name, g, options={"wounded_pullback": "off"})
            self.assertEqual(d.k["wounded_pullbacks"], 0, name)
            g2 = FakeGame()
            d2 = run(name, g2)
            self.assertEqual(d2.k["wounded_pullbacks"], 1, name)     # S1 is at 30%

    def test_pawn_that_stood_up_is_redrafted(self):
        """LESSONS §4 'Turtle Go here failures': the game undrafts a downed
        pawn; when it stands up again Go here has no option until re-drafted."""
        g = DraftingGame()
        d = make("turtle")
        d.terrain = Terrain(g, size=60, tile=30)
        d.options = {}
        d.reset(g, {"squad": [{"id": i, "x": p["x"], "z": p["z"]} for i, p in g.squad.items()]})
        for k in range(8):
            if k == 2:
                g.down("S1")
            if k == 4:
                g.squad["S1"]["downed"] = False                 # stands up, undrafted
            d.now, d.step_ticks = k * 30, 30
            d.step(g)
        self.assertIn("S1", g.drafted)
        self.assertEqual(d.k["redrafts"], 1)
        self.assertEqual(d.k["orders_failed"], 0)

    def test_goto_redrafts_on_no_order_matched(self):
        g = DraftingGame()
        d = make("turtle")
        d.terrain = Terrain(g, size=60, tile=30)
        d.options = {}
        d.reset(g, {"squad": [{"id": i, "x": p["x"], "z": p["z"]} for i, p in g.squad.items()]})
        d.drafted = set(g.squad)                    # stale belief: S0 was undrafted behind our back
        self.assertIsNotNone(d.goto("S0", (25, 30)))
        self.assertEqual((d.k["redraft_on_error"], d.k["orders_failed"]), (1, 0))
        self.assertIn("S0", g.drafted)

    def test_stand_off_moves_out_of_throw_range(self):
        g = FakeGame(raid_x=30)
        d = run("spread", g, steps=2, options={"vs_throwers": "stand_off"})
        self.assertGreater(d.k["thrower_moves"], 0)
        self.assertEqual(d.opt, {"vs_throwers": "stand_off"})


if __name__ == "__main__":
    unittest.main()
