"""Run episodes through the harness (EVAL_SPEC.md).

  python3 tools/run_eval.py --agents amove --scenarios theme_pirate_mixed --runs 1 \\
      --results results/rca_smoke.jsonl
  python3 tools/run_eval.py --agents amove,b0 --scenarios all --runs 5 --resume ...
'all' excludes check-tier scenarios (frag_check): name them explicitly.
Run long batches detached: nohup python3 tools/run_eval.py ... > log 2>&1 &
"""
import argparse
from pathlib import Path

import _path  # noqa: F401
from rca import ROOT
from rca.eval.harness import Cycle, load_manifests, run_batch
from rca.game.session import Watchdog
from rca.rimmolt import RimMolt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", default="amove")
    ap.add_argument("--scenarios", default="all", help="comma-separated ids or 'all'")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--max-ticks", type=int, default=15000, help="2500 = 1 in-game hour")
    ap.add_argument("--step-ticks", type=int, default=120, help="calm cycle")
    ap.add_argument("--fast-ticks", type=int, default=30)
    ap.add_argument("--fast-radius", type=int, default=40)
    ap.add_argument("--cycle", choices=("adaptive", "fixed"), default="adaptive")
    ap.add_argument("--no-reflex", dest="reflex", action="store_false",
                    help="micro layer observes and counts but never moves anybody")
    ap.add_argument("--results", type=Path, default=ROOT / "results/rca.jsonl")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--option", action="append", default=[], metavar="KEY=VALUE",
                    help="tactical option, e.g. vs_throwers=stand_off (doctrines that offer it)")
    ap.add_argument("--restart-every", type=int, default=100,
                    help="planned game restart after this many episodes (0 = never)")
    a = ap.parse_args()
    options = dict(o.split("=", 1) for o in a.option)
    rm = RimMolt()
    cycle = Cycle(a.step_ticks, a.fast_ticks, a.fast_radius, a.cycle == "adaptive")
    run_batch(rm, load_manifests(a.scenarios), a.agents.split(","), a.runs, a.results, cycle,
              a.reflex, a.max_ticks, a.resume, Watchdog(rm, restart_every=a.restart_every),
              log=lambda s: print(s, flush=True), options=options)
    print(f"done -> {a.results}", flush=True)


if __name__ == "__main__":
    main()
