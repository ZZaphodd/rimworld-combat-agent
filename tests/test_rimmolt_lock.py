"""The shared/exclusive game lock in rca/rimmolt.py (the user, 2026-10-07): another process's call
waits for a held sequence or gets RimMoltBusy; a process never waits on itself."""
import multiprocessing as mp
import tempfile
import time
import unittest
from pathlib import Path

from rca import rimmolt


class FakeRm(rimmolt.RimMolt):
    def _call(self, _tool, _timeout=None, **args):
        return {"tool": _tool}


def _hold(path, ready, seconds):
    with rimmolt.exclusive(path=path):
        ready.set()
        time.sleep(seconds)


def _try_call(path, wait, out):
    try:
        FakeRm(lock_wait=wait, lock_path=path).call("get_status")
        out.put("ok")
    except rimmolt.RimMoltBusy:
        out.put("busy")


class LockTest(unittest.TestCase):
    def setUp(self):
        self.path = str(Path(tempfile.mkdtemp()) / "game.lock")
        self.ctx = mp.get_context("spawn")

    def test_calls_inside_own_exclusive_do_not_wait(self):
        rm = FakeRm(lock_wait=0.1, lock_path=self.path)
        with rm.exclusive():
            with rm.exclusive():                 # nested sequences
                self.assertEqual(rm.call("get_status"), {"tool": "get_status"})
        self.assertEqual(rm.call("get_status"), {"tool": "get_status"})

    def test_other_process_is_busy_while_held_then_free(self):
        ready, out = self.ctx.Event(), self.ctx.Queue()
        holder = self.ctx.Process(target=_hold, args=(self.path, ready, 1.5))
        holder.start()
        self.assertTrue(ready.wait(10))
        p = self.ctx.Process(target=_try_call, args=(self.path, 0.2, out))
        p.start(); p.join(10)
        self.assertEqual(out.get(timeout=5), "busy")         # the overlay's short wait: skip
        p = self.ctx.Process(target=_try_call, args=(self.path, 10, out))
        p.start(); p.join(15)
        self.assertEqual(out.get(timeout=5), "ok")           # a normal call waits for the end
        holder.join(10)

    def test_readers_overlap(self):
        a = FakeRm(lock_path=self.path)
        out = self.ctx.Queue()
        with a.lock.shared(1):
            p = self.ctx.Process(target=_try_call, args=(self.path, 0.2, out))
            p.start(); p.join(10)
            self.assertEqual(out.get(timeout=5), "ok")


if __name__ == "__main__":
    unittest.main()


class FakeGame(rimmolt.RimMolt):
    """A clock that runs at `rate` ticks/s while unpaused; wait_for_event advances exactly."""
    def __init__(self, rate=360, pause_at=None, **kw):
        super().__init__(lock_path=str(Path(tempfile.mkdtemp()) / "g.lock"), **kw)
        self.rate, self.t, self.since, self.pause_at = rate, 1000.0, None, pause_at

    def _now(self):
        if self.since is not None:
            self.t += (time.monotonic() - self.since) * self.rate
            self.since = time.monotonic()
            if self.pause_at and self.t >= self.pause_at:        # the game pauses itself (a letter)
                self.t, self.since = self.pause_at, None
        return int(self.t)

    def _call(self, _tool, _timeout=None, **args):
        if _tool == "get_status":
            return {"ticksGame": self._now(), "paused": self.since is None}
        if _tool == "set_speed":
            self._now()
            self.since = time.monotonic() if args["action"] == "unpause" else None
            return {"ok": True}
        if _tool == "wait_for_event":
            self.t = int(self._now()) + args["maxGameTicks"]
            return {"ticksWaited": args["maxGameTicks"]}
        raise AssertionError(_tool)


class SkipTest(unittest.TestCase):
    def test_lands_exactly_and_ends_paused(self):
        g = FakeGame()
        r = g.skip(700, poll=0.02)
        self.assertEqual((r["ticks"], r["early"]), (700, None))
        self.assertTrue(g.call("get_status")["paused"])

    def test_until_and_a_pause_from_the_game_end_it_early(self):
        g = FakeGame()
        r = g.skip(5000, poll=0.02, until=lambda rm: rm.call("get_status")["ticksGame"] >= 1100)
        self.assertEqual(r["early"], "until")
        self.assertLess(r["ticks"], 5000)
        g = FakeGame(pause_at=1300)
        r = g.skip(5000, poll=0.02)
        self.assertEqual((r["early"], r["end"]), ("paused", 1300))
