"""Scenario saves from scenarios.json (PROCEDURES §6). Theme/check specs are
built by build_themes.py instead.

  python3 tools/build_scenarios.py --only std_pirate_mirror_forest
"""
import argparse
import json
from pathlib import Path

import _path  # noqa: F401
from rca import ROOT
from rca.game.builders import scenario
from rca.rimmolt import RimMolt

ap = argparse.ArgumentParser()
ap.add_argument("--specs", type=Path, default=ROOT / "scenarios.json")
ap.add_argument("--only")
ap.add_argument("--out", type=Path, default=ROOT / "scenarios_out")
a = ap.parse_args()
rm = RimMolt()
for spec in json.loads(a.specs.read_text()):
    if spec.get("tier") in ("theme", "check") or (a.only and spec["id"] != a.only):
        continue
    scenario.build_checked(rm, spec, a.out)
