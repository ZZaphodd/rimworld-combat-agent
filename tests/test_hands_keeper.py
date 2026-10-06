"""hands.Keeper: attack orders only on a change of target (results/audit_attack_orders.md)."""
import importlib.util
import math
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hands", ROOT / "tools" / "hands.py")
hands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hands)
ORIG = {k: getattr(hands, k) for k in ("fire", "melee", "shots_fired", "weapon_cycle", "counts_shots", "fireable",
                                       "expected_dpt", "_verb", "cover", "go", "_wdef", "fire_at_will", "stop",
                                       "rm", "pawns", "ids", "wait", "projectiles")}


def restore():
    for k, v in ORIG.items():
        setattr(hands, k, v)
    hands._HANDLED.clear()
    hands._POS.clear()
    hands._SEEN.clear()
    hands._PENDING.clear()


class Restored(unittest.TestCase):
    def tearDown(self):
        restore()


class Fake:
    def __init__(self):
        self.orders, self.shots, self.open = [], {"A": 0}, {"X", "Y", "Z"}

    def fire(self, name, t):
        if t not in self.open:
            return False
        self.orders.append((name, "fire", t))
        return True

    def melee(self, name, t):
        self.orders.append((name, "melee", t))
        return True


class KeeperTest(Restored):
    def setUp(self):
        self.f = Fake()
        hands.fire, hands.melee = self.f.fire, self.f.melee
        hands.shots_fired = lambda n: self.f.shots[n]
        hands.weapon_cycle = lambda n: 80
        hands.counts_shots = lambda n: True
        hands.fireable = lambda n, t: t in self.f.open
        self.k = hands.Keeper()

    def run_(self, frm, to, ranked, standing, job_of, shoot_every=None, step=10):
        for now in range(frm, to, step):
            if shoot_every and now % shoot_every == 0:
                self.f.shots["A"] += 1
            self.k.pick("A", ranked, now, standing, job_of(self.k.target("A")))

    def test_same_target_ordered_once_while_the_job_names_it(self):
        self.run_(0, 600, ["X", "Y"], {"X", "Y"}, lambda t: f"attacking {t}." if t else "", shoot_every=70)
        self.assertEqual(self.f.orders, [("A", "fire", "X")])

    def test_order_that_ended_is_given_again_on_the_same_target(self):
        self.k.pick("A", ["X", "Y"], 0, {"X", "Y"}, "")
        self.k.pick("A", ["X", "Y"], 10, {"X", "Y"}, "watching for targets.")    # fire at will now
        self.assertEqual(self.f.orders, [("A", "fire", "X"), ("A", "fire", "X")])

    def test_fallen_target_switches_once(self):
        self.k.pick("A", ["X", "Y"], 0, {"X", "Y"}, "")
        self.run_(10, 200, ["Y"], {"Y"}, lambda t: f"attacking {t}." if t else "", shoot_every=50)
        self.assertEqual(self.f.orders, [("A", "fire", "X"), ("A", "fire", "Y")])

    def test_stall_after_an_early_shot_then_no_switch_back(self):
        self.k.pick("A", ["X", "Y"], 0, {"X", "Y"}, "")
        self.f.shots["A"] = 1                                      # one shot early
        self.k.pick("A", ["X", "Y"], 90, {"X", "Y"}, "attacking X.")
        for now in range(100, 340, 10):                           # then silence: stall at 90 + 3 * 80
            self.k.pick("A", ["X", "Y"], now, {"X", "Y"}, "attacking X.")
        self.assertEqual(self.f.orders[-1], ("A", "fire", "Y"))
        n = len(self.f.orders)
        for now in range(340, 560, 10):                           # X marked bad: no A -> B -> A
            self.f.shots["A"] += 1
            self.k.better("A", ["X"], now)
            self.k.pick("A", ["X", "Y"], now, {"X", "Y"}, "attacking Y.")
        self.assertEqual(len(self.f.orders), n)

    def test_unfireable_priority_does_not_pull_the_pawn_away(self):
        self.f.open = {"Y"}
        self.k.pick("A", ["X", "Y"], 0, {"X", "Y"}, "")
        for now in range(10, 500, 10):
            self.f.shots["A"] += 1
            self.k.better("A", ["X"], now)
            self.k.pick("A", ["X", "Y"], now, {"X", "Y"}, "attacking Y.")
        self.assertEqual(self.f.orders, [("A", "fire", "Y")])

    def test_better_switches_when_the_priority_comes_into_reach(self):
        self.f.open = {"Y"}
        self.k.pick("A", ["X", "Y"], 0, {"X", "Y"}, "")
        self.f.open = {"X", "Y"}
        self.assertIsNone(self.k.better("A", ["X"], 40))          # within one cycle: no look
        self.assertEqual(self.k.better("A", ["X"], 90), "X")

    def test_held_or_busy_pawn_gets_no_order(self):
        self.k.hold("A", until=100)
        self.k.pick("A", ["X"], 50, {"X"}, "moving.")
        self.k.pick("A", ["X"], 60, {"X"}, "wandering.")
        self.assertEqual(self.f.orders, [])
        self.k.pick("A", ["X"], 100, {"X"}, "watching for targets.")   # hold over
        self.assertEqual(self.f.orders, [("A", "fire", "X")])

    def test_melee_order_given_again_only_when_the_job_lost_it(self):
        self.k.pick("A", ["X"], 0, {"X"}, "", kind="melee")
        for now in range(10, 300, 10):
            self.k.pick("A", ["X"], now, {"X"}, "melee attacking X.", kind="melee")
        self.k.pick("A", ["X"], 310, {"X"}, "watching for targets.", kind="melee")
        self.assertEqual(self.f.orders, [("A", "melee", "X"), ("A", "melee", "X")])



class AssignTest(Restored):
    """Keeper.assign: expected damage, spread, hysteresis, friendly-fire radii."""

    def setUp(self):
        self.f = Fake()
        self.f.shots = {"A": 0, "B": 0}
        hands.fire, hands.melee = self.f.fire, self.f.melee
        hands.shots_fired = lambda n: self.f.shots[n]
        hands.weapon_cycle = lambda n: 80
        hands.counts_shots = lambda n: True
        hands.expected_dpt = lambda n, dist: max(0.0, 1.0 - dist / 30)    # closer is better, 0 at 30
        hands._verb = lambda n: "Verb_Shoot"
        hands.cover = lambda a, b: 1.0
        self.calls = []
        hands.go = lambda n, x, z: self.calls.append(("go", n))
        hands.fire_at_will = lambda n, on: self.calls.append(("fire at will", n, on))
        hands.stop = lambda n: self.calls.append(("stop", n))
        self.k = hands.Keeper()

    @staticmethod
    def p(x, z):
        return {"x": x, "z": z}

    def jobs(self):
        return {n: f"attacking {t}." for n, t in ((n, self.k.target(n)) for n in ("A", "B")) if t}

    def test_two_shooters_spread_over_two_equal_raiders(self):
        ours = {"A": self.p(0, 0), "B": self.p(0, 1)}
        foes = {"X": self.p(10, 0), "Y": self.p(10, 1)}
        out = self.k.assign(["A", "B"], foes, ours, 0, {})
        self.assertEqual(sorted(out.values()), ["X", "Y"])

    def test_focus_weight_pulls_both_onto_the_top_threat(self):
        ours = {"A": self.p(0, 0), "B": self.p(0, 1)}
        foes = {"X": self.p(10, 0), "Y": self.p(10, 1)}
        out = self.k.assign(["A", "B"], foes, ours, 0, {}, weight={"X": 3.0})
        self.assertEqual(list(out.values()), ["X", "X"])

    def test_one_shooters_priority_overrides_the_raider_weight(self):
        ours = {"A": self.p(0, 0), "B": self.p(0, 1)}
        foes = {"X": self.p(5, 0), "Y": self.p(25, 1)}             # Y far: B would share X (0.42 > 0.17)
        out = hands.Keeper().assign(["A", "B"], foes, ours, 0, {})
        self.assertEqual((out["A"], out["B"]), ("X", "X"))
        out = self.k.assign(["A", "B"], foes, ours, 0, {}, weight={("B", "Y"): 3.0, "X": 1.0})
        self.assertEqual((out["A"], out["B"]), ("X", "Y"))

    def test_focus_then_unfocus_splits_again(self):
        ours = {"A": self.p(0, 0), "B": self.p(0, 1)}
        foes = {"X": self.p(10, 0), "Y": self.p(10, 1)}
        self.k.assign(["A", "B"], foes, ours, 0, {}, weight={"X": 3.0})
        for now in range(10, 200, 10):
            self.f.shots["A"] += 1; self.f.shots["B"] += 1
            out = self.k.assign(["A", "B"], foes, ours, now, self.jobs())
        self.assertEqual(sorted(out.values()), ["X", "Y"])

    def test_nothing_worth_it_holds_fire_until_the_next_order(self):
        ours = {"A": self.p(0, 0)}
        self.k.assign(["A"], {"X": self.p(10, 0)}, ours, 0, {})
        out = self.k.assign(["A"], {"X": self.p(40, 0)}, ours, 10, {"A": "attacking X."})   # out of reach
        self.assertIsNone(out["A"])
        self.assertEqual(self.calls, [("stop", "A"), ("fire at will", "A", False)])   # no Go here on its own cell
        out = self.k.assign(["A"], {"X": self.p(40, 0)}, ours, 20, {})
        self.assertIsNone(out["A"])
        self.assertEqual(len(self.calls), 2)                                          # held, nothing more
        out = self.k.assign(["A"], {"X": self.p(10, 0)}, ours, 30, {})                # back in reach
        self.assertEqual(out["A"], "X")
        self.assertEqual(self.calls[2:], [("fire at will", "A", True)])
        self.assertEqual(self.k.quiet, {})

    def test_game_fire_at_will_on_a_risky_raider_is_stopped(self):
        ours = {"A": self.p(0, 0), "K": self.p(12, 0)}            # K 2 from X, 12 from A: full risk
        out = self.k.assign(["A"], {"X": self.p(10, 0)}, ours, 0, {"A": "attacking X."})
        self.assertIsNone(out["A"])
        self.assertEqual(self.calls, [("stop", "A"), ("fire at will", "A", False)])
        self.assertEqual(self.f.orders, [])
        self.k.assign(["A"], {"X": self.p(10, 0)}, ours, 10, {})
        self.assertEqual(len(self.calls), 2)

    def test_idle_shooter_with_nothing_in_reach_is_not_stopped(self):
        out = self.k.assign(["A"], {"X": self.p(40, 0)}, {"A": self.p(0, 0)}, 0, {"A": "standing."})
        self.assertIsNone(out["A"])
        self.assertEqual(self.calls, [("fire at will", "A", False)])

    def test_small_gain_does_not_switch_big_gain_does_after_a_cycle(self):
        ours = {"A": self.p(0, 0)}
        foes = {"X": self.p(12, 0)}
        self.k.assign(["A"], foes, ours, 0, {})
        foes["Y"] = self.p(10, 0)                    # slightly better: 0.67 vs 0.6
        for now in range(10, 200, 10):
            self.f.shots["A"] += 1
            self.k.assign(["A"], foes, ours, now, self.jobs())
        self.assertEqual(self.k.target("A"), "X")
        foes["Z"] = self.p(1, 0)                     # much better: 0.97
        self.k.assign(["A"], foes, ours, 205, self.jobs())   # within the cycle since the last look
        self.assertEqual(self.k.target("A"), "X")
        for now in range(210, 300, 10):
            self.f.shots["A"] += 1
            self.k.assign(["A"], foes, ours, now, self.jobs())
        self.assertEqual(self.k.target("A"), "Z")
        self.assertEqual([o[2] for o in self.f.orders], ["X", "Z"])

    def test_fallen_target_is_replaced_at_once(self):
        ours = {"A": self.p(0, 0)}
        self.k.assign(["A"], {"X": self.p(5, 0), "Y": self.p(20, 0)}, ours, 0, {})
        self.k.assign(["A"], {"Y": self.p(20, 0)}, ours, 5, {"A": "attacking X."})
        self.assertEqual(self.k.target("A"), "Y")

    def test_friendly_fire_radius(self):
        ours = {"A": self.p(0, 0), "K": self.p(11, 0)}            # K in melee with X, 11 cells away
        foes = {"X": self.p(10, 0), "Y": self.p(0, 20)}           # Y off K's lane
        out = self.k.assign(["A"], foes, ours, 0, {})
        self.assertEqual(out["A"], "Y")
        k2 = hands.Keeper()
        ours = {"A": self.p(0, 0), "K": self.p(4, 0)}             # K within 5 of A: never hit
        out = k2.assign(["A"], {"X": self.p(5, 0), "Y": self.p(20, 0)}, ours, 0, {})
        self.assertEqual(out["A"], "X")

    def test_order_that_ended_is_given_again_without_a_switch(self):
        ours = {"A": self.p(0, 0)}
        foes = {"X": self.p(5, 0)}
        self.k.assign(["A"], foes, ours, 0, {})
        self.k.assign(["A"], foes, ours, 10, {"A": "watching for targets."})
        self.assertEqual(self.f.orders, [("A", "fire", "X"), ("A", "fire", "X")])


class CardTest(unittest.TestCase):
    """weapon_stats / expected_dpt from canned info cards."""

    def setUp(self):
        self.cards = {
            "Gun_Revolver": {"stats": [{"stats": [{"label": "Damage", "value": "12"}, {"label": "Range", "value": "26"},
                                                  {"label": "Accuracy (close)", "value": "80%"}, {"label": "Accuracy (short)", "value": "75%"},
                                                  {"label": "Accuracy (medium)", "value": "55%"}, {"label": "Accuracy (long)", "value": "40%"},
                                                  {"label": "Ranged cooldown", "value": "1.60 s"}, {"label": "Aiming time", "value": "0.3 s"}]}]},
            "Weapon_GrenadeFrag": {"stats": [{"stats": [{"label": "Range", "value": "12.9"}, {"label": "Ranged cooldown", "value": "2.67 s"},
                                                        {"label": "Aiming time", "value": "1.5 s"}]}]},
        }
        self.defs = {"R": "Gun_Revolver", "G": "Weapon_GrenadeFrag"}
        hands._WSTATS.clear(); hands._DEF.clear(); hands._PSTATS.clear()
        hands._wdef = lambda n: self.defs[n]
        hands._PSTATS.update({"R": (1.0, 1.0), "G": (1.0, 1.0)})
        self.real_call = hands.rm.call
        hands.rm.call = lambda tool, **a: self.cards[a["def"]] if tool == "get_info_card" else {}

    def tearDown(self):
        hands.rm.call = self.real_call
        restore()

    def test_revolver_bands_interpolate(self):
        w = hands.weapon_stats("R")
        self.assertEqual(w["acc"], [0.8, 0.75, 0.55, 0.4])
        cyc = (0.3 + 1.6) * 60
        self.assertAlmostEqual(hands.expected_dpt("R", 3), 0.8 * 12 / cyc)
        self.assertAlmostEqual(hands.expected_dpt("R", 18.5), (0.75 + (0.55 - 0.75) * 6.5 / 13) * 12 / cyc)
        self.assertEqual(hands.expected_dpt("R", 27), 0.0)        # beyond 26

    def test_card_without_accuracy_rows_counts_as_sure_hit(self):
        w = hands.weapon_stats("G")
        self.assertEqual(w["acc"], [1.0, 1.0, 1.0, 1.0])
        self.assertGreater(hands.expected_dpt("G", 10), 0)


class FriendlyFireTest(unittest.TestCase):
    def test_intercept_factor(self):
        self.assertEqual(hands._intercept(5.0), 0.0)
        self.assertAlmostEqual(hands._intercept(12.0), 1.0)
        self.assertTrue(0 < hands._intercept(8.0) < 0.5)

    def test_ally_on_the_line_and_splash(self):
        p = lambda x, z: {"x": x, "z": z}
        a, x = p(0, 0), p(15, 0)
        self.assertGreater(hands.ff_risk(a, x, [a, p(10, 0)]), 0.5)          # in the lane, 10 out
        self.assertEqual(hands.ff_risk(a, x, [a, p(3, 0)]), 0.0)             # inside the safe radius
        self.assertEqual(hands.ff_risk(a, p(6, 0), [a, p(3, 0)], explosive=True), 1.0)   # splash



class GuardWorld:
    """A frag thrown by R (at 20,0) at Z (0,0): in flight at t3, lying at (0,1) from t6 to t60."""

    def __init__(self):
        self.t = 0
        self.ours = {"Z": {"x": 0, "z": 0}, "Y": {"x": 2, "z": 1}, "W": {"x": 0, "z": 12}}
        self.gone = []
        self.aim, self.thrower_alive, self.flight, self.land = "targeting colonist Z", True, [(18, 0)], (0, 1)

    def call(self, name, **kw):
        if name == "get_status":
            return {"ticksGame": 383 + self.t}
        if name == "get_pawn":
            return {"weapon": "Frag grenades" if kw["id"] == "R" else "Revolver", "health": 100}
        return {}

    def pawns(self, side):
        if side == "hostile":
            return [{"id": "R", "label": "R", "x": 20, "z": 0, "targeting": self.aim}] if self.thrower_alive else []
        return [{"id": n, "label": n, "x": p["x"], "z": p["z"]} for n, p in self.ours.items()]

    def projectiles(self):
        if 3 <= self.t < 6 + 3 * (len(self.flight) - 1):
            x, z = self.flight[min((self.t - 3) // 3, len(self.flight) - 1)]
            return [("G1", "Frag", x, z)]
        if 3 <= self.t < 60:
            return [("G1", "Frag", *self.land)]
        return []

    def go(self, name, x, z):
        self.gone.append((self.t, name, (x, z)))
        self.ours[name] = {"x": x, "z": z}


class GuardTest(Restored):
    def setUp(self):
        self.w = GuardWorld()
        hands.rm = self.w
        hands.pawns, hands.projectiles, hands.go = self.w.pawns, self.w.projectiles, self.w.go
        hands.ids = lambda: {n: n for n in self.w.ours}
        hands.wait = lambda dt: setattr(self.w, "t", self.w.t + dt)

    def run_calls(self, k, n=2):
        for _ in range(50 // n):                             # one guard call per controller step
            hands.guard(n=n, dt=3, quiet=True, keeper=k)

    def test_a_grenade_moves_each_pawn_once_across_calls(self):
        k = hands.Keeper()
        self.run_calls(k)
        moves = [g[1] for g in self.w.gone]
        self.assertEqual(moves.count("Z"), 1, self.w.gone)   # the target, at the throw
        self.assertEqual(moves.count("Y"), 1, self.w.gone)   # 1.0 from where it lies
        self.assertNotIn("W", moves)
        for t, n, c in self.w.gone:
            if n == "Y":
                self.assertGreaterEqual(math.dist(c, (0, 1)), 4)
        self.assertEqual((k.held, k.dodges), ({}, {}))      # released once it went off

    def test_unknown_target_is_read_from_the_line_of_flight(self):
        self.w.aim = None                                    # the grenadier's targeting is not readable
        self.w.ours["Y"] = {"x": 16, "z": 6}                 # nearest to where it first shows, off its line
        self.w.flight = [(18, 0), (12, 0), (6, 0)]           # straight at Z (0, 0)
        self.run_calls(hands.Keeper())
        moves = [g[1] for g in self.w.gone]
        self.assertEqual(moves[0], "Z", self.w.gone)
        self.assertNotIn("Y", moves)
        self.assertNotIn("W", moves)

    def test_the_line_is_read_after_three_cells_not_one(self):
        self.w.aim = None
        self.w.ours = {"Z": {"x": 0, "z": 0}, "V": {"x": 0, "z": 7}, "W": {"x": 0, "z": 20}}
        self.w.flight = [(18, 0), (17, 0), (16, 1), (15, 1), (12, 2), (9, 3), (6, 4)]   # bound for V
        self.w.land = (0, 7)
        self.run_calls(hands.Keeper())
        moves = [g[1] for g in self.w.gone]
        self.assertEqual(moves[0], "V", self.w.gone)
        self.assertNotIn("Z", moves)

    def test_grenade_still_watched_after_its_thrower_fell(self):
        self.w.thrower_alive = False
        self.run_calls(hands.Keeper())
        self.assertIn("Z", [g[1] for g in self.w.gone])

    def test_a_slow_flight_is_not_a_lying_grenade(self):
        self.w.ours["Y"] = {"x": 10, "z": 2}                 # beside its path, far from where it lands
        self.w.flight = [(18, 0), (14, 0), (10, 0), (10, 0), (10, 0), (6, 0), (3, 0)]   # 9 ticks on (10, 0)
        self.run_calls(hands.Keeper())
        self.assertNotIn("Y", [g[1] for g in self.w.gone], self.w.gone)

    def test_one_poll_per_call_works_too(self):
        self.w.aim = None
        self.w.ours["Y"] = {"x": 2, "z": 1}
        self.run_calls(hands.Keeper(), n=1)
        moves = [g[1] for g in self.w.gone]
        self.assertEqual((moves.count("Z"), moves.count("Y")), (1, 1), self.w.gone)

    def test_dodge_cell_keeps_its_walk_clear_of_a_lying_grenade(self):
        me = {"x": 50, "z": 50}                              # a frag lies 2 cells east of it
        foes = [{"x": 50, "z": 38}]
        c = hands._dodge_cell(me, 50, 50, [me], foes, avoid=[(52, 50)])
        self.assertGreaterEqual(hands._seg_dist((52, 50), (50, 50), c), 2.0, c)   # never walks past it
        self.assertGreater(math.dist(c, (52, 50)), hands.LYING_R + 1, c)
        me = {"x": 50, "z": 50}                              # a frag lies 5 cells east: do not cross it
        c = hands._dodge_cell(me, 50, 50, [me], foes, avoid=[(55, 51)])
        self.assertGreater(hands._seg_dist((55, 51), (50, 50), c), hands.LYING_R, c)

    def test_without_a_keeper_too(self):
        self.run_calls(None)
        self.assertEqual([g[1] for g in self.w.gone].count("Z"), 1, self.w.gone)


if __name__ == "__main__":
    unittest.main()
