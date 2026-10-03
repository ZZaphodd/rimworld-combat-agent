"""RimMolt MCP client (RIMMOLT_API.md §1): stateless JSON-RPC, one POST per call."""
import json
import urllib.request

DEFAULT_URL = "http://localhost:8787/mcp"


class RimMoltError(RuntimeError):
    pass


class RimMolt:
    def __init__(self, url=DEFAULT_URL, timeout=30):
        self.url, self.timeout, self._id = url, timeout, 0
        self.calls = 0

    def call(self, _tool, _timeout=None, **args):
        """Call a tool; return its JSON payload ({"text": ...} if not JSON).
        Raises on protocol errors and isError; in-band {ok: false}/{error} is the
        caller's job, because some tools use it for normal answers."""
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
