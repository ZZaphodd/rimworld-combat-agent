#!/bin/sh
# Verify the watchdog paths once (PROCEDURES §10), 2026-10-03:
#  A. planned restart: --restart-every 1 -> the game is quit and relaunched before episode 2;
#  B. crash relaunch: the game is killed between batches; the next batch's watchdog relaunches it.
cd "$(dirname "$0")/../.." || exit 1
R=results/prebaseline/restart_check.jsonl
P="RimWorld by Ludeon"
echo "## A: planned restart"
python3 tools/run_eval.py --results $R --resume --agents amove --scenarios theme_frag_check --runs 2 --restart-every 1 || { touch results/prebaseline/restart.failed; exit 1; }
echo "## B: kill the game, then a batch must relaunch it"
pkill -f "$P Studios"
for i in $(seq 1 24); do pgrep -f "$P Studios" >/dev/null || break; sleep 5; done
pgrep -f "$P Studios" >/dev/null && { echo "game did not exit"; touch results/prebaseline/restart.failed; exit 1; }
echo "game process gone at $(date +%T)"
python3 tools/run_eval.py --results $R --resume --agents amove --scenarios theme_frag_check --runs 3 --restart-every 0 || { touch results/prebaseline/restart.failed; exit 1; }
touch results/prebaseline/restart.done
