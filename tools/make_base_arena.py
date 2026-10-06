"""Base-defense arena from a colony save (PROCEDURES §1c): pawns and items out, buildings kept,
Phoebe at Strive to Survive. The source save is never written.

  python3 tools/make_base_arena.py --source Ithfunda --name arena_col_ithfunda --observer 8,8 \
      --hostile OutlanderCivil
  python3 tools/make_base_arena.py --strip-from arena_col_ithfunda --name arena_col_ithfunda2

--strip-from: a copy of a base arena without shelves, hydroponics basins and workbenches
(buildings that take bills), indoors and out (the user, 2026-10-06).
"""
import argparse
import json

import _path  # noqa: F401
from rca.game.builders import base
from rca.rimmolt import RimMolt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", help="the colony save to read (never written)")
    ap.add_argument("--strip-from", help="an arena_col_* save to copy without shelves, hydroponics, workbenches")
    ap.add_argument("--name", required=True, help="arena_col_<name>")
    ap.add_argument("--observer", help="x,z of a clear cell away from the base (with --source)")
    ap.add_argument("--hostile", default="", help="faction defs to set hostile (the squads' factions)")
    a = ap.parse_args()
    if a.strip_from:
        return print(json.dumps(base.strip(RimMolt(), a.strip_from, a.name)))
    if not (a.source and a.observer):
        ap.error("--source and --observer, or --strip-from")
    obs = tuple(int(v) for v in a.observer.split(","))
    hostile = [f for f in a.hostile.split(",") if f]
    print(json.dumps(base.make(RimMolt(), a.source, a.name, obs, hostile)))


if __name__ == "__main__":
    main()
