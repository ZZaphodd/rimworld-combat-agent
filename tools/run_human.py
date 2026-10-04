"""Observe-only episode: you play, the harness only watches and grades (EVAL_SPEC §3 rows).

  python3 tools/run_human.py --scenario t500_pirate_grenadier
  python3 tools/run_human.py --scenario t500_pirate_mixed --player kim --results results/human/play.jsonl

The scenario loads paused. Draft and fight as you like; the harness never pauses or advances
time. It stops when the raid is gone, the squad is down, or after --max-ticks of game time.
"""
import argparse
from pathlib import Path

import _path  # noqa: F401
from rca import ROOT
from rca.eval.harness import load_manifests, run_observed_episode
from rca.eval.results import append_row
from rca.rimmolt import RimMolt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--player", default="human")
    ap.add_argument("--max-ticks", type=int, default=15000)
    ap.add_argument("--poll", type=float, default=1.0, help="seconds between observations")
    ap.add_argument("--results", type=Path, default=ROOT / "results/human/play.jsonl")
    a = ap.parse_args()
    log = lambda s: print(s, flush=True)          # noqa: E731
    m = load_manifests([a.scenario])[0]
    row = run_observed_episode(RimMolt(), m, a.max_ticks, a.poll, log, player=a.player)
    append_row(a.results, row)
    log(f"   {row['outcome']} grade={row['grade']} LER={row['ler']} lost={row['deaths']} "
        f"downed={row['downed_at_end']} | enemy seen {row['enemies_seen']} killed "
        f"{row['enemies_killed']}+{row['enemies_killed_inferred']}? escaped {row['enemies_escaped']} "
        f"| ticks={row['ticks']} wall={row['wall_s']}s -> {a.results}")


if __name__ == "__main__":
    main()
