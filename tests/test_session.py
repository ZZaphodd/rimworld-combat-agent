"""Save guard and watchdog restart cadence offline (no game)."""
import unittest
from unittest import mock

from rca.game import session
from rca.rimmolt import RimMoltError


class FakeRM:
    def __init__(self):
        self.calls = []

    def call(self, tool, _timeout=None, **a):
        self.calls.append((tool, a))
        return {"ok": True}

    def alive(self):
        return True


class SaveGuard(unittest.TestCase):
    def test_personal_saves_refused(self):
        rm = FakeRM()
        for name in ("New Arrivals1", "Autosave-1", "Gados"):
            with self.assertRaises(RimMoltError):
                session.save(rm, name)
        self.assertFalse(any(t == "save_game" for t, _ in rm.calls))

    def test_scenario_names_allowed(self):
        rm = FakeRM()
        session.save(rm, "scenario_tmp_phase2")
        self.assertIn(("save_game", {"name": "scenario_tmp_phase2", "overwrite": True}), rm.calls)


class Restart(unittest.TestCase):
    def test_planned_restart_after_n_episodes(self):
        w = session.Watchdog(FakeRM(), restart_every=3, log=lambda s: None)
        with mock.patch.object(w, "planned_restart") as pr:
            for _ in range(3):
                w.ensure()
                w.episode_done()
            pr.assert_not_called()
            w.ensure()
            pr.assert_called_once()

    def test_zero_disables(self):
        w = session.Watchdog(FakeRM(), restart_every=0, log=lambda s: None)
        w.episodes = 1000
        with mock.patch.object(w, "planned_restart") as pr:
            w.ensure()
            pr.assert_not_called()


if __name__ == "__main__":
    unittest.main()
