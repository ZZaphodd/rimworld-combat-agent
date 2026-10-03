"""arena_forest / arena_open from the planet page, and arena_fort (PROCEDURES §1-§2).

Run with RimWorld on the 'Create world' page. Faction list must be fixed BY
HAND first: the Add... float menu vanishes unless the real mouse is over it.
"""
import time

from ...rimmolt import RimMoltError, things_of
from .. import session
from ..debug import Debug

REQUIRED_FACTIONS = ["Pirate gang", "Rough outlander union", "Fierce tribe", "Savage tribe",
                     "Mechanoid hive"]
OBSERVER_CELL = (240, 240)
OPEN_RECT = (50, 50, 200, 200)
FORT = (110, 110, 140, 140)          # granite wall outline
FORT_GAP = (124, 126)                # z-range of the single opening in the east wall
FORT_SANDBAGS_X = 128


def wait_stage(rm, done, timeout=300):
    for _ in range(timeout):
        try:
            s = rm.call("game_setup_status")
            if done(s):
                return s
        except Exception:
            pass                     # busy while generating
        time.sleep(1)
    raise TimeoutError("setup stage did not advance")


def check_factions(rm):
    w = next(w for w in rm.call("list_windows")["windows"] if w["type"] == "Page_CreateWorldParams")
    labels = rm.call("get_window_ui", index=w["index"])["labels"]
    have = labels[labels.index("Factions") + 1:labels.index("Add...")]
    missing = [f for f in REQUIRED_FACTIONS if f not in have]
    if missing:
        raise SystemExit(f"Add these factions on the planet page first: {missing}")


def pick_tile(rm):
    """Flat inland temperate forest, no river, nothing within 5 tiles."""
    tiles = rm.call("find_world_tiles", biome="TemperateForest", hilliness="Flat", coastal=False,
                    river=False, tempMin=10, tempMax=20, limit=60)["tiles"]
    for t in tiles:
        s = rm.call("select_starting_site", tile=t["tile"])["surroundings"]
        if not s.get("nearbyObjects") and all(b["biome"] == "temperate forest" for b in s["biomes"]):
            return t["tile"]
    raise RimMoltError("no clean arena tile found")


def create(rm, log=print):
    if rm.call("game_setup_status").get("stage") != "planet":
        raise SystemExit("Open the 'Create world' page first (new colony -> The Rich Explorer "
                         "-> Phoebe/Peaceful).")
    check_factions(rm)
    rm.call("create_world", coverage=0.3, rainfall="Normal", temperature="Normal",
            population="Normal", pollution=0)
    wait_stage(rm, lambda s: s.get("stage") == "starting_site")
    tile = pick_tile(rm)
    log(f"tile: {tile}")
    rm.call("select_starting_site", tile=tile, confirm=True)
    rm.call("choose_ideoligion", mode="classic")
    rm.call("edit_starting_pawn", action="rename", index=0, first="Arena", nick="Observer",
            last="Keeper")
    rm.call("start_game")
    wait_stage(rm, lambda s: s.get("programState") == "Playing")
    time.sleep(3)
    prepare_and_save(rm, log)


def prepare_and_save(rm, log=print):
    for w in rm.call("list_windows")["windows"]:
        if w["type"] == "Dialog_NodeTree":
            rm.call("window_action", index=w["index"], option="OK")
    for _ in range(30):                          # the explorer lands by drop pod
        if not any(things_of(rm, d) for d in ("DropPodIncoming", "ActiveDropPod")):
            break
        rm.wait(120, max_seconds=20)
    rm.call("set_speed", action="pause")
    rm.call("dev_mode", devMode=True)
    d = Debug(rm, log)
    for entry in ("Destroy factionless animals", "Destroy player animals", "Clear All Fog"):
        d.run(entry)
    obs = rm.call("list_colonists")["colonists"][0]["id"]
    lx, lz = d.pos(obs)
    if not d.teleport(obs, *OBSERVER_CELL):
        raise RimMoltError(f"observer stuck at {d.pos(obs)}")
    d.clear_area(lx - 8, lz - 8, lx + 8, lz + 8)    # the explorer's kit must not arm squads
    d.run("Destroy factionless animals")
    d.remove_loose_weapons()
    session.save(rm, "arena_forest")
    log("saved arena_forest")
    d.clear_area(*OPEN_RECT)
    session.save(rm, "arena_open")
    log("saved arena_open")


def make_fort(rm, log=print):
    """arena_fort = arena_open + granite compound with one east gap, in god mode."""
    session.load(rm, "arena_open")
    rm.call("dev_mode", devMode=True, godMode=True)
    x0, z0, x1, z1 = FORT
    g0, g1 = FORT_GAP
    walls = [(x0, z1, x1, z1), (x0, z0, x1, z0), (x0, z0, x0, z1),
             (x1, z0, x1, g0 - 1), (x1, g1 + 1, x1, z1)]
    for a, b, c, e in walls:
        r = rm.call("build", **{"def": "Wall", "stuff": "BlocksGranite", "minX": a, "minZ": b,
                                "maxX": c, "maxZ": e, "fill": "filled"})
        if r.get("rejected"):
            log(f"wall rejected: {r.get('reasons')}")
    r = rm.call("build", **{"def": "Sandbags", "minX": FORT_SANDBAGS_X, "minZ": g0 - 6,
                            "maxX": FORT_SANDBAGS_X, "maxZ": g1 + 6, "fill": "filled"})
    if r.get("rejected"):
        log(f"sandbags rejected: {r.get('reasons')}")
    rm.call("dev_mode", godMode=False)
    log("\n".join(rm.call("get_area", minX=x0 - 2, minZ=z0 - 2, maxX=x1 + 2, maxZ=z1 + 2,
                          render="ascii").get("grid", [])))
    session.save(rm, "arena_fort")
    log("saved arena_fort")
