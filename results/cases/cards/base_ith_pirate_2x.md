# base_ith_pirate_2x · civil outlanders ×8 (guns + 3 throwers) vs 25 Waster melee · Ithfunda base — repelled

**Situation:** `base-arena` `raid-far` `raid-melee` `raid-outnumbers` `us-low-skill`
**Plays seen:** `mouth-hold` `rotation` `carry-downed` `molotov-into-group` (naive agent: `turtle`)
**Numbers:** ours 8 (shotgun, heavy SMG, revolver, 2 bolt-action rifles, frag, 2 molotov), 500 pt
· raid 25 Drifters (knives, clubs; no gun, no throwable), 875 pt (2× budget: 1000) · count ratio 0.32 · raid
from the west edge (2–9, 87–102), ~130 cells · base `arena_col_ithfunda` (PROCEDURES §1c)

## Sides
- Ours (shooting/melee): Jahames 1/4 pump shotgun, flak vest; Haney 2/0 heavy SMG; Fumiko 4/0
  bolt-action rifle, flak pants (Tough); Leslie 2/0 bolt-action rifle, flak jacket; Park 0/1
  revolver, firefoam pack; Caitlin 3/3 frag; Susumu 4/2 and Christ 5/2 molotov. The base had no
  items, so no loadout.
- Raid: 25 Drifters; melee 13–15: John 15, Farik 14, Dani 13, Daichi 13 (Brawlers); Kolya 11.

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| naive agent `turtle` | hold a planned concave ~11 cells west of the start and fire | the yard's west side | defeat: squad down t5177, 9 of 25 out | 0 dead, 8 downed, 1 permanent | 57.4 |
| Claude (alone), attempt 1 — discarded (compaction mid-battle) | door hold, guns 1–3 cells behind the plug | Ithfunda east room | stopped at t6663: 7 of 25 out, Jahames downed | – | – |
| Claude (alone), attempt 2 | door hold: one plug on the cell inside the doorway, guns 2+ cells back (from ~t9900), rotation, throws into the corridor queue | Ithfunda east room | **repelled** (t15403) | 0 (1 downed, 1 permanent) | **12.3** |

## Scenes (attempt 2)
- **t0–3636** `raid-wrecking`: the raid smashed and burned furniture across the base for ~3600
  ticks before the first raider came up the corridor; 3 died on the colony's spike traps on the
  way.
- **t3770–9601** `mouth-hold` `rotation`: one raider at a time in the doorway (133, 187):
  Dani, Furr, Svejgaard, Hairy, Kolya, Snuff dead there, Koromaru 2 cells below it; Humberto
  downed in the corridor. Jahames (plug) 100 → 42% on the first two (Dani, Furr). A swap ordered at
  ~t4271 moved neither pawn before Furr died (gone t4374); Leslie reached (133, 188) at t4426 and the
  doorway cell (133, 187) at t4454; Jahames stayed on (133, 188) until t5844. A ~2400-tick lull
  (t4382–6820) while the raid burned the yard.
- **t6994** `molotov-into-group` `fire`: three throws ordered at once on Svejgaard, 4–5 cells
  below the plug (in the air t7090–7102); one molotov burst in the room, fire on the plug cell
  from t7176. Two more three-throw rounds followed (t7345–7357 on Koromaru; t8328–8394 with no new
  order, the throwers still "attacking Koromaru"). Molotovs burst on the plug cell at ~t7427
  (Leslie 100 → 87, Haney 83 → 72) and on (132, 188) at ~t8462 (Leslie 79 → 68, Haney 72 → 63);
  Park's firefoam ~t7472.
- **~t9900**: the float menu showed "Fire at …: Too close" for the pawns next to the doorway
  raider; only Park, 2 cells back, had been shooting. Guns moved 2+ cells back (in place
  t10134–10199). Separately, Kolya sat at 20% t8483–9236 (dead t9411) while the plug cell stood
  empty (t8470–9133); cause not established.
- **t10368** `our-downed` `carry-downed`: Leslie went down on the plug cell during a swap; Park
  carried her out (from the orthogonal cell; from the diagonal one the carry stalled).
- **t10984**: John (melee 15) stepped from the doorway diagonally past the rock corner into the
  room while the plug cell was held; with Evgeny he fought inside: John gone ~t11670, Evgeny
  ~t11860. Farik also stepped in to (134, 188) (t11103, gone by t11122) and the downed Paul crawled
  in (shot ~t11950). Jahames down ~t11560.
- **t11122** `raid-breaking`: the raid fled with 13–14 of 25 out; 4 fleeing raiders died on spike
  traps, 5 escaped.

## What the play stood on (observed)
- Site: the Ithfunda east room (sites.md, base arenas): one door at the top of a 1-wide, 8-cell corridor,
  a dead end behind it.
- The raid came up a few at a time between long spells of wrecking the base.
- 7 of the 20 raider deaths were the colony's spike traps (turtle's row: 3 killed + 6 inferred,
  no trace, so how many of its kills were traps is not known).
- Turtle's squad held slots its planner packed around (105, 163), ~11 cells west of its start
  (113–120, 162–166) (turtle's row: plan center, on_slot_share 0.98).

## Sources
journal `journals/base_ith_pirate_2x_claude_20261006.md` · traces
`results/human/traces/base_ith_pirate_2x_claude_20261006-170538.jsonl.gz` (attempt 2),
`..._164110_try1.jsonl.gz` (attempt 1, row in `results/human/discarded.jsonl`) · sheet
`sheets/base_ith_pirate_2x_start.md` · naive agent row `results/base/ladder.jsonl`
