"""Raid composition census (PROCEDURES §8): spawn, classify, delete, repeat."""
import json
import statistics
import time
from collections import Counter, defaultdict

from .. import ROOT
from . import session
from .debug import Debug
from .weapons import CLASSES, weapon_class, weapon_name

OUT = ROOT / "census/raids.jsonl"
DEFAULT_CONFIGS = ["Pirate:1000", "Pirate:3000", "OutlanderRough:1000", "OutlanderRough:3000",
                   "TribeRough:1000", "TribeRough:3000", "TribeSavage:1000", "Mechanoid:6000"]
RELOAD_EVERY = 100
CLEAR_EVERY = 5                 # 'Destroy non-colonists' costs ~1 s; batch it
FRESH_ARENA = {"Mechanoid"}     # late mech pods leaked into the next sample
MECH_SETTLE_STEPS = 60


def sample(rm, d, faction, points):
    raid = d.spawn_raid_by_faction(faction, points,
                                   max_steps=MECH_SETTLE_STEPS if faction in FRESH_ARENA else 20)
    rows = []
    for t in raid:
        w = weapon_name(rm.call("get_pawn", id=t["id"]).get("weapon"))
        kind = t.get("kind") or t.get("def", "")
        rows.append({"kind": kind, "weapon": w, "class": weapon_class(w, kind)})
    return rows


def run(rm, configs, per_config, attempts_factor=2, out=OUT, log=print):
    d = Debug(rm, log)
    done, stale = 0, True
    for cfg in configs:
        faction, points = cfg.split(":")
        ok = fails = 0
        for attempt in range(attempts_factor * per_config):
            if ok >= per_config:
                break
            if stale or faction in FRESH_ARENA or done % RELOAD_EVERY == 0:
                session.load(rm, "arena_open")
            elif done % CLEAR_EVERY == 0:
                d.run("Destroy non-colonists")
                d.close()
            stale = False
            t0 = time.time()
            try:
                rows = sample(rm, d, faction, int(points))
            except Exception as e:                # one bad spawn shouldn't stop 1000
                log(f"   ! {cfg} attempt {attempt}: {e}")
                fails, stale = fails + 1, True
                continue
            done, ok = done + 1, ok + 1
            with out.open("a") as f:
                f.write(json.dumps({"faction": faction, "points": int(points), "route": "faction",
                                    "raiders": rows, "t": round(time.time() - t0, 2)}) + "\n")
        log(f"== {cfg}: {ok} raids, {fails} failed spawns")


def report(path=OUT, log=print):
    raids = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    by = defaultdict(list)
    for r in raids:
        by[(r["faction"], r["points"])].append(r)
    classes = [c for c, _ in CLASSES] + ["other"]
    for (fac, pts), rs in sorted(by.items()):
        sizes = [len(r["raiders"]) for r in rs]
        total = Counter(x["class"] for r in rs for x in r["raiders"])
        n = sum(total.values())
        dom = [max(Counter(x["class"] for x in r["raiders"]).values()) / len(r["raiders"])
               for r in rs if r["raiders"]]
        melee = [sum(x["class"] == "melee" for x in r["raiders"]) / max(1, len(r["raiders"]))
                 for r in rs]
        log(f"\n== {fac} {pts}pt: {len(rs)} raids, size median {statistics.median(sizes)} "
            f"({min(sizes)}-{max(sizes)})")
        log("   class share: " + "  ".join(f"{c} {100 * total[c] / n:.0f}%" for c in classes
                                          if total[c]))
        log(f"   dominant class >=60% in {100 * sum(x >= 0.6 for x in dom) / len(dom):.0f}%, "
            f">=80% in {100 * sum(x >= 0.8 for x in dom) / len(dom):.0f}%; melee-heavy "
            f"{100 * sum(m >= 0.5 for m in melee) / len(melee):.0f}%")
