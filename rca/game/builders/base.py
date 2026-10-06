"""Base-defense arenas from a player's colony save (PROCEDURES §1c; the user, 2026-10-06).

Keep the buildings (power, turrets, traps, walls, doors) and clear what a colony holds: weapons,
consumables, food and materials. The storyteller is Phoebe at Strive to Survive, as in the other
arenas. The source save is only loaded, never written: the arena is saved under its own
`arena_col_<name>` name, and the items and the storyteller are edited in that new file.

    make(rm, "Ithfunda", "arena_col_ithfunda", observer=(10, 10))
"""
import hashlib
import os
import re
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from ...rimmolt import RimMoltError
from .. import session
from ..debug import Debug
from .arena import DIFFICULTY, STORYTELLER, strip_anomaly

SAVES = Path(os.environ.get("RIMWORLD_SAVES", Path.home() / "Library/Application Support/RimWorld/Saves"))
KEEP_ITEMS = re.compile(r"^Chunk")       # stone and slag chunks: map clutter, not supplies
# Second version of the base arenas (the user, 2026-10-06): raiders spent the battles wrecking the
# colony's furniture, which dragged them out and turned them into mood management. Every shelf,
# hydroponics basin and workbench goes, indoors and out; a workbench is any building that takes
# production bills (list_recipes), so research benches stay.
STRIP_DEFS = re.compile(r"^(Shelf|ShelfSmall|Bookcase|BookcaseSmall|HydroponicsBasin)$")


def item_ids(rm):
    """Ids of every item on the current map except chunks."""
    r = rm.call("list_things", category="item", verbose=True, confirm=True, limit=100000)
    if r.get("truncated"):
        raise RimMoltError("item list truncated")
    return {t["id"] for t in r.get("things", []) if not KEEP_ITEMS.match(t.get("def") or "")}


def edit_save(path, drop_ids, storyteller=STORYTELLER, difficulty=DIFFICULTY):
    """Remove the things whose <id> is in drop_ids (at any depth) and set the storyteller and its
    difficulty (a custom difficulty block goes). Returns the number of things removed."""
    tree = ET.parse(path)
    root = tree.getroot()
    removed = 0
    for parent in list(root.iter()):
        for child in list(parent):
            idn = child.find("id")
            if idn is not None and (idn.text or "").strip() in drop_ids:
                parent.remove(child)
                removed += 1
    st = root.find("game/storyteller")
    if st is None:
        raise RimMoltError(f"{path}: no storyteller block")
    st.find("def").text = storyteller
    st.find("difficulty").text = difficulty
    for custom in st.findall("difficultyValues"):
        st.remove(custom)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return removed


OURS = ("arena_col_", "scenario_base")     # saves the builders made: never the user's own


def clear_conditions(names, conds=("SolarFlare",), backup=None, saves=None, log=print):
    """Remove active game conditions stored in base saves, offline (the user, 2026-10-07: the
    Monler colony was saved during a solar flare, so every Monler battle started under it, with
    the base's power off). Only arena_col_* and scenario_base* saves; each file that changes is
    copied to `backup` first (default: RimWorld/rca_backup/<time>/, outside the Saves folder).
    Returns {name: [condition defs removed]}."""
    folder = Path(saves or SAVES)
    backup = Path(backup or folder.parent / "rca_backup" / time.strftime("%Y%m%d-%H%M%S"))
    out = {}
    for name in names:
        if not name.startswith(OURS):
            raise RimMoltError(f"{name}: only builder saves ({', '.join(OURS)}*) are edited")
        path = folder / f"{name}.rws"
        tree = ET.parse(path)
        removed = []
        for gcm in tree.getroot().iter("gameConditionManager"):
            active = gcm.find("activeConditions")
            for li in list(active if active is not None else []):
                if li.findtext("def") in conds:
                    active.remove(li)
                    removed.append(li.findtext("def"))
        if removed:
            backup.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup / path.name)
            tree.write(path, encoding="utf-8", xml_declaration=True)
            left = [li.findtext("def") for g in ET.parse(path).getroot().iter("gameConditionManager")
                    for li in (g.find("activeConditions") if g.find("activeConditions") is not None else [])]
            if any(d in conds for d in left):
                raise RimMoltError(f"{name}: {left} still active after the edit")
        out[name] = removed
        log(f"{name}: removed {removed or 'nothing'}")
    return out


def _clear_cell(rm, x, z):
    """No building or item on (x, z) (a pawn is destroyed there, and T: Destroy takes the cell)."""
    things = rm.call("list_things", category="all", nearX=x, nearZ=z, radius=0.5, verbose=True,
                     confirm=True).get("things", [])
    return not [t for t in things if t.get("category") not in ("Pawn", "Plant", "Filth")]


def clear_pawns(rm, d, observer, log=print):
    """Every pawn off the map but one colonist, the observer, put on `observer` (PROCEDURES §1)."""
    if not _clear_cell(rm, *observer):
        raise RimMoltError(f"observer cell {observer} is not clear")
    for entry in ("Destroy non-colonists", "Destroy player animals", "Destroy factionless animals"):
        d.run(entry)
    here = rm.call("get_map").get("index", 0)
    cols = [c for c in rm.call("list_colonists")["colonists"] if c.get("mapIndex", here) == here]
    if not cols:
        raise RimMoltError("no colonist left to be the observer")
    keep, rest = cols[0], cols[1:]
    for c in rest:                                   # one at a time on the clear cell, then gone
        if not d.teleport(c["id"], *observer):
            raise RimMoltError(f"{c['id']} did not reach {observer}")
        d.destroy_at(*observer)
    if not d.teleport(keep["id"], *observer):
        raise RimMoltError(f"observer stuck at {d.pos(keep['id'])}")
    d.close()
    pawns = rm.call("list_things", category="pawn", verbose=True, confirm=True)["things"]
    left = [p["id"] for p in pawns if not p.get("dead") and p["id"] != keep["id"]]
    if left:
        raise RimMoltError(f"pawns left: {left[:10]}")
    log(f"observer {keep['id']} at {observer}; {len(rest)} colonists removed")
    return keep["id"]


def strip_foreign(rm, d, log=print):
    """Destroy every building owned by a faction other than the colony: insect hives (they breed
    insects that join the next raid spawned: rand base build, 2026-10-06), ancient security
    turrets, mech clusters. Returns the defs removed."""
    me = next((p.get("faction") for p in rm.call("list_things", category="pawn", faction="player",
                                                verbose=True, confirm=True)["things"]), None)
    b = rm.call("list_things", category="building", verbose=True, confirm=True, limit=100000)["things"]
    foreign = [t for t in b if t.get("faction") not in (None, me)]
    for t in foreign:
        d.destroy_at(t["x"], t["z"])
    d.close()
    left = [t["id"] for t in rm.call("list_things", category="building", verbose=True, confirm=True,
                                     limit=100000)["things"] if t.get("faction") not in (None, me)]
    if left:
        raise RimMoltError(f"foreign buildings left: {left[:10]}")
    log(f"foreign buildings removed: {sorted({t['def'] for t in foreign})} ({len(foreign)})")
    return [t["def"] for t in foreign]


def make_hostile(rm, d, defs, log=print):
    """Set the colony's relation with each faction def in `defs` to Hostile ('Set Faction
    Relations'). The squads are spawned as a raid of their faction and then recruited, so that
    faction must be hostile: in a colony's world it can be an ally (Ithfunda: OutlanderCivil came
    as "Friendlies", 2026-10-06)."""
    for fdef in defs:
        names = [f["name"] for f in rm.call("get_world")["factions"] if f.get("def") == fdef]
        if not names:
            raise RimMoltError(f"no {fdef} faction in this world")
        for name in names:
            for _ in range(3):              # from an ally the first pick stops at Neutral (goodwill 84)
                d.run("Set Faction Relations")
                menu = next(w for w in rm.call("list_windows")["windows"] if w["type"] == "FloatMenu")
                rm.call("window_action", index=menu["index"], option=f"{name} - Hostile")
                if {f["name"]: f.get("relation") for f in rm.call("get_world")["factions"]}.get(name) == "Hostile":
                    break
        rel = {f["name"]: f.get("relation") for f in rm.call("get_world")["factions"]}
        if any(rel.get(n) != "Hostile" for n in names):
            raise RimMoltError(f"{fdef} not hostile: {[(n, rel.get(n)) for n in names]}")
        log(f"{fdef} ({', '.join(names)}) set hostile")
    d.close()


def colony_buildings(rm):
    """Buildings owned by the colony (the observer's faction) on the current map."""
    me = next((p.get("faction") for p in rm.call("list_things", category="pawn", faction="player",
                                                verbose=True, confirm=True)["things"]), None)
    return [t for t in rm.call("list_things", category="building", verbose=True, confirm=True,
                               limit=100000)["things"] if t.get("faction") == me]


def takes_bills(rm, thing_id):
    """True if the building takes production bills (RimMolt list_recipes)."""
    try:
        return bool(rm.call("list_recipes", id=thing_id).get("recipes"))
    except RimMoltError:
        return False


def strip_targets(rm, buildings):
    """The colony buildings that STRIP_DEFS names or that take bills (one bills check per def)."""
    first = {}
    for t in buildings:
        first.setdefault(t["def"], t)
    defs = {d for d, t in first.items() if STRIP_DEFS.match(d) or takes_bills(rm, t["id"])}
    return [t for t in buildings if t["def"] in defs]


def strip(rm, source, name, log=print):
    """A base arena without shelves, hydroponics basins and workbenches, made from an existing
    base arena (`source`, an arena_col_* save, only loaded) and saved as `name`."""
    if not source.startswith("arena_col_") or name.lower() != source.lower() + "2":
        raise RimMoltError(f"strip reads arena_col_<name> and writes arena_col_<name>2, not {source!r} -> {name!r}")
    src = SAVES / f"{source}.rws"
    digest = hashlib.md5(src.read_bytes()).hexdigest()
    session.load(rm, source)
    gone = strip_targets(rm, colony_buildings(rm))
    defs = sorted({t["def"] for t in gone})
    session.save(rm, name)
    path = SAVES / f"{name}.rws"
    n = edit_save(path, {t["id"] for t in gone})
    log(f"{name}: {n} of {len(gone)} buildings removed in the file: {defs}")
    session.load(rm, name)                       # check the edited file as the game reads it
    left = [t["def"] for t in colony_buildings(rm) if t["def"] in defs]
    st = rm.call("get_status")
    if left or "phoebe" not in (st.get("storyteller") or "").lower() \
            or (st.get("difficulty") or "").lower() != "strive to survive" or item_ids(rm):
        raise RimMoltError(f"{name} check failed: left {left[:10]}, {st.get('storyteller')} / {st.get('difficulty')}")
    rm.call("dev_mode", devMode=False)
    session.save(rm, name)
    if hashlib.md5(src.read_bytes()).hexdigest() != digest:
        raise RimMoltError(f"the source arena {source} changed")
    log(f"{name}: checked and saved; {source} unchanged")
    return {"name": name, "source": source, "removed": n, "defs": defs}


def make(rm, source, name, observer, hostile=(), log=print):
    if not name.startswith("arena_col_"):
        raise RimMoltError(f"base arenas are named arena_col_*, not {name!r}")
    if source.lower() == name.lower():          # the Saves folder ignores case (APFS)
        raise RimMoltError("the arena must not be the source save")
    src = SAVES / f"{source}.rws"
    digest = hashlib.md5(src.read_bytes()).hexdigest()
    session.load(rm, source)                     # read only
    rm.call("dev_mode", devMode=True)
    d = Debug(rm, log)
    d.run("Clear All Fog")
    clear_pawns(rm, d, observer, log)
    strip_anomaly(rm, d, log)
    strip_foreign(rm, d, log)
    make_hostile(rm, d, hostile, log)
    drop = item_ids(rm)
    session.save(rm, name)
    path = SAVES / f"{name}.rws"
    n = edit_save(path, drop)
    log(f"{name}: {n} of {len(drop)} items removed in the file; storyteller {STORYTELLER} {DIFFICULTY}")
    session.load(rm, name)                       # check the edited file as the game reads it
    left = item_ids(rm)
    st = rm.call("get_status")
    cols = rm.call("list_colonists")["colonists"]
    if left or len(cols) != 1 or "phoebe" not in (st.get("storyteller") or "").lower() \
            or (st.get("difficulty") or "").lower() != "strive to survive":
        raise RimMoltError(f"{name} check failed: items {len(left)}, colonists {len(cols)}, "
                           f"{st.get('storyteller')} / {st.get('difficulty')}")
    rm.call("dev_mode", devMode=False)
    session.save(rm, name)
    if hashlib.md5(src.read_bytes()).hexdigest() != digest:
        raise RimMoltError(f"the source save {source} changed")
    log(f"{name}: checked and saved ({st.get('storyteller')}, {st.get('difficulty')}); {source} unchanged")
    return {"name": name, "source": source, "items_removed": n, "observer": observer, "hostile": list(hostile)}
