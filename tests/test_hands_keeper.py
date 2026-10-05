"""hands.Keeper: attack orders only on a change of target (results/audit_attack_orders.md)."""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hands", ROOT / "tools" / "hands.py")
hands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hands)


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


class KeeperTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
