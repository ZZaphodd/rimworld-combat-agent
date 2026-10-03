"""Micro drills, judged per EVENT (WORKFLOW.md test layers), not per battle.

Frag drill: the frozen theme squad (theme_base) stands drafted on its slots with
fire at will OFF, so positioning and targeting are held fixed and nobody kills
the throwers. `count` Grenadier_Destructive spawn at `range` cells east (inside
the 12.9 throw range); non-frag carriers are destroyed, so every projectile is
a frag. The only thing that differs between modes is the micro layer:
  off: observes and counts (counterfactual: who was in the blast at landing)
  on:  dodges; after release the drill walks the pawn back to its slot, unless
       the slot is still inside a live hazard (hysteresis via cell_ok).
A session ends after `events` exploded frags, when fewer than half the squad
stands, or at `max_ticks`; then the base is reloaded.

Per event (one exploded frag): pawns in the blast reach at landing, escaped,
stayed, battle-log hits, moves with fuse left at the order, false-alarm moves
(the pawn was not inside 1.9 of the frag's final cell when ordered).
"""
import json
import math
import time

from .. import ROOT
from ..eval.tracker import short_name
from ..game import session
from ..game.builders.theme import load_base
from ..game.debug import Debug
from ..rimmolt import RimMoltError, hostiles, player_pawns
from ..terrain import Terrain
from .reflex import HIT_R, MICRO_VERSION, VISCOSITY, MicroLayer

KIND = "Grenadier_Destructive"


def fire_at_will(rm, pid, want):
    """Set a drafted pawn's fire-at-will toggle by reading its state first
    (LESSONS bug 14: the old scripts toggled blind). Returns the final state."""
    def state():
        for a in rm.call("inspect_thing", id=pid).get("actions") or []:
            if "fire at will" in (a.get("label") or "").lower():
                return a.get("active")
        return None
    s = state()
    if s is not None and s != want:
        rm.call("do_thing_action", id=pid, label="Fire at will")
        s = state()
    return s


def setup(rm, base, count, rng, log=print):
    """Load theme_base, freeze the squad, spawn frag-only grenadiers."""
    session.start_episode(rm, base["save"])
    rm.call("dev_mode", devMode=True)              # spawning needs it; off before the clock runs
    d = Debug(rm, log)
    ids = [p["id"] for p in base["squad"]]
    slots = {k: tuple(v) for k, v in base["slots"].items()}
    cx = round(sum(s[0] for s in slots.values()) / len(slots))
    cz = round(sum(s[1] for s in slots.values()) / len(slots))
    terrain = Terrain(rm)
    cells = []
    for i in range(count):
        wx, wz = cx + rng, cz - 3 * (count - 1) // 2 + 3 * i
        cells.append(next(((wx + dx, wz) for dx in (0, 1, -1, 2, -2) if terrain.passable(wx + dx, wz)),
                          (wx, wz)))
    new = d.spawn_pawn(KIND, cells)
    weapons = {t["id"]: (rm.call("get_pawn", id=t["id"]).get("weapon") or "") for t in new}
    for t in new:
        if "frag" not in weapons[t["id"]].lower():
            d.destroy_at(t["x"], t["z"])
    d.close()
    rm.call("dev_mode", devMode=False)
    throwers = [t["id"] for t in new if "frag" in weapons[t["id"]].lower()]
    rm.call("draft", action="draft", ids=",".join(ids))
    faw = {pid: fire_at_will(rm, pid, False) for pid in ids}
    if any(v for v in faw.values()):
        raise RimMoltError(f"fire at will still on for {[p for p, v in faw.items() if v]}")
    return ids, slots, throwers, terrain, {"faw_unknown": sum(v is None for v in faw.values())}


def session_run(rm, base, dodge, events=12, count=3, rng=12, step=30, max_ticks=6000, log=print):
    ids, slots, throwers, terrain, info = setup(rm, base, count, rng, log)
    if not throwers:
        raise RimMoltError("no frag carrier among the spawned grenadiers")
    names = {t["id"]: short_name(t.get("label")) for t in player_pawns(rm) if t["id"] in ids}
    dup = len(set(names.values())) < len(names)
    micro = MicroLayer(rm, terrain, VISCOSITY["amove"], enabled=dodge, log=log)
    micro.start(names)
    t0 = rm.call("get_status")["ticksGame"]
    now, owned_before, returns = 0, set(), 0
    wall0 = time.time()
    while True:
        pawns = {t["id"]: t for t in player_pawns(rm) if t["id"] in ids}
        fighters = [{"id": i, "pos": (t["x"], t["z"])} for i, t in pawns.items()
                    if not t.get("downed")]
        hs = hostiles(rm)
        owned = micro.step(fighters, hs, now, step)
        for f in fighters:                  # positioning held fixed: back to the slot
            pid = f["id"]
            if (dodge and pid not in owned and tuple(f["pos"]) != slots[pid]
                    and (pid in owned_before or pid in micro.fled)
                    and micro.cell_ok(pid, slots[pid])):
                rm.call("order_pawn", id=pid, x=slots[pid][0], z=slots[pid][1], command="Go here")
                returns += 1
        owned_before = owned
        rm.wait(step)
        now = rm.call("get_status")["ticksGame"] - t0
        standing = sum(not p.get("downed") for p in pawns.values())
        if (micro.k["frags_exploded"] >= events or standing < len(ids) / 2 or now >= max_ticks
                or not hs):
            break
    micro.step([], [], now, step)           # flush the last explosions
    for pid in names:
        micro.harvest(pid)
    return {"micro": micro, "ticks": now, "wall_s": round(time.time() - wall0, 1),
            "throwers": len(throwers), "standing_end": standing, "squad": len(ids),
            "returns": returns, "names_unique": not dup, **info}


def event_rows(res, dodge, session_id):
    out = []
    for e in res["micro"].events:
        cell = tuple(e["cell"])
        false_alarm = sum(math.dist(tuple(m["from"]), cell) > HIT_R for m in e["moves"])
        out.append({
            "kind": "event", "session": session_id, "dodge": dodge, "micro_version": MICRO_VERSION,
            "frag": e["frag"], "cell": e["cell"], "landed_seen": e["landed_seen"],
            "gone_seen": e["gone_seen"], "in_blast": len(e["in_blast"]),
            "in_zone": len(e["in_zone"]), "escaped": len(e["escaped"]), "stayed": len(e["stayed"]),
            "lost_track": len(e["lost_track"]), "hit_pawns": len(e["hit"]),
            "hit_entries": sum(e["hit"].values()),
            "hit_in_blast": sum(p in e["hit"] for p in e["in_blast"]),
            "moves": len(e["moves"]), "false_alarm_moves": false_alarm,
            "fuse_left_at_move": [m["left"] for m in e["moves"]],
            "latency": [m["tick"] - e["landed_seen"] for m in e["moves"]]})
    return out


def run(rm, sessions=3, events=12, out=None, modes=(False, True), log=print, watchdog=None, **kw):
    """Alternate modes per session so drift in the game hits both alike."""
    out = out or ROOT / "results/drills/frag_drill.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    base = load_base()
    for s in range(sessions):
        for dodge in modes:
            sid = f"{int(time.time())}-{'on' if dodge else 'off'}-{s}"
            for attempt in range(2):
                try:
                    if watchdog:
                        watchdog.ensure()
                    res = session_run(rm, base, dodge, events, log=log, **kw)
                    break
                except Exception as e:
                    log(f"   drill session error (attempt {attempt + 1}): {e!r}")
                    res = None
            if res is None:
                continue
            rows = event_rows(res, dodge, sid)
            k = res["micro"].k
            summary = {"kind": "session", "session": sid, "dodge": dodge,
                       "micro_version": MICRO_VERSION, "ticks": res["ticks"],
                       "wall_s": res["wall_s"], "throwers": res["throwers"],
                       "standing_end": res["standing_end"], "squad": res["squad"],
                       "returns": res["returns"], "names_unique": res["names_unique"],
                       "faw_unknown": res["faw_unknown"], "kpis": res["micro"].kpis(),
                       "moves": res["micro"].moves, "time": time.time()}
            with out.open("a") as f:
                for r in rows + [summary]:
                    f.write(json.dumps(r) + "\n")
            log(f"   session {sid}: {k['frags_exploded']} frags, in blast {k['in_blast_at_landing']}, "
                f"escaped {k['escaped']}, moves {k['moves']}, standing {res['standing_end']}/{res['squad']}")
    return out


def summarize(rows):
    """Per mode: events with someone in the blast at landing, pawn-level escape
    rate, hit rate, false alarms, latency."""
    out = {}
    for dodge in (False, True):
        ev = [r for r in rows if r.get("kind") == "event" and r["dodge"] == dodge]
        hot = [r for r in ev if r["in_blast"]]
        inb = sum(r["in_blast"] for r in hot)
        moves = sum(r["moves"] for r in ev)
        lat = [x for r in ev for x in r["latency"]]
        left = [x for r in ev for x in r["fuse_left_at_move"] if x is not None]
        out["on" if dodge else "off"] = {
            "frags": len(ev), "events_in_blast": len(hot), "pawns_in_blast": inb,
            "escaped": sum(r["escaped"] for r in hot), "stayed": sum(r["stayed"] for r in hot),
            "lost_track": sum(r["lost_track"] for r in hot),
            "escape_rate": round(sum(r["escaped"] for r in hot) / inb, 3) if inb else None,
            "hit_in_blast": sum(r["hit_in_blast"] for r in hot),
            "hit_rate_in_blast": round(sum(r["hit_in_blast"] for r in hot) / inb, 3) if inb else None,
            "hit_pawns_all": sum(r["hit_pawns"] for r in ev),
            "hits_per_frag": round(sum(r["hit_pawns"] for r in ev) / len(ev), 3) if ev else None,
            "events_all_escaped": sum(r["escaped"] == r["in_blast"] for r in hot),
            "moves": moves, "false_alarm_moves": sum(r["false_alarm_moves"] for r in ev),
            "latency_median": sorted(lat)[len(lat) // 2] if lat else None,
            "fuse_left_median": sorted(left)[len(left) // 2] if left else None}
    return out
