#!/bin/sh
# Home-theme verification of the fixed doctrines (kite v3, focus v2, hold v4), 120-tick step.
R=results/exec_v2.jsonl
E="python3 eval.py --max-ticks 15000 --results $R --resume"
$E --agents kite --scenarios theme_pirate_melee,theme_tribal_melee --runs 5
$E --agents doctrine --scenarios theme_pirate_mixed,theme_mechs --runs 5
$E --agents hold --scenarios theme_mechs --runs 4
$E --agents hold --scenarios theme_tribal_melee,theme_pirate_melee --runs 2
touch results/exec_v2.done
