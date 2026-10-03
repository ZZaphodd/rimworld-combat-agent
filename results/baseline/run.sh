#!/bin/sh
# Baseline matrix (pre-freeze): core 6 doctrines x 7 themes x 10, then casualty-option comparison x 5.
# Re-runs each block once with --resume to fill episodes lost to a crash.
cd "$(dirname "$0")/../.."
TH=theme_mechs,theme_pirate_grenadier,theme_pirate_melee,theme_pirate_mixed,theme_pirate_sniper,theme_tribal_archers,theme_tribal_melee
COMMON="--scenarios $TH --max-ticks 15000 --restart-every 100 --resume"
for pass in 1 2; do
  python3 -u tools/run_eval.py --agents amove,doctrine,turtle,spread,kite,close --runs 10 $COMMON --results results/baseline/core.jsonl
done
for pass in 1 2; do
  python3 -u tools/run_eval.py --agents doctrine --option rescue=off --runs 5 $COMMON --results results/baseline/options.jsonl
  python3 -u tools/run_eval.py --agents turtle --option wounded_pullback=off --runs 5 $COMMON --results results/baseline/options.jsonl
done
date > results/baseline/run.done
