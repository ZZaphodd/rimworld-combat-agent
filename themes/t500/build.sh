#!/bin/sh
# t500 scenario set (PROCEDURES §7): fresh game before each load-heavy stage.
cd "$(dirname "$0")/../.."
restart() { python3 -c "import sys; sys.path.insert(0,'.'); from rca.rimmolt import RimMolt; from rca.game.session import Watchdog; Watchdog(RimMolt()).planned_restart()"; }
set -e
restart
python3 tools/build_themes.py --set t500 --base
python3 tools/build_themes.py --set t500 --themes pirate_mixed,pirate_melee,pirate_grenadier,pirate_sniper
restart
python3 tools/build_themes.py --set t500 --themes tribal_melee,tribal_archers,mechs
python3 tools/build_themes.py --set t500 --frag-check
touch themes/t500/build.done
