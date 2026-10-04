"""arena_forest / arena_open from the planet page, and arena_fort (PROCEDURES §1-§2).

new_game() goes from any state to the planet page (The Rich Explorer, Phoebe,
Strive to Survive). The faction list must then be fixed BY HAND: the Add...
float menu vanishes unless the real mouse is over it. create() does the rest.
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


STORYTELLER, DIFFICULTY = "Phoebe", "Rough"     # Rough = Strive to Survive (WORKFLOW)
# Anomaly content that would disturb a battle: an "ancient danger" ruin's sleepers come out when
# a casket is shot, its fleshbeast guards count as live hostiles (every episode timed out), and
# the Void Monolith drives Anomaly events. Found in the 2026-10-04 arena (GAME_FACTS §7).
ANOMALY_DEFS = ("AncientCryptosleepCasket", "VoidMonolith")
ENTITY_FACTION = "Dark entities"
MAP_SIZE = 250                                  # the game's design size; arenas so far


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


def new_game(rm):
    """Quit whatever is loaded (unsaved progress discarded) and walk the setup
    pages up to the planet page."""
    if rm.call("game_setup_status").get("programState") == "Playing":
        rm.call("return_to_title", confirm=True)
        wait_stage(rm, lambda s: s.get("stage") == "main_menu")
    rm.call("main_menu", action="new_colony")
    wait_stage(rm, lambda s: s.get("stage") == "scenario")
    for _ in range(2):              # the first call may only return the list (review gate)
        if rm.call("select_scenario", name="The Rich Explorer").get("stage") == "storyteller":
            break
    for _ in range(2):              # same review gate on the storyteller page
        if rm.call("select_storyteller", storyteller=STORYTELLER, difficulty=DIFFICULTY,
                   reloadAnytime=True).get("stage") == "planet":
            break
    wait_stage(rm, lambda s: s.get("stage") == "planet")


def set_map_size(rm, size=MAP_SIZE):
    """Planet page -> Advanced settings 'Edit...' -> Dialog_AdvancedGameConfig radio."""
    page = next(w["index"] for w in rm.call("list_windows")["windows"]
                if w["type"] == "Page_CreateWorldParams")
    rm.call("window_action", index=page, clickButton="Edit...", row="Advanced settings")
    time.sleep(0.5)
    dlg = next(w["index"] for w in rm.call("list_windows")["windows"]
               if w["type"] == "Dialog_AdvancedGameConfig")
    rm.call("window_action", index=dlg, clickButton=f"{size}x{size}")
    time.sleep(0.3)
    chosen = [r["label"] for r in rm.call("get_window_ui", index=dlg).get("radios", [])
              if r.get("chosen") and "x" in r["label"]]
    rm.call("window_action", index=dlg, clickButton="Close")
    if not any(c.startswith(f"{size}x{size}") for c in chosen):
        raise RimMoltError(f"map size not set: {chosen}")


def pick_tile(rm):
    """Flat inland temperate forest, no river, nothing within 5 tiles."""
    tiles = rm.call("find_world_tiles", biome="TemperateForest", hilliness="Flat", coastal=False,
                    river=False, tempMin=10, tempMax=20, limit=60)["tiles"]
    for t in tiles:
        s = rm.call("select_starting_site", tile=t["tile"])["surroundings"]
        if not s.get("nearbyObjects") and all(b["biome"] == "temperate forest" for b in s["biomes"]):
            return t["tile"]
    raise RimMoltError("no clean arena tile found")


def create(rm, map_size=MAP_SIZE, log=print):
    if rm.call("game_setup_status").get("stage") != "planet":
        raise SystemExit("Open the 'Create world' page first (make_arena.py --new-game).")
    check_factions(rm)
    set_map_size(rm, map_size)
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
    difficulty = rm.call("get_status").get("difficulty")
    if difficulty != "strive to survive":
        raise RimMoltError(f"difficulty is {difficulty!r}, not the evaluation standard")
    prepare_and_save(rm, log)


def strip_anomaly(rm, d, log=print):
    """Destroy entity-faction pawns, cryptosleep caskets and the monolith on the
    loaded map; never a cell another pawn stands on. Returns what was removed."""
    pawns = rm.call("list_things", category="pawn", verbose=True, confirm=True)["things"]
    cells = {}
    for t in pawns:
        cells.setdefault((t["x"], t["z"]), []).append(t)
    targets = [t for t in pawns if t.get("faction") == ENTITY_FACTION]
    for name in ANOMALY_DEFS:
        targets += things_of(rm, name)
    removed = []
    for t in targets:
        at = (t["x"], t["z"])
        others = [p for p in cells.get(at, []) if p["id"] != t["id"]]
        if others:
            raise RimMoltError(f"{t['id']} shares {at} with {[p['id'] for p in others]}")
        d.destroy_at(*at)
        removed.append(t.get("def") or t.get("kind"))
    d.close()
    left = [t["id"] for t in rm.call("list_things", category="pawn", verbose=True,
                                     confirm=True)["things"] if t.get("faction") == ENTITY_FACTION]
    left += [t["id"] for name in ANOMALY_DEFS for t in things_of(rm, name)]
    if left:
        raise RimMoltError(f"anomaly content left: {left}")
    log(f"stripped anomaly content: {removed}")
    return removed


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
    strip_anomaly(rm, d, log)
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
