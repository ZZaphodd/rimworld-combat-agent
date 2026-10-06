"""Base-defense ladder (PROCEDURES §1c): how many times our points a base holds against.

For each map and raid family in scenarios_base.json, run the rungs from the lowest multiple up
with one agent (default turtle), and stop that ladder after two defeats in a row. Rows go to
results/base/ladder.jsonl (tools/night.py run --rows).

  python3 tools/base_ladder.py --agent turtle
  python3 tools/base_ladder.py --summary
  python3 tools/base_ladder.py --v2 --agent turtle     # the v2 arenas: scenarios_base2, ladder2.jsonl

v2 (the user, 2026-10-06): the same specs on arenas without shelves, hydroponics basins and
workbenches, which the raids spent their time wrecking.
"""
import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict

import _path  # noqa: F401
from rca import ROOT

ROWS = ROOT / "results/base/ladder.jsonl"
SPECS = ROOT / "scenarios_base.json"
SCEN = ROOT / "scenarios_base"
LOST = ("defeat",)


def use_v2():
    """Point ROWS/SPECS/SCEN at the v2 arenas (scenarios_base2, ladder2.jsonl)."""
    global ROWS, SPECS, SCEN
    ROWS, SPECS, SCEN = ROOT / "results/base/ladder2.jsonl", ROOT / "scenarios_base2.json", ROOT / "scenarios_base2"


def ladders():
    out = defaultdict(list)
    for s in json.loads(SPECS.read_text()):
        m = re.match(r"base2?_(\w+?)_(\w+?)_(\d+)x$", s["id"])
        if m and (SCEN / f"scenario_{s['id']}.json").exists():
            out[(m.group(1), m.group(2))].append((int(m.group(3)), s["id"]))
    return {k: sorted(v) for k, v in out.items()}


def rows():
    return [json.loads(l) for l in ROWS.read_text().splitlines() if l.strip()] if ROWS.exists() else []


def summary():
    by = {(r["scenario"], (r.get("router") or {}).get("agent")): r for r in rows()}
    for (mp, fam), rungs in sorted(ladders().items()):
        cells = []
        for mult, pid in rungs:
            hit = [r for (sc, _), r in by.items() if sc == pid]
            cells.append(f"x{mult} " + (f"{hit[-1]['grade']} ({hit[-1].get('badness')})" if hit else "-"))
        print(f"{mp:4} {fam:7} " + " | ".join(cells))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="turtle")
    ap.add_argument("--max-ticks", type=int, default=30000)
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--v2", action="store_true", help="the v2 arenas (scenarios_base2, ladder2.jsonl)")
    a = ap.parse_args()
    if a.v2:
        use_v2()
    if a.summary:
        return summary()
    ROWS.parent.mkdir(parents=True, exist_ok=True)
    done = {(r["scenario"], (r.get("router") or {}).get("agent")) for r in rows()}
    for (mp, fam), rungs in sorted(ladders().items()):
        losses = 0
        for mult, pid in rungs:
            if losses >= 2:
                print(f"{pid}: skipped (two defeats below)", flush=True)
                continue
            if (pid, a.agent) not in done:
                subprocess.run([sys.executable, str(ROOT / "tools/night.py"), "run", pid, "--agent", a.agent,
                                "--max-ticks", str(a.max_ticks), "--rows", str(ROWS),
                                "--why", f"base ladder x{mult}"], check=False)
            r = [r for r in rows() if r["scenario"] == pid and (r.get("router") or {}).get("agent") == a.agent]
            losses = losses + 1 if r and r[-1]["grade"] in LOST else 0
    summary()


if __name__ == "__main__":
    main()
