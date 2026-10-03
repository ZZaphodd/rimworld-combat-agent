"""Theme scenarios: one frozen squad vs one raid flavour, by rejection sampling
(PROCEDURES §7), plus frag_check, the reflex check scenario."""
import json
from collections import Counter

from ... import ROOT
from ...rimmolt import RimMoltError
from ...terrain import Terrain
from .. import session
from ..debug import Debug
from ..weapons import weapon_class, weapon_name
from .scenario import assaults, make_squad, pawn_row

BASE_SAVE = "theme_base"
BASE_META = ROOT / "themes/base.json"
SAMPLES = ROOT / "themes/samples.jsonl"
ARENA = "arena_forest"
SQUAD = {"faction": "OutlanderRough", "points": 1500, "place": [125, 125], "size": (12, 15),
         "max_top_share": 0.5}
POINTS = 1500                                   # = squad points
MECH_POINTS = [1500, 2000, 2500, 3000, 4000]    # low points fail to generate more often
FRAG_CHECK = {"kind": "Grenadier_Destructive", "count": 5, "distance": 27, "min_frag_share": 0.6}


def share(raid, *classes):
    return sum(r["class"] in classes for r in raid) / len(raid)


def top_share(raid):
    return max(Counter(r["class"] for r in raid).values()) / len(raid)


THEMES = {
    "pirate_grenadier": (["Pirate"], lambda r: share(r, "explosive") >= 0.6,
                         "Pirate raid, >=60% explosive weapons (grenades, launchers)"),
    "pirate_sniper": (["Pirate"], lambda r: share(r, "long") >= 0.6,
                      "Pirate raid, >=60% long-range weapons (snipers)"),
    "pirate_melee": (["Pirate"], lambda r: share(r, "melee") >= 0.6, "Pirate raid, >=60% melee"),
    "pirate_mixed": (["Pirate"], lambda r: top_share(r) < 0.5, "Pirate raid, no weapon class >= 50%"),
    "tribal_melee": (["TribeRough", "TribeSavage"], lambda r: share(r, "melee") >= 0.7,
                     "Tribal raid, >=70% melee"),
    "tribal_archers": (["TribeRough", "TribeSavage"], lambda r: share(r, "bow", "long") >= 0.6,
                       "Tribal raid, >=60% bows/greatbows"),
    "mechs": (["Mechanoid"], None,
              "Mechanoid raid (game-chosen strategy/arrival), must pass the assault check"),
}


def classify(rm, pawns):
    rows = []
    for t in pawns:
        w = weapon_name(rm.call("get_pawn", id=t["id"]).get("weapon"))
        kind = t.get("kind") or t.get("def", "")
        rows.append({"id": t["id"], "kind": kind, "weapon": w, "class": weapon_class(w, kind),
                     "x": t["x"], "z": t["z"]})
    return rows


def build_base(rm, max_attempts=40, log=print):
    d = Debug(rm, log)
    lo, hi = SQUAD["size"]
    for attempt in range(1, max_attempts + 1):
        session.load(rm, ARENA)
        observers = [c["id"] for c in rm.call("list_colonists")["colonists"]]
        raid = d.spawn_raid(SQUAD["faction"], SQUAD["points"])
        rows = classify(rm, raid)
        log(f"   base attempt {attempt}: {len(rows)} pawns, top share {top_share(rows):.2f}")
        if lo <= len(rows) <= hi and top_share(rows) < SQUAD["max_top_share"]:
            break
    else:
        raise RimMoltError(f"no balanced squad in {max_attempts} attempts")
    ids = make_squad(d, raid, SQUAD["place"])
    d.remove_observers(observers, ids)
    d.close()
    session.save(rm, BASE_SAVE)
    cls = {r["id"]: r["class"] for r in rows}
    squad = [{**pawn_row(rm, i), "class": cls[i]} for i in ids]
    meta = {"save": BASE_SAVE, "arena": ARENA, "spec": SQUAD, "attempts": attempt, "squad": squad,
            "slots": {p["id"]: [p["x"], p["z"]] for p in squad}}
    BASE_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return meta


def load_base():
    return json.loads(BASE_META.read_text())


def spawn_mechs(rm, d, base, ladder, tries=3, log=print):
    for pts in ladder:
        for _ in range(tries):
            session.load(rm, base["save"])
            try:
                return pts, d.spawn_raid_by_faction("Mechanoid", pts, max_steps=60)
            except RimMoltError as e:
                log(f"   mechs {pts}pt: {e}")
    raise RimMoltError("no mech raid spawned at any point level")


def _manifest(spec, save, base, rows):
    return {"id": spec["id"], "save": save, "spec": spec,
            "squad": [{k: p[k] for k in ("id", "name", "weapon", "x", "z", "health")}
                      for p in base["squad"]],
            "enemy": [{"id": r["id"], "def": r["kind"], "weapon": r["weapon"], "class": r["class"],
                       "x": r["x"], "z": r["z"]} for r in rows]}


def _squad_spec(base):
    return {"base_save": base["save"], "faction": SQUAD["faction"], "points": SQUAD["points"],
            "place": SQUAD["place"]}


def save_theme(rm, d, name, base, rows, faction, points, out_dir, scenarios_path, log=print):
    ids = [p["id"] for p in base["squad"]]
    d.place({k: tuple(v) for k, v in base["slots"].items()})   # it wandered while settling
    d.close()
    save = f"scenario_theme_{name}"
    session.save(rm, save)
    if not assaults(rm, save, ids, log=log):
        return False
    spec = {"id": f"theme_{name}", "tier": "theme", "note": THEMES[name][2], "arena": ARENA,
            "squad": _squad_spec(base),
            "enemy": {"faction": faction, "points": points,
                      **({"method": "faction"} if faction == "Mechanoid" else
                         {"strategy": "ImmediateAttack", "arrival": "EdgeWalkIn"})}}
    (out_dir / f"{save}.json").write_text(json.dumps(_manifest(spec, save, base, rows), indent=2,
                                                     ensure_ascii=False))
    upsert_scenario(scenarios_path, spec)
    log(f"   saved {save}")
    return True


def build_group(rm, names, base, max_attempts, out_dir, scenarios_path, log=print):
    """Every spawned raid is offered to all still-missing themes of its faction
    group (the predicates are disjoint), so no draw is wasted."""
    d = Debug(rm, log)
    factions = THEMES[names[0]][0]
    pending, results, tried, mech_pts = list(names), {}, Counter(), None
    attempt = 0
    for attempt in range(1, max_attempts + 1):
        if not pending:
            break
        faction = factions[(attempt - 1) % len(factions)]
        if faction == "Mechanoid":
            mech_pts, raid = spawn_mechs(rm, d, base, [mech_pts] if mech_pts else MECH_POINTS,
                                         log=log)
            points = mech_pts
        else:
            session.load(rm, base["save"])
            points = POINTS
            try:
                raid = d.spawn_raid(faction, POINTS)
            except RimMoltError as e:
                log(f"   attempt {attempt}: {e}")
                tried["spawn_failed"] += 1
                continue
        rows = classify(rm, raid)
        tried[faction] += 1
        with SAMPLES.open("a") as f:
            f.write(json.dumps({"faction": faction, "points": points,
                                "classes": [r["class"] for r in rows]}) + "\n")
        hit = next((n for n in pending if THEMES[n][1] is None or THEMES[n][1](rows)), None)
        log(f"   attempt {attempt} ({faction} {points}pt): {len(rows)} raiders -> {hit or 'reject'}")
        if hit and save_theme(rm, d, hit, base, rows, faction, points, out_dir, scenarios_path, log):
            pending.remove(hit)
            results[hit] = {"accepted_at_attempt": attempt, "faction": faction, "points": points,
                            "size": len(rows)}
        elif hit:
            tried["loitering"] += 1
    for n in pending:
        results[n] = {"accepted": False}
    for n in results:
        results[n].update(group_attempts=attempt, tried=dict(tried))
    return results


def build_frag_check(rm, base, out_dir, scenarios_path, max_attempts=15, log=print):
    """5 Grenadier_Destructive ~27 cells east of the frozen squad (lordless: no
    fleeing/satisfied message), rerolled until >= 60% carry frags."""
    d, fc = Debug(rm, log), FRAG_CHECK
    ids = [p["id"] for p in base["squad"]]
    cx = round(sum(p["x"] for p in base["squad"]) / len(ids))
    cz = round(sum(p["z"] for p in base["squad"]) / len(ids))
    for attempt in range(1, max_attempts + 1):
        session.load(rm, base["save"])
        terrain = Terrain(rm)
        cells = []
        for i in range(fc["count"]):
            wx, wz = cx + fc["distance"], cz - 6 + 3 * i
            cells.append(next((wx + dx, wz) for dx in (0, 1, -1, 2, -2, 3)
                              if terrain.passable(wx + dx, wz)))
        rows = classify(rm, d.spawn_pawn(fc["kind"], cells))
        frags = sum("frag" in (r["weapon"] or "").lower() for r in rows)
        log(f"   frag_check attempt {attempt}: {[r['weapon'] for r in rows]}")
        if not rows or frags / len(rows) < fc["min_frag_share"]:
            continue
        d.place({k: tuple(v) for k, v in base["slots"].items()})
        d.close()
        save = "scenario_theme_frag_check"
        session.save(rm, save)
        if not assaults(rm, save, ids, log=log):
            continue
        spec = {"id": "theme_frag_check", "tier": "check",
                "note": f"Reflex check: {len(rows)} {fc['kind']} ({frags} with frag grenades) "
                        f"spawned ~{fc['distance']} cells east of the theme squad (debug Spawn "
                        "Pawn, no raid lord: no fleeing/satisfied message).",
                "arena": ARENA, "squad": _squad_spec(base),
                "enemy": {"method": "spawn_pawn", **fc}}
        m = _manifest(spec, save, base, rows)
        (out_dir / f"{save}.json").write_text(json.dumps(m, indent=2, ensure_ascii=False))
        upsert_scenario(scenarios_path, spec)
        return m
    raise RimMoltError(f"no frag-heavy grenadier group in {max_attempts} attempts")


def upsert_scenario(path, spec):
    scs = [s for s in json.loads(path.read_text()) if s["id"] != spec["id"]] + [spec]
    path.write_text(json.dumps(scs, indent=2, ensure_ascii=False) + "\n")
