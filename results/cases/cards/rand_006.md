# rand_006 · savage bows ×8 vs 13 Drifters, all melee · open — repelled by Claude, then by the human with none hurt badly

**Situation:** `open-arena` `raid-far` `raid-melee` `raid-outnumbers` `us-bows` `us-skill-mismatch`
**Plays seen:** `loadout` `breach` (by deconstruction) `mouth-hold` `rotation` `carry-downed` (naive agent: `kite`)
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
| naive agent `kite` | pack kite | open ground | squad down, 0 kills | 0 dead, 8 downed, 9 permanent | 73.4 |
| Claude (2026-10-18) | loadout (greatbow to Berro, ikwas to Cane and Llolou); the walled hall's south-wall corner cell (213, 167) deconstructed by Red, the job given at the start; one melee pawn then two on the cells touching it, the bows on the raider in it; rotations | NE ridge + walled hall, breach (213, 167) | **repelled** (t6727): 8 dead, 1 downed, 4 fled; raid fled t5826 | Berro dead, 1 permanent | **24.9** |
| **human** (2026-10-18; Claude did the same loadout and opened the south wall's middle cell (209, 167) with Red, the squad waiting outside, handed over at t1950) | three melee-able pawns on the three cells touching the breach (Llolou (208, 168), Cane (209, 168), Hare (210, 168)), five bows packed behind in a 3×3 block (z 169–171); the middle front swapped once with the pawn right behind it | NE ridge + walled hall, breach (209, 167) | **repelled** (t6097): 7 dead, 3 downed, 3 fled; raid fled t4795 | 0 lost, 0 downed, 0 permanent, health lost 100% | **4.0** |

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
- **Human, intents (told after the battle):**
  - Three cells touch the middle breach on purpose: the two diagonal ones hit for free.
  - Hare holds a bow, but standing in the front row and hitting in melee does more damage than
    shooting it.
  - Had two front pawns looked better than three, the player would have used the bump on the inside
    of the east wall's middle (a wall cell at (213, 175) inside the x 214 wall, by the terrain map).
- **Human, t1950–2122** `approach` → `mouth-hold`: from Claude's hand-over (wall open, the raid 71
  cells out) all eight went in: Llolou, Cane and Hare on (208–210, 168), the bows on (208–210, 169),
  (209–210, 170) and (209, 171).
- **Human, t2900–4795** `melee-contact` → `mouth-hold` `rotation`: the raiders came into the breach
  one at a time; Andy, Wes and Max went down there. Of the seven dead, Kat, Wttytt and Lainey died in
  it, Sly and Bryan just outside, Eva at (207, 164), and Zornie's corpse lay inside at (209, 169). Only the
  middle front cell, straight ahead of the breach, took real damage: Cane 100% → 50% (t4184), then
  Toad from right behind took his cell (t4205–4341) and went to 70%. The diagonal front cells took
  little (Llolou 13 damage, Hare none) and dealt much (melee: Llolou 123, Hare 91 with 2 shots
  fired). Bows: Blue 178, Berro 170, Hawk 101, Toad 101, Red 92.

## What the play stood on (observed)
- The one-cell breach fed a 13-raider melee raid in one at a time; the bows did most of the damage
  (Blue 189, Hawk 152, Hare 145, Toad 140, Red 125).
- The losses came in the rotations: the front cell stood empty during them, and a front pawn at 43%
  died while leaving.
- The human's breach in the middle of the wall had three cells touching it: the raider in it was hit
  from all three and from the bows, while the hits it gave went to the middle one.

## Sources
journal `journals/rand_006_claude_20261018.md` · trace `results/human/traces/rand_006_claude_20261018-052806.jsonl.gz` ·
human: trace `results/human/traces/rand_006_human_20261018-055003.jsonl.gz` ·
sheet `sheets/rand_006_start.md` · naive agent row `results/night/router.jsonl`
