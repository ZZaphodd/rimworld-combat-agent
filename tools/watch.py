"""Read-only watcher for a battle someone else is playing (run_human.py): wait for the game to
move on, then print who stands where (health, weapon, job, distance) and draw a labelled
offscreen frame. Never pauses, orders or moves the camera.

  python3 tools/watch.py --ticks 600 --wait 90          # in the background, once per look
  python3 tools/watch.py --now                          # look right away

It returns after --ticks game ticks have passed, an enemy comes within --near cells of our
squad for the first time in this look, or --wait seconds of wall time. The frame goes to
results/human/hands_watch_<tick>.jpg (local, not versioned); the printed rect and screenshot
path let a report redraw it later.
"""
import argparse
import math
import sys
import time

import _path  # noqa: F401
from rca import ROOT
from rca.eval import frames
from rca.eval.tracker import short_name
from rca.rimmolt import RimMolt

PROJ = ("Proj_GrenadeFrag", "Proj_GrenadeMolotov", "Proj_GrenadeEMP", "Proj_GrenadeSmoke")


def live(rm):
    things = rm.call("list_things", category="pawn", verbose=True, confirm=True).get("things", [])
    return [p for p in things if not p.get("dead")]


def sides(pawns):
    ours = [p for p in pawns if p.get("faction") == "New Arrivals" or p.get("kind") == "Colonist"]
    them = [p for p in pawns if p.get("hostile")]
    return ours, them


def centroid(ps):
    return (sum(p["x"] for p in ps) / len(ps), sum(p["z"] for p in ps) / len(ps))


def nearest(p, others):
    return min((math.dist((p["x"], p["z"]), (o["x"], o["z"])) for o in others), default=999)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=600, help="return after this many game ticks")
    ap.add_argument("--wait", type=float, default=90, help="return after this many seconds")
    ap.add_argument("--near", type=float, default=30, help="return when an enemy comes this close")
    ap.add_argument("--now", action="store_true")
    a = ap.parse_args()
    rm = RimMolt()
    t_start, wall0 = rm.call("get_status")["ticksGame"], time.time()
    was_near = None
    while not a.now:
        try:
            ours, them = sides(live(rm))
            tick = rm.call("get_status")["ticksGame"]
        except Exception:                          # loading
            time.sleep(2)
            continue
        standing = [p for p in ours if not p.get("downed")]
        close = bool(standing and them and min(nearest(p, standing) for p in them) <= a.near)
        if was_near is None:
            was_near = close
        if tick - t_start >= a.ticks or (close and not was_near) or time.time() - wall0 > a.wait:
            break
        time.sleep(2)
    st = rm.call("get_status")
    ours, them = sides(live(rm))
    if not ours:
        print("no squad on the map")
        return
    print(f"tick {st['ticksGame'] - 383} (game {st['ticksGame']}) | paused={st.get('paused')} "
          f"| ours {len(ours)} (down {sum(1 for p in ours if p.get('downed'))}) "
          f"| them {len(them)} (down {sum(1 for p in them if p.get('downed'))})")
    standing = [p for p in ours if not p.get("downed")] or ours
    for label, group, other in (("OURS", ours, them), ("THEM", them, standing)):
        print(label)
        for p in sorted(group, key=lambda p: nearest(p, other)):
            g = rm.call("get_pawn", id=p["id"])
            w = (g.get("weapon") or "-").split(" (")[0]
            print(f"   {short_name(p['label'])[:11]:11} @{p['x']},{p['z']} {g.get('health')}%"
                  f"{' DOWN' if p.get('downed') else ''} {w[:22]} | {(g.get('job') or '')[:34]}"
                  f" | nearest foe {nearest(p, other):.0f}")
    fires = rm.call("list_things", category="all", defName="Fire", confirm=True).get("things", [])
    proj = sum(len(rm.call("list_things", category="all", defName=d, confirm=True).get("things", []))
               for d in PROJ)
    print(f"fires {len(fires)} | grenades in the air {proj}")
    cx, cz = centroid(standing)
    near = [p for p in them if math.dist((p["x"], p["z"]), (cx, cz)) < 45]
    pts = [(p["x"], p["z"]) for p in ours] + [(p["x"], p["z"]) for p in near]
    xs, zs = [x for x, _ in pts], [z for _, z in pts]
    w = min(max(max(xs) - min(xs) + 14, 40), 80)
    h = min(max(max(zs) - min(zs) + 14, 30), 56)
    x0 = int(max(0, min(250 - w, (min(xs) + max(xs)) / 2 - w / 2)))
    z0 = int(max(0, min(250 - h, (min(zs) + max(zs)) / 2 - h / 2)))
    r = rm.call("screenshot", x=x0, z=z0, w=w, h=h, include_ui=False,
                pixels_per_cell=max(9, min(18, 760 // w)))
    marks = [{"n": short_name(p["label"]), "x": p["x"], "z": p["z"], "d": bool(p.get("downed")),
              "side": "ours" if p in ours else "them"} for p in ours + them]
    out = ROOT / f"results/human/hands_watch_{st['ticksGame'] - 383}.jpg"
    frames.annotate(r["path"], (x0, x0 + w, z0, z0 + h), str(out), marks,
                    caption=f"t{st['ticksGame'] - 383}", gamma=1.3)
    print(f"rect x{x0}-{x0 + w} z{z0}-{z0 + h}")
    print("shot", r["path"].replace(str(__import__('pathlib').Path.home()), "~"))
    print("frame", out.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
