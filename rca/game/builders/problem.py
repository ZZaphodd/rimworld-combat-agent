"""Random problems for the router night run (TODO roadmap 3, failure mining).

One problem = an arena x our squad (a raid of a random non-mechanoid faction at
`points`, recruited: a player-side mech squad would need a mechanitor) x the
enemy (a raid of a random faction at `points`, mechanoids included). Saved as
scenario_rand_NNN with its manifest in scenarios_rand/, so a person can replay
it later (tools/run_human.py --manifest).

No assault check: a raid that loiters (low-point mechs mostly do) is a problem
for the router too (go and get them, or wait).
"""
import json

from ... import ROOT
from ...rimmolt import RimMoltError
from .. import session
from ..debug import Debug, formation
from .scenario import make_squad, pawn_row
from .theme import classify

OUT = ROOT / "scenarios_rand"
# Copies of the evaluation arenas with every human faction made hostile (the Empire and the
# civil outlanders start neutral), so the evaluation arenas stay as they are.
ARENAS = ("arena_forest_night", "arena_open_night")
PLACE = (125, 125)
# Raid factions that are not a human or mech fighting force (or are Anomaly/ancient set pieces).
NOT_RAIDERS = {"PlayerColony", "Entities", "HoraxCult", "Ancients", "AncientsHostile", "Insect",
               "TradersGuild", "Salvagers"}
MECH = "Mechanoid"


def raid_factions(d):
    """FactionDefs the debug raid menus can use now: humans from 'specifics',
    mechanoids from 'faction' (specifics filters them out early in a game)."""
    def defs(entry):
        r = d.run(entry)
        out = [o.rsplit("(", 1)[1].rstrip(")") for o in r["optionList"]["options"]
               if "(" in o and not o.endswith("[NO]")]
        d.close()
        return out
    humans = [f for f in defs("Execute raid with specifics...") if f not in NOT_RAIDERS | {MECH}]
    mechs = [f for f in defs("Execute raid with faction...") if f == MECH]
    return humans, mechs


def next_index():
    OUT.mkdir(exist_ok=True)
    nums = [int(p.stem.rsplit("_", 1)[1]) for p in OUT.glob("scenario_rand_*.json")]
    return max(nums, default=0) + 1


def spawn(d, faction, points, tries=3):
    for _ in range(tries):
        try:
            if faction == MECH:
                return d.spawn_raid_by_faction(faction, points, max_steps=60)
            return d.spawn_raid(faction, points, instant=True)
        except RimMoltError as e:
            d.log(f"   {e}")
            d.close()
    return []


def make(rm, idx, rng, factions, points=500, log=print, arenas=ARENAS):
    """Build problem `idx`; factions = (humans, mechs) from raid_factions().
    Returns the manifest, or None if no squad or no enemy could be spawned."""
    humans, mechs = factions
    d = Debug(rm, log)
    arena = rng.choice(arenas)
    session.load(rm, arena)
    observers = [c["id"] for c in rm.call("list_colonists")["colonists"]]
    squad_faction, raid = None, []
    for f in rng.sample(humans, len(humans)):
        raid = spawn(d, f, points)
        if raid:
            squad_faction = f
            break
    if not raid:
        return None
    for t in [t for t in raid if t.get("def") != "Human"]:   # pack animals can't be recruited
        d.destroy_at(t["x"], t["z"])
    raid = [t for t in raid if t.get("def") == "Human"]
    if not raid:
        return None
    squad_cls = {r["id"]: r for r in classify(rm, raid)}
    ids = make_squad(d, raid, PLACE)
    d.remove_observers(observers, ids)
    enemy_faction = rng.choice(humans + mechs)
    enemy = spawn(d, enemy_faction, points)
    d.close()
    if not enemy:
        return None
    if enemy_faction == MECH:                   # settle waits let the squad wander
        d.place(formation(ids, PLACE))
        d.close()
    rows = classify(rm, enemy)
    pid = f"rand_{idx:03d}"
    save = f"scenario_{pid}"
    session.save(rm, save)
    squad = [{**pawn_row(rm, i), "class": squad_cls[i]["class"], "kind": squad_cls[i]["kind"]}
             for i in ids]
    manifest = {
        "id": pid, "save": save,
        "spec": {"id": pid, "tier": "rand", "arena": arena,
                 "squad": {"faction": squad_faction, "points": points, "place": list(PLACE)},
                 "enemy": {"faction": enemy_faction, "points": points,
                           **({"method": "faction"} if enemy_faction == MECH else
                              {"strategy": "ImmediateAttack", "arrival": "EdgeWalkIn"})}},
        "squad": squad,
        "enemy": [{"id": r["id"], "def": r["kind"], "weapon": r["weapon"], "class": r["class"],
                   "x": r["x"], "z": r["z"]} for r in rows]}
    OUT.mkdir(exist_ok=True)
    (OUT / f"{save}.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    log(f"   saved {save}: {arena}, squad {squad_faction} x{len(ids)} vs "
        f"{enemy_faction} x{len(rows)}")
    return manifest

