#!/bin/sh
# Reflex v2 (adaptive cycle + reflex v2) on both check scenarios, plus 5 more
# frag_check runs for every setting (frag events are rare: n=5 was thin).
R=results/reflex_check.jsonl
E="python3 eval.py --max-ticks 15000 --results $R --resume --agents b1,turtle,spread"
$E --runs 5 --scenarios theme_pirate_grenadier
$E --runs 10 --scenarios theme_frag_check
$E --runs 10 --scenarios theme_frag_check --cycle fixed --no-reflex
$E --runs 10 --scenarios theme_frag_check --no-reflex
touch results/reflex_v2.done
