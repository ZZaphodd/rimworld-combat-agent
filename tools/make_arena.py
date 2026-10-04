"""Arena saves (PROCEDURES §1-§2).

  python3 tools/make_arena.py --new-game # quit to title, walk to the planet page
                                         # (then add the factions BY HAND)
  python3 tools/make_arena.py            # from the 'Create world' page
  python3 tools/make_arena.py --resume   # world already started: clean up and save
  python3 tools/make_arena.py --fort     # arena_fort from arena_open
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
a = ap.parse_args()
rm = RimMolt()
if a.new_game:
    arena.new_game(rm)
    print("On the planet page. Add by hand:", ", ".join(arena.REQUIRED_FACTIONS))
elif a.resume:
    arena.prepare_and_save(rm)
elif a.fort:
    arena.make_fort(rm)
else:
    arena.create(rm, a.map_size)
