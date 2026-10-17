# rand_150 · civil outlanders ×9 vs rough outlanders ×9 (gun duel, no grenadiers) · open — repelled

**Situation:** `open-arena` `raid-far` `us-low-skill` `us-skill-mismatch`
**Plays seen:** `loadout` `skirmish-line` `melee-lock`
**Numbers:** ours 9 (short 6, long 1, melee 2), range median 25.9 · raid 9 (short 5, long 2, melee 2), 490 pt · count ratio 1.0 · raid from the W edge (0–6, 142–156), ~125 cells

## Sides
- Ours: Lover 12, Axle 9/12, Queen 6/8, the rest 0–2; revolvers, autopistols, two shotguns, a
  bolt-action rifle, two knives.
- Raid: Lawman 8 (good autopistol), Hyf 6 and Fausto 0 (rifles), machine pistols, a shotgun,
  Paul (good revolver, full flak), two knives.

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| naive agent `doctrine` | focus fire | open ground | defeat (captives) | 12 (incl. kidnap count) | 172.7 |
| Claude (alone) | loadout; two rows 40 cells east; knives and shotguns on whoever reached the line; a late rush on the holders | open ground | **repelled** | 2 dead | 36.4 |
| Claude, re-measure 2026-10-06 | the same plan; ranged fire by `Keeper.assign` (one kept order per target, spread, Lawman and the rifles weighted, hold fire when nothing is worth it) | open ground | **repelled** | **0** | **6.4** |

## Scenes
- **t2145–3650**: the raid's knives, shotgun and machine pistols came to the line and died or
  went down there; none of ours down.
- **t3650–5224** `raid-holds`: two pistols held at 16–19 cells and the rifles at 35; one of ours
  died in the trade, one in the rush that killed Paul; then the raid left.

- **Re-measure t2304–2842** `raid-holds`: Lover kept Lawman from t2304 (Nytro and Axle joined
  for a while). **Lawman dead t2842**. The raid's knives died 3–6 cells out (t2939, t3457); our
  knives never went out.
- **Re-measure t3457–4486**: Kipper and Paul died where they held, at 14 and 18 cells (t3748,
  t3859); the raid fled at t3859. Pavel walked in from 13 to 9 cells and died there (~t3972).
  Hyf walked east, stopped 10 cells out at (155,121) and died there (t4486). None of ours went
  down.

## What the play stood on (observed)
- First play: the raiders who closed died; the ones who held at 16–19 cells cost us both dead
  (Nytro in the trade, Ash in the rush). Re-measure: the holders (Lawman, Kipper, Paul) died to
  fire at 14–22 cells; none of ours lost.
- Rifle in the best hand: 5 shots all fight in the first play (at least 27 target switches; the
  stall rule was ~90 ticks, shorter than the rifle's aim + cooldown of 192). In the re-measure
  with kept orders: 12 shots, 134 damage. The re-measure's control step was also ~4× shorter
  (the wait-setting change).

## Sources
journal `journals/rand_150_claude_20261005.md` · trace `results/human/traces/rand_150_claude_20261005-170343.jsonl.gz` ·
re-measure: journal `journals/rand_150_claude_20261006.md` · trace `results/human/traces/rand_150_claude_20261006-092317.jsonl.gz` ·
sheet `sheets/rand_150_start.md` · naive agent row `results/night/router.jsonl`
