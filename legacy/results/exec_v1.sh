#!/bin/sh
# KPI baselines of the v1 doctrines on their home themes (before any fix).
R=results/exec_v1.jsonl
E="python3 eval.py --runs 3 --max-ticks 15000 --results $R --resume"
$E --agents kite --scenarios theme_pirate_melee,theme_tribal_melee
$E --agents doctrine --scenarios theme_pirate_mixed,theme_mechs
$E --agents hold --scenarios theme_mechs,theme_tribal_melee --runs 2
$E --agents close --scenarios theme_pirate_sniper --runs 2
$E --agents spread --scenarios theme_pirate_grenadier --runs 2
touch results/exec_v1.done
