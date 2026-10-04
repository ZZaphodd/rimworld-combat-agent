#!/bin/sh
# baseline-v2: 6 doctrines x the 6 t500 themes x 10 on Strive to Survive (WORKFLOW evaluation standard).
# Re-runs once with --resume to fill episodes lost to a crash or left invalid.
cd "$(dirname "$0")/../.."
for pass in 1 2; do
  python3 -u tools/run_eval.py --agents amove,doctrine,turtle,spread,kite,close --runs 10 \
    --scenarios tier:t500 --max-ticks 15000 --restart-every 100 --resume \
    --results results/baseline_v2/core.jsonl
done
date > results/baseline_v2/run.done
