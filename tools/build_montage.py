"""Threat montage on the loaded map (rca/game/builders/montage.py).

  python3 tools/build_montage.py [--samples 3] [--save montage_threats]

Expects a fresh, paused map (dev mode on, observer far from the map centre).
Writes results/montage/montage.json and prints the legend table.
"""
import argparse
import json

import _path  # noqa: F401
from rca import ROOT
from rca.game.builders import montage
from rca.rimmolt import RimMolt

ap = argparse.ArgumentParser()
ap.add_argument("--samples", type=int, default=3, help="extra raids per cell for size stats")
ap.add_argument("--save", default="montage_threats")
a = ap.parse_args()
out = ROOT / "results/montage"
out.mkdir(parents=True, exist_ok=True)
result = montage.build(RimMolt(), a.samples, a.save, log=lambda m: print(m, flush=True))
(out / "montage.json").write_text(json.dumps(result, indent=1))
print(montage.legend(result))
