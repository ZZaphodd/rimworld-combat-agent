# base2_caw_staircase · civil outlanders ×8 vs a raid that grows after each win · Cawalia Union base v2

**Situation:** `base-arena` `raid-far` `traps-many` `turrets`
**Numbers:** ours 8 (OutlanderCivil, 500 pt) · raid 500 pt × the staircase's multiplier, the kind rotating
tribe / pirate / mech · base `arena_col_cawalia2` (275×275 open ground; 1,421 spike traps: a ring round the
map edge and arcs ~50 cells out, the north arc z 190–199, x 90–199; 13 powered sniper turrets ("uranium
slug turret", minimum range 12, 30 shots before rearming) and 7 mini-turrets; squad start (100, 108))

The user's design (2026-10-08): Claude plays every battle directly, moving so the raid walks over trap
fields; +0.5× after a win, −0.5× after a loss; spike traps left is the second measure (a loss with many
traps left reads as too little maneuvering). State: `results/base/cawalia_staircase.jsonl`
(`tools/cawalia.py show`).

## Battles
| n | multiplier | raid | play | result | lost / downed | traps used | badness |
|---|---|---|---|---|---|---|---|
| 1 | 2× | 16 tribal archers (bows, greatbows, pila) from the north edge | rifles to the best shooters; a line south of the north arc (z 160) so the archers' firing cells lay beyond the arc; kite back when one came within 22 (`arc-lure`) | **repelled** (fled t1932) | 0 / 0 | 20 | **0.7** |
| 2 | 2.5× | 10 pirates (4 sniper rifles, a triple rocket launcher) from the south edge | rifles to the sh 4–5 shooters; a rifle line at z 104 behind the south turrets (z 98), short guns at z 111 | **repelled** (fled t1495) | 0 / 0 | 20 | **0.0** |
| 3 | 3× | 10 mechs (4 Pikemen, 4 Lancers, 2 Scythers) from the NE corner | waited out a ~13,000-tick gathering (two broke); bait north of the arc, back across it to the north turrets; rifles from just outside the Lancers' reach (34–35) on the idle ones | **decisive** | 0 / 0 | 4 | **2.4** |

## Scenes
- **1 · t0–1450**: the archers wrecked the north fields (a ship casket, lamps) and walked south; the line
  formed at z 160 as they reached the arc. 4 out by t1452, 11 traps used crossing the edge ring and the arc.
- **1 · t1450–2350** `kite`: four archers crossed the arc to firing cells ~10 cells past it (151–169,
  171–180), inside the north sniper turrets' reach (z 152) and the rifles'; the line stepped back twice
  (z 160 → 154). The raid fled at t1932 with 11 of 16 out; the fleeing crossed the edge ring again.
- **2 · t0–1495**: the pirates spread over the south field wrecking buildings, crossed the edge ring
  (6 traps) and walked into the south arc; six out at z 47–54 under the south turrets (range 46 against
  the sniper rifles' 44.9); fled at t1495. None came within 50 cells of the line; it fired no shot.
- **3 · t0–13000**: the mechs gathered at (228–239, 203–215) for ~13,000 ticks; two of ours broke while
  waiting drafted (moods 18–28).
- **3 · t13000–21664**: the mechs went for the NE buildings and turrets; five out to the turrets (191, 136)
  and (176, 152), the rest one by one to the rifles from 34–35 cells (outside the charge lances' 32.9);
  idle mechs did not walk toward rifles shooting them from outside their range. 4 traps used.
