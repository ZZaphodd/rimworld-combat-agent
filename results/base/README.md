# Base-defense ladder (2026-10-06)

How many times our points a colony base holds against (the user's request; PROCEDURES §1c).
- Bases: `arena_col_ithfunda` and `arena_col_monler`, made from two of the user's colonies.
  - Kept: buildings (walls, doors, traps, generators).
  - Cleared: every item but chunks.
  - Storyteller: Phoebe, Strive to Survive. No mortars on either side.
- Ours: OutlanderCivil 500 points (7–10 pawns), placed in the base's yard.
- Raids: tribe, pirate and mechanoid at 2, 3, 4, 6 and 8 times our points.
  - Tribe and pirate raids: `ImmediateAttack`. Mechanoid raids: `StageThenAttack`.
  - Mechanoid 3× and 8× (Ithfunda) and 3× and 6× (Monler) loitered in all three builds and are
    not in the ladder yet.
- Agent: `turtle` (holds the start and fires), one run per rung, via `tools/base_ladder.py`.
  - A ladder stops after two defeats in a row.
- Rows: `ladder.jsonl` (tools/night.py rows plus router and badness).

| base | raid | 2× | 3× | 4× | 6× | 8× |
|---|---|---|---|---|---|---|
| Ithfunda | tribe | defeat 109.7 | defeat 100.1 | – | – | – |
| Ithfunda | pirate | defeat 57.4 | defeat 124.4 | – | – | – |
| Ithfunda | mech | pyrrhic 90.3 | (not built) | defeat 97.8 | defeat 133.3 | (not built) |
| Monler | tribe | **repelled 20.0** | defeat 69.8 | defeat 89.8 | – | – |
| Monler | pirate | **repelled 29.9** | unresolved 72.4 | **repelled 0.8** | defeat 107.0 | defeat 78.8 |
| Monler | mech | defeat 85.4 | (not built) | defeat 86.9 | (not built) | – |

Raid sizes (our pawns / raiders), from the manifests:

| base | raid | 2× | 3× | 4× | 6× | 8× |
|---|---|---|---|---|---|---|
| Ithfunda | tribe | 8 / 10 | 9 / 17 | 8 / 22 | 8 / 35 | 8 / 42 |
| Ithfunda | pirate | 8 / 25 | 9 / 13 | 9 / 16 | 9 / 25 | 7 / 34 |
| Ithfunda | mech | 9 / 6 | – | 9 / 13 | 9 / 16 | – |
| Monler | tribe | 8 / 18 | 8 / 27 | 8 / 36 | 8 / 54 | 8 / 63 |
| Monler | pirate | 8 / 13 | 8 / 13 | 8 / 14 | 8 / 24 | 8 / 34 |
| Monler | mech | 8 / 22 | – | 9 / 11 | – | 9 / 20 |

## Observations
- With `turtle`, Ithfunda fell at the lowest rung for tribe and pirate raids. Monler held 2× for
  both, and pirates also at 4×.
- The rungs are not monotone in size or result:
  - The same points bought different raids. Ithfunda pirates were 25 at 2× and 13 at 3×; Monler
    mechs were 22 at 2× and 11 at 4×.
  - Monler pirates at 4× were repelled with almost no damage (badness 0.8), after 3× ran out of
    time.
- One run per rung: a single draw each.
- `turtle` stands in the yard and does not use the rooms, doors or valleys. These rows are a
  baseline for play that does.

## v2: without shelves, hydroponics basins and workbenches (2026-10-06)
The user saw the v1 raids spend the battles wrecking the colony's furniture (PROCEDURES §1c
step 8). The user's judgment: v2 is the fair measurement of a battle, and the v1 rows, run with
the colony's stockpile shelves still standing, are contaminated.
- Arenas: `arena_col_ithfunda2` and `arena_col_monler2` are the same bases without that
  furniture, indoors and out.
- Problems: the same 30 specs were rebuilt as `base2_*` (`scenarios_base2/`). 29 were built;
  Monler mechanoid 6× loitered in all three builds, as in v1.
- Rebuilding drew new raids and new squads: a v1 rung and its v2 rung share the points, not the
  pawns.
- Runs: `turtle`, one run per rung, rows in `ladder2.jsonl`.

v1 → v2, the first v2 pass (– not run: two defeats below; bold: the grade went up; the Monler v2
cells ran with the solar flare, rows in `ladder2_monler_flare.jsonl`):

| base | raid | 2× | 3× | 4× | 6× | 8× |
|---|---|---|---|---|---|---|
| Ithfunda | tribe | defeat 109.7 → **repelled 20.1** | defeat 100.1 → defeat 129.1 | – → defeat 140.2 | – | – |
| Ithfunda | pirate | defeat 57.4 → defeat 103.1 | defeat 124.4 → defeat 62.1 | – | – | – |
| Ithfunda | mech | pyrrhic 90.3 → **decisive 28.1** | (not built) → defeat 91.2 | defeat 97.8 → defeat 113.5 | defeat 133.3 → – | (not built) → – |
| Monler | tribe | repelled 20.0 → repelled 5.2 | defeat 69.8 → **repelled 10.5** | defeat 89.8 → defeat 149.6 | – → defeat 88.0 | – |
| Monler | pirate | repelled 29.9 → repelled 24.4 | unresolved 72.4 → defeat 77.7 | repelled 0.8 → pyrrhic 84.9 | defeat 107.0 → defeat 134.8 | defeat 78.8 → defeat 172.4 |
| Monler | mech | defeat 85.4 → defeat 68.6 | (not built) → defeat 123.5 | defeat 86.9 → – | (not built) | – |

Monler's colony was saved during a solar flare (13,972 ticks from tick 19,852,000), so every
Monler battle above, v1 and v2, started under it with the base's power off (its four autodoors,
lights) for about the first 12,500 ticks ("The solar flare is ending." in 9 v1 and 5 v2 rows).
The user, 2026-10-07: remove it. It was removed from `arena_col_monler2` and its 14 v2 scenario
saves (`tools/make_base_arena.py --clear-conditions SolarFlare`, originals backed up outside the
Saves folder). The 11 Monler turtle v2 rows moved to `ladder2_monler_flare.jsonl`; turtle reruns
those rungs on the saves without the flare (in the turtle_at section below).

Raid sizes v1 → v2 (our pawns / raiders):

| base | raid | 2× | 3× | 4× | 6× | 8× |
|---|---|---|---|---|---|---|
| Ithfunda | tribe | 8/10 → 9/10 | 9/17 → 8/18 | 8/22 → 8/24 | 8/35 → 8/34 | 8/42 → 9/46 |
| Ithfunda | pirate | 8/25 → 8/11 | 9/13 → 9/13 | 9/16 → 8/19 | 9/25 → 8/26 | 7/34 → 7/35 |
| Ithfunda | mech | 9/6 → 9/6 | – → 7/10 | 9/13 → 8/14 | 9/16 → 9/7 | – → 8/13 |
| Monler | tribe | 8/18 → 9/17 | 8/27 → 8/25 | 8/36 → 7/38 | 8/54 → 8/50 | 8/63 → 9/66 |
| Monler | pirate | 8/13 → 9/11 | 8/13 → 8/13 | 8/14 → 9/15 | 8/24 → 8/28 | 8/34 → 9/30 |
| Monler | mech | 8/22 → 9/22 | – → 9/11 | 9/11 → 9/13 | – | 9/20 → 9/20 |

Observations:
- 15 rungs ran in both ladders.
  - The grade went up on 3: Ithfunda tribe 2× and mech 2×, Monler tribe 3×.
  - It went down on 2: Monler pirate 3× (unresolved → defeat) and 4× (repelled → pyrrhic).
  - It stayed the same on 10.
- v2 battles ended sooner on 10 of the 15 (ticks to the row's end).
  - Monler tribe 2×: 16871 → 9474. Ithfunda tribe 2×: 12459 → 8501.
  - The largest change went the other way: Monler pirate 4×, 10060 → 22754.
- A change can come from the furniture or from the new draw: one run per rung does not separate
  them.
  - For example, Ithfunda pirates 2× were 25 raiders in v1 and 11 in v2, and v2 went worse
    (badness 103.1 against 57.4).
- The direct plays below are on the v1 arenas.

## turtle at the strategic layer's pick: `turtle_at` with plan `base2_r1` (2026-10-07)
The user: v2 is the fair measurement, and even turtle needs the strategic layer to mark where to
hold (PROCEDURES §1c).
- Picks: Claude, by hand, from start information only (`results/base/plans/base2_r1.json`):
  - every Ithfunda problem holds the east room behind its door (133, 187);
  - every Monler problem holds R2 behind (145, 84), with the passage doors held open (the user's
    attempt-2 layout);
  - front cells (the plug and the doorway's diagonals) go to knives, then throwers with fire held,
    then the weakest guns; the best guns sit on the corridor axis 2 cells back.
- Agent `turtle_at` v1 (turtle v9 at the pick; in the room no sally and no attack orders that
  walk: `rca/tactical/turtle_at.py`), rows in `ladder2_turtle_at.jsonl`.
- Baseline: turtle v9 on the same 29 problems (`ladder2.jsonl`): the 8 Ithfunda rows of the first
  v2 pass (2026-10-06) and 21 rows from 2026-10-07 (`--all-rungs`: the rungs the first pass
  skipped, and every Monler rung again on the saves without the solar flare).
- One run per problem on each side.

Grade and badness as recorded, turtle → turtle_at (bold: the grade went up); ours lost (dead or
kidnapped: the rows' `deaths`); raiders killed (incl. inferred) of those seen. The recorded badness
counts a kidnapped pawn twice (`rca/eval/ranking.lost` adds `squad_kidnapped` to `deaths`, which
already holds it; found 2026-10-07); the observations give both.

| base | raid | rung | turtle | turtle_at | ours lost | raiders killed |
|---|---|---|---|---|---|---|
| Ithfunda | tribe | 2× | repelled 20.1 | **decisive 7.0** | 0 → 0 | 7 → 10 of 10 |
| Ithfunda | tribe | 3× | defeat 129.1 | defeat 90.1 | 3 → 2 | 4 → 10 of 18 |
| Ithfunda | tribe | 4× | defeat 140.2 | defeat 63.5 | 5 → 1 | 4 → 14 of 24 |
| Ithfunda | tribe | 6× | defeat 119.3 | defeat 73.2 | 5 → 2 | 2 → 15 of 34 |
| Ithfunda | tribe | 8× | defeat 89.1 | defeat 75.4 | 2 → 1 | 2 → 13 of 46 |
| Ithfunda | pirate | 2× | defeat 103.1 | defeat 40.8 | 2 → 1 | 3 → 7 of 11 |
| Ithfunda | pirate | 3× | defeat 62.1 | **repelled 26.2** | 0 → 1 | 3 → 4 of 13 |
| Ithfunda | pirate | 4× | unresolved 64.5 | defeat 122.0 | 2 → 8 | 4 → 13 of 19 |
| Ithfunda | pirate | 6× | defeat 106.9 | defeat 93.3 | 5 → 4 | 3 → 10 of 26 |
| Ithfunda | pirate | 8× | defeat 84.8 | defeat 78.2 | 3 → 2 | 3 → 5 of 35 |
| Ithfunda | mech | 2× | decisive 28.1 | decisive 2.1 | 0 → 0 | 6 → 6 of 6 |
| Ithfunda | mech | 3× | defeat 91.2 | defeat 93.6 | 3 → 3 | 1 → 8 of 10 |
| Ithfunda | mech | 4× | defeat 113.5 | **unresolved 34.4** | 7 → 2 | 4 → 11 of 14 |
| Ithfunda | mech | 6× | defeat 120.6 | **unresolved 7.0** | 7 → 0 | 0 → 0 of 7 |
| Ithfunda | mech | 8× | defeat 100.3 | **unresolved 53.0** | 5 → 0 | 0 → 0 of 13 |
| Monler | tribe | 2× | repelled 8.0 | repelled 7.1 | 0 → 0 | 9 → 8 of 17 |
| Monler | tribe | 3× | repelled 15.9 | unresolved 17.6 | 0 → 1 | 12 → 14 of 25 |
| Monler | tribe | 4× | defeat 86.4 | **repelled 22.0** | 1 → 0 | 11 → 13 of 38 |
| Monler | tribe | 6× | defeat 99.4 | **repelled 23.3** | 3 → 0 | 10 → 25 of 50 |
| Monler | tribe | 8× | defeat 179.0 | defeat 78.4 | 7 → 1 | 11 → 18 of 66 |
| Monler | pirate | 2× | repelled 22.2 | defeat 57.0 | 0 → 0 | 4 → 7 of 11 |
| Monler | pirate | 3× | defeat 107.5 | defeat 90.4 | 4 → 4 | 5 → 3 of 13 |
| Monler | pirate | 4× | repelled 0.0 | repelled 38.0 | 0 → 2 | 8 → 8 of 15 |
| Monler | pirate | 6× | defeat 169.6 | defeat 143.3 | 6 → 7 | 6 → 10 of 28 |
| Monler | pirate | 8× | defeat 115.5 | defeat 108.5 | 4 → 0 | 7 → 7 of 30 |
| Monler | mech | 2× | defeat 85.8 | **decisive 12.1** | 3 → 0 | 12 → 22 of 22 |
| Monler | mech | 3× | defeat 103.4 | **decisive 25.2** | 3 → 1 | 6 → 11 of 11 |
| Monler | mech | 4× | defeat 94.3 | **decisive 9.4** | 2 → 0 | 4 → 13 of 13 |
| Monler | mech | 8× | defeat 127.4 | defeat 110.5 | 6 → 6 | 4 → 8 of 20 |

Observations:
- Badness was lower with turtle_at on 24 of the 29 problems as recorded (mean 89.2 → 55.3); with
  each kidnapped pawn counted once, on 22 (mean 79.6 → 52.5: Monler pirate 3× and 8× turn the
  other way).
  - Grades: up on 10, down on 3, the same on 16.
  - Ours lost (dead or kidnapped): 88 → 49 in total, of them kidnapped 28 → 8. Raiders killed:
    155 → 293.
- Monler mechanoids 2×, 3× and 4× went from defeat to decisive, all 22, 11 and 13 mechs killed.
- Four rows timed out at 30,000 ticks (unresolved): turtle_at does not sally.
  - Ithfunda mech 6× (7 centipedes) never came to the room. Mech 8× (6 centipede blasters and
    escorts) reached the doorway only from tick 25,622; 5 of ours were downed at the end. In both
    none of ours and none of theirs died; turtle met them in the yard and lost 7 and 5.
  - Ithfunda mech 4×: 11 of 14 killed when time ran out.
  - Monler tribe 3×: the raid fled at tick 9107 and one raider stayed active to the limit.
  - turtle's sally rule would have fired in 26 of the 29 turtle_at rows (recorded, not acted on).
- The grade went down on 3:
  - Ithfunda pirate 4×: all 8 of ours died (turtle lost 2).
  - Monler pirate 2×: all 9 of ours were downed, none died. A pawn went on a fire starting spree
    in the room and the squad was burned by superheated air.
  - Monler tribe 3×: the timeout above (repelled 15.9 → unresolved 17.6).
- Battles were longer: median 19,220 ticks against turtle's 12,542. turtle_at's first shot came at
  a median tick of 5,877.
  - Mental breaks showed up in 4 turtle_at battles (sad wander in Ithfunda mech 2×, an insulting
    spree in Ithfunda pirate 2×, the fire starting spree above, sad wander and an ambrosia binge in
    Monler tribe 3×) and in 2 of turtle's (sad wander in Ithfunda mech 2× and Monler tribe 2×).
- Every plan door was set (Hold open read and pressed only to change it); no agent errors, no
  invalid rows.

## Direct plays: Claude and the user (PROCEDURES §15–16)
Scope (the user, 2026-10-06): win the battle using the base, by any method; furniture that takes
firing cells is uninstalled (PROCEDURES §1c). Claude, and at times the user, plays the rungs where `turtle` first lost (rows in `results/human/play.jsonl`;
journals and cards in `results/cases/`).

| problem | turtle | direct play | play |
|---|---|---|---|
| base_ith_pirate_2x | defeat 57.4 | Claude: **repelled 12.3** (attempt 2; attempt 1 discarded) | the east room's door ([card](../cases/cards/base_ith_pirate_2x.md)); 7 of the 20 raider deaths were the colony's spike traps (turtle's row has 6 inferred kills and no trace, so its trap deaths are not known) |
| base_ith_tribe_2x | defeat 109.7 | Claude: **decisive 4.8** | the same door, melee pawns on its two diagonal cells too ([card](../cases/cards/base_ith_tribe_2x.md)); 3 raiders died away from us on the stretches where the pirates died on spike traps, and 1 lost health on one (z 122) and went down further east at (186, 110) |
| base_mon_tribe_3x | defeat 69.8 | (Claude's run discarded) · **the user: repelled 1.9** (attempt 2; attempt 1 discarded) | room R2 at the end of the straight passage x 145, cleared of benches, all eight within 3 cells of the door (Philly away t10513–11242), frags on an area order up the passage ([card](../cases/cards/base_mon_tribe_3x.md)) |
