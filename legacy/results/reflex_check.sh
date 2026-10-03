#!/bin/sh
# Reflex validation: old setting (fixed 120-tick cycle, reflex observe-only) vs
# adaptive 30/120@40 cycle + reflex, aggressive/turtle/spread, 5 runs each.
R=results/reflex_check.jsonl
E="python3 eval.py --max-ticks 15000 --results $R --resume --agents b1,turtle,spread --runs 5"
for S in theme_frag_check theme_pirate_grenadier; do
  $E --scenarios $S --cycle fixed --no-reflex
  $E --scenarios $S
done
touch results/reflex_check.done
