"""Observe-only episode: you play, the harness only watches and grades (EVAL_SPEC §3 rows).

  python3 tools/run_human.py --scenario t500_pirate_grenadier
  python3 tools/run_human.py --scenario t500_pirate_mixed --player kim --results results/human/play.jsonl
  python3 tools/run_human.py --manifest scenarios_rand/scenario_rand_007.json   # a night-run problem

The scenario loads paused. Draft and fight as you like; the harness never pauses or advances
time. It stops when the raid is gone, the squad is down, or after --max-ticks of game time.
Every poll also goes to a trace (rca/eval/trace.py) in results/human/traces/, named in the
row's "trace" field; --no-trace skips it.
"""
import argparse
import json
import time
from pathlib import Path

import _path  # noqa: F401
from rca import ROOT
from rca.eval.harness import load_manifests, run_observed_episode
from rca.eval.results import append_row
from rca.eval.trace import Trace
from rca.rimmolt import RimMolt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario")
    ap.add_argument("--manifest", type=Path, help="a manifest file (e.g. scenarios_rand/...)")
    ap.add_argument("--player", default="human")
    ap.add_argument("--max-ticks", type=int, default=15000)
    ap.add_argument("--poll", type=float, default=1.0, help="seconds between observations")
    ap.add_argument("--results", type=Path, default=ROOT / "results/human/play.jsonl")
    ap.add_argument("--trace-dir", type=Path, default=ROOT / "results/human/traces")
    ap.add_argument("--no-trace", action="store_true")
    ap.add_argument("--trace-light", action="store_true",
                    help="for a human at the GUI: no per-pawn reads while the game runs (with RimMolt's "
                         "'Mirror AI inspection' on they change the selection); weapons read once at "
                         "load, no raider health")
    ap.add_argument("--remove-intruders", action="store_true",
                    help="destroy the storyteller's own arrivals and play on instead of ending the "
                         "run as invalid (listed in the row's storyteller_removed; Cawalia, the user)")
    a = ap.parse_args()
    log = lambda s: print(s, flush=True)          # noqa: E731
    if not (a.scenario or a.manifest):
        ap.error("--scenario or --manifest required")
    m = json.loads(a.manifest.read_text()) if a.manifest else load_manifests([a.scenario])[0]
    trace = None
    if not a.no_trace:
        path = a.trace_dir / f"{m['id']}_{a.player}_{time.strftime('%Y%m%d-%H%M%S')}.jsonl.gz"
        trace = Trace(path, m, a.player, light=a.trace_light)
    row = run_observed_episode(RimMolt(), m, a.max_ticks, a.poll, log, player=a.player,
                               trace=trace, remove_intruders=a.remove_intruders)
    if trace:
        p = trace.path.resolve()
        row["trace"] = str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p)
    append_row(a.results, row)
    log(f"   {row['outcome']} grade={row['grade']} LER={row['ler']} lost={row['deaths']} "
        f"downed={row['downed_at_end']} | enemy seen {row['enemies_seen']} killed "
        f"{row['enemies_killed']}+{row['enemies_killed_inferred']}? escaped {row['enemies_escaped']} "
        f"| ticks={row['ticks']} wall={row['wall_s']}s -> {a.results}")


if __name__ == "__main__":
    main()
