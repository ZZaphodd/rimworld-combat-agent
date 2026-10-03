#!/bin/sh
# Reflex v3b (gate ignores rockets/clumping; neighbourhood hysteresis): b1 v4, spread v4,
# turtle v7, same scenarios/runs/cycle as threatmap_check.sh, appended to the same jsonl.
# Run detached:  nohup sh results/threatmap_check_v3b.sh > results/threatmap_check_v3b.log 2>&1 &
# Each block runs twice with --resume: the 2nd pass fills episodes lost to a crash.
R=results/threatmap_check.jsonl
E="python3 eval.py --max-ticks 15000 --results $R --resume --agents b1,turtle,spread"
RESTARTS=0

alive() {
  curl -s -m 10 -X POST http://localhost:8787/mcp -H 'Content-Type: application/json' \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_status","arguments":{}}}' \
    | grep -q '"result"'
}

ensure_game() {
  alive && return 0
  if pgrep -f "RimWorld by Ludeon Studios" > /dev/null; then
    sleep 60
    alive && return 0
  fi
  if [ "$RESTARTS" -ge 2 ]; then
    echo "!! game down after two relaunches: stopping"
    touch results/threatmap_check_v3b.failed
    exit 1
  fi
  RESTARTS=$((RESTARTS + 1))
  echo "!! game down: relaunch $RESTARTS at $(date)"
  open steam://rungameid/294100
  i=0
  while [ $i -lt 60 ]; do
    sleep 5
    alive && { sleep 20; echo "!! game back at $(date)"; return 0; }
    i=$((i + 1))
  done
  ensure_game
}

for S in "theme_frag_check 10" "theme_pirate_grenadier 5"; do
  set -- $S
  for PASS in 1 2; do
    ensure_game
    $E --scenarios $1 --runs $2 --reflex-version 3
  done
done
touch results/threatmap_check_v3b.done
