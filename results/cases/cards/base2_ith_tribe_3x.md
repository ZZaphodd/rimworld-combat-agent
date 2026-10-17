# base2_ith_tribe_3x · civil outlanders ×8 vs 18 tribals (15 melee) · Ithfunda base v2 — repelled

**Situation:** `base-arena` `raid-far` `raid-melee` `raid-outnumbers`
**Plays seen:** `mouth-hold` `melee-lock` `rotation` (naive agents: `turtle`, `turtle_at`)
**Numbers:** ours 8 (heavy SMG, 2 autopistols, 2 pump shotguns, 2 bolt-action rifles, knife), 500 pt ·
raid 18 TribeRoughNeanderthal (3×: 1500 pt) · count ratio 0.44 · raid from the south edge (~105, 4) ·
base `arena_col_ithfunda2`

## Sides
- Ours (shooting/melee): Karlsen 18/12 heavy SMG; Shen 11/10 autopistol (firefoam); Schaefer 9/1
  (Tough), Lumpy 8/6 pump shotguns; Gnugfur 3/7, Binx 0/1 bolt-action rifles; Pepper 0/10 autopistol
  (Brawler); Val 4/3 knife.
- Raid: 7 penitents (knives, clubs), 3 berserkers (spears), 4 warriors (ikwas), the chief Lelacacan
  (spear, steel plate), 2 archers, a heavy archer (pila).

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| naive agent `turtle` | concave in the yard | Ithfunda yard | defeat | 3 (1 dead, 2 kidnapped) | 109.1 |
| naive agent `turtle_at` (plan base2_r1) | door hold, plug + guns 2 back | Ithfunda east room | defeat | 2 | 90.1 |
| Claude (alone) | door hold, melee on the plug and diagonals, plug rotation | Ithfunda east room | **repelled** (fled t10419) | 2 dead (one bled out after the raid left), 2 downed | **50.0** |

## Scenes (Claude; trace ticks)
- **t8076–8797** `mouth-hold`: the raid queued in the corridor; raiders died in the doorway one at a
  time; the axis cells took arrows; the plug at 45 %.
- **t8797–10011** `rotation`: plug swapped twice; Gnugfur died on the plug within ~200 ticks; Val and
  Binx downed on the front cells; the empty plug cell stayed covered from three sides.
- **t10367**: the raid fled with 9 dead and more downed. Val bled to death in the corridor afterwards.

## What the play stood on (Claude's reasons)
- base_ith_tribe_2x's door hold against a bigger tribal raid; rotation when the plug fell below ~50 %.
