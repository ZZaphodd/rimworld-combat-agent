"""Stream overlay for OBS: a local page that shows the battle being played (read-only).

  python3 tools/overlay.py                  # http://127.0.0.1:8765/  -> OBS Browser source, 1920x1080

It polls the game the way tools/watch.py does (status, pawns, health, messages; never orders,
pauses or moves the camera) and reads which problem is running and who plays it from the process
list (tools/night.py run <id> --agent <a>, tools/run_human.py --manifest ... --player <p>). Our
pawns are left to the game's own colonist bar. The
v2 base ladder's rows (results/base/ladder2.jsonl) are shown beside it. Binds to 127.0.0.1 only.
"""
import argparse
import json
import re
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import _path  # noqa: F401
from rca import ROOT
from rca.rimmolt import RimMolt

PAGE = Path(__file__).with_name("overlay.html")
LADDER = ROOT / "results/base/ladder2.jsonl"
STATE = {"ok": False, "note": "starting"}
NOISE = re.compile(r"Auto-attack target is down or gone")   # the mod's per-pawn notices


def running():
    """(problem id, player) of the battle in progress, from the process list; (None, None) if none."""
    out = subprocess.run(["ps", "-axo", "command"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        m = re.search(r"night\.py run (\S+)\s+--agent (\S+)", line)
        if m:
            return m.group(1), m.group(2)
        m = re.search(r"run_human\.py --manifest \S*scenario_(\S+?)\.json.*?--player (\S+)", line)
        if m:
            return m.group(1), "you" if m.group(2) == "human" else m.group(2)
    return None, None


def ladder():
    rows = [json.loads(l) for l in LADDER.read_text().splitlines() if l.strip()] if LADDER.exists() else []
    return [{"id": r["scenario"], "grade": r.get("grade"), "badness": r.get("badness")} for r in rows]


def raid(rm):
    """Standing and downed raiders (one call; no per-pawn queries)."""
    them = [p for p in rm.call("list_things", category="pawn", faction="hostile", verbose=True,
                               confirm=True).get("things") or [] if not p.get("dead")]
    return {"standing": sum(1 for p in them if not p.get("downed")),
            "downed": sum(1 for p in them if p.get("downed"))}


def poll(rm, period):
    seen_from = last_pid = last_tick = None
    while True:
        try:
            pid, player = running()
            st = rm.call("get_status")
            tick = st.get("ticksGame") or 0
            # a new battle, or a load (the clock goes back): only messages from here on
            if pid != last_pid or last_tick is None or tick < last_tick:
                seen_from, last_pid = tick, pid
            last_tick = tick
            cond = rm.call("get_conditions")         # the HUD's date and hour
            msgs = [m.get("text") for m in (rm.call("get_alerts").get("recentMessages") or [])
                    if (seen_from or 0) <= (m.get("tick") or 0) <= tick      # later than now: from before a load
                    and m.get("text") and not NOISE.search(m["text"])]
            them = raid(rm) if pid else {"standing": 0, "downed": 0}
            STATE.clear()
            STATE.update({"ok": True, "pid": pid, "player": player, "date": cond.get("date"), "hour": cond.get("hour"),
                          "paused": bool(st.get("paused")), "them": them,
                          "msgs": [m[:90] for m in msgs[-3:]], "ladder": ladder(), "at": time.time()})
        except Exception as e:                   # loads, restarts, odd replies: keep the last state, marked stale
            STATE.update({"ok": False, "note": type(e).__name__})
        time.sleep(period)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/state.json"):
            body, kind = json.dumps(STATE, ensure_ascii=False).encode(), "application/json"
        else:
            body, kind = PAGE.read_bytes(), "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--period", type=float, default=3.0, help="seconds between game polls")
    a = ap.parse_args()
    threading.Thread(target=poll, args=(RimMolt(), a.period), daemon=True).start()
    print(f"overlay on http://127.0.0.1:{a.port}/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
