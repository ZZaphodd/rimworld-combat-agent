"""Minimal RimMolt MCP client (stdlib only).

RimMolt's MCP server is stateless JSON-RPC over HTTP, so a plain POST per call
is enough — no session handshake needed.
"""
import json
import urllib.request

DEFAULT_URL = "http://localhost:8787/mcp"


class RimMoltError(RuntimeError):
    pass


class RimMolt:
    def __init__(self, url=DEFAULT_URL, timeout=30):
        self.url = url
        self.timeout = timeout
        self._id = 0

    def call(self, _tool, _timeout=None, **args):
        """Call a tool and return its JSON payload as a dict."""
        name, timeout = _tool, _timeout
        self._id += 1
        body = json.dumps({
            "jsonrpc": "2.0", "id": self._id, "method": "tools/call",
            "params": {"name": name, "arguments": args},
        }).encode()
        req = urllib.request.Request(self.url, body, {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        })
        with urllib.request.urlopen(req, timeout=timeout or self.timeout) as resp:
            msg = json.load(resp)
        if "error" in msg:
            raise RimMoltError(f"{name}: {msg['error']}")
        result = msg["result"]
        text = "".join(c.get("text", "") for c in result.get("content", []))
        if result.get("isError"):
            raise RimMoltError(f"{name}: {text}")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}
