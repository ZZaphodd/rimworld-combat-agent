#!/bin/sh
# Unpack the versioned scenario/arena saves into RimWorld's Saves folder.
# RimWorld can't load .gz, and raids are generated randomly, so these saves are the
# only way to reproduce a scenario exactly. Existing files are not overwritten unless -f.
set -e
DEST="${RIMWORLD_SAVES:-$HOME/Library/Application Support/RimWorld/Saves}"
FORCE=0; [ "$1" = "-f" ] && FORCE=1
cd "$(dirname "$0")/saves"
for gz in *.rws.gz; do
  out="$DEST/${gz%.gz}"
  if [ -e "$out" ] && [ $FORCE -eq 0 ]; then echo "skip (exists): ${gz%.gz}"; continue; fi
  gunzip -c "$gz" > "$out" && echo "restored: ${gz%.gz}"
done
