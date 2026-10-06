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

## Claude's plays (PROCEDURES §16)
Claude plays the rungs where `turtle` first lost, one run each (rows in `results/human/play.jsonl`;
journals and cards in `results/cases/`).

| problem | turtle | Claude | play |
|---|---|---|---|
| base_ith_pirate_2x | defeat 57.4 | **repelled 12.3** (attempt 2; attempt 1 discarded) | the east room's door ([card](../cases/cards/base_ith_pirate_2x.md)); 7 of the 20 raider deaths were the colony's spike traps (turtle's row has 6 inferred kills and no trace, so its trap deaths are not known) |
| base_ith_tribe_2x | defeat 109.7 | **decisive 4.8** | the same door, melee pawns on its two diagonal cells too ([card](../cases/cards/base_ith_tribe_2x.md)); 3 raiders died and 1 went down away from us, on the stretches where the pirates died on spike traps |
