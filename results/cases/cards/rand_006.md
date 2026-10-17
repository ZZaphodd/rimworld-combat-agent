# rand_006 · savage bows ×8 vs 13 Drifters, all melee · open — repelled by Claude

**Situation:** `open-arena` `raid-far` `raid-melee` `raid-outnumbers` `us-bows` `us-skill-mismatch`
**Plays seen:** `loadout` `breach` (by deconstruction) `mouth-hold` `rotation` `carry-downed` (agent: `kite`)
**Numbers:** ours 8 (bow 6 after the loadout, melee 2), range median 25.9 · raid 13 (melee 13), 455 pt, closer share 1.0 · count ratio 0.62 · raid from the south edge (175–187, 0–6), ~133 cells

## Sides
- Ours (TribeSavage; shooting/melee, weapon at the start): Berro 12/9 steel ikwa; Hawk 7/3
  greatbow; Blue 10/5 recurve bow; Llolou 6/6 short bow (Nimble); Cane 9/11 recurve bow; Toad 4/1
  steel ikwa; Red 0/0 greatbow (construction 13); Hare 2/5 greatbow (the raid's target). No armour.
- Raid (Drifters, pirates): Wttytt knife 12 (Brawler), Bryan club 9, Eva club 8, Lainey club 8,
  Jumper club 7, eight more at melee 0–4; most weapons at 24–59%.

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| agent `kite` | pack kite | open ground | squad down, 0 kills | 0 dead, 8 downed, 9 permanent | 73.4 |
| Claude (2026-10-18) | loadout (greatbow to Berro, ikwas to Cane and Llolou); the walled hall's south-wall corner cell (213, 167) deconstructed by Red, the job given at the start; one melee pawn then two on the cells touching it, the bows on the raider in it; rotations | NE ridge + walled hall, breach (213, 167) | **repelled** (t6727): 8 dead, 1 downed, 4 fled; raid fled t5826 | Berro dead, 1 permanent | **24.9** |

## Scenes
- **t0–2025** `us-skill-mismatch` → `loadout` `breach`: the nook was out of reach in time (the raid
  started 86 cells from it, we 96); the hall was ~95 cells for us and ~166 for the raid. Red
  (construction 13) took the job by himself and had the granite wall down ~t1845–2025, the raid
  59 cells out and strung out.
- **t2865–5826** `melee-contact` → `mouth-hold` `rotation`: eight raiders died one at a time on the
  breach cell (Zornie, Wes, Kat, Bryan, Moe, Andy, Sly, Max) under five to six bows. A limestone urn
  on (213, 168) can be walked through but not stood on (the user; tested after the battle on another
  urn); Llolou was caught on it in melee on his way, and it was gone by the end, so two inside
  cells touched the breach in the fight.
- **t3826–4787** `our-downed` → `carry-downed`: Llolou went down on (213, 168); Berro carried him
  deep in (~440 ticks). While that cell was empty Carson got in and was downed inside.
- **t5266–5444** `rotation`: Berro (43%) was ordered out of (213, 168) and died there before he got
  out; front swaps took 100–240 ticks through the cells round a 2×2 table.
- **t5826** `raid-breaking`: 9 of 13 out; four walked east off the map.

## What the play stood on (observed)
- The one-cell breach fed a 13-raider melee raid in one at a time; the bows did most of the damage
  (Blue 189, Hawk 152, Hare 145, Toad 140, Red 125).
- The losses came in the rotations: the front cell stood empty during them, and a front pawn at 43%
  died while leaving.

## Sources
journal `journals/rand_006_claude_20261018.md` · trace `results/human/traces/rand_006_claude_20261018-052806.jsonl.gz` ·
sheet `sheets/rand_006_start.md` · agent row `results/night/router.jsonl`
