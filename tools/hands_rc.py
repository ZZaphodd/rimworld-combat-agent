"""Mixed hands (2026-10-17): game time and the pawn picture through rimcockpit 0.2.0, orders through RimMolt.

  python3 -c "import sys; sys.path.insert(0, 'tools'); from hands_rc import *; st()"

Everything in tools/hands.py is here too; what changes is where time and some reads come from:
- Time moves only through rimcockpit's `advance` (wait, skip, and through them guard, wait_safe and
  frags), never through RimMolt's wait: rimcockpit's 0.2.0 notice asks that one side drive time.
  wait() runs at the normal pace (60 ticks/s, as RimMolt's wait did, so the harness's 1 s polls see
  the same); skip() at the batch pace.
- st() and wait_safe() read the pawns from rimcockpit's snapshot.
- Orders (go, fire, attack, melee, hit, draft, manage_gear) and the reads rimcockpit does not have yet
  (projectiles and raiders' targeting for guard's grenade reflex, brief, fireable, the float menus)
  stay on RimMolt. Pawn ids are the game's thing ids on both sides.

The frozen 0.2.0 client is read from RIMCOCKPIT_CLIENT, by default a clone of the private rimcockpit
repo in ~/.cache/rimcockpit (never copied into this public repo). Reads use the observer token, time
the pilot token. Claude's play never asks for concealed pawns (rimcockpit D68/D74).
"""
import math
import os
import sys
from pathlib import Path

import hands as H
from hands import *  # noqa: F401,F403  (orders and the RimMolt reads)

CLIENT = Path(os.environ.get("RIMCOCKPIT_CLIENT")
              or Path.home() / ".cache/rimcockpit/clients/python/releases/0.2.0")
sys.path.insert(0, str(CLIENT))
import rimcockpit  # noqa: E402
if Path(rimcockpit.__file__).resolve().parent != (CLIENT / "rimcockpit").resolve():
    raise ImportError(f"rimcockpit came from {rimcockpit.__file__}, not {CLIENT}")
from rimcockpit import Client  # noqa: E402

PACE = os.environ.get("RCA_PACE", "normal")
NAME = "rca.hands"
_CLIENTS = {}


def client(role="observer"):
    """One rimcockpit client per role and process (observer reads, pilot time)."""
    if role not in _CLIENTS:
        _CLIENTS[role] = Client(NAME, role)
    return _CLIENTS[role]


def advance(n, pace=None):
    """Exactly n game ticks through rimcockpit, ending paused (a dialog that force-pauses the game is
    ticked through, as RimMolt's forced wait did). Prints a line when it stopped short or was not exact;
    returns the reply."""
    r = client("pilot").advance(n=n, pace=pace or PACE, onForcePause="continue")
    exact = getattr(r.exact, "ok", r.exact)          # {ok, ticksGameDelta, skipped}
    if r.stopReason != "done" or not exact or r.ticksAdvanced != n:
        print(f"   advance {n}: stopped {r.stopReason} after {r.ticksAdvanced} "
              f"(exact={exact}, outside={r.outsideTicks}) at {r.endTick}", flush=True)
    return r


def wait(t):
    return advance(t)


def skip(t, until=None, chunk=600):
    """Fast-forward t ticks at the batch pace, for stretches where nothing needs an answer. With
    `until` (called with no argument), it advances in chunks and stops once until() is true. Returns
    {start, end, ticks, early}."""
    start = now()
    end, early = start, None
    while end - start < t:
        step = min(chunk if until else t, t - (end - start))
        end = advance(step, pace="batch").endTick
        if until and until():
            early = "until"
            break
    return {"start": start, "end": end, "ticks": end - start, "early": early}


H.wait, H.skip = wait, skip              # guard, wait_safe and frags in hands call these


def snap(side=None, include=("weapon", "job"), life=None):
    """The snapshot's pawn rows (dicts) and its tick; side: "player", "hostile", "neutral", "wild";
    life: a list of "standing", "downed", "dead"."""
    r = client().snapshot(include=list(include), side=[side] if side else None, life=life, limit=500)
    return r.raw.get("pawns") or [], r.header.ticksGame


def now():
    return client().status().header.ticksGame


def row_line(p):
    """One pawn as st() prints it: name@x,z health% [DOWN] weapon | job."""
    w = ((p.get("weapon") or {}).get("def") or "-").replace("Gun_", "").replace("MeleeWeapon_", "")
    hp = p.get("summaryHealth")
    hp = "?" if hp is None else round(hp * 100)
    j = p.get("job") or {}
    job = j.get("jobText") or p.get("jobDef") or ""
    d = (j.get("pather") or {}).get("destination") or {} if (j.get("pather") or {}).get("moving") else {}
    dest = d.get("cell") or (d if "x" in d else None)
    go_to = f" ->{dest['x']},{dest['z']}" if dest else ""
    return (f"{(p.get('shortName') or '?')[:9]}@{p['x']},{p['z']} {hp}%"
            f"{' DOWN' if p.get('downed') else ''} {w} | {str(job)[:28]}{go_to}  [{p['id']}]")


def st(jobs=True):
    """Our squad and the raid from one snapshot (the living; ids in brackets for hit())."""
    rows, tick = snap(life=["standing", "downed"])
    print("tick", tick - 383, "(game", tick, ")")             # as hands.st: the rand scenarios start at 383
    for side, head in (("player", "OURS "), ("hostile", "THEM ")):
        mine = [p for p in rows if p.get("side") == side]
        print(head + str(len(mine)))
        for p in mine:
            print("  ", row_line(p) if jobs else row_line({**p, "job": None, "jobDef": None}))


def alarm_reason(rows, dist):
    """Why wait_safe should stop, from snapshot rows: one of ours down, or a standing raider within
    dist cells of a standing pawn of ours; None when neither."""
    ours = [p for p in rows if p.get("side") == "player" and not p.get("dead")]
    down = [p["shortName"] for p in ours if p.get("downed")]
    if down:
        return f"down: {', '.join(down)}"
    them = [p for p in rows if p.get("side") == "hostile" and not p.get("dead") and not p.get("downed")]
    for o in ours:
        for h in them:
            d = math.dist((o["x"], o["z"]), (h["x"], h["z"]))
            if d <= dist:
                return f"near: {h['shortName']} {d:.1f} from {o['shortName']}"
    return None


def wait_safe(ticks, alarm=25, chunk=60):
    """Advance up to `ticks` in chunks, returning early (with the reason) when a raider comes within
    `alarm` cells of a standing pawn of ours, or one more of ours goes down (snapshot reads)."""
    rows, t0 = snap(include=())
    down0 = {p["id"] for p in rows if p.get("side") == "player" and p.get("downed")}
    t = t0
    while t - t0 < ticks:
        t = advance(min(chunk, ticks - (t - t0))).endTick
        rows, _ = snap(include=())
        fresh = [p for p in rows if p["id"] not in down0]
        why = alarm_reason(fresh, alarm)
        if why:
            print(f"   wait_safe stopped at {t}: {why}", flush=True)
            return why
    return None


H.wait_safe = wait_safe
