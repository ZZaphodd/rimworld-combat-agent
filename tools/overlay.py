"""Stream overlay for OBS: a local page that shows the battle being played (read-only).

  python3 tools/overlay.py                  # http://127.0.0.1:8765/  -> OBS Browser source, 1920x1080
  # avatar (찹쌀이, tools/avatar.html): http://127.0.0.1:8765/avatar?obs&flavor=white&mode=battle&emotion=calm

It polls the game the way tools/watch.py does (status, both sides' strength, messages, the HUD's date; never
orders, pauses or moves the camera). A battle is announced by session.start_episode through
macOS's notify system (rca.game.live: start time and the harness's process id); the overlay
holds the names, so a change of start time is a new battle, and the problem and player come from
that process's command line (night.py run <id> --agent <a>, run_human.py --manifest ...
--player <p>; another harness shows its script name). Our pawns are left to the game's own
colonist bar. The
v2 base ladder's rows of the last agent seen (results/base/ladder2.jsonl for turtle,
ladder2_<agent>.jsonl for another) are shown beside it. Binds to 127.0.0.1 only.
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
from rca.game import defs, live
from rca.rimmolt import RimMolt, RimMoltBusy

PAGE = Path(__file__).with_name("overlay.html")
AVATAR = Path(__file__).with_name("avatar.html")    # 찹쌀이: /avatar?obs&flavor=white&mode=battle&emotion=calm
LADDER = ROOT / "results/base/ladder2.jsonl"
STATE = {"ok": False, "note": "starting"}
MODE = {"strength": "health"}                 # or "standing": switch live with /set?strength=standing
NOISE = re.compile(r"Auto-attack target is down or gone")   # the mod's per-pawn notices


def parse(cmd):
    """(problem id, player) from a harness's command line; an unknown harness gives its script."""
    m = re.search(r"night\.py run (\S+)\s+--agent (\S+)", cmd)
    if m:
        return m.group(1), m.group(2)
    m = re.search(r"run_human\.py .*?--(?:manifest \S*?scenario_(\S+?)\.json|scenario (\S+))", cmd)
    if m:
        p = re.search(r"--player (\S+)", cmd)
        player = p.group(1) if p else "human"
        return m.group(1) or m.group(2), "you" if player == "human" else player
    m = re.search(r"(\w+)\.py\b", cmd)
    return (m.group(1) if m else cmd[:40]), None


OVER = set()                                   # start values whose harness was seen gone


def battle():
    """(start ms, problem id, player) of the announced battle; id None when its process has ended.
    A start whose process was once seen gone stays over: its pid may later be reused by another
    program (the review, 2026-10-06), and a zombie (stat Z) counts as gone."""
    start, pid = live.read()
    if not start or not pid or start in OVER:
        return start, None, None
    out = subprocess.run(["ps", "-p", str(pid), "-o", "stat=,command="], capture_output=True, text=True).stdout.strip()
    stat, _, cmd = out.partition(" ")
    if not out or stat.startswith("Z"):
        OVER.add(start)
        return start, None, None
    return (start, *parse(cmd.strip()))


LAST = {"agent": "turtle"}                     # the ladder shown between battles: the last agent seen


def ladder(player=None):
    """(agent, rows) of the v2 ladder the live agent writes: ladder2.jsonl for turtle,
    ladder2_<agent>.jsonl for another agent (tools/base_ladder.py)."""
    if player and player not in ("you", "claude", "human"):
        LAST["agent"] = player
    agent = LAST["agent"]
    f = LADDER if agent == "turtle" else LADDER.with_name(f"{LADDER.stem}_{agent}.jsonl")
    rows = [json.loads(l) for l in f.read_text().splitlines() if l.strip()] if f.exists() else []
    return agent, [{"id": r["scenario"], "grade": r.get("grade"), "badness": r.get("badness")}
                   for r in rows if r.get("outcome") != "invalid"]


def manifest(pid):
    """The problem's manifest (scenarios*/scenario_<id>.json), or None."""
    hits = sorted(ROOT.glob(f"scenarios*/scenario_{pid}.json")) if pid else []
    return json.loads(hits[0].read_text()) if hits else None


class Strength:
    """Each side's combat points for one battle (the user's tug-of-war, 2026-10-06).

    A pawn is worth its kind's combatPower times its xenotype factor, as a raid pays for it
    (rca.game.defs). Raiders: kind from the pawn list, xenotype unknown to RimMolt, so the raid
    faction's expected factor (the manifest's enemy faction). Ours: recruited pawns show kind
    "Colonist", so the manifest's kinds when it has them (times the xenotype from list_genes),
    else an equal share of the squad's point budget. Without a manifest every pawn counts
    FALLBACK points ("approx"). Now = the standing pawns' points, times health % in the
    "health" mode (one get_pawn per standing pawn) or not in the "standing" mode; downed and dead
    count 0. Start = the highest total seen (pawns that arrive later raise it)."""
    FALLBACK = 50.0

    def __init__(self, rm, pid):
        m = manifest(pid)
        self.approx = m is None
        self.raid_factor = defs.xenotype_factor(faction=m["spec"]["enemy"]["faction"]) if m else 1.0
        self.ours = {}
        squad = (m or {}).get("squad") or []
        if squad and all(x.get("kind") for x in squad):
            xeno = {c["id"]: c.get("xenotype") for c in rm.call("list_genes").get("colonists") or []}
            self.ours = {x["id"]: (defs.combat_power(x["kind"], self.FALLBACK) or self.FALLBACK)
                         * defs.xenotype_factor(xenotype=xeno.get(x["id"])) for x in squad}
            self.basis = "manifest kinds"
        elif squad:
            share = float(m["spec"]["squad"].get("points") or 0) / len(squad) or self.FALLBACK
            self.ours = {x["id"]: share for x in squad}
            self.basis = "squad budget"
        else:
            self.basis = "no manifest"
        self.start = {"ours": 0.0, "raid": 0.0}
        self.series, self.t0 = [], None

    def side(self, rm, faction, worth, mode):
        pawns = [p for p in rm.call("list_things", category="pawn", faction=faction, verbose=True,
                                    confirm=True).get("things") or [] if not p.get("dead")]
        now = 0.0
        for p in pawns:
            if p.get("downed"):
                continue
            w = worth(p)
            if mode == "health":
                w *= (rm.call("get_pawn", id=p["id"]).get("health") or 0) / 100.0
            now += w
        return now, sum(1 for p in pawns if not p.get("downed")), sum(1 for p in pawns if p.get("downed"))

    def update(self, rm, tick, mode):
        ours, o_up, o_dn = self.side(rm, "player", lambda p: self.ours.get(p["id"], self.FALLBACK), mode)
        raid, r_up, r_dn = self.side(rm, "hostile", lambda p: (defs.combat_power(p.get("kind"), self.FALLBACK)
                                                             or self.FALLBACK) * self.raid_factor, mode)
        self.start["ours"], self.start["raid"] = max(self.start["ours"], ours), max(self.start["raid"], raid)
        pct = lambda now, start: round(100 * now / start, 1) if start else 0.0
        self.t0 = tick if self.t0 is None else self.t0
        self.series.append([tick - self.t0, pct(ours, self.start["ours"]), pct(raid, self.start["raid"])])
        if len(self.series) > 600:                       # keep it light: every other point
            self.series = self.series[::2]
        return {"mode": mode, "basis": self.basis, "approx": self.approx,
                "ours": {"now": round(ours), "start": round(self.start["ours"]), "pct": pct(ours, self.start["ours"]),
                         "standing": o_up, "downed": o_dn},
                "raid": {"now": round(raid), "start": round(self.start["raid"]), "pct": pct(raid, self.start["raid"]),
                         "standing": r_up, "downed": r_dn},
                "series": self.series}


def poll(rm, period):
    seen_from = last_start = last_tick = load_from = None
    strength = None
    while True:
        try:
            start, pid, player = battle()
            st = rm.call("get_status")
            tick = st.get("ticksGame") or 0
            # a new battle (another start value), or a load (the clock goes back): messages from here on
            if last_tick is None or tick < last_tick:     # a load: remember where it began
                seen_from = load_from = tick
                strength = None
            if start != last_start:                       # a new battle: from its load, if one was seen
                seen_from = load_from if load_from is not None else tick
                load_from, last_start, strength = None, start, None
            last_tick = tick
            cond = rm.call("get_conditions")         # the HUD's date and hour
            msgs = [m.get("text") for m in (rm.call("get_alerts").get("recentMessages") or [])
                    if (seen_from or 0) <= (m.get("tick") or 0) <= tick      # later than now: from before a load
                    and m.get("text") and not NOISE.search(m["text"])]
            if pid and strength is None:
                strength = Strength(rm, pid)
            power = strength.update(rm, tick, MODE["strength"]) if pid and strength else None
            ladder_agent, rows = ladder(player)
            STATE.clear()
            STATE.update({"ok": True, "busy": False, "pid": pid, "player": player, "date": cond.get("date"), "hour": cond.get("hour"),
                          "paused": bool(st.get("paused")), "power": power,
                          "msgs": [m[:90] for m in msgs[-3:]], "ladder": rows, "ladder_agent": ladder_agent,
                          "at": time.time()})
        except RimMoltBusy:                      # another client holds the game (a build's debug sequence):
            STATE.update({"busy": True})         # keep the last state and skip this poll
        except Exception as e:                   # loads, restarts, odd replies: keep the last state, marked stale
            STATE.update({"ok": False, "note": type(e).__name__})
        time.sleep(period)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/set"):
            q = dict(kv.split("=", 1) for kv in self.path.partition("?")[2].split("&") if "=" in kv)
            if q.get("strength") in ("health", "standing"):
                MODE["strength"] = q["strength"]
            body, kind = json.dumps(MODE).encode(), "application/json"
        elif self.path.startswith("/state.json"):
            body, kind = json.dumps(STATE, ensure_ascii=False).encode(), "application/json"
        elif self.path.startswith("/avatar"):
            body, kind = AVATAR.read_bytes(), "text/html; charset=utf-8"
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
    ap.add_argument("--strength", choices=("health", "standing"), default="health",
                    help="health: standing pawns' points x health %% (a get_pawn each); standing: full points")
    a = ap.parse_args()
    MODE["strength"] = a.strength
    threading.Thread(target=poll, args=(RimMolt(lock_wait=0.5), a.period), daemon=True).start()
    print(f"overlay on http://127.0.0.1:{a.port}/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
