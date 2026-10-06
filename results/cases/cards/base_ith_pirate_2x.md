# base_ith_pirate_2x · civil outlanders ×8 (guns + 3 throwers) vs 25 Waster melee · Ithfunda base — repelled

**Situation:** `base-arena` `raid-far` `raid-melee` `raid-outnumbers` `us-low-skill`
**Plays seen:** `mouth-hold` `rotation` `carry-downed` `molotov-into-group` (agent: `turtle`)
**Numbers:** ours 8 (shotgun, heavy SMG, revolver, 2 bolt-action rifles, frag, 2 molotov), 500 pt
· raid 25 Drifters (knives, clubs; no gun, no throwable), 1000 pt (2×) · count ratio 0.32 · raid
from the west edge (2–9, 87–102), ~110 cells · base `arena_col_ithfunda` (PROCEDURES §1c)

## Sides
- Ours (shooting/melee): Jahames 1/4 pump shotgun, flak vest; Haney 2/0 heavy SMG; Fumiko 4/0
  bolt-action rifle, flak pants (Tough); Leslie 2/0 bolt-action rifle, flak jacket; Park 0/1
  revolver, firefoam pack; Caitlin 3/3 frag; Susumu 4/2 and Christ 5/2 molotov. The base had no
  items, so no loadout.
- Raid: 25 Drifters; melee 13–15: John 15, Farik 14, Dani 13, Daichi 13 (Brawlers); Kolya 11.

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| agent `turtle` | hold the start and fire | the yard | defeat: squad down t5177, 9 of 25 out | 0 dead, 8 downed | 57.4 |
| Claude (alone), attempt 1 — discarded (compaction mid-battle) | door hold, guns 1–3 cells behind the plug | east room | stopped at t6663: 7 of 25 out, Jahames downed | – | – |
| Claude (alone), attempt 2 | door hold: one plug on the cell inside the doorway, guns 2+ cells back (from ~t9900), rotation, throws into the corridor queue | east room | **repelled** (t15403) | 0 (1 downed, 1 permanent) | **12.3** |

## Scenes (attempt 2)
- **t0–3636** `raid-wrecking`: the raid smashed and burned furniture across the base for ~3600
  ticks before the first raider came up the corridor; 3 died on the colony's spike traps on the
  way.
- **t3770–9601** `mouth-hold` `rotation`: one raider at a time in the doorway (133, 187):
  Dani, Furr, Svejgaard, Hairy, Koromaru, Kolya, Snuff dead there or just below it; Humberto
  downed in the corridor. Jahames (plug) 100 → 42% on the first two, swapped out with Furr still
  in the doorway. A ~2400-tick lull (t4378–6820) while the raid burned the yard.
- **t6994** `molotov-into-group` `fire`: three throws at once on a raider 4–5 cells below the plug;
  the corridor burned and the firefoam was spent.
- **~t9900**: the pawns next to the doorway raider had "Fire at …: Too close"; only Park, 2 cells
  back, had been shooting (Kolya sat at 20% for ~900 ticks). Guns moved 2+ cells back.
- **t10368** `our-downed` `carry-downed`: Leslie went down on the plug cell during a swap; Park
  carried her out (from the orthogonal cell; from the diagonal one the carry stalled).
- **t10984**: John (melee 15) stepped from the doorway diagonally past the rock corner into the
  room while the plug cell was held; with Evgeny he fought inside until ~t11860. Jahames down.
- **t11122** `raid-breaking`: the raid fled with 13–14 of 25 out; 4 fleeing raiders died on spike
  traps, 5 escaped.

## What the play stood on (observed)
- Site: the east room (sites.md, base arenas): one door at the top of a 1-wide, 8-cell corridor,
  a dead end behind it.
- The raid came up a few at a time between long spells of wrecking the base.
- 7 of the 20 raider deaths were the colony's spike traps (turtle's row: 3 killed + 6 inferred,
  no trace, so how many of its kills were traps is not known).
- Turtle's squad stood in the yard (113–120, 162–166), its start.

## Sources
journal `journals/base_ith_pirate_2x_claude_20261006.md` · traces
`results/human/traces/base_ith_pirate_2x_claude_20261006-170538.jsonl.gz` (attempt 2),
`..._164110_try1.jsonl.gz` (attempt 1, row in `results/human/discarded.jsonl`) · sheet
`sheets/base_ith_pirate_2x_start.md` · agent row `results/base/ladder.jsonl`
