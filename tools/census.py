"""Raid composition census (PROCEDURES §8).

  python3 tools/census.py --per-config 125
  python3 tools/census.py --report
"""
import argparse

import _path  # noqa: F401
from rca.game import census
from rca.rimmolt import RimMolt

ap = argparse.ArgumentParser()
ap.add_argument("--configs", default=",".join(census.DEFAULT_CONFIGS))
ap.add_argument("--per-config", type=int, default=125)
ap.add_argument("--report", action="store_true")
a = ap.parse_args()
if not a.report:
    census.run(RimMolt(), a.configs.split(","), a.per_config)
census.report()
