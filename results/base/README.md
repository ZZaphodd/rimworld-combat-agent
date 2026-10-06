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
step 8).
- Arenas: `arena_col_ithfunda2` and `arena_col_monler2` are the same bases without that
  furniture, indoors and out.
- Problems: the same 30 specs were rebuilt as `base2_*` (`scenarios_base2/`). 29 were built;
  Monler mechanoid 6× loitered in all three builds, as in v1.
- Rebuilding drew new raids and new squads: a v1 rung and its v2 rung share the points, not the
  pawns.
- Runs: `turtle`, one run per rung, rows in `ladder2.jsonl`.

v1 → v2 (– not run: two defeats below; bold: the grade went up):

| base | raid | 2× | 3× | 4× | 6× | 8× |
|---|---|---|---|---|---|---|
| Ithfunda | tribe | defeat 109.7 → **repelled 20.1** | defeat 100.1 → defeat 129.1 | – → defeat 140.2 | – | – |
| Ithfunda | pirate | defeat 57.4 → defeat 103.1 | defeat 124.4 → defeat 62.1 | – | – | – |
| Ithfunda | mech | pyrrhic 90.3 → **decisive 28.1** | (not built) → defeat 91.2 | defeat 97.8 → defeat 113.5 | defeat 133.3 → – | (not built) → – |
| Monler | tribe | repelled 20.0 → repelled 5.2 | defeat 69.8 → **repelled 10.5** | defeat 89.8 → defeat 149.6 | – → defeat 88.0 | – |
| Monler | pirate | repelled 29.9 → repelled 24.4 | unresolved 72.4 → defeat 77.7 | repelled 0.8 → pyrrhic 84.9 | defeat 107.0 → defeat 134.8 | defeat 78.8 → defeat 172.4 |
| Monler | mech | defeat 85.4 → defeat 68.6 | (not built) → defeat 123.5 | defeat 86.9 → – | (not built) | – |

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

## Direct plays: Claude and the user (PROCEDURES §15–16)
Scope (the user, 2026-10-06): win the battle using the base, by any method; furniture that takes
firing cells is uninstalled (PROCEDURES §1c). Claude, and at times the user, plays the rungs where `turtle` first lost (rows in `results/human/play.jsonl`;
journals and cards in `results/cases/`).

| problem | turtle | direct play | play |
|---|---|---|---|
| base_ith_pirate_2x | defeat 57.4 | Claude: **repelled 12.3** (attempt 2; attempt 1 discarded) | the east room's door ([card](../cases/cards/base_ith_pirate_2x.md)); 7 of the 20 raider deaths were the colony's spike traps (turtle's row has 6 inferred kills and no trace, so its trap deaths are not known) |
| base_ith_tribe_2x | defeat 109.7 | Claude: **decisive 4.8** | the same door, melee pawns on its two diagonal cells too ([card](../cases/cards/base_ith_tribe_2x.md)); 3 raiders died away from us on the stretches where the pirates died on spike traps, and 1 lost health on one (z 122) and went down further east at (186, 110) |
| base_mon_tribe_3x | defeat 69.8 | (Claude's run discarded) · **the user: repelled 1.9** (attempt 2; attempt 1 discarded) | room R2 at the end of the straight passage x 145, cleared of benches, all eight within 3 cells of the door (Philly away t10513–11242), frags on an area order up the passage ([card](../cases/cards/base_mon_tribe_3x.md)) |
