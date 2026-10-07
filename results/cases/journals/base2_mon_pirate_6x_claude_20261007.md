# base2_mon_pirate_6x — Claude, 2026-10-07
Trace `results/human/traces/base2_mon_pirate_6x_claude_20261007-144941.jsonl.gz` · row
`results/human/play.jsonl` (agent claude) · result: **repelled** (raid fled t13165, cleared t20524),
lost 0, downed 4 at the end, permanent 0, HP lost 322 %, badness **24.9** (turtle_at 113.3,
turtle 119.6; kidnaps counted once).
Sheets: sheets/base2_mon_pirate_6x_start.md (base_mon_tribe_3x: site and door states used;
base_ith_*: guns 2+ cells from the doorway).

## Card at the start
Ours: civil outlanders ×8, shooting 0–8 — Egan pump shotgun (0/5, Brawler, Bloodlust, flak vest),
Rutana pump shotgun (4/5), Merlicek machine pistol (8/0), Willy heavy SMG (2/0), Dan revolver
(2/7), Adam bolt-action rifle (1/0), Kieri autopistol (5/2, low-shield pack), Willow incendiary
launcher (8/6). Raid: 28 pirates from the west edge (4, 124), ~150 cells by path: 7 Elites (marine or
recon armour; LMGs, Hellcat rifles, chain shotgun, assault rifle), 5 sniper rifles, a Doomsday
rocket launcher, a minigun, a molotov grenadier, 2 shield-belt slashers, 2 drifters, gunners.
Tags `base-arena` `raid-far` `raid-outnumbers` `raid-outranges` `us-low-skill`.
Plan: Monler R2 with R2's door (145, 84), the inner door (145, 86) and the outer door (145, 94) held
open (the user's attempt-2 door states), but nobody on the passage axis x 145: the save-map line of
sight showed the axis cells seen from ~50 outside cells up to 33 away, and the off-axis cells only
from the doorway and 1–2 corridor cells. Cells: Egan (144, 82), Rutana (146, 82), Merlicek (143, 81),
Willy (147, 81), Dan (142, 82), Adam (148, 82), Kieri (144, 80), Willow (146, 80), fire held. Kieri's
low shield (radius 4.9, 1800 ticks, bullets out not in) to go up when the raid reached the passage
bottom.

## Scenes
### t0–1405 `raid-far` → walk in
All eight on their cells by t1405; the raid smashed furniture far west.
### t3206 `raid-wrecking`
saw: 23 standing, 1 downed, 4 missing before any contact, near the west yard (not seen how).
### t4633–6553 `raid-wrecking`
Raiders smashed the hall's chairs, a transport pod and the darktorch (145, 88) in the passage; Ross
(Elite, Hellcat) came down to (145, 89) and went back twice.
### t6674 `breach` → `melee-lock`
saw: Ross walked through the doorway to (145, 83), diagonal to Egan and Rutana. chose: Egan and
Rutana melee him (a gun can't fire at an adjacent raider), the rest fire at will. followed: Ross
down by t6734. Carboturf (Elite, chain shotgun, melee 14) the same at t6975, down by t7065.
### t7065–8568
Two more raiders down at the doorway; Egan 68 %. The raid went back to the yard to smash generators.
### t11148 `top-threat`
saw: Egan 51 % (a sniper gunshot in the foot, pain 77 %); Codex (boss, Hellcat) standing in the inner
door (145, 86), which sees Egan's, Rutana's, Kieri's and Willow's cells. chose: Egan back to (149, 76).
followed: Egan downed on his cell (t11215) before he moved.
### t11215–11458 `fire`
chose: Willow's incendiary launcher at Codex in the inner door (explicit Fire at). followed: Codex down;
the shot started a fire at (145, 86–87).
### t11610–12000
Smog (gunner) walked in to (145, 83): Rutana and Willow meleed, down by t12000. Kieri downed on (144, 80)
by Wan from (145, 87): (144, 80) is one of the few room cells seen from the passage. The low shield was
never deployed (held for a bigger wave).
### t12120–12312 `carry-downed`
Willow carried Egan, Dan carried Kieri to the back (149, 76–77); both then crawled ("Crawling to bed").
### t12825–13216 `breach`
Vas (sniper) walked into the room past the line to (146, 80), Wan to (145, 83); meleed and shot down.
Willy 44 %. **t13165 "Pirates from The Gray Vipers are fleeing."** 9 killed + 5 inferred of 28 by the end.
### t13817–20524 `fire` after the raid broke
Willow and Dan tended the downed. The fire from the incendiary spread into R2 (fires at (142–145,
76–87)): "being burned by superheated air", heatstroke and burns on everyone in R2; Willy (t ~17000)
and Dan (~t20000) downed. Carrying out to R3 (through the east door (150, 79)):
- a Drop given before arrival left two downed in R2;
- a Go here given before pickup cancelled a carry;
- Rescue (to a bed) routed the carriers back through R2;
- a carry stalled until the carrier stood on a cell orthogonal to the downed pawn.
Harness end t20524 (raid gone): 4 downed (Egan, Kieri, Willy, Dan).
After the end (not in the row): Willow and Merlicek went down in R2's heat while carrying.

## What the play stood on (observed)
- Off-axis cells: no raider shot into R2 from the passage or the hall; every kill came when a raider
  stood in the doorway, walked into the room, or stood in the inner door.
- Raiders walked through the open doorway into the room one at a time (Ross, Carboturf, Smog, Wan, and
  Vas past the line); adjacent pawns meleed, the rest shot.
- Downs of ours: Egan (sniper in the foot, then shot from the inner door), Kieri (a passage-visible
  cell), then two to heat after the fire.
- The fire came from our incendiary shot, as the heat in turtle_at's run of this problem came from a
  fire in R2.

## New tags / sites (for the user to look at)
- tag `off-axis-hold` *(new, 2026-10-07)*: inside a room behind an open door, every pawn on a cell
  that sees the doorway but not the approach corridor.
- site note: Monler R2's off-axis cells and the cells seen from the passage (save-map line of sight)
  in sites.md.
