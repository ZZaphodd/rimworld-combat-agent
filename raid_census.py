"""Raid composition census: how skewed are generated raids?

No fighting: spawn a raid with the debug menu, record every raider's weapon and
pawn kind, delete the raid, repeat. One JSON line per raid in census/raids.jsonl.

  python3 raid_census.py --per-config 125                 # default config grid
  python3 raid_census.py --configs Pirate:1000,TribeRough:2000 --per-config 50
  python3 raid_census.py --report                         # summary from the file
"""
import argparse
import json
import re
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

from rimmolt_client import RimMolt
from scenario_builder import Builder

OUT = Path("census/raids.jsonl")
DEFAULT_CONFIGS = ["Pirate:1000", "Pirate:3000", "OutlanderRough:1000", "OutlanderRough:3000",
                   "TribeRough:1000", "TribeRough:3000", "TribeSavage:1000", "Mechanoid:6000"]
RELOAD_EVERY = 100            # reset the arena now and then so clutter can't pile up
CLEAR_EVERY = 5               # 'Destroy non-colonists' costs ~1s; batch it
# Mech pods can land long after the raid fires and 'Destroy non-colonists' does
# not touch pods in flight: they leaked into the next sample (one "raid" of 133).
# So every mech sample starts from a fresh arena and waits out all pods.
FRESH_ARENA = {"Mechanoid"}
MECH_SETTLE_STEPS = 60        # x60 ticks

# Coarse tactical classes; order matters (first match wins).
CLASSES = [
    ("explosive", ("launcher", "grenade", "molotov", "emp", "inferno", "toxbomb", "rocket",
                   "doomsday", "triple rocket", "thump cannon", "incinerator")),
    ("long",      ("sniper", "greatbow", "charge lance", "bolt-action", "marksman",
                   "needle gun")),                      # needle gun = pikeman's sniper
    ("support",   ("lmg", "minigun", "heavy charge blaster", "heavy smg")),
    ("bow",       ("short bow", "recurve bow", "bow")),
    ("thrown",    ("pila", "javelin")),
    ("short",     ("shotgun", "smg", "machine pistol", "autopistol", "revolver", "pistol",
                   "chain shotgun", "spiner")),
    ("medium",    ("assault rifle", "charge rifle", "rifle", "beam", "blaster", "gun", "cannon")),
    ("melee",     ("sword", "knife", "club", "mace", "spear", "axe", "hammer", "ikwa", "gladius",
                   "horn", "claw", "blade", "fist", "bite", "scythe", "lance", "pike")),
]


def weapon_name(label):
    return re.sub(r"\s*\(.*?\)\s*", "", (label or "")).replace("Biocoded ", "").strip() or "none"


def weapon_class(name, kind=""):
    low = name.lower()
    if name == "none":
        low = kind.lower()                      # mechs carry built-in weapons: use the kind
        mech = {"mech_lancer": "medium", "mech_pikeman": "long", "mech_scyther": "melee",
                "mech_centurion": "support", "mech_centipedeblaster": "support",
                "mech_centipedegunner": "support", "mech_centipedeburner": "explosive",
                "mech_warqueen": "support", "mech_warurchin": "short", "mech_termite": "explosive",
                "mech_tesseron": "medium", "mech_legionary": "medium", "mech_militor": "short",
                "mech_scorcher": "explosive", "mech_diabolus": "explosive"}
        return mech.get(low, "other")
    for cls, keys in CLASSES:
        if any(k in low for k in keys):
            return cls
    return "other"


def sample(b, rm, faction, points):
    """'Execute raid with faction' = 3 debug steps (each is paced ~0.5s on screen) and
    lets the game choose strategy/arrival, i.e. the natural mix, not one we picked."""
    raid = b.spawn_raid_by_faction(
        faction, points, max_steps=MECH_SETTLE_STEPS if faction in FRESH_ARENA else 20)
    rows = []
    for t in raid:
        w = weapon_name(rm.call("get_pawn", id=t["id"]).get("weapon"))
        kind = t.get("kind") or t.get("def", "")
        rows.append({"kind": kind, "weapon": w, "class": weapon_class(w, kind)})
    return rows


def clear(b):
    b.dbg(action="run", path="Destroy non-colonists")
    b.dbg(action="close")


def run(configs, per_config, max_attempts_factor=2):
    """per_config successful raids per config; failed spawns are retried (and
    counted) up to max_attempts_factor * per_config attempts."""
    rm = RimMolt()
    b = Builder(rm)
    OUT.parent.mkdir(exist_ok=True)
    done, stale = 0, True
    for cfg in configs:
        faction, points = cfg.split(":")
        ok = fails = 0
        for attempt in range(max_attempts_factor * per_config):
            if ok >= per_config:
                break
            if stale or faction in FRESH_ARENA or done % RELOAD_EVERY == 0:
                b.load("arena_open")
            elif done % CLEAR_EVERY == 0:
                clear(b)                          # raids barely move between samples
            stale = False
            t0 = time.time()
            try:
                rows = sample(b, rm, faction, int(points))
            except Exception as e:                       # one bad spawn shouldn't stop 1000
                print(f"   ! {cfg} attempt {attempt}: {e}")
                fails += 1
                stale = True
                continue
            done += 1
            ok += 1
            with OUT.open("a") as f:
                f.write(json.dumps({"faction": faction, "points": int(points), "route": "faction",
                                    "raiders": rows,
                                    "t": round(time.time() - t0, 2)}) + "\n")
            if ok % 25 == 1:
                print(f"{cfg} {ok}/{per_config}: {len(rows)} raiders "
                      f"{dict(Counter(r['class'] for r in rows))} ({time.time() - t0:.1f}s)",
                      flush=True)
        print(f"== {cfg}: {ok} raids, {fails} failed spawns "
              f"({100 * fails / max(1, ok + fails):.0f}% of attempts)", flush=True)


def report(path=OUT):
    raids = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    by = defaultdict(list)
    for r in raids:
        by[(r["faction"], r["points"])].append(r)
    classes = [c for c, _ in CLASSES] + ["other"]
    for (fac, pts), rs in sorted(by.items()):
        sizes = [len(r["raiders"]) for r in rs]
        total = Counter(x["class"] for r in rs for x in r["raiders"])
        n = sum(total.values())
        dom = []                                 # share of the single biggest class per raid
        for r in rs:
            c = Counter(x["class"] for x in r["raiders"])
            dom.append(max(c.values()) / len(r["raiders"]) if r["raiders"] else 0)
        top = Counter(tuple(sorted(Counter(x["class"] for x in r["raiders"]).items(),
                                   key=lambda kv: -kv[1])[:2]) for r in rs)
        print(f"\n== {fac} {pts}pt: {len(rs)} raids, size median {statistics.median(sizes)} "
              f"(min {min(sizes)}, max {max(sizes)})")
        print("   class share: " + "  ".join(f"{c} {100 * total[c] / n:.0f}%"
                                              for c in classes if total[c]))
        print(f"   dominant-class share per raid: median {statistics.median(dom):.2f}, "
              f">=60% in {100 * sum(d >= 0.6 for d in dom) / len(dom):.0f}% of raids, "
              f">=80% in {100 * sum(d >= 0.8 for d in dom) / len(dom):.0f}%")
        melee = [sum(x["class"] == "melee" for x in r["raiders"]) / max(1, len(r["raiders"]))
                 for r in rs]
        print(f"   melee-heavy (>=50% melee): {100 * sum(m >= 0.5 for m in melee) / len(melee):.0f}%"
              f"   any explosive: {100 * sum(any(x['class'] == 'explosive' for x in r['raiders']) for r in rs) / len(rs):.0f}%")
        print("   top-2 class combos: " + "; ".join(
            f"{'+'.join(f'{c}{k}' for c, k in combo)} x{cnt}" for combo, cnt in top.most_common(4)))
        other = Counter(x["weapon"] for r in rs for x in r["raiders"] if x["class"] == "other")
        if other:
            print(f"   unclassified weapons: {dict(other.most_common(6))}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default=",".join(DEFAULT_CONFIGS))
    ap.add_argument("--per-config", type=int, default=125)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.report:
        report()
    else:
        run(a.configs.split(","), a.per_config)
        report()
