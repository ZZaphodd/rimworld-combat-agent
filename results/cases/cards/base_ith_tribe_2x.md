# base_ith_tribe_2x · civil outlanders ×8 vs 10 Neanderthal tribals · Ithfunda base — decisive

**Situation:** `base-arena` `raid-far` `raid-melee` `raid-strong-1v1` `raid-outnumbers`
**Plays seen:** `mouth-hold` `rotation` (naive agent: `turtle`)
**Numbers:** ours 8 (shotgun, knife, 3 autopistols, rifle, revolver, molotov), 500 pt · raid 10
TribeRoughNeanderthal (spears, ikwas, a knife, a short bow, a pila), 590 pt (2× budget: 1000) · count ratio
0.8 · raid from the south edge (48–52, 2–5), ~175 cells · base `arena_col_ithfunda`

## Sides
- Ours (shooting/melee): Graves 8/12 pump shotgun; Semyon 4/11 steel knife; Phat 4/9 molotov
  (Tough); Wright 8/2, El 7/0 autopistols; Vang 1/1 autopistol, flak vest and pants; Tina 1/1
  bolt-action rifle, flak vest; Petra 3/1 revolver.
- Raid: berserkers Orange, Goraxada, Enmar (spears); warriors Donkey, Scorpion, Komodo (ikwas);
  chief Ñabaigo (spear, steel plate armour); penitent Légua (knife); archers Raven (short bow),
  Jaguar (pila). Shooting 0–4, melee 2–8.

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| naive agent `turtle` | hold a planned concave ~14 cells south of the start (plan center (116, 151)) and fire | south of the yard | defeat: squad down t6436 with 3 of 10 out | 2 dead, 6 downed, 9 permanent | 109.7 |
| Claude (alone) | door hold: three melee pawns on the plug and the doorway's two diagonal cells, five guns 2+ cells back (four after the one swap, which put Graves's shotgun on the plug) | Ithfunda east room | **decisive** (t24014) | 0 (0 downed) | **4.8** |

## Scenes
- **t0–4810** `raid-wrecking`: the raid smashed and burned furniture all the way north; first
  raider up the corridor at ~t4810.
- **t4925–18271** `mouth-hold`: Goraxada, Orange, Donkey and Légua died in the doorway (~140–410
  ticks each) with three of ours meleeing and five firing (four after the swap: Graves moved to the plug,
  Semyon back to (130, 195)); Raven (archer) was shot down in the
  corridor. Semyon (first plug) 100 → 47% on Goraxada, swapped for Graves. Lulls of ~3300–4400
  ticks between arrivals. Enmar (29%) last seen t13546 at (91, 153) while igniting a spike trap;
  dead there (inferred).
- **t18280** `raid-breaking`: fled with 6 of 10 out; Scorpion (85, 153) and Komodo (181, 122) then died on the
  spike-trap stretches; Jaguar lost health on z 122 (x 153–159, 100 → 21% by t19439) and went down
  at (186, 110) at t22947, off the stretch; Ñabaigo escaped west.

## What the play stood on (observed)
- Site: the Ithfunda east room (sites.md, base arenas), the same as base_ith_pirate_2x.
- No raider got into the room; our lowest health was 47% (Semyon).
- Turtle's row: first contact t2866, "decided to kidnap" at t6106, squad down t6436, raid fled t8566.

## Sources
journal `journals/base_ith_tribe_2x_claude_20261006.md` · trace
`results/human/traces/base_ith_tribe_2x_claude_20261006-175528.jsonl.gz` · sheet
`sheets/base_ith_tribe_2x_start.md` · naive agent row `results/base/ladder.jsonl`
