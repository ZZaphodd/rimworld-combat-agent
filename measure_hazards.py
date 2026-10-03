"""Measure the reaction window of telegraphed area attacks.

Static stats (get_info_card) give each weapon's aiming time; this script
measures what the game lets us *see* of the rest. It spawns hostile carriers of
one pawn kind next to the frozen theme squad (fire at will off, so the throwers
survive), samples every `--tick` ticks, and logs:
  * the carrier's targeting/job each sample (is aiming observable?);
  * every explosive projectile: first seen, position track, last seen;
  * every 'Explosion' thing: where and when blasts happen.

  python3 measure_hazards.py Grenadier_Destructive --count 3 --samples 10
"""
import argparse
import json
import math
import statistics

from rimmolt_client import RimMolt
from scenario_builder import Builder

EXPLOSIVE = ("grenade", "rocket", "doomsday", "shell", "molotov", "emp", "incendiary", "smoke",
             "explosion")
# category='all' on a forest map is truncated by thousands of plants, so ask for
# the projectile defs we know about by name (plus the carriers themselves).
PROJECTILE_DEFS = ("Proj_GrenadeFrag", "Proj_GrenadeMolotov", "Proj_GrenadeEMP", "Proj_GrenadeTox",
                   "Proj_GrenadeSmoke", "Bullet_Rocket", "Bullet_DoomsdayRocket",
                   "Bullet_IncendiaryLauncher", "Bullet_EMPLauncher", "Bullet_SmokeLauncher",
                   "Explosion")


def things(rm, cat="all"):
    out = rm.call("list_things", category="pawn", confirm=True, verbose=True)["things"]
    for d in PROJECTILE_DEFS:
        out += rm.call("list_things", category="all", defName=d, verbose=True)["things"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--samples", type=int, default=10, help="projectiles to track")
    ap.add_argument("--tick", type=int, default=2)
    ap.add_argument("--distance", type=int, default=12)
    ap.add_argument("--max-ticks", type=int, default=4000)
    a = ap.parse_args()

    rm = RimMolt()
    b = Builder(rm)
    b.load("theme_base")
    rm.call("debug_menu", action="run", tab="settings", path="Never Force Normal Speed", value=True)
    rm.call("debug_menu", action="close")
    squad = rm.call("list_things", category="pawn", faction="player", confirm=True)["things"]
    ids = [t["id"] for t in squad]
    rm.call("draft", action="draft", ids=",".join(ids))
    for pid in ids:                                   # stay put and don't kill the throwers
        rm.call("do_thing_action", id=pid, label="Fire at will")
    cx = round(statistics.mean(t["x"] for t in squad))
    cz = round(statistics.mean(t["z"] for t in squad))
    cells = ";".join(f"{cx + a.distance},{cz - 2 + 2 * i}" for i in range(a.count))
    b.dbg(action="run", path=f"Spawn Pawn... > {a.kind}")
    b.dbg(action="click", cells=cells)
    b.dbg(action="close")
    carriers = {t["id"]: t for t in rm.call("list_things", category="pawn", faction="hostile",
                                            confirm=True)["things"]}
    weapons = {i: rm.call("get_pawn", id=i).get("weapon") for i in carriers}
    print(f"spawned {len(carriers)} x {a.kind} at ~{a.distance} cells: {weapons}")

    tracks, blasts, aim_log = {}, [], {i: [] for i in carriers}
    t0 = rm.call("get_status")["ticksGame"]
    seen_blast = set()
    while True:
        rm.call("wait_for_event", _timeout=30, maxGameTicks=a.tick, maxSeconds=10,
                pause="always", force=True)
        now = rm.call("get_status")["ticksGame"] - t0
        snapshot = things(rm)
        present = set()
        for t in snapshot:
            name = (t.get("def", "") + " " + t.get("label", "")).lower()
            if t.get("category") == "Pawn" or not any(k in name for k in EXPLOSIVE):
                continue
            if t["def"] == "Explosion":
                if t["id"] not in seen_blast:
                    seen_blast.add(t["id"])
                    blasts.append({"tick": now, "x": t["x"], "z": t["z"]})
                continue
            if t["def"].startswith(("Weapon_", "Gun_")):
                continue                              # dropped weapons, not projectiles
            present.add(t["id"])
            tr = tracks.setdefault(t["id"], {"def": t["def"], "first": now, "pos": []})
            tr["pos"].append((now, t["x"], t["z"]))
        for tid, tr in tracks.items():
            if tid not in present and "last" not in tr:
                tr["last"] = tr["pos"][-1][0]
        for t in snapshot:
            if t["id"] in carriers:
                aim_log[t["id"]].append((now, (t.get("targeting") or "-")[:40]))
        finished = [tr for tr in tracks.values() if "last" in tr]
        if len(finished) >= a.samples or now > a.max_ticks:
            break

    print(f"\n{'projectile':24} {'seen':>5} {'last':>5} {'life':>5} {'moving':>6} {'resting':>7}  path")
    rows = []
    for tr in sorted(finished, key=lambda r: r["first"]):
        pos = tr["pos"]
        last_move = max((p[0] for i, p in enumerate(pos[1:], 1)
                         if (p[1], p[2]) != (pos[i - 1][1], pos[i - 1][2])), default=pos[0][0])
        rest = tr["last"] - last_move
        rows.append({"def": tr["def"], "life": tr["last"] - tr["first"],
                     "moving": last_move - tr["first"], "resting": rest})
        print(f"{tr['def']:24} {tr['first']:5} {tr['last']:5} {tr['last'] - tr['first']:5} "
              f"{last_move - tr['first']:6} {rest:7}  {pos[0][1:]}->{pos[-1][1:]}")
    print("\nblasts:", blasts[:12])
    print("\ncarrier targeting samples (first 25 changes):")
    for cid, log in aim_log.items():
        changes = [log[0]] + [b for a_, b in zip(log, log[1:]) if a_[1] != b[1]] if log else []
        print(f"  {cid}: {changes[:25]}")
    out = {"kind": a.kind, "tick": a.tick, "weapons": weapons, "projectiles": rows,
           "blasts": blasts}
    with open("results/hazards.jsonl", "a") as f:
        f.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    main()
