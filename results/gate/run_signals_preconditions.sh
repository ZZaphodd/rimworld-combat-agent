#!/bin/sh
# Gate run for feat/signals-preconditions: every agent whose version changed
# (all six: amove 6, doctrine 6, turtle 9, spread 6, kite 6, close 4) on the 7
# baseline themes x 10, same settings as baseline-v1 (adaptive cycle, max 15000
# ticks, restart every 100). Two --resume passes fill episodes lost to a crash;
# stop (no 2nd pass) after two crash relaunches (PROCEDURES §10).
cd "$(dirname "$0")/../.."
TH=theme_mechs,theme_pirate_grenadier,theme_pirate_melee,theme_pirate_mixed,theme_pirate_sniper,theme_tribal_archers,theme_tribal_melee
OUT=results/gate/signals-preconditions
for pass in 1 2; do
  # fixed after the run: the original "$(grep -c ... || echo 0)" printed "0\n0" (grep -c prints 0
  # AND exits 1), so the test errored and never stopped; no relaunch happened in this run.
  n=$(grep -c 'relaunching RimWorld' $OUT.log 2>/dev/null); n=${n:-0}
  if [ "$n" -ge 2 ]; then
    date > $OUT.failed; exit 1
  fi
  python3 -u tools/run_eval.py --agents amove,doctrine,turtle,spread,kite,close --runs 10 \
    --scenarios $TH --max-ticks 15000 --restart-every 100 --resume --results $OUT.jsonl
done
date > $OUT.done
