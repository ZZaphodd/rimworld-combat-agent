"""How far from a resting frag grenade does its blast still hurt?

Sets the reflex layer's danger radius from data instead of the XML guess. The
theme squad stands drafted with fire at will off; grenadiers spawned ~14 cells
away throw at it. For every frag grenade: its rest cell, and when it vanishes
(= exploded), each squad pawn's distance to it and whether that pawn's log got a
new frag-grenade damage entry since the previous check. Grenades that blow up
within a few ticks of each other are skipped (hits can't be attributed).

  python3 measure_blast.py --grenades 25
"""
import argparse
import json
import math
import statistics
from collections import Counter

from battle_tracker import short_name
from reflexes import frag_damage_entries
from rimmolt_client import RimMolt
from scenario_builder import Builder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grenades", type=int, default=25)
    ap.add_argument("--tick", type=int, default=6)
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--max-ticks", type=int, default=8000)
    a = ap.parse_args()
    rm = RimMolt()
    b = Builder(rm)
    b.load("theme_base")
    rm.call("debug_menu", action="run", tab="settings", path="Never Force Normal Speed", value=True)
    rm.call("debug_menu", action="close")
    squad = rm.call("list_things", category="pawn", faction="player", confirm=True,
                    verbose=True)["things"]
    ids = [t["id"] for t in squad]
    names = {t["id"]: short_name(t.get("label")) for t in squad}
    rm.call("draft", action="draft", ids=",".join(ids))
    for pid in ids:
        rm.call("do_thing_action", id=pid, label="Fire at will")
    seen_log = {pid: {(e["tick"], e["text"]) for e in frag_damage_entries(rm, pid, names[pid])}
                for pid in ids}
    cx = round(statistics.mean(t["x"] for t in squad))
    cz = round(statistics.mean(t["z"] for t in squad))
    b.dbg(action="run", path="Spawn Pawn... > Grenadier_Destructive")
    b.dbg(action="click", cells=";".join(f"{cx + 14},{cz - 3 + 3 * i}" for i in range(a.count)))
    b.dbg(action="close")
    t0 = rm.call("get_status")["ticksGame"]
    last, rows, steps = {}, [], Counter()
    while len(rows) < a.grenades:
        before = rm.call("get_status")["ticksGame"]
        rm.call("wait_for_event", _timeout=30, maxGameTicks=a.tick, maxSeconds=10,
                pause="always", force=True)
        now = rm.call("get_status")["ticksGame"] - t0
        steps[now + t0 - before] += 1
        cur = {t["id"]: (t["x"], t["z"]) for t in rm.call(
            "list_things", category="all", defName="Proj_GrenadeFrag", verbose=True)["things"]}
        gone = [g for g in last if g not in cur]
        if gone:
            pos = {t["id"]: (t["x"], t["z"]) for t in rm.call(
                "list_things", category="pawn", faction="player", confirm=True)["things"]}
            hit = {}
            for pid in pos:
                new = {(e["tick"], e["text"]) for e in frag_damage_entries(rm, pid, names[pid])}
                hit[pid] = bool(new - seen_log[pid])
                seen_log[pid] |= new
            if len(gone) == 1:
                g = last[gone[0]]
                for pid, p in pos.items():
                    rows.append({"d": round(math.dist(p, g), 2), "hit": hit[pid]}) \
                        if math.dist(p, g) <= 6 else None
                print(f"{now}: blast at {g}: " + ", ".join(
                    f"{math.dist(p, g):.1f}{'*' if hit[pid] else ''}" for pid, p in pos.items()
                    if math.dist(p, g) <= 6), flush=True)
        last = cur
        if now > a.max_ticks or not pos_alive(rm):
            break
    by = {}
    for r in rows:
        by.setdefault(math.ceil(r["d"] * 2) / 2, []).append(r["hit"])
    print("\ndistance  n  hit-rate")
    for d in sorted(by):
        print(f"{d:5.1f} {len(by[d]):4} {sum(by[d]) / len(by[d]):6.2f}")
    print("actual ticks per wait:", dict(steps))
    with open("results/hazards.jsonl", "a") as f:
        f.write(json.dumps({"kind": "frag_blast_radius", "rows": rows}) + "\n")


def pos_alive(rm):
    return any(not c.get("downed") for c in rm.call("list_colonists")["colonists"])


if __name__ == "__main__":
    main()
