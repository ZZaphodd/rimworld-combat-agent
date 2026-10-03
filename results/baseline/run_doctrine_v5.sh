#!/bin/sh
# Re-run the doctrine agent at v5 (rescue off by default) for the baseline freeze.
cd "$(dirname "$0")/../.."
TH=theme_mechs,theme_pirate_grenadier,theme_pirate_melee,theme_pirate_mixed,theme_pirate_sniper,theme_tribal_archers,theme_tribal_melee
for pass in 1 2; do
  python3 -u tools/run_eval.py --agents doctrine --runs 10 --scenarios $TH --max-ticks 15000 --restart-every 100 --resume --results results/baseline/core.jsonl
done
date > results/baseline/doctrine_v5.done
