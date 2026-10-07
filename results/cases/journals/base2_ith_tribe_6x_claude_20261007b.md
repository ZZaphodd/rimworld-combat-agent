# base2_ith_tribe_6x — Claude, 2026-10-07 (attempt 2: the user's play reviewed)
Trace `results/human/traces/base2_ith_tribe_6x_claude_20261007-183526.jsonl.gz` · row
`results/human/play.jsonl` (agent claude, the third base2_ith_tribe_6x row) · result: **repelled** (raid fled t8785,
cleared t16608), 1 dead (Felix, after the raid fled), 1 downed (Jeyce), 0 permanent, HP lost 164 %,
badness **19.6** (the user 44.9, Claude attempt 1 80.1, turtle_at 73.2, turtle 99.3). Raid: 9 killed
+ 13 inferred of 34, 9 escaped.
Before it: one start discarded at t3044 (results/human/discarded.jsonl): reinstall orders on chairs in
the dining room west of the east room stalled, and the squad scattered on other work.

## Card at the start
Same sides as attempt 1. The plan is the user's play (cards/base2_ith_tribe_6x.md, the user's row),
with the user's corrections: the door (133, 187) held open (the user meant to); frags thrown at the
ground at the far end of the straight corridor, never at a raider; the same loadout (weapons only);
the user's six dining chairs reinstalled on (132, 188), (134, 188), (132–134, 189), (133, 190) for
the back row to lean out; Jeyce on the plug (133, 188), Felix (134, 188), Elsie with the frags
(132, 188), Smith (133, 189) on the axis, Kuma (132, 189), Paulo (134, 189), Kate (133, 190), Hono
(134, 190).

## Scenes
### t0–4567 setup
Construction set to priority 1 for all eight (`set_work_priority`; it had been unassigned). Three
went off to build spike traps across the map (unrestricted area — the user) and two wandered the yard;
drafted and sent to their cells at t2384. Five of six chairs in place by ~t3400 (haulers drafted then;
the sixth left). All on their cells at t4567.
### t4567–5300 `frag-max-range`
Elsie on an attack order at the rock (133, 177) at the end of the straight corridor (the user's
"marble") from t4587, before contact: the throws broke the rock by ~t5300 (rock rubble), so the
orders went to the ground cell (133, 178) instead (`do_thing_action Command_VerbTarget targetX/Z`; a
one-shot order, given again every ~120 ticks). Légua, Isaolca, Camalbobai out by t5509.
### t5509–7306 `mouth-hold` `frag-max-range`
The raid came up the corridor; Nanare, Xevega, Goshawk, the chief Abansamitran, Bicaio, Gagua out by
t7105 with Jeyce (plug) 100 → 57 %. Frag sightings on z 185–188 are the throws in flight from (132,
188); no frag hit on our own in Elsie's log (the loop stopped the throws if one did).
### t7306–8050
Panther, Roco, Orange, Aro, White out in the doorway (plug and right diagonal meleeing, guns behind).
Elsie, next to the doorway raider, could not throw while one stood there. Jeyce down on the plug at
t8050 (34 %).
### t8050–8785 `carry-downed` `rotation`
Smith (behind, orthogonal) carried Jeyce to (130, 194); Felix ordered to the plug, Kate to (134, 188):
Kate ended on the plug cell and Felix in the doorway (133, 187), meleeing from there.
Megascarab, Grasshopper, Mole, Spider out. **t8785 "Neanderthals from Kikbo Nation are fleeing."**
All but Jeyce at 84–100 %.
### t8785–9024 after the flee
Felix was still in the doorway (133, 187); sent back to (133, 188), but the loop's "melee whoever is
adjacent" sent him at Gapebal again (fleeing raiders queued in the corridor). Felix
(84 %) was gone by t9024: dead (row: squad_dead 1, kidnapped 0); Gapebal died later.
### t8815–16608
Hono tended Jeyce (no medicine; bleeding 2.97 → 1.85/day by t10000). Raid cleared at t16608.

## What the play stood on (observed)
- The user's cells and chairs, the door held open, throws only at the ground far down the corridor:
  Elsie 11,619 damage dealt; kills by records Kuma 5, Smith 3, Hono 3, Kate 2, Elsie 2, Paulo 1.
- The raid broke at t8785 with 16 of 34 out; ours then: one downed, everyone else at 84–100 %.
- The one death came after the raid fled, from a melee order on a fleeing raider in the doorway.

## New tags / sites (for the user to look at)
- none new.
