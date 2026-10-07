# base2_ith_tribe_6x · civil outlanders ×8 vs 34 tribals (32 melee) · Ithfunda base v2 — pyrrhic

**Situation:** `base-arena` `raid-far` `raid-melee` `raid-outnumbers` `raid-strong-1v1`
**Plays seen:** `mouth-hold` `melee-lock` `rotation` `frag-into-queue` `carry-downed` `friendly-fire` (agents: `turtle`, `turtle_at`)
**Numbers:** ours 8 (heavy SMG, 2 revolvers, 2 machine pistols, 2 knives, frag grenades), 500 pt · raid 34
TribeRoughNeanderthal (6×: 3000 pt) · count ratio 0.24 · raid from the east edge (~244, 132) · base
`arena_col_ithfunda2`

## Sides
- Ours (shooting/melee): Smith 15/9 steel knife; Kate 5/8 revolver (firefoam); Hono 8/0 heavy SMG
  (flak vest, smokepop); Kuma 4/0 machine pistol (flak pants); Jeyce 1/6 excellent revolver (flak
  vest, smokepop); Paulo 1/3 machine pistol (Nimble); Elsie 1/2 steel knife; Felix 0/13 frag grenades.
- Raid: 12 berserkers (spears), 12 warriors (ikwas), 7 penitents (knives, clubs; Inegato and White
  melee 14), the chief Abansamitran (spear, steel plate), Laga (pila), Caba (short bow).

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| agent `turtle` | concave in the yard | Ithfunda yard | defeat | 5 | 99.3 |
| agent `turtle_at` (plan base2_r1) | door hold, plug + guns 2 back | Ithfunda east room | defeat: squad down (10 killed + 5 inferred) | 2 dead, 6 downed | 73.2 |
| Claude (alone) | loadout (best shooter the heavy SMG, frags to the weakest), door hold, melee on the plug and diagonals, frags down the corridor axis, rotation; retreat behind the next door | Ithfunda east room | **pyrrhic** (fled t10042) | 3 dead (2 by our own frags), 3 downed, 7 permanent | 80.1 |

## Scenes (Claude; trace ticks)
- **t4119–6663** `mouth-hold` `frag-into-queue`: the raid queued in the corridor x 133; the plug
  and both diagonals meleed the doorway raider, Elsie threw from (133, 189) down the axis; 13 of 34
  out by t6663. Felix (plug) 100 → 42 % over four raiders, rotated out at t5350.
- **t6744–7647** `carry-downed` `rotation`: Jeyce (diagonal) and Kate (plug) downed; each carried
  out by the pawn on an orthogonal cell; Kuma took the plug.
- **~t7491, ~t8840** `friendly-fire`: a frag thrown from off the axis (132, 193) struck the rock by
  the doorway and killed Kuma on the plug; later bursts at the doorway killed Paulo (plug) and downed
  Felix. The thrower's Fire at will had been switched back on by `hands.stop()` (undraft + draft)
  since ~t4500, so she also threw at raiders she picked, next to our own.
- **t9192–10042**: two left standing went through the door (133, 197) to the second back room; the
  closed door stopped the chasers, who wrecked the east room and left the downed alone; the raid fled
  at t10042 with 19 of 34 out.
- **t10725–19192**: tending without medicine took ~2100 ticks per tend (doctors at manipulation
  34–38 %); restarting the order restarts it.

## What the play stood on (Claude's reasons)
- base2_ith_tribe_3x's door hold against twice the raid; the frags to thin the corridor queue so the
  plug met fewer raiders (base_ith_pirate_2x threw molotovs into the same queue).
