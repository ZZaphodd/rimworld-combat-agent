#!/bin/sh
# Phase-2 doctrine smoke runs (not the baseline matrix): 2 episodes per doctrine
# on its home themes, then one episode per vs_throwers option on grenadier themes.
cd "$(dirname "$0")/../.." || exit 1
R=results/phase2/smoke.jsonl
run() { python3 tools/run_eval.py --results $R --resume "$@"; }
run --agents doctrine --scenarios theme_pirate_mixed,theme_mechs --runs 2
run --agents turtle --scenarios theme_pirate_melee,theme_tribal_melee --runs 2
run --agents spread --scenarios theme_pirate_grenadier,theme_frag_check --runs 2
run --agents kite --scenarios theme_pirate_melee,theme_tribal_melee --runs 2
run --agents close --scenarios theme_pirate_sniper,theme_mechs --runs 2
O=results/phase2/options.jsonl
for o in stand_off close_in; do
  python3 tools/run_eval.py --results $O --resume --agents spread --scenarios theme_pirate_grenadier --runs 1 --option vs_throwers=$o
  python3 tools/run_eval.py --results $O --resume --agents turtle --scenarios theme_frag_check --runs 1 --option vs_throwers=$o
done
touch results/phase2/smoke.done
