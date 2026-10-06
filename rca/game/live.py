"""The "a battle started" signal for watchers such as tools/overlay.py (the user, 2026-10-06).

macOS's notify system (notifyd, libSystem) keeps one 64-bit state per name for every process
of the session: `announce()` (called by session.start_episode) sets the start time in
milliseconds and this process's id; `read()` returns them. A state lives while some process
holds the name: the harness holds it for the whole battle, and a watcher that registers first
keeps it after the harness exits. A new battle is a start value *different* from the last one
(the wall clock can step back on a time sync). Elsewhere than macOS both calls do nothing.
"""
import ctypes
import os
import time

START = b"org.rca.episode.start"
PID = b"org.rca.episode.pid"
_lib, _tokens = None, {}


def _notify():
    global _lib
    if _lib is None:
        try:
            lib = ctypes.CDLL("/usr/lib/libSystem.B.dylib")
            lib.notify_register_check.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
            lib.notify_set_state.argtypes = [ctypes.c_int, ctypes.c_uint64]
            lib.notify_get_state.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_uint64)]
            lib.notify_post.argtypes = [ctypes.c_char_p]
            _lib = lib
        except (OSError, AttributeError):
            _lib = False
    return _lib or None


def _token(name):
    """This process's registration for `name`, kept for its lifetime (it keeps the state alive)."""
    lib = _notify()
    if not lib:
        return None
    if name not in _tokens:
        tok = ctypes.c_int()
        if lib.notify_register_check(name, ctypes.byref(tok)) != 0:
            return None
        _tokens[name] = tok
    return _tokens[name]


def announce(now_ms=None, pid=None, names=(START, PID)):
    """Mark a battle start: the start time (ms) and the announcing process's id. The pid goes
    first, so a reader that sees the new start also sees its pid."""
    lib = _notify()
    if not lib:
        return False
    start_name, pid_name = names
    for name, value in ((pid_name, pid or os.getpid()), (start_name, now_ms or int(time.time() * 1000))):
        tok = _token(name)
        if tok is None:
            return False
        lib.notify_set_state(tok, value)
        lib.notify_post(name)
    return True


def read(names=(START, PID)):
    """(start ms, pid) of the last battle announced; (0, 0) when none is held."""
    lib = _notify()
    out = []
    for name in names:
        tok = _token(name)
        v = ctypes.c_uint64()
        if lib and tok is not None and lib.notify_get_state(tok, ctypes.byref(v)) == 0:
            out.append(v.value)
        else:
            out.append(0)
    return tuple(out)
