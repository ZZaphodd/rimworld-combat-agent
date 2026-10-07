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
