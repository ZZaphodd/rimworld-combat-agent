# base2_ith_pirate_4x · civil outlanders ×8 (shooting 0–9) vs 19 Wasters with toxbombs, rockets, an incendiary · Ithfunda base v2 — repelled

**Situation:** `base-arena` `raid-far` `raid-outranges` `raid-throwers` `us-low-skill` `tox`
**Plays seen:** `closed-door-hold` `off-axis-hold` `focus-fire` (naive agents: `turtle`, `turtle_at`)
**Numbers:** ours 8 (5 revolvers/autopistol, pump shotgun, 2 bolt-action rifles), 500 pt · raid 19
PirateWaster (4×: 2000 pt) · count ratio 0.42 · raid from the south edge (~118, 4) · base `arena_col_ithfunda2`

## Sides
- Ours (shooting/melee): Selyn 9/1 revolver; Starry 4/4 pump shotgun; Minnow 4/2, Mie 0/0 bolt-action
  rifles; Rapha 2/0, Daiki 0/1, Siso 1/3 revolvers; Paul 0/0 autopistol.
- Raid: toxbomb launchers Euthanizer, Raywolfen; Hellcats Skrap (14), Rynyk; incendiary launcher Ryan
  (13); Doomsday Rubout; LMGs Maker (boss, marine armour), Nicole; Azy assault rifle; Will sniper;
  slashers Raz, Carlos, Lenka (shield belt); others.

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| naive agent `turtle` | concave in the yard | Ithfunda yard | unresolved (timeout) | 2 | 64.5 |
| naive agent `turtle_at` (plan base2_r1) | door held open, plug + guns 2 back on the axis | Ithfunda east room | defeat | 8 (all) | 122.0 |
| Claude (alone) | door **closed**, everyone off the axis; focus fire on gas/rocket/incendiary holders at the doorway | Ithfunda east room | **repelled** (fled t12223) | 0 (0 downed) | **1.5** |

## Scenes (Claude; trace ticks)
- **t9841–10141** `breach`: the door broke; Raz and Euthanizer (toxbombs) walked in; all eight on
  Euthanizer; both down before a toxbomb was fired.
- **t10951–11822** `focus-fire`: Raywolfen (toxbombs) and Rubout (Doomsday) shot down at the doorway.
- **t11822–12305** `fire`: Ryan's incendiary lit the west cells; three burned; two put the fires out
  while three shot Ryan down; the raid fled.

## What the play stood on (Claude's reasons)
- The raid's gas, fire and rockets need a line of sight into the room; a closed door and off-axis
  cells kept them from having one until a raider stood in the doorway, where every gun could reach it.
