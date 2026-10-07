# base2_ith_tribe_6x — Claude, 2026-10-07
Trace `results/human/traces/base2_ith_tribe_6x_claude_20261007-171736.jsonl.gz` · row
`results/human/play.jsonl` (agent claude) · result: **pyrrhic** (raid fled t10042, cleared t19192),
3 dead (Kuma, Paulo, Smith), 3 downed at the end, 7 permanent, HP lost 578 %, badness **80.1**
(turtle defeat 99.3, turtle_at defeat 73.2; kidnaps counted once). Raid: 9 killed + 15 inferred of
34, 7 escaped. **Two of the three dead and one of the downed were our own frags.**
Sheets: sheets/base2_ith_tribe_6x_start.md (base2_ith_tribe_3x: site, cells, rotation;
base_ith_pirate_2x: throws into the corridor queue; base_mon_tribe_3x: the thrower against the wall).

## Card at the start
Ours (shooting/melee): Smith 15/9 steel knife, Kate 5/8 revolver (firefoam), Hono 8/0 heavy SMG
(flak vest, smokepop), Kuma 4/0 machine pistol (flak pants), Jeyce 1/6 excellent revolver (flak
vest, smokepop), Paulo 1/3 machine pistol (Nimble), Elsie 1/2 steel knife, Felix 0/13 frag grenades.
Raid: 34 tribals from the east edge (~244, 132): 12 berserkers (spears), 12 warriors (ikwas), 7
penitents, the chief Abansamitran (spear, steel plate), a pila, a short bow. Tags `base-arena`
`raid-far` `raid-melee` `raid-outnumbers` `raid-strong-1v1`.
Plan: loadout — Smith the heavy SMG, Hono the excellent revolver, Jeyce Smith's knife, Felix Elsie's
knife plus Hono's flak vest and Kuma's flak pants, Elsie the frags. East room, door (133, 187) held
open: Felix plug (133, 188), Jeyce (132, 188) and Kate (134, 188) on the diagonals (melee), Elsie
(133, 189) on the corridor axis with Fire at will off, throwing only at raiders at z ≤ 183 while the
queue stood still; Smith (132, 189), Hono (134, 189), Kuma (131, 189), Paulo (133, 190).

## Scenes
### t0–3775 `raid-wrecking` → in place
Loadout and the armour swap took ~1500 ticks (a second wear order cancels the first). All in place
by t3775; the raid smashed lamps and furniture across the yard; one raider gone before contact.
### t4119–5329 `mouth-hold` `melee-lock`
Panther, Worm, Asza, Lion died in the doorway (plug + both diagonals meleeing). Felix (plug) 100 →
61 % after the first two, 42 % by t5329. First frag order t4280 (Worm at (133, 178)).
### t5350 `rotation`
chose: Felix to the back (130, 193), Kate to the plug, Paulo (Nimble) to (134, 188). The rotation
needed a "no melee orders until on the new cell" rule: a melee order from the old cell kept Kate on
the diagonal.
### t5350–6663 `frag-into-queue`
The queue stood in the corridor x 133, z 178–186. Snake, Lion, Légua, Grasshopper, White, Gagua,
Xevega, Roco out (frags and the doorway melee); Elsie's log: blasts on Grasshopper, Xevega, Emu,
Gagua. 13 out by t6663.
### t6744–7364 `our-downed` `carry-downed`
Jeyce down on (132, 188) (ikwa: left arm cut off). Kuma carried him to (130, 194) from (131, 188)
(orthogonal). Kate down on the plug at t7109; Elsie (orthogonal, behind) carried her out; Kuma took
the plug (100 → 44 % by t7647, two raiders).
### ~t7491 `friendly-fire`
Elsie, still walking back at (132, 193) — off the corridor axis — threw at Caba (133, 183) on an
order my loop gave while she was off her cell; the frag struck the rock by the doorway (sightings at
(132, 188–189)): Kuma, on the plug, shredded and dead; Smith's ear shattered.
### t7765–8843 `rotation` `friendly-fire`
Paulo to the plug, Hono to (134, 188), Smith 26 % to (132, 189). Elsie's later blasts hit the queue
(Lobster, Aro, Goshawk, Gapebal, Megascarab), the chief Abansamitran died in the doorway (t8719).
**~t8840 a frag burst on the doorway: Lobster dead, Paulo dead, Felix (back on (132, 188), 42 %)
downed.** Cause: my loop cancelled each finished or moved frag target with `hands.stop()`, which
undrafts and drafts, and drafting turns Fire at will back on — so from the first cancel (~t4500)
Elsie also threw at targets she picked herself, including raiders next to our own. Frag sightings
at the doorway (133, 186–188): t4885, t5168, t6401, t8638–8786. (`stop()` says so in its own
docstring; fixed after the battle: it now restores Fire at will.)
### t8880–9192
Smith (26 %), carrying Felix from (132, 189), was dead by t8968 (cause not seen; Aro had come to
(132, 187)); Aro stepped onto (132, 188) and attacked Elsie (57 %). Standing: Elsie, Hono (melee 0).
### t9192–10042 retreat behind the next door
chose: Elsie and Hono through the door (133, 197) to the second back room ((133, 210), (135, 209)),
the door (133, 207) held open. followed: the closed door (133, 197) stopped the chasers; the raiders
wrecked the east room's furniture and walls and left the three downed alone. **t10042 "Neanderthals
from Kikbo Nation are fleeing."** (19 of 34 out by t8843.)
### t10725–19192 tending
Tend orders (no medicine) on Jeyce (bleeding 484 %/day, blood loss 0.44 → 0.81) and Kate. A tend took
~2100 ticks (Hono medicine 4, manipulation 38 %; Elsie 1, 34 %); two re-orders and an undraft (the
doctors then left to beat out yard fires) restarted it. First tend landed t~15700 (Jeyce 4.8 → 1.2
/day); at the end Jeyce 0.86, Kate 0.62, Felix 0.64 blood loss, Felix untended.

## What the play stood on (observed)
- The corridor queue stood still while the doorway fight went on; frags thrown straight down the
  axis from (133, 189) landed among it (Elsie: 12,908 damage dealt by the records).
- Two throws went wrong: one from off the axis (struck the rock by the doorway), and the thrower's
  own picks after `stop()` turned Fire at will back on (bursts at the doorway).
- The plug: Felix 100 → 42 % over four doorway raiders (t4119–5329); Kate held ~1750 ticks
  (t5350–7109) while the frags thinned the queue; Kuma 100 → 44 % over two.
- A closed door with nobody visible behind it held the chasers off; the raid fled ~800 ticks later.

## New tags / sites (for the user to look at)
- tag `frag-into-queue` *(new, 2026-10-07)*: a thrower on the corridor axis behind the plug throwing
  at the queue standing still below the doorway.
- tag `friendly-fire` *(new, 2026-10-07)*: our own explosive downing or killing our pawns.
