"""Look at a base problem's map and check a position plan, offline (no game; rca.strategic.siteplan).

  python3 tools/site_plan.py show base2_ith_pirate_2x [--box X0 Z0 X1 Z1] [--plan PLAN]
  python3 tools/site_plan.py check results/base/plans/base2_r1.json

show prints the problem's save map around the squad (or the plan's cells): % rock, # wall or
impassable building, + door (D held open), f furniture a pawn cannot stop on, ^ trap, T turret,
o our pawn at the start, r raider at the start, A-Z the plan's cells, R rear cells, * anchor.
check validates every entry against its manifest and map and fails on errors or missing problems.
"""
import argparse
import json
import statistics
import string
import sys

import _path  # noqa: F401
from rca import ROOT
from rca.game import savemap
from rca.strategic import siteplan


def manifest(pid):
    hits = sorted(ROOT.glob(f"scenarios*/scenario_{pid}.json"))
    if not hits:
        sys.exit(f"no manifest for {pid}")
    return json.loads(hits[0].read_text())


def render(m, smap, box, site=None):
    x0, z0, x1, z1 = box
    over = {}
    for t in smap.traps:
        over[t["cell"]] = "^"
    for t in smap.turrets:
        over[t["cell"]] = "T"
    for d in smap.doors:
        if d["hold_open"]:
            over[d["cell"]] = "D"
    for p in m["enemy"]:
        over[(p["x"], p["z"])] = "r"
    for p in m["squad"]:
        over[(p["x"], p["z"])] = "o"
    letters = {}
    if site:
        for i, (k, c) in enumerate(sorted(site.cells.items(), key=lambda kv: (-kv[1][1], kv[1][0]))):
            letters[k] = string.ascii_uppercase[i % 26]
            over[c] = letters[k]
        for c in site.rear:
            over.setdefault(c, "R")
        over.setdefault(site.anchor, "*")
        for c, held in site.doors:
            over[c] = "D" if held else "+"
    out = ["      " + "".join(str(x // 10 % 10) if x % 10 == 0 else " " for x in range(x0, x1 + 1)),
           "      " + "".join(str(x % 10) for x in range(x0, x1 + 1))]
    for z in range(z1, z0 - 1, -1):
        row = []
        for x in range(x0, x1 + 1):
            ch = over.get((x, z)) or smap.cell(x, z)
            if ch == "." and not smap.standable(x, z):
                ch = "f"
            row.append(ch)
        out.append(f"{z:>4}  " + "".join(row))
    return "\n".join(out), letters


def show(a):
    m = manifest(a.pid)
    smap = savemap.load(m["save"])
    site = None
    if a.plan:
        e = (siteplan.load(a.plan).get("problems") or {}).get(a.pid)
        site = siteplan.build(a.pid, e) if e else None
    if a.box:
        box = a.box
    else:
        pts = list(site.cells.values()) + [site.anchor] if site else [(p["x"], p["z"]) for p in m["squad"]]
        cx, cz = statistics.median(p[0] for p in pts), statistics.median(p[1] for p in pts)
        r = 15 if site else 25
        box = (int(cx - r * 2), int(cz - r), int(cx + r * 2), int(cz + r))
    text, letters = render(m, smap, box, site)
    print(text)
    sp = m["spec"]
    rx = statistics.median(p["x"] for p in m["enemy"])
    rz = statistics.median(p["z"] for p in m["enemy"])
    kinds = {}
    for p in m["enemy"]:
        kinds[p["def"]] = kinds.get(p["def"], 0) + 1
    print(f"\n{a.pid}: raid {sp['enemy']['faction']} {sp['enemy']['points']} pts {sp['enemy']['strategy']}, "
          f"{len(m['enemy'])} at median ({rx:g},{rz:g}): {kinds}")
    for p in m["squad"]:
        tag = f"{letters[p['id']]} " if p["id"] in letters else ""
        print(f"  {tag}{p['id']:<14} {p['name'][:26]:<26} {p.get('weapon', '')}  start ({p['x']},{p['z']})")
    near = [d for d in smap.doors if box[0] <= d["cell"][0] <= box[2] and box[1] <= d["cell"][1] <= box[3]]
    print("doors in view: " + ", ".join(f"{d['cell']}{' held open' if d['hold_open'] else ''}" for d in near))


def check(a):
    data = siteplan.load(a.plan)
    probs = data.get("problems") or {}
    pids = sorted(p.stem[len("scenario_"):] for p in (ROOT / data.get("for", "scenarios_base2")).glob("scenario_*.json"))
    bad = 0
    for pid in pids:
        if pid not in probs:
            print(f"{pid}: MISSING")
            bad += 1
            continue
        m = manifest(pid)
        smap = savemap.load(m["save"])
        errs, warns = siteplan.validate(probs[pid], m, smap)
        if smap.unknown or smap.unknown_packed:
            warns.append(f"map: {smap.unknown_packed} packed cells and buildings {sorted(smap.unknown)} unknown to "
                         f"data/buildings.json (drawn as rock / left off)")
        s = siteplan.build(pid, probs[pid]) if not errs else None
        print(f"{pid}: {'ERROR' if errs else 'ok'}  {siteplan.describe(s) if s else ''}")
        for x in errs:
            print(f"   error: {x}")
        for x in warns:
            print(f"   warn: {x}")
        bad += bool(errs)
    extra = sorted(set(probs) - set(pids))
    for pid in extra:
        print(f"{pid}: not a problem of {data.get('for')}")
    print(f"{len(pids) - bad}/{len(pids)} valid" + (f", {len(extra)} unknown" if extra else ""))
    return 1 if bad or extra else 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("pid")
    s.add_argument("--box", type=int, nargs=4)
    s.add_argument("--plan")
    c = sub.add_parser("check")
    c.add_argument("plan")
    a = ap.parse_args()
    if a.cmd == "show":
        show(a)
    else:
        sys.exit(check(a))


if __name__ == "__main__":
    main()
