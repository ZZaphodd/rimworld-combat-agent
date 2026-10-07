# base2_ith_tribe_6x · civil outlanders ×8 vs 34 tribals (32 melee) · Ithfunda base v2 — repelled (the user)

**Situation:** `base-arena` `raid-far` `raid-melee` `raid-outnumbers` `raid-strong-1v1`
**Plays seen:** `closed-door-hold` `furniture-bait` `frag-at-rock` `mouth-hold` `melee-lock` `rotation` `frag-into-queue` `carry-downed` `friendly-fire` (agents: `turtle`, `turtle_at`)
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
| **the user** | Claude's loadout; chairs hauled into the east room; door (133, 187) left **closed** until the raid broke it; Jeyce on the plug, Felix and Elsie (frags, against the wall) on the diagonals, five guns packed 1–2 rows behind (Smith on the axis (133, 189)); frags at the rock beside the corridor while the door held, then down the corridor; Paulo took the frags when Elsie went down | Ithfunda east room | **repelled** (fled t9911) | 1 dead (Felix), 2 downed | **44.9** |

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

## Scenes (the user; watcher looks ~t, trace ticks t)
- **~t700–3800** `furniture-bait`: wooden dining chairs hauled into the east room by undrafted pawns
  while the raid crossed the map; six drafted on the room's west side (129–132, 188–190) by ~t3200;
  Felix, Smith and Jeyce came up the corridor last (~t3800) with Grasshopper ~14 cells behind.
- **~t4000–4870** `closed-door-hold` `frag-at-rock`: the door (133, 187) not held open, so it closed;
  Jeyce on (133, 188), Felix (134, 188), Elsie (132, 188). Grasshopper bashed the door (82 % at ~t4110).
  Elsie on an attack order at "the marble" (her log: "deliberately launched her frag grenade at the
  marble"); frag sightings (132, 184–188) at t4682–4979, while the door still stood. The door broke by
  ~t4870 with Grasshopper at 46 % and the chief Abansamitran at 52 % behind him; the chief went down in
  the doorway.
- **~t4870–7680** `mouth-hold` `frag-into-queue`: the queue in the corridor; frag sightings at z 178–186
  (t5219–7331); Jeyce (plug) 100 → 49 % by ~t6930, down by ~t7680 and crawled back; Felix (right
  diagonal) 57 % at t7418, dead by ~t7680 (cause not seen).
- **~t8530**: Elsie down on the left diagonal (29 %); Paulo took her frags ("Paulo threw his frag
  grenade at Panther"); Kate on the right diagonal.
- **~t9490–9911**: Kate and Paulo down; Smith, Kuma, Hono standing at 100 %; **t9911 the raid fled**
  (~17 of 34 out).
- **after**: Hono and Smith tended (Elsie back up by ~t12040, then tending Kate); the raid set ~300
  fires in the yard, none near the room.
- No hit on our own pawns in Elsie's or Paulo's log (short logs). Records: Smith 6 kills (89 shots),
  Paulo 4 (104), Kuma 3 (139), Elsie 7,468 damage dealt. Light trace: its weapons line was read before
  the loadout, so five weapons there are the pre-swap ones.

## What the play stood on (Claude's reasons)
- base2_ith_tribe_3x's door hold against twice the raid; the frags to thin the corridor queue so the
  plug met fewer raiders (base_ith_pirate_2x threw molotovs into the same queue).
