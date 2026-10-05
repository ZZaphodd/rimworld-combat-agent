# rand_018 · tribal melee ×11 vs Neanderthal melee ×6 · open — not solved

**Situation:** `open-arena` `raid-far` `raid-melee` `raid-strong-1v1` `us-outnumber` `us-melee-pawns` `us-low-skill`
**Plays seen:** `corner-ambush` (rock pocket tip), `mouth-hold` at room doors, `rotation`
**Numbers:** ours 11 (melee 11) · raid 6 (melee 6), 310 pt · count ratio 1.83 · raid from the south edge (155–168, 0–1), ~130 cells

## Sides
- Ours (TribeRough, baseline humans; melee): Bear steel club 16, Red knife 10, Bilma spear 8,
  Monkey ikwa 7, Fox knife 5, Lánbo club 4, Cambiar club 4, Cómaro knife 4 (the raid's target),
  Scorpion spear 3, Seado club 3, Cheetah knife 2. No armour.
- Raid (Neanderthals; melee): Purple ikwa 11 (Slowpoke, Brawler), Nabia spear 8, Raro spear 6
  (Nimble), Skunk knife 5 (Brawler), Iobust ikwa 4, Pelican knife 4.

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| agent `amove` | attack-move | open ground | won (t3364, 2 kills) | 0 lost, 4 downed, 23 permanent | 83.3 |
| Claude attempt 1 | tip ambush, up to 5 per raider | west rock pocket | defeat, 2 raiders killed | 3 dead + 4 kidnapped | 187.0 |
| Claude attempt 2 | hold ruin rooms R1+R2 (five 1-cell entrances) | big ruin | defeat, 2 killed + 1 downed | 2 dead + 2 kidnapped | 153.0 |

## Scenes
- **Attempt 1, t3376–5463**: the first four arrived together round rock B's tip, the last two
  ~20–40 cells behind; several of ours per raider, but our pawns went down at 39–58% health and
  the raiders kept fighting to ~25%.
- **Attempt 2, t1440–4558**: the raid came to the rooms' north side as we arrived (one of ours
  caught outside). One raider per door, but most door exchanges were lost; three raiders at
  30–36% outlasted five of ours.

## What the play stood on (observed)
- Neanderthal melee vs baseline tribal melee: in both attempts our pawns went down at 30–60%
  health, while raiders at 25–36% kept fighting.
- The agent's run ended with the raid gone after two kills; neither of Claude's runs saw the
  raid leave before the squad was down (one draw each).

## Sources
journal `journals/rand_018_claude_20261005.md` · traces `results/human/traces/rand_018_claude_20261005-{133618,134137}.jsonl.gz` ·
sheet `sheets/rand_018_start.md` · agent row `results/night/router.jsonl`
