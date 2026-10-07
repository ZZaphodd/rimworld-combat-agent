"""RimMolt MCP client (RIMMOLT_API.md §1): stateless JSON-RPC, one POST per call.

Every process that talks to the game goes through this client, and they share one lock file
(`fcntl.flock`; the user, 2026-10-07). A call takes the lock shared for its one request, so
readers overlap. A multi-step sequence takes it exclusive for the whole sequence
(`with exclusive():`, used by the debug-menu helpers): RimMolt closes an open debug option list
and disarms an armed tool on any other call, so the overlay polling every 3 s broke builds
between "run" and "pick". The OS drops the lock when a process dies. It covers only clients of
this module, not clicks in the game's GUI.
"""
import contextlib
import fcntl
import json
import os
import threading
import time
import urllib.request
from pathlib import Path

DEFAULT_URL = "http://localhost:8787/mcp"
LOCK_PATH = Path(os.environ.get("RCA_RIMMOLT_LOCK") or Path(__file__).resolve().parents[1] / ".rimmolt.lock")


class RimMoltError(RuntimeError):
    pass


class RimMoltBusy(RimMoltError):
    """The lock was not free within the caller's wait (another process holds the game)."""


class _GameLock:
    """One lock file per process: shared per call, exclusive per sequence. A process that holds
    it exclusive does not ask again (flock would make it wait on itself); threads of one
    process take turns on an RLock."""

    def __init__(self, path):
        self.path, self.fd, self.depth = Path(path), None, 0
        self.thread = threading.RLock()

    def _flock(self, mode, wait):
        if self.fd is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)
        end = time.monotonic() + wait
        while True:
            try:
                fcntl.flock(self.fd, mode | fcntl.LOCK_NB)
                return
            except BlockingIOError:
                if time.monotonic() >= end:
                    raise RimMoltBusy(f"the game is held by another client ({self.path.name})")
                time.sleep(0.02)

    @contextlib.contextmanager
    def shared(self, wait):
        with self.thread:
            if self.depth:
                yield
                return
            self._flock(fcntl.LOCK_SH, wait)
            try:
                yield
            finally:
                fcntl.flock(self.fd, fcntl.LOCK_UN)

    @contextlib.contextmanager
    def exclusive(self, wait=300):
        with self.thread:
            if not self.depth:
                self._flock(fcntl.LOCK_EX, wait)
            self.depth += 1
            try:
                yield
            finally:
                self.depth -= 1
                if not self.depth:
                    fcntl.flock(self.fd, fcntl.LOCK_UN)


_LOCKS = {}


def game_lock(path=None):
    path = Path(path or LOCK_PATH)
    return _LOCKS.setdefault(str(path), _GameLock(path))


def exclusive(wait=300, path=None):
    """Hold the game for a multi-step sequence (debug run -> pick -> click, a window dialog)."""
    return game_lock(path).exclusive(wait)


class RimMolt:
    def __init__(self, url=DEFAULT_URL, timeout=30, lock_wait=120, lock_path=None):
        """lock_wait: seconds a call waits for another client's sequence to end before
        RimMoltBusy (the overlay passes a fraction of a second and skips that poll)."""
        self.url, self.timeout, self._id = url, timeout, 0
        self.calls = 0
        self.lock_wait, self.lock = lock_wait, game_lock(lock_path)

    def exclusive(self, wait=300):
        return self.lock.exclusive(wait)

    def call(self, _tool, _timeout=None, **args):
        """Call a tool; return its JSON payload ({"text": ...} if not JSON).
        Raises on protocol errors and isError; in-band {ok: false}/{error} is the
        caller's job, because some tools use it for normal answers."""
        with self.lock.shared(self.lock_wait):
            return self._call(_tool, _timeout, **args)

    def _call(self, _tool, _timeout=None, **args):
        self._id += 1
        self.calls += 1
        body = json.dumps({"jsonrpc": "2.0", "id": self._id, "method": "tools/call",
                           "params": {"name": _tool, "arguments": args}}).encode()
        req = urllib.request.Request(self.url, body, {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"})
        with urllib.request.urlopen(req, timeout=_timeout or self.timeout) as resp:
            msg = json.load(resp)
        if "error" in msg:
            raise RimMoltError(f"{_tool}: {msg['error']}")
        result = msg["result"]
        text = "".join(c.get("text", "") for c in result.get("content", []))
        if result.get("isError"):
            raise RimMoltError(f"{_tool}: {text}")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}

    def wait(self, ticks, max_seconds=60):
        """Advance `ticks` game ticks and pause. force bypasses RimMolt's 1-hour
        crisis cap; the wait may still end early on a letter or message, so
        callers read the clock from get_status, not from the request."""
        return self.call("wait_for_event", _timeout=max_seconds + 30, maxGameTicks=ticks,
                         maxSeconds=max_seconds, pause="always", force=True)

    def alive(self):
        """Liveness probe for the watchdog: get_status answers at all."""
        try:
            self.call("get_status", _timeout=10)
            return True
        except Exception:
            return False


def hostiles(rm, live_only=True):
    """Hostile pawns (verbose). confirm=True: without it a big list comes back as
    a largeOutput notice with no 'things' key."""
    things = rm.call("list_things", category="pawn", faction="hostile", verbose=True,
                     confirm=True)["things"]
    return [t for t in things if not t.get("dead") and not (live_only and t.get("downed"))]


def player_pawns(rm):
    return rm.call("list_things", category="pawn", faction="player", verbose=True,
                   confirm=True)["things"]


def things_of(rm, def_name):
    return rm.call("list_things", category="all", defName=def_name, verbose=True,
                   confirm=True).get("things", [])
