#!/bin/sh
# Pre-baseline checks (not the baseline matrix), 2026-10-03:
#  1. mech cells that recorded enemy_fire_share 0.0 before the firelog fix;
#  2. the no_progress rule 2 on the two cells where rule 1 fired in won battles
#     (also turtle's Go here failures: orders_failed / redrafts);
#  3. one episode per non-natural casualty option.
cd "$(dirname "$0")/../.." || exit 1
D=results/prebaseline
run() { python3 tools/run_eval.py --resume "$@"; }
run --results $D/mech_recheck.jsonl --agents doctrine,close --scenarios theme_mechs --runs 2
run --results $D/signal_check.jsonl --agents turtle,kite --scenarios theme_tribal_melee --runs 2
run --results $D/options_check.jsonl --agents doctrine --scenarios theme_pirate_mixed --runs 1 --option rescue=off
run --results $D/options_check.jsonl --agents doctrine --scenarios theme_pirate_mixed --runs 1 --option wounded_pullback=off
run --results $D/options_check.jsonl --agents turtle --scenarios theme_pirate_melee --runs 1 --option wounded_pullback=off
touch $D/checks.done
