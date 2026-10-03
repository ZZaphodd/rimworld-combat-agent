"""Theme scenarios: one frozen squad vs raids of a single tactical flavour.

  python3 theme_builder.py --base                # squad -> save 'theme_base' + themes/base.json
  python3 theme_builder.py --themes all          # one scenario_theme_<name> per theme
  python3 theme_builder.py --themes pirate_sniper,mechs
  python3 theme_builder.py --frag-check          # scenario_theme_frag_check (tier 'check')

The squad is built ONCE (balanced OutlanderRough raid, recruited, placed,
observer removed) and frozen in 'theme_base', so every theme fights the same
pawns. Themes come from rejection sampling: reload the base, spawn a raid,
classify its weapons with raid_census.weapon_class, keep it if a missing
theme's predicate holds (every raid is logged to themes/samples.jsonl, so
acceptance rates per predicate can be read off afterwards). The base is reloaded for every attempt so the squad is
identical; after acceptance it is re-placed on its slots (it wandered a few
cells while the raid settled).
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from raid_census import weapon_class, weapon_name
from rimmolt_client import RimMolt, RimMoltError
from scenario_builder import Builder

BASE_SAVE = "theme_base"
BASE_META = Path("themes/base.json")
ARENA = "arena_forest"
SQUAD = {"faction": "OutlanderRough", "points": 1500, "place": [125, 125],
         "size": (12, 15), "max_top_share": 0.5}
POINTS = 1500                    # = squad points: equal threat
MECH_POINTS = [1500, 2000, 2500, 3000, 4000]   # lowest that spawns reliably is used


def share(raid, *classes):
    return sum(r["class"] in classes for r in raid) / len(raid)


def top_share(raid):
    return max(Counter(r["class"] for r in raid).values()) / len(raid)


THEMES = {
    "pirate_grenadier": (["Pirate"], lambda r: share(r, "explosive") >= 0.6,
                         "Pirate raid, >=60% explosive weapons (grenades, launchers)"),
    "pirate_sniper":    (["Pirate"], lambda r: share(r, "long") >= 0.6,
                         "Pirate raid, >=60% long-range weapons (snipers)"),
    "pirate_melee":     (["Pirate"], lambda r: share(r, "melee") >= 0.6,
                         "Pirate raid, >=60% melee"),
    "pirate_mixed":     (["Pirate"], lambda r: top_share(r) < 0.5,
                         "Pirate raid, no weapon class >= 50%"),
    "tribal_melee":     (["TribeRough", "TribeSavage"], lambda r: share(r, "melee") >= 0.7,
                         "Tribal raid, >=70% melee"),
    "tribal_archers":   (["TribeRough", "TribeSavage"], lambda r: share(r, "bow", "long") >= 0.6,
                         "Tribal raid, >=60% bows/greatbows"),
    "mechs":            (["Mechanoid"], None,
                         "Mechanoid raid (game-chosen strategy/arrival), must pass the assault check"),
}


def classify(rm, pawns):
    rows = []
    for t in pawns:
        w = weapon_name(rm.call("get_pawn", id=t["id"]).get("weapon"))
        kind = t.get("kind") or t.get("def", "")
        rows.append({"id": t["id"], "kind": kind, "weapon": w,
                     "class": weapon_class(w, kind), "x": t["x"], "z": t["z"]})
    return rows


def build_base(b, max_attempts=40):
    rm = b.rm
    lo, hi = SQUAD["size"]
    stats = Counter()
    for attempt in range(1, max_attempts + 1):
        b.load(ARENA)
        observers = [c["id"] for c in rm.call("list_colonists")["colonists"]]
        raid = b.spawn_raid(SQUAD["faction"], SQUAD["points"])
        rows = classify(rm, raid)
        ok_size = lo <= len(rows) <= hi
        ok_mix = top_share(rows) < SQUAD["max_top_share"]
        stats["size_ok"] += ok_size
        stats["mix_ok"] += ok_mix
        print(f"   base attempt {attempt}: {len(rows)} pawns, top share {top_share(rows):.2f} "
              f"{dict(Counter(r['class'] for r in rows))}", flush=True)
        if ok_size and ok_mix:
            break
    else:
        raise RimMoltError(f"no balanced squad in {max_attempts} attempts {dict(stats)}")
    ids = b.make_squad(raid, SQUAD["place"])
    b.remove_observers(observers, ids)
    rm.call("debug_menu", action="close")
    b.save(BASE_SAVE)
    squad = [{**b._pawn_row(i), "class": next(r["class"] for r in rows if r["id"] == i)}
             for i in ids]
    meta = {"save": BASE_SAVE, "arena": ARENA, "spec": SQUAD, "attempts": attempt,
            "attempt_stats": dict(stats), "squad": squad,
            "slots": {p["id"]: [p["x"], p["z"]] for p in squad}}
    BASE_META.parent.mkdir(exist_ok=True)
    BASE_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"   saved {BASE_SAVE}: {len(ids)} pawns "
          f"{dict(Counter(p['class'] for p in squad))} after {attempt} attempts")
    return meta


def spawn_mechs(b, base, points_ladder, tries=3):
    """Mech raids below some point level fail to generate; walk up the ladder."""
    for pts in points_ladder:
        for _ in range(tries):
            b.load(base["save"])
            try:
                return pts, b.spawn_raid_by_faction("Mechanoid", pts, max_steps=60)
            except RimMoltError as e:
                print(f"   mechs {pts}pt: {e}", flush=True)
    raise RimMoltError("no mech raid spawned at any point level")


def build_group(b, names, base, max_attempts, out_dir, scenarios_path):
    """Rejection-sample raids for themes that share factions. One raid can only
    match one theme (the predicates are disjoint), so every spawned raid is
    offered to all still-missing themes of its faction instead of being wasted."""
    rm = b.rm
    factions = THEMES[names[0]][0]
    pending, results = list(names), {}
    tried, mech_pts = Counter(), None
    samples = Path("themes/samples.jsonl")
    for attempt in range(1, max_attempts + 1):
        if not pending:
            break
        faction = factions[(attempt - 1) % len(factions)]
        if faction == "Mechanoid":
            mech_pts, raid = spawn_mechs(b, base, [mech_pts] if mech_pts else MECH_POINTS)
            points = mech_pts
        else:
            b.load(base["save"])
            points = POINTS
            try:
                raid = b.spawn_raid(faction, POINTS)
            except RimMoltError as e:
                print(f"   attempt {attempt}: {e}", flush=True)
                tried["spawn_failed"] += 1
                continue
        rows = classify(rm, raid)
        tried[faction] += 1
        with samples.open("a") as f:
            f.write(json.dumps({"faction": faction, "points": points,
                                "classes": [r["class"] for r in rows]}) + "\n")
        hit = next((n for n in pending if THEMES[n][1] is None or THEMES[n][1](rows)), None)
        print(f"   attempt {attempt} ({faction} {points}pt): {len(rows)} raiders "
              f"{dict(Counter(r['class'] for r in rows))} -> {hit or 'reject'}", flush=True)
        if hit is None:
            continue
        if save_theme(b, hit, base, rows, faction, points, out_dir, scenarios_path):
            pending.remove(hit)
            results[hit] = {"accepted_at_attempt": attempt, "faction": faction,
                            "points": points, "size": len(rows)}
        else:
            tried["loitering"] += 1
    for n in pending:
        print(f"   ! {n}: no matching raid in {max_attempts} attempts", flush=True)
        results[n] = {"accepted": False}
    for n in results:
        results[n].update(group_attempts=attempt, tried=dict(tried))
    return results


def save_theme(b, name, base, rows, faction, points, out_dir, scenarios_path):
    rm = b.rm
    factions, _, desc = THEMES[name]
    ids = [p["id"] for p in base["squad"]]
    b.place(ids, {k: tuple(v) for k, v in base["slots"].items()})
    rm.call("debug_menu", action="close")
    save = f"scenario_theme_{name}"
    b.save(save)
    if not b.assaults(save, ids):
        print(f"   {name}: raid did not assault, rejecting", flush=True)
        return False
    spec = {"id": f"theme_{name}", "tier": "theme", "note": desc, "arena": ARENA,
            "squad": {"base_save": base["save"], "faction": SQUAD["faction"],
                      "points": SQUAD["points"], "place": SQUAD["place"]},
            "enemy": {"faction": faction, "points": points,
                      **({"method": "faction"} if faction == "Mechanoid" else
                         {"strategy": "ImmediateAttack", "arrival": "EdgeWalkIn"})}}
    manifest = {"id": spec["id"], "save": save, "spec": spec,
                "squad": [{k: p[k] for k in ("id", "name", "weapon", "x", "z", "health")}
                          for p in base["squad"]],
                "enemy": [{"id": r["id"], "def": r["kind"], "weapon": r["weapon"],
                           "class": r["class"], "x": r["x"], "z": r["z"]} for r in rows]}
    (out_dir / f"{save}.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    upsert_scenario(scenarios_path, spec)
    print(f"   saved {save}", flush=True)
    return True


FRAG_CHECK = {"kind": "Grenadier_Destructive", "count": 5, "distance": 27, "min_frag_share": 0.6}


def build_frag_check(b, base, out_dir, scenarios_path, max_attempts=15):
    """Reflex validation: theme_pirate_grenadier is mostly doomsday/molotov/triple
    rocket with one frag thrower, so it barely exercises the frag reflex. This
    one is FRAG_CHECK['count'] grenadiers spawned (debug Spawn Pawn, no raid lord:
    the game won't post 'fleeing'/'satisfied', grading falls back to fates) east
    of the frozen squad; rerolled until most carry frag grenades."""
    from reflexes import TiledGrid
    rm, fc = b.rm, FRAG_CHECK
    ids = [p["id"] for p in base["squad"]]
    cx = round(sum(p["x"] for p in base["squad"]) / len(ids))
    cz = round(sum(p["z"] for p in base["squad"]) / len(ids))
    for attempt in range(1, max_attempts + 1):
        b.load(base["save"])
        grid = TiledGrid(rm)
        cells = []
        for i in range(fc["count"]):
            want = (cx + fc["distance"], cz - 6 + 3 * i)
            cells.append(next(c for c in ((want[0] + d, want[1]) for d in (0, 1, -1, 2, -2, 3))
                              if grid.passable(*c)))
        before = b.hostiles()
        b.dbg(action="run", path=f"Spawn Pawn... > {fc['kind']}")
        b.dbg(action="click", cells=";".join(f"{x},{z}" for x, z in cells))
        b.dbg(action="close")
        new = [t for k, t in b.hostiles().items() if k not in before]
        rows = classify(rm, new)
        frags = sum("frag" in (r["weapon"] or "").lower() for r in rows)
        print(f"   frag_check attempt {attempt}: {len(rows)} spawned, weapons "
              f"{[r['weapon'] for r in rows]}", flush=True)
        if not rows or frags / len(rows) < fc["min_frag_share"]:
            continue
        b.place(ids, {k: tuple(v) for k, v in base["slots"].items()})
        rm.call("debug_menu", action="close")
        save = "scenario_theme_frag_check"
        b.save(save)
        if not b.assaults(save, ids):
            print("   frag_check: grenadiers did not come, rerolling", flush=True)
            continue
        spec = {"id": "theme_frag_check", "tier": "check",
                "note": f"Reflex check: {len(rows)} {fc['kind']} ({frags} with frag grenades) "
                        f"spawned ~{fc['distance']} cells east of the theme squad (debug Spawn "
                        "Pawn, no raid lord: no fleeing/satisfied message).",
                "arena": ARENA,
                "squad": {"base_save": base["save"], "faction": SQUAD["faction"],
                          "points": SQUAD["points"], "place": SQUAD["place"]},
                "enemy": {"method": "spawn_pawn", "kind": fc["kind"], "count": fc["count"],
                          "distance": fc["distance"], "min_frag_share": fc["min_frag_share"]}}
        manifest = {"id": spec["id"], "save": save, "spec": spec,
                    "squad": [{k: p[k] for k in ("id", "name", "weapon", "x", "z", "health")}
                              for p in base["squad"]],
                    "enemy": [{"id": r["id"], "def": r["kind"], "weapon": r["weapon"],
                               "class": r["class"], "x": r["x"], "z": r["z"]} for r in rows]}
        (out_dir / f"{save}.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        upsert_scenario(scenarios_path, spec)
        print(f"   saved {save} after {attempt} attempts", flush=True)
        return manifest
    raise RimMoltError(f"no frag-heavy grenadier group in {max_attempts} attempts")


def upsert_scenario(path, spec):
    scs = json.loads(path.read_text())
    scs = [s for s in scs if s["id"] != spec["id"]] + [spec]
    path.write_text(json.dumps(scs, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", action="store_true")
    ap.add_argument("--themes", default="")
    ap.add_argument("--frag-check", action="store_true")
    ap.add_argument("--max-attempts", type=int, default=150)
    ap.add_argument("--out", type=Path, default=Path("scenarios_out"))
    ap.add_argument("--scenarios", type=Path, default=Path("scenarios.json"))
    a = ap.parse_args()
    b = Builder(RimMolt())
    base = build_base(b) if a.base else json.loads(BASE_META.read_text())
    if a.frag_check:
        build_frag_check(b, base, a.out, a.scenarios)
    names = list(THEMES) if a.themes == "all" else [t for t in a.themes.split(",") if t]
    groups = {}
    for n in names:
        groups.setdefault(tuple(THEMES[n][0]), []).append(n)
    log = Path("themes/build_log.jsonl")
    for fac, group in groups.items():
        print(f"== themes {group} ({'/'.join(fac)})", flush=True)
        res = build_group(b, group, base, a.max_attempts, a.out, a.scenarios)
        with log.open("a") as f:
            for n, r in res.items():
                f.write(json.dumps({"theme": n, **r}) + "\n")
