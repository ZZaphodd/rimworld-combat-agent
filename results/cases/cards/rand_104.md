# rand_104 · savage tribe ×8 (bows) vs civil outlanders ×8 with three throwers · forest

**Situation:** `forest-arena` `raid-far` `raid-throwers` `us-bows` `us-outrange` `us-skill-mismatch`
**Plays seen:** `loadout` `skirmish-line` `melee-lock`
**Numbers:** ours 8 (bow 6, long 1, thrown 1), range median 25.9 (max 29.9) · raid 8 (short 4, explosive 3, melee 1), 460 pt, outrange share 0, closer share 0.62 · count ratio 1.0 · raid from the east edge (244–249, 107–120), ~122 cells

## Sides
- Ours (shooting/melee, start weapon → after the loadout): **Cambiar** 12/7 recurve bow (poor)
  → greatbow; Crica 9/12 short bow (poor) → recurve bow (poor); White 7/6 recurve bow, Jogger,
  Bloodlust; Donkey 6/0 recurve bow, Jogger; Roamb 5/6 recurve bow (60%); Rrodoañocer 5/10 short
  bow; Goenaban 4/7 greatbow → short bow (poor), Slowpoke; Cheetah 2/7 pila, Tough. No armour, no
  melee weapons, no abilities.
- Raid: Cholaky frags (shooting 10), Annie frags (flak vest), Rabbit molotovs (shooting 10,
  Jogger); Bishop pump shotgun (10, flak vest); Sammy autopistol (good; 8/10, flak vest);
  Georgette steel knife (8/9, Wimp); Lady revolver; Mac autopistol (poor, 1).

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| agent `turtle` (no loadout) | hold a tree line | forest near the start | squad down | 4 dead, 4 downed, 8 permanent | 105.5 |
| human (Claude's loadout) | one north–south line in the forest 24 cells west of the start; centre stepped back into an arc | forest, x 90–104, z 103–137 | decisive, raid fled t6457, 8 of 8 out | 2 dead, 2 downed, 1 permanent | 46.0 |
| Claude (replay of the user's plan) | same line and loadout; early melee locks on Bishop and Cholaky | same | repelled, raid fled t4907, 6 of 8 out | 1 dead, 3 downed | 35.3 |

## Scenes
- **t0–75** `us-skill-mismatch` → `loadout`: the greatbow to Cambiar (12), Cambiar's recurve to
  Crica (9), Crica's short bow to Goenaban (4).
- **t848–1722** `approach` → `skirmish-line`: one line at x 101–104, z 105–137, 4–5 cells apart,
  32 long; the raid in a column along z 119, throwers in front. Player: the line stands where
  the greatbow at its longest range reaches the rock chunks by the raid's path with one cell to
  spare (slate chunks at (132–133, 115–116): 28.9–29.8 cells from Cambiar's cell (104, 123); the
  greatbow's range is 29.9).
- **t2197–2980** `thrower-close`: in the forest the first hits came at ~11 cells. Rabbit's
  molotov landed in front of the line's centre and burned there all battle. Rabbit downed
  t2582, Cholaky downed t2980 — two of three throwers, no loss of ours. The centre stepped back
  to x 90–95 (an arc, wings forward). Player: the greatbow loses damage every time it moves, so
  the pawns around it took the molotov landings instead of Cambiar dodging; White in the middle
  to keep the line balanced.
- **t2938–4031** `raid-holds`: Bishop (shotgun) worked on the north end from 13–16 cells
  (Goenaban 100 → 44%). Donkey, nearest the throwers at (99, 113), died between t3188 and t3250
  in one hit: Lady's revolver (shooting 4) destroyed his head (confirmed by the player in the
  game's UI; the player had thought for a moment the raid had been misread).
  Player: the north side was under heavy pressure, the south had room. The player rated Bishop
  (shotgun) and Georgette (knife) the top threats; both came from the same side (north). Georgette
  (Wimp) went down without much cost, so little fire was taken off Bishop. Georgette (knife) reached Crica (melee 12) and died t3753. Rrodoañocer died at
  the north end (t3833–4031).
- **t4031–5655** `raid-holds` `thrower-close`: a slow exchange at 14–24 cells; Annie threw ~10
  frags at the south group. Goenaban downed t4677 (Bishop); Bishop dead t5269; Crica downed
  t5573 (Mac); Sammy dead t5699.
- **t6425–6710** → `melee-lock`: Cheetah (pila, Tough) locked Annie, the last thrower, in
  melee so she could not throw (the player's intent); Roamb joined; Annie downed t6710. Lady dead, raid fled t6457; Mac killed t7128.

## Scenes of Claude's replay (journal: `journals/rand_104_claude_20261005.md`)
- **t1786–2370** `thrower-close` → `frag-dodge`: Rabbit's molotov and two frags thrown at White
  (sidestepped); Rabbit downed t2370.
- **t2370–3807** → `melee-lock`: Crica locked Bishop, Cheetah (+ White) locked Cholaky; Annie
  dead t2919 (bows). Georgette joined Bishop against Crica: Crica down t3425; Bishop, free,
  downed Cambiar (the greatbow) t3732. Georgette dead t3792, Cholaky dead t3807.
- **t3734–3867** `no-enemy-melee` → `melee-lock`: Goenaban + Rrodoañocer on Bishop: dead t3867.
- **t3867–4917** `raid-holds`: three gunners at 20–24 cells shot whoever walked or carried
  (Rrodoañocer down carrying Crica, Goenaban dead walking back); all bows on Sammy, standing
  still: Sammy dead, raid fled t4907.

## What the play stood on (observed)
- No site, but a range mark: the line was placed by the greatbow's range to rock chunks beside
  the raid's path (above), in the forest 21–24 cells west of the start.
- Forest: contact at ~11 cells, so the bows' 23–30 did not show; the fight ran at 10–24 cells.
- The throwers walked at the front of the raid's column: they were the first targets.
- Losses: the pawn nearest the throwers, then the north half of a 32-cell line, where both of
  the player's top threats (Bishop, Georgette) came in.

## Sources
report `results/human/reports/rand_104.md` · trace `results/human/traces/rand_104_human_loadout_20261005-101114.jsonl.gz` ·
watcher records `results/human/raw/rand_104/` · agent row `results/night/router.jsonl`
