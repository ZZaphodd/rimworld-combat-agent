"""Base-defense ladder (PROCEDURES §1c): how many times our points a base holds against.

For each map and raid family in scenarios_base.json, run the rungs from the lowest multiple up
with one agent (default turtle), and stop that ladder after two defeats in a row. Rows go to
results/base/ladder.jsonl (tools/night.py run --rows).

  python3 tools/base_ladder.py --agent turtle
  python3 tools/base_ladder.py --summary
  python3 tools/base_ladder.py --v2 --agent turtle     # the v2 arenas: scenarios_base2, ladder2.jsonl
  python3 tools/base_ladder.py --v2 --agent turtle --all-rungs           # also the skipped rungs
  python3 tools/base_ladder.py --v2 --agent turtle_at --option plan=results/base/plans/base2_r1.json

v2 (the user, 2026-10-06): the same specs on arenas without shelves, hydroponics basins and
workbenches, which the raids spent their time wrecking. Rows of an agent other than turtle go to
their own file (ladder2_<agent>.jsonl, or --rows), keyed by scenario, agent and options; an agent
with per-problem input (turtle_at's plan) is checked on every rung before the first run.
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
    """Valid rows (an episode the storyteller spoiled is not a rung's result)."""
    out = [json.loads(l) for l in ROWS.read_text().splitlines() if l.strip()] if ROWS.exists() else []
    return [r for r in out if r.get("outcome") != "invalid"]


def mine(r, agent, options):
    """A row of this agent with these options (rows from before options were passed have none)."""
    rt = r.get("router") or {}
    return rt.get("agent") == agent and (rt.get("options") or {}) == options


def summary(agent="turtle", options=None):
    hits = defaultdict(list)
    for r in rows():
        if mine(r, agent, options or {}):
            hits[r["scenario"]].append(r)
    for (mp, fam), rungs in sorted(ladders().items()):
        cells = []
        for mult, pid in rungs:
            h = hits.get(pid)
            cells.append(f"x{mult} " + (f"{h[-1]['grade']} ({h[-1].get('badness')})" if h else "-"))
        print(f"{mp:4} {fam:7} " + " | ".join(cells))


def preflight(agent, options):
    """Every rung's per-problem input, checked before the first run: [(pid, error)]."""
    sys.path.insert(0, str(ROOT))
    from rca.tactical import make
    a = make(agent)
    if not hasattr(a, "preflight"):
        return []
    a.options = dict(options)
    bad = []
    for rungs in ladders().values():
        for _, pid in rungs:
            try:
                a.preflight(json.loads((SCEN / f"scenario_{pid}.json").read_text()))
            except Exception as e:
                bad.append((pid, str(e)))
    return bad


def main():
    global ROWS
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="turtle")
    ap.add_argument("--option", action="append", default=[], help="k=v, passed to night.py run")
    ap.add_argument("--rows", help="rows file (default: ladder[2].jsonl for turtle, ladder2_<agent>.jsonl else)")
    ap.add_argument("--max-ticks", type=int, default=30000)
    ap.add_argument("--all-rungs", action="store_true", help="no stop after two defeats")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--v2", action="store_true", help="the v2 arenas (scenarios_base2, ladder2.jsonl)")
    a = ap.parse_args()
    from rca.eval.results import canonical
    a.agent = canonical(a.agent)                 # night.py stores the canonical name (hold -> turtle)
    if a.v2:
        use_v2()
    if a.rows:
        ROWS = ROOT / a.rows                     # an absolute path stays as it is
    elif a.agent != "turtle":
        ROWS = ROWS.with_name(f"{ROWS.stem}_{a.agent}.jsonl")
    options = dict(o.split("=", 1) for o in a.option)
    if a.summary:
        return summary(a.agent, options)
    bad = preflight(a.agent, options)
    if bad:
        for pid, e in bad:
            print(f"{pid}: {e}")
        sys.exit(f"{len(bad)} rungs fail the {a.agent} preflight: nothing run")
    ROWS.parent.mkdir(parents=True, exist_ok=True)
    opt_args = [x for o in a.option for x in ("--option", o)]
    for (mp, fam), rungs in sorted(ladders().items()):
        losses = 0
        for mult, pid in rungs:
            if losses >= 2 and not a.all_rungs:
                print(f"{pid}: skipped (two defeats below)", flush=True)
                continue
            if not any(r["scenario"] == pid and mine(r, a.agent, options) for r in rows()):
                subprocess.run([sys.executable, str(ROOT / "tools/night.py"), "run", pid, "--agent", a.agent,
                                *opt_args, "--max-ticks", str(a.max_ticks), "--rows", str(ROWS),
                                "--why", f"base ladder x{mult}"], check=False)
            r = [r for r in rows() if r["scenario"] == pid and mine(r, a.agent, options)]
            losses = losses + 1 if r and r[-1]["grade"] in LOST else 0
    summary(a.agent, options)


if __name__ == "__main__":
    main()
