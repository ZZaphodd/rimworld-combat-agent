"""Theme scenarios and frag_check (PROCEDURES §7).

  python3 tools/build_themes.py --base               # theme_base + themes/base.json
  python3 tools/build_themes.py --themes all
  python3 tools/build_themes.py --frag-check
"""
import argparse
import json
from pathlib import Path

import _path  # noqa: F401
from rca import ROOT
from rca.game.builders import theme
from rca.rimmolt import RimMolt

ap = argparse.ArgumentParser()
ap.add_argument("--base", action="store_true")
ap.add_argument("--themes", default="")
ap.add_argument("--frag-check", action="store_true")
ap.add_argument("--max-attempts", type=int, default=150)
ap.add_argument("--out", type=Path, default=ROOT / "scenarios_out")
ap.add_argument("--specs", type=Path, default=ROOT / "scenarios.json")
a = ap.parse_args()
rm = RimMolt()
base = theme.build_base(rm) if a.base else theme.load_base()
if a.frag_check:
    theme.build_frag_check(rm, base, a.out, a.specs)
names = list(theme.THEMES) if a.themes == "all" else [t for t in a.themes.split(",") if t]
groups = {}
for n in names:
    groups.setdefault(tuple(theme.THEMES[n][0]), []).append(n)
for group in groups.values():
    res = theme.build_group(rm, group, base, a.max_attempts, a.out, a.specs)
    with (ROOT / "themes/build_log.jsonl").open("a") as f:
        for n, r in res.items():
            f.write(json.dumps({"theme": n, **r}) + "\n")
