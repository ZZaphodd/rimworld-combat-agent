# base2_caw_staircase · civil outlanders ×8 vs a raid that grows after each win · Cawalia Union base v2

**Situation:** `base-arena` `raid-far` `traps-many` `turrets`
**Numbers:** ours 8 (OutlanderCivil, 500 pt) · raid 500 pt × the staircase's multiplier, the kind rotating
tribe / pirate / mech · base `arena_col_cawalia2` (275×275 open ground; 1,421 spike traps: a ring round the
map edge and arcs ~50 cells out, the north arc z 190–199, x 90–199; 13 powered sniper turrets ("uranium
slug turret", minimum range 12, 30 shots before rearming) and 7 mini-turrets; squad start (100, 108))

The user's design (2026-10-08): Claude plays every battle directly, moving so the raid walks over trap
fields; +0.5× after a win, −0.5× after a loss; spike traps left is the second measure (a loss with many
traps left reads as too little maneuvering). State: `results/base/cawalia_staircase.jsonl`
(`tools/cawalia.py show`). Tick cap 30,000; 60,000 for mech battles from battle 14 (the user; asked after battles 12–13, which
Claude first reported as reaching 30,000 — they were stopped at t29529 by a storyteller raid). From
battle 22 the storyteller's arrivals are removed and the battle plays on (`--remove-intruders`).
From battle 25 new builds carry 2 days of survival meals by the squad's start (the user). From battle 15 the step comes from a sliding window of the last 6
counted battles (2 per raid kind): more wins → up 0.5×, more losses → down, a tie → hold (the user).

## Battles
| n | multiplier | raid | play | result | lost / downed | traps used | badness |
|---|---|---|---|---|---|---|---|
| 1 | 2× | 16 tribal archers (bows, greatbows, pila) from the north edge | rifles to the best shooters; a line south of the north arc (z 160) so the archers' firing cells lay beyond the arc; kite back when one came within 22 (`arc-lure`) | **repelled** (fled t1932) | 0 / 0 | 20 | **0.7** |
| 2 | 2.5× | 10 pirates (4 sniper rifles, a triple rocket launcher) from the south edge | rifles to the sh 4–5 shooters; a rifle line at z 104 behind the south turrets (z 98), short guns at z 111 | **repelled** (fled t1495) | 0 / 0 | 20 | **0.0** |
| 3 | 3× | 10 mechs (4 Pikemen, 4 Lancers, 2 Scythers) from the NE corner | waited out a ~13,000-tick gathering (two broke); bait north of the arc, back across it to the north turrets; rifles from just outside the Lancers' reach (34–35) on the idle ones | **decisive** | 0 / 0 | 4 | **2.4** |
| 4 | 3.5× | 30 tribals (~18 bows and pila, 12 melee) from the west edge | rifles to the two sh 4–15 with autopistols; a line just north of the SW patch, back south across it when the melee came | **repelled** (fled t3237) | 0 / 0 | 39 | **0.0** |
| 5 | 4× | 16 pirates (2 doomsday + 1 triple rocket launcher, minigun, 2 snipers, chain shotguns, grenadiers) from the south edge | rifles to the sh 3–18 with short guns; line behind the south turrets, 10 apart, then back to the block's south wall; focus on the two that walked in | **repelled** (fled t3003) | 0 / 0 | 30 | **0.7** |
| 6 | 4.5× | 8 mechs (2 Centurions, 3 Centipede blasters, 2 Lancers, a Pikeman) from the SE corner | line behind the south turrets; a 3-pawn poke from north of the arc; waited out the gathering (~12,000 ticks); kited back at 28 and focused the Centurions | **decisive** | 1 / 0 | 18 | **15.0** |
| 7 | 5× | 45 tribals (31 bows and pila, 13 melee) from the NW corner | a column south of the north arc's east part, then a row north of the arc (z 212) | **repelled** (fled t4383) | 0 / 0 | 43 | **0.0** |
| 8 | 5.5× | 21 pirates (3 doomsday + 1 triple rocket launcher, 4 chain shotguns, 4 assault rifles, LMG, minigun, incinerator) from the NW corner | rifles to the sh 5–9 with short guns; a line south of the north arc, then north of it (z 226), 8 apart | **repelled** (fled t5924) | 0 / 0 | 26 | **0.0** |
| 9 | 6× | 12 mechs (4 Centipede blasters, 3 Lancers, 3 Scythers, a Centurion, a Pikeman) from the west edge | a column north of the north arc through the gathering and assault; rifles to ~32–35 of the last three (outside their reach) | **decisive** | 0 / 0 | 26 | **0.0** |
| 10 | 6.5× | 61 tribal melee from the SW corner | a group north of the south arc; a zigzag across the arc when a raider came within 22 (re-sent every 20 ticks: the group turned back and forth in the band and was caught); then stood and shot point blank | **repelled** (fled t4008) | 1 / 2 | 66 | **26.0** |
| 11 | 7× | 26 pirate melee (21 slashers with shield belts) from the SW corner | rifles to the sh 7–10 with short guns; the zigzag across the south arc, each crossing after the last had arrived | **repelled** (fled t2546) | 0 / 0 | 32 | **0.0** |
| 12 | 7.5× | 15 mechs (7 Scythers, 5 Centipede blasters, 2 Lancers, a Centurion) from the NE corner | parked far south; the turrets took 14; five rifles walked ~130 cells to the last Centipede and backed off every 30 ticks | **invalid** (a storyteller raid at t29529; not counted) | 0 / 0 | 30 | 5.8 |
| 13 | 7.5× | the same | undrafted through the gathering; a leash along the arc's north side, then turrets at the block's north wall; stood at 28.5 from the last Centipede | **invalid** (the same storyteller raid at t29529; not counted) | 1 / 2 | 38 | 32.2 |
| 14 | 7.5× | the same (cap 60,000) | killed all seven Scythers near the south turrets; the rest kited south and west; downed pawns left untended | **conceded** (a loss; squad down t47655) | 4 / 3 | 54 | 83.2 |
| 15 | 8× | 67 tribal archers from the north edge | a line just behind the north turrets, the block's north wall behind it; rifles on whoever came within 26 | **repelled** (fled t3501) | 0 / 0 | 69 | **0.0** |
| 16 | 8.5× | 34 pirates (8 sniper rifles, 3 triple rocket launchers, 2 incendiary launchers, LMGs, miniguns) from the west edge | rifles to the sh 7–17 with a knife and a revolver; the squad inside the block's east room, out of the snipers' sight | **repelled** (fled t5528) | 0 / 0 | 70 | **0.0** |
| 17 | 9× | 21 mechs (13 Lancers, 3 Pikemen, 3 Diabolus, a Cyclops, a Scorcher) from the north edge | the squad in the block's east room through the assault; then the Pikeman from 33 and the Lancers from 34–36 | **decisive** | 0 / 0 | 42 | **0.0** |
| 18 | 9.5× | 76 tribal archers from the SE corner | good rifles to the sh 4–5; a line behind the south turrets, then the block's east room when the archers reached 28 | **repelled** (fled t3987) | 0 / 0 | 63 | **0.0** |
| 19 | 10× | 44 pirates (7 sniper rifles, 3 rocket launchers, miniguns, shotguns, EMP, incinerator) from the SE corner | rifles to the sh 12–13 with short guns; the squad in the block's east room from the start | **repelled** (fled t5459) | 0 / 0 | 58 | **0.0** |
| 20 | 10.5× | 16 mechs (8 Centipede blasters, 5 Lancers, a War queen, a Scyther, a Scorcher) from the south edge | the east room, out north at the assault; the last three from 31–38 | **invalid** (the War queen's urchins counted as intruders; fixed) | 0 / 0 | 25 | — |
| 21 | 10.5× | the same | the same | **invalid** (a storyteller raid at t29529) | 0 / 0 | 30 | — |
| 22 | 10.5× | the same (storyteller arrivals removed) | the east room, then most of the squad north of the block; the last three Centipedes from 28–34 | **decisive** | 0 / 1 | 33 | **10.0** |
| 23 | 11× | 82 tribals (61 bows and pila, 21 melee) from the west edge | the squad in the block's east room (two rifles lost in a failed swap) | **repelled** (fled t3922) | 0 / 0 | 76 | **0.0** |
| 24 | 11.5× | 42 pirate melee (and an assault rifle) from the south edge | rifles to the sh 6–13; the zigzag across the south arc (seven crossings) | **repelled** (fled t3684) | 0 / 0 | 66 | **0.0** |
| 25 | 12× | 40 Scythers from the east edge | the zigzag across the south arc (Scythers kept pace), then a stand under the south turrets | **conceded** (7 lost; timeout t60095) | 7 / 0 | 72 | 101.0 |
| 26 | 12.5× | 112 tribal melee from the north edge | the zigzag spot taken by the raid first; back to the block's north wall under the turrets, then the north room | **pyrrhic** (fled t4619) | 0 / 5 | 134 | 44.6 |

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
- **4 · t0–1860**: the raid went NE across the trap wedge (41–51, 89–107) for the west turrets and field
  buildings (19 traps, 7 out by t1139; 12 by t1829), not for the line 60 cells south.
- **4 · t1860–3240** `arc-lure`: the line north of the SW patch (z 79) drew three melee and the archers;
  back south across the patch to z 63; the raid fled at t3237 with 17 of 30 out; 15 more traps on its way
  out west.
- **5 · t0–3003**: the pirates crossed the south arc for the turret (176, 98) (20 traps); two marine-armoured
  shotgunners took cells inside the turret (154, 98)'s minimum range; both rocket launchers were spent on
  the turrets and the field; the line, back at the block's south wall, shot the two that walked in. Fled at
  t3003 with 10 of 16 out; all 13 turrets stood.
- **6 · t0–13000**: the mechs gathered south of the arc's east end; a poke from north of the arc pulled
  them 12–20 cells north and back; moods fell 46 → 30 while waiting (no break).
- **6 · t13000–19414**: the assault crossed the arc's east end for the turret (176, 98) (15 traps); Lancers
  and Pikeman out to the turrets; the Centurions felled that turret from inside its minimum range;
  Suhanmoo shot dead at 29.2 cells from a Centurion on a melee job (its own turret gun, likely) while the
  line kited at 28.
- **7 · t0–4383**: the raid went for the NW field, the west turret (73, 136) and the north turret
  (110, 152), never toward the line (57+ away); 25 of 45 out or down to the turrets and traps (26 traps
  by t3456, 43 in all); fled at t4383. The line fired no shot.
- **8 · t0–5924**: the pirates went for the NW field, the west turrets and the north turret (110, 152),
  never toward the line (37+ away); 16 of 21 out to the turrets and traps; three fled north across the
  arc. The line fired no shot.
- **9 · t0–21435**: the mechs gathered west of the arc for ~10,000 ticks (moods 49 → 16–28; two broke
  later); the assault took four turrets west and north of the block ((73, 136), (110, 152), (132, 152),
  (73, 114)) and lost 9 of 12 there; the rifles finished the Centurion and two Centipedes from 32–35.
- **10 · t1370–4255**: 61 melee; the rifles thinned the front from z 66 (15 out by t1841); the zigzag
  controller re-sent its crossing every 20 ticks, so the group stayed in the band and six raiders reached
  it (Prokop dead, two down); 66 traps used, the most so far; the raid fled at t4008.
- **11 · t1541–2748** `arc-lure`: four crossings of the south arc with the shield-belted slashers 16–30
  behind; 15 of 26 out by t2466 (turrets and traps); fled at t2546. No hit taken.
- **12–13 · mech 7.5×**: the turrets took 13–14 of 15, then ran out of slugs (60 uranium on the map, one
  rearm); the last Centipede blasters stood far NW out of any loaded turret's reach; bolt-action rifles
  barely scratched them (~1 % per 250 ticks for three); both runs were stopped at t29529 by a
  storyteller raid (invalid), first reported as the 30,000-tick cap. The second
  cost Mad (a Centipede stepped 3 cells into range of the rifles at 28.5).
- **14 · mech 7.5× (cap 60,000)**: the Scythers died to the rifles near the south turrets, but breaks sent
  two pawns wandering into the mechs, three downed pawns bled out untended over ~10,000–20,000 ticks,
  and two full-health Centipedes plus the Centurion were left with the turrets dry; conceded.
- **15 · t0–3501** `arc-lure`: 67 archers crossed the north arc into four full turrets (49 traps by
  t1686, 69 in all, the most so far); the line behind the turrets took no hit; fled at t3501.
- **16 · t0–9093**: the squad sheltered in the block's east room; the raid spent itself on the NW
  field, the west and north turrets and the block's west side (70 traps, the most so far); fled at
  t5528.
- **17 · t0–27868**: the squad sheltered in the block's east room while the assault crossed the north arc
  and took the north turrets; 18 of 21 out to turrets and traps; the last three (a Pikeman, two idle
  Lancers) shot from just outside their reach. No hit taken.
- **18 · t0–3987**: 76 archers crossed the south arc's east end into the south turrets (43 traps by
  t1306); the squad went into the east room as they reached 28 of the line; one broke at its door; fled
  at t3987 with 46 out. No hit taken.
- **19 · t0–5459**: the squad in the east room from the start; the raid crossed the south arc's
  east end into the south and east turrets (58 traps); fled with 30 of 44 out. No hit taken.
- **20–22 · mech 10.5×**: the War queen's urchins first ended a run as "intruders" (fixed), a storyteller
  raid at t29529 the next (now removed); the third won: the turrets took the War queen and all but three
  Centipedes, finished by the rifles from just outside their reach at t42415. The squad, drafted for
  ~40,000 ticks, was starving (food 3–4 %) by the end.
- **23 · t0–3922**: 82 tribals spent themselves on the west field, the west and north turrets and 76
  traps while the squad sat in the east room; fled with 50 out. No hit taken.
- **24 · t1041–7039** `arc-lure`: the zigzag across the south arc against 41 melee pirates: 40 out over
  seven crossings, 66 traps; no hit taken.
- **25 · mech 12×**: 40 Scythers; 18 fell to traps and turrets before reaching the group; the zigzag
  could not open distance from Scythers (as fast as the pawns), three pawns broke, and the rest went down
  one by one; 38 of 40 Scythers out by the cap; conceded with 7 lost.
- **26 · tribe 12.5×**: 112 melee crossed the north arc (73 traps in the first 1,500 ticks, 134 in all)
  and reached the planned kite spot before the squad; fire orders stopped three pawns mid-retreat; five
  down, none dead; the raid broke on the north turrets and the block's north room.
