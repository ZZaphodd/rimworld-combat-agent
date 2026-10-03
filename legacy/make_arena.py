"""Create the arena saves (arena_forest, arena_open) from the planet page on.

Run with RimWorld sitting on the "Create world" page. The faction list there
must be edited BY HAND first (the Add... float menu vanishes unless the real
mouse is over it): make sure Pirate gang, Rough outlander union, Fierce tribe
and Savage tribe are present — Biotech's default list swaps them for xenotype
variants.

  python3 make_arena.py
"""
import time

from rimmolt_client import RimMolt, RimMoltError

REQUIRED_FACTIONS = ["Pirate gang", "Rough outlander union", "Fierce tribe",
                     "Savage tribe", "Mechanoid hive"]
OBSERVER_CELL = (240, 240)
OPEN_RECT = (50, 50, 200, 200)


def wait_stage(rm, done, timeout=300):
    for _ in range(timeout):
        try:
            s = rm.call("game_setup_status")
            if done(s):
                return s
        except Exception:
            pass  # busy while generating
        time.sleep(1)
    raise TimeoutError("setup stage did not advance")


def window(rm, type_):
    return next(w for w in rm.call("list_windows")["windows"] if w["type"] == type_)


def check_factions(rm):
    w = window(rm, "Page_CreateWorldParams")
    labels = rm.call("get_window_ui", index=w["index"])["labels"]
    have = labels[labels.index("Factions") + 1:labels.index("Add...")]
    missing = [f for f in REQUIRED_FACTIONS if f not in have]
    if missing:
        raise SystemExit(f"Add these factions on the planet page first: {missing}")
    print("factions:", have)


def pick_tile(rm):
    """Flat inland temperate forest, no river, nothing within 5 tiles."""
    tiles = rm.call("find_world_tiles", biome="TemperateForest", hilliness="Flat",
                    coastal=False, river=False, tempMin=10, tempMax=20, limit=60)["tiles"]
    for t in tiles:
        r = rm.call("select_starting_site", tile=t["tile"])
        s = r["surroundings"]
        if not s.get("nearbyObjects") and all(
                b["biome"] == "temperate forest" for b in s["biomes"]):
            return t["tile"]
    raise RimMoltError("no clean arena tile found")


def remove_loose_weapons(rm):
    """Ruins can hold weapons (even persona ones) that a squad would grab."""
    groups = rm.call("list_things", category="item", summary=True, confirm=True)["groups"]
    for g in groups:
        if not g["def"].startswith(("Gun_", "MeleeWeapon_", "Weapon_")):
            continue
        for t in rm.call("list_things", category="item", defName=g["def"])["things"]:
            debug(rm, action="run", path="T: Destroy")
            debug(rm, action="click", x=t["x"], z=t["z"])
            print(f"removed {g['def']} at {(t['x'], t['z'])}")


def debug(rm, **args):
    r = rm.call("debug_menu", **args)
    if not r.get("ok"):
        raise RimMoltError(f"debug_menu {args}: {r.get('error')}")
    return r


def main():
    rm = RimMolt()
    if rm.call("game_setup_status").get("stage") != "planet":
        raise SystemExit("Open the 'Create world' page first (new colony -> "
                         "The Rich Explorer -> Phoebe/Peaceful).")
    check_factions(rm)

    rm.call("create_world", coverage=0.3, rainfall="Normal", temperature="Normal",
            population="Normal", pollution=0)
    wait_stage(rm, lambda s: s.get("stage") == "starting_site")
    tile = pick_tile(rm)
    print("tile:", tile)
    rm.call("select_starting_site", tile=tile, confirm=True)
    rm.call("choose_ideoligion", mode="classic")
    rm.call("edit_starting_pawn", action="rename", index=0,
            first="Arena", nick="Observer", last="Keeper")
    rm.call("start_game")
    wait_stage(rm, lambda s: s.get("programState") == "Playing")
    time.sleep(3)
    prepare_and_save(rm)


def prepare_and_save(rm):
    # Intro letter, then a clean, paused, fog-free, animal-free map.
    for w in rm.call("list_windows")["windows"]:
        if w["type"] == "Dialog_NodeTree":
            rm.call("window_action", index=w["index"], option="OK")
    # The scenario lands the colonist by drop pod; let it land and open.
    for _ in range(30):
        pods = [t for d in ("DropPodIncoming", "ActiveDropPod")
                for t in rm.call("list_things", category="all", defName=d)["things"]]
        if not pods:
            break
        rm.call("wait_for_event", _timeout=60, maxGameTicks=120, maxSeconds=20,
                pause="always", force=True)
    rm.call("set_speed", action="pause")
    rm.call("dev_mode", devMode=True)
    for entry in ("Destroy factionless animals", "Destroy player animals", "Clear All Fog"):
        debug(rm, action="run", path=entry)

    obs = rm.call("list_colonists")["colonists"][0]["id"]
    land = rm.call("get_pawn", id=obs)
    landing = (land["x"] - 8, land["z"] - 8, land["x"] + 8, land["z"] + 8)
    for _ in range(5):  # the first click occasionally misses; retry from fresh position
        p = rm.call("get_pawn", id=obs)
        if (p["x"], p["z"]) == OBSERVER_CELL:
            break
        debug(rm, action="run", path="T: Teleport")
        if rm.call("debug_menu", action="click", x=p["x"], z=p["z"]).get("armedTool"):
            rm.call("debug_menu", action="click", x=OBSERVER_CELL[0], z=OBSERVER_CELL[1])
    else:
        raise RimMoltError(f"observer stuck at {(p['x'], p['z'])}")

    # The explorer's starting kit (charge rifle, meds...) must not arm squads.
    debug(rm, action="run", path="Clear area (rect)")
    debug(rm, action="click", cells="{},{};{},{}".format(*landing))
    debug(rm, action="run", path="Destroy factionless animals")
    remove_loose_weapons(rm)
    rm.call("save_game", name="arena_forest", overwrite=True)
    print("saved arena_forest")

    x0, z0, x1, z1 = OPEN_RECT
    debug(rm, action="run", path="Clear area (rect)")
    debug(rm, action="click", cells=f"{x0},{z0};{x1},{z1}")
    rm.call("save_game", name="arena_open", overwrite=True)
    print("saved arena_open")

    raidable = rm.call("get_world")["factions"]
    print("world factions:", [f"{f['def']}:{f['relation']}" for f in raidable])


# ---------------------------------------------------------------- fort arena
FORT = (110, 110, 140, 140)      # stone wall outline
FORT_GAP = (124, 126)            # z-range of the single opening in the east wall
FORT_SANDBAGS_X = 128            # sandbag line facing the gap from inside


def make_fort(rm=None):
    """arena_fort = arena_open + a walled compound with one east choke point.
    Built in god mode (instant, free); god mode is switched off before saving."""
    from scenario_builder import Builder
    rm = rm or RimMolt()
    Builder(rm).load("arena_open")
    rm.call("dev_mode", devMode=True, godMode=True)
    x0, z0, x1, z1 = FORT
    g0, g1 = FORT_GAP
    walls = [(x0, z1, x1, z1), (x0, z0, x1, z0), (x0, z0, x0, z1),   # N, S, W
             (x1, z0, x1, g0 - 1), (x1, g1 + 1, x1, z1)]              # E minus gap
    for a, b, c, d in walls:
        r = rm.call("build", **{"def": "Wall", "stuff": "BlocksGranite",
                        "minX": a, "minZ": b, "maxX": c, "maxZ": d, "fill": "filled"})
        if r.get("rejected"):
            print("wall rejected:", r.get("reasons"), r.get("failedCells", [])[:5])
    r = rm.call("build", **{"def": "Sandbags", "minX": FORT_SANDBAGS_X, "minZ": g0 - 6,
                            "maxX": FORT_SANDBAGS_X, "maxZ": g1 + 6, "fill": "filled"})
    if r.get("rejected"):
        print("sandbags rejected:", r.get("reasons"), r.get("failedCells", [])[:5])
    rm.call("dev_mode", godMode=False)
    print(rm.call("get_area", minX=x0 - 2, minZ=z0 - 2, maxX=x1 + 2, maxZ=z1 + 2,
                  render="ascii").get("grid", ""))
    rm.call("set_speed", action="pause")
    rm.call("save_game", name="arena_fort", overwrite=True)
    print("saved arena_fort")


if __name__ == "__main__":
    import sys
    if "--resume" in sys.argv:  # world already started; just clean up and save
        prepare_and_save(RimMolt())
    elif "--fort" in sys.argv:  # derive arena_fort from arena_open
        make_fort()
    else:
        main()
