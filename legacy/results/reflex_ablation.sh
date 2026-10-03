#!/bin/sh
# Ablation: adaptive cycle WITHOUT reflex actions, to split the cycle's effect from the reflex's.
R=results/reflex_check.jsonl
E="python3 eval.py --max-ticks 15000 --results $R --resume --agents b1,turtle,spread --runs 5 --no-reflex"
$E --scenarios theme_pirate_grenadier
$E --scenarios theme_frag_check
touch results/reflex_ablation.done
