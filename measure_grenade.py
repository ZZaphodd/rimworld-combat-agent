"""Measure how much time a pawn has to react to a frag grenade.

Spawns a grenadier raid against the theme squad, advances the game a couple of
ticks at a time, and records for every explosive projectile thing we can see:
first tick seen (in flight or landed), where it lands, and the tick it vanishes
(= explosion). The gap between 'landed' and 'gone' is the reaction window the
harness decision cycle has to fit into.

  python3 measure_grenade.py [--samples 15] [--tick 2]
"""
import argparse
import json
import time

from rimmolt_client import RimMolt
from scenario_builder import Builder

PROJ_HINTS = ("grenade", "proj_", "molotov", "shell", "bullet_launcher")


def projectiles(rm):
    things = rm.call("list_things", category="all", confirm=True, verbose=True,
                     limit=5000)["things"]
    return {t["id"]: t for t in things
            if any(h in (t.get("def", "") + t.get("label", "")).lower() for h in PROJ_HINTS)
            and t.get("category") != "Pawn"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=15)
    ap.add_argument("--tick", type=int, default=2)
    ap.add_argument("--max-ticks", type=int, default=6000)
    a = ap.parse_args()

    rm = RimMolt()
    b = Builder(rm)
    b.load("scenario_theme_pirate_grenadier")
    rm.call("debug_menu", action="run", tab="settings", path="Never Force Normal Speed", value=True)
    rm.call("debug_menu", action="close")
    # Squad stands drafted in place so it is a stable target.
    ids = [c["id"] for c in rm.call("list_colonists")["colonists"]]
    rm.call("draft", action="draft", ids=",".join(ids))

    seen, done = {}, []
    t0 = rm.call("get_status")["ticksGame"]
    wall = time.time()
    while len(done) < a.samples:
        rm.call("wait_for_event", _timeout=30, maxGameTicks=a.tick, maxSeconds=10,
                pause="always", force=True)
        now = rm.call("get_status")["ticksGame"] - t0
        cur = projectiles(rm)
        for pid, t in cur.items():
            s = seen.setdefault(pid, {"def": t.get("def"), "first": now, "pos": []})
            s["pos"].append((now, t["x"], t["z"]))
        for pid, s in list(seen.items()):
            if pid not in cur and "gone" not in s:
                s["gone"] = now
                # 'landed' = first sample from which the position stopped changing
                pos = s["pos"]
                land = next((p[0] for i, p in enumerate(pos)
                             if all((q[1], q[2]) == (p[1], p[2]) for q in pos[i:])), pos[-1][0])
                s["landed"] = land
                s["fuse"] = s["gone"] - land
                s["flight"] = land - s["first"]
                done.append(s)
                print(f"{s['def']:28} flight>={s['flight']:3} ticks, on ground {s['fuse']:3} ticks, "
                      f"landed at {pos[-1][1:]}")
        if now > a.max_ticks:
            print("max ticks reached")
            break
    fuses = sorted(s["fuse"] for s in done)
    print(json.dumps({"samples": len(done), "tick_resolution": a.tick,
                      "fuse_ticks": fuses,
                      "by_def": {d: sorted(s["fuse"] for s in done if s["def"] == d)
                                 for d in {s["def"] for s in done}},
                      "wall_s": round(time.time() - wall, 1)}, indent=1))


if __name__ == "__main__":
    main()
