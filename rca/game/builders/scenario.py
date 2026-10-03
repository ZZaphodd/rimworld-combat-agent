"""Scenario saves from scenarios.json specs + the assault check (PROCEDURES §5-§6)."""
import json
import math

from ...rimmolt import RimMoltError, hostiles
from .. import session
from ..debug import Debug, formation


def pawn_row(rm, pid):
    p = rm.call("get_pawn", id=pid)
    return {"id": pid, "name": p["name"], "weapon": p.get("weapon"), "x": p["x"], "z": p["z"],
            "health": p["health"]}


def make_squad(d, raid, place, spacing=2, width=5):
    """Recruit every raider into the colony, then place them in formation."""
    for p in raid:
        d.recruit(p)
    ids = [p["id"] for p in raid]
    cols = {c["id"] for c in d.rm.call("list_colonists")["colonists"]}
    missing = [i for i in ids if i not in cols]
    if missing:
        raise RimMoltError(f"{len(missing)} squad pawns not recruited: {missing}")
    d.place(formation(ids, place, spacing, width))
    return ids


def spawn_enemy(d, en):
    if en.get("method") == "faction":
        return d.spawn_raid_by_faction(en["faction"], en["points"])
    return d.spawn_raid(en["faction"], en["points"], en.get("strategy", "ImmediateAttack"),
                        en.get("arrival", "EdgeWalkIn"))


def build(rm, spec, out_dir, log=print):
    """Arena -> squad (recruited raid) -> observer removed -> enemy -> save + manifest."""
    d = Debug(rm, log)
    sid = spec["id"]
    session.load(rm, spec.get("arena", "arena_open"))
    observers = [c["id"] for c in rm.call("list_colonists")["colonists"]]
    sq = spec["squad"]
    ids = make_squad(d, d.spawn_raid(sq["faction"], sq["points"]), sq.get("place", [125, 125]),
                     sq.get("spacing", 2), sq.get("width", 5))
    d.remove_observers(observers, ids)
    enemy = spawn_enemy(d, spec["enemy"])
    d.close()
    save = f"scenario_{sid}"
    session.save(rm, save)
    manifest = {"id": sid, "save": save, "spec": spec,
                "squad": [pawn_row(rm, i) for i in ids],
                "enemy": [{"id": p["id"], "def": p.get("kind") or p["def"], "x": p["x"],
                           "z": p["z"]} for p in enemy]}
    (out_dir / f"{save}.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    log(f"   saved {save}: squad {len(ids)}, enemy {len(enemy)}")
    return manifest


def assaults(rm, save, squad_ids, ticks=3000, min_close=0.3, log=print):
    """Reload, wait `ticks` with no orders: the raid must come (someone aiming at
    a colonist, a squad pawn down, or the median gap shrinking by 30%). Mech
    raids pick their own strategy and sometimes just loiter."""
    def median_gap():
        us = [p for p in (rm.call("get_pawn", id=i) for i in squad_ids) if "x" in p]
        if not us:
            return 0.0
        cx = sum(p["x"] for p in us) / len(us)
        cz = sum(p["z"] for p in us) / len(us)
        ds = sorted(math.dist((h["x"], h["z"]), (cx, cz)) for h in hostiles(rm, live_only=False))
        return ds[len(ds) // 2] if ds else 0.0

    session.load(rm, save)
    d0 = median_gap()
    rm.wait(ticks, max_seconds=90)
    d1 = median_gap()
    aiming = any((t.get("targeting") or "").startswith(("targeting colonist", "attacking colonist"))
                 for t in hostiles(rm))
    hurt = sum(1 for i in squad_ids if (p := rm.call("get_pawn", id=i)).get("dead")
               or "x" not in p or p.get("downed"))
    ok = aiming or hurt > 0 or d1 <= d0 * (1 - min_close)
    log(f"   assault check: gap {d0:.0f} -> {d1:.0f}, aiming={aiming}, down={hurt} -> "
        f"{'ok' if ok else 'LOITERING'}")
    return ok


def build_checked(rm, spec, out_dir, tries=3, log=print):
    for attempt in range(tries):
        m = build(rm, spec, out_dir, log)
        if assaults(rm, m["save"], [p["id"] for p in m["squad"]], log=log):
            return m
        log(f"   rebuilding {spec['id']} (attempt {attempt + 2})")
    raise RimMoltError(f"{spec['id']}: enemy never assaulted in {tries} builds")
