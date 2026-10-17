"""Check rca/sight.py against the game: a pawn of ours is teleported to many cells round a target raider
and the float menu's "Fire at <target>" answer (enabled, or disabled with its reason) is compared with
sight.shoot_line on the things of each cell (sight.ThingGrid; --legend uses get_area's ascii instead).
Time never moves; dev mode is on for RimMolt's debug teleport. Door cells are left out (a pawn put there
by teleport may not hold the door open as one who walked in does).

  python3 tools/sight_probe.py --save scenario_rand_227 --shooter Carol --target Vector \
      --at 186,96 --at 180,88 --at 169,103 --n 120 --out results/sight/rand_227.jsonl

Cells are picked by what sight.py says, to spend the samples where the rules are tested: shots that
need a lean, cells whose straight line is blocked near a corner, pawns on one row or column (the
AngleFlat question), the range edge and the adjacent ring; random cells fill the rest. --no-load uses
the game as it stands (the save already loaded).
"""
import argparse
import json
import random
import sys
from pathlib import Path

import _path  # noqa: F401
from rca import sight
from rca.eval.tracker import short_name
from rca.game import session
from rca.game.debug import Debug
from rca.game.weapons import weapon_range
from rca.rimmolt import RimMolt
from rca.terrain import Terrain

STANDABLE = set(".*")


def pick_cells(grid, terrain, target, rng, n, taken, seed):
    """Up to n shooter cells round target, the interesting ones first."""
    tx, tz = target
    r = int(rng) + 2
    cells = [(x, z) for x in range(tx - r, tx + r + 1) for z in range(tz - r, tz + r + 1)
             if (x, z) != target and terrain.inside(x, z) and terrain.cell(x, z) in STANDABLE and (x, z) not in taken
             and not grid.door(x, z) and not grid.blocks(x, z)
             and (x - tx) ** 2 + (z - tz) ** 2 <= (rng + 1.5) ** 2]
    groups = {"lean": [], "blocked": [], "aligned": [], "edge": [], "adjacent": [], "other": []}
    for c in cells:
        d2 = (c[0] - tx) ** 2 + (c[1] - tz) ** 2
        ans = sight.shoot_line(grid, c, target, rng)
        if d2 <= 2:
            groups["adjacent"].append(c)
        elif abs(d2 ** 0.5 - rng) < 1.2:
            groups["edge"].append(c)
        elif ans and ans != (c, target):
            groups["lean"].append(c)
        elif c[0] == tx or c[1] == tz:
            groups["aligned"].append(c)
        elif not sight.line_of_sight(grid, c, target):
            groups["blocked"].append(c)
        else:
            groups["other"].append(c)
    rnd = random.Random(seed)
    quota = {"lean": n * 3 // 10, "blocked": n * 3 // 10, "aligned": n // 6, "edge": n // 12, "adjacent": 4}
    out = []
    for k, q in quota.items():
        rnd.shuffle(groups[k])
        out += [(c, k) for c in groups[k][:q]]
    rest = [c for k in groups for c in groups[k] if (c, k) not in out and c not in {o[0] for o in out}]
    rnd.shuffle(rest)
    out += [(c, "other") for c in rest[:max(0, n - len(out))]]
    return out


def menu_answer(rm, shooter_id, target_id, target_name):
    opts = rm.call("order_pawn", id=shooter_id, targetId=target_id).get("options", [])
    fire = [o for o in opts if o["label"].lower().startswith(f"fire at {target_name.lower()}")]
    if not fire:
        return None, "no fire option"
    o = fire[0]
    return not o["disabled"], o["label"].split(": ", 1)[1] if ": " in o["label"] else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", required=True)
    ap.add_argument("--no-load", action="store_true")
    ap.add_argument("--shooter", required=True, help="short name of a pawn of ours with a gun")
    ap.add_argument("--target", required=True, help="short name of a raider")
    ap.add_argument("--at", action="append", required=True, help="target cell x,z (repeatable)")
    ap.add_argument("--n", type=int, default=120, help="shooter cells per target cell")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--legend", action="store_true", help="judge cells by get_area's ascii, not the things")
    a = ap.parse_args()
    rm = RimMolt()
    if not a.no_load:
        session.load(rm, a.save)
    rm.call("dev_mode", devMode=True)
    d = Debug(rm)
    pawns = {side: rm.call("list_things", category="pawn", faction=side, verbose=True, confirm=True)["things"]
             for side in ("player", "hostile")}
    sh = next(p for p in pawns["player"] if short_name(p["label"]) == a.shooter)
    tg = next(p for p in pawns["hostile"] if short_name(p["label"]) == a.target)
    rng = weapon_range(rm.call("get_pawn", id=sh["id"]).get("weapon") or "")
    taken = {(p["x"], p["z"]) for side in pawns.values() for p in side if p["id"] not in (sh["id"], tg["id"])}
    terrain = Terrain(rm)
    fetch = lambda x0, z0, x1, z1: rm.call("get_area", minX=x0, minZ=z0, maxX=x1, maxZ=z1,  # noqa: E731
                                           layer="things", confirm=True)["things"]
    rotations = lambda name: {(t["x"], t["z"]): t.get("rotation") for t in rm.call(  # noqa: E731
        "list_things", category="all", defName=name, verbose=True, confirm=True, limit=2000).get("things") or []}
    grid = sight.TerrainGrid(terrain) if a.legend else sight.ThingGrid(fetch, rotations=rotations)
    rm.call("draft", action="draft", ids=sh["id"])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, spec in enumerate(a.at):
        target = tuple(int(v) for v in spec.split(","))
        if not d.teleport(tg["id"], *target):
            sys.exit(f"could not put {a.target} on {target}")
        for cell, kind in pick_cells(grid, terrain, target, rng, a.n, taken, a.seed + i):
            if not d.teleport(sh["id"], *cell):
                rows.append({"target": target, "shooter": cell, "kind": kind, "skip": "teleport failed"})
                continue
            game, why = menu_answer(rm, sh["id"], tg["id"], a.target)
            ans = sight.shoot_line(grid, cell, target, rng)
            rows.append({"save": a.save, "range": rng, "target": target, "shooter": cell, "kind": kind,
                         "game": game, "why": why, "sight": ans, "agree": game == (ans is not None)})
        d.close()
    with a.out.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    done = [r for r in rows if "agree" in r and r["game"] is not None]
    bad = [r for r in done if not r["agree"]]
    print(f"{len(done)} compared, {len(bad)} differ, {len(rows) - len(done)} skipped -> {a.out}")
    for k in ("lean", "blocked", "aligned", "edge", "adjacent", "other"):
        ks = [r for r in done if r["kind"] == k]
        print(f"  {k:9} {len(ks):4} compared, {sum(not r['agree'] for r in ks)} differ")
    for r in bad[:30]:
        print("  differ:", r["target"], r["shooter"], r["kind"], "game", r["game"], r["why"], "sight", r["sight"])


if __name__ == "__main__":
    main()
