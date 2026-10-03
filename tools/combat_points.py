"""Re-extract the XML tables: data/combat_power.json (PawnKindDef combatPower)
and data/weapon_ranges.json (weapon verb ranges, mech kind -> weapons).

  python3 tools/combat_points.py [--game /path/to/RimWorldMac.app]
"""
import argparse
import json
from pathlib import Path

import _path  # noqa: F401
from rca.game import defs

ap = argparse.ArgumentParser()
ap.add_argument("--game", type=Path, default=defs.GAME)
a = ap.parse_args()
t = defs.extract(a.game)
defs.TABLE.write_text(json.dumps(t, indent=1) + "\n")
print(f"{len(t)} kinds -> {defs.TABLE}")
w = defs.extract_weapons(a.game)
defs.RANGES.write_text(json.dumps(w, indent=1) + "\n")
print(f"{len(w['weapons'])} weapons, {len(w['mech_kinds'])} mech kinds -> {defs.RANGES}")
