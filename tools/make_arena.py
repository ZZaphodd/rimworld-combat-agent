"""Arena saves (PROCEDURES §1-§2).

  python3 tools/make_arena.py --new-game # quit to title, walk to the planet page
                                         # (then add the factions BY HAND)
  python3 tools/make_arena.py            # from the 'Create world' page
  python3 tools/make_arena.py --resume   # world already started: clean up and save
  python3 tools/make_arena.py --fort     # arena_fort from arena_open
  python3 tools/make_arena.py --strip-anomaly arena_forest,scenario_t500_mechs,...
                                         # load, strip Anomaly content, save again
"""
import argparse

import _path  # noqa: F401
from rca.game.builders import arena
from rca.rimmolt import RimMolt

ap = argparse.ArgumentParser()
ap.add_argument("--new-game", action="store_true")
ap.add_argument("--resume", action="store_true")
ap.add_argument("--fort", action="store_true")
ap.add_argument("--map-size", type=int, default=arena.MAP_SIZE)
ap.add_argument("--strip-anomaly", help="comma-separated saves to clean (arena.strip_anomaly)")
a = ap.parse_args()
rm = RimMolt()
if a.strip_anomaly:
    from rca.game import session
    from rca.game.debug import Debug
    for save in a.strip_anomaly.split(","):
        session.load(rm, save)
        n = len(arena.strip_anomaly(rm, Debug(rm), log=lambda s: print(f"{save}: {s}")))
        session.save(rm, save)
        print(f"{save}: saved ({n} removed)")
elif a.new_game:
    arena.new_game(rm)
    print("On the planet page. Add by hand:", ", ".join(arena.REQUIRED_FACTIONS))
elif a.resume:
    arena.prepare_and_save(rm)
elif a.fort:
    arena.make_fort(rm)
else:
    arena.create(rm, a.map_size)
