# rand_127 · savage tribe ×10 vs Neanderthal melee ×7 · forest

**Situation:** `forest-arena` `raid-far` `raid-melee` `raid-strong-1v1` `us-bows` `us-low-skill` `us-melee-pawns` `us-outnumber` `us-skill-mismatch`
**Plays seen:** `loadout` `breach` `mouth-hold` `rotation` `finish-downed`
**Numbers:** ours 10 (bow 5, melee 4, thrown 1), range median 20.9 · raid 7 (melee 6, bow 1), 310 pt, closer share 0.86 · count ratio 1.43 · raid from the north edge, 130 cells

## Sides
- Ours (shooting/melee): Barracuda 10/11 and Laque 8/9 short bows; Crica 1/10 ikwa; Mabe 2/7
  pila; Trout 4/6 ikwa (awful); Grasshopper 4/1 ikwa; Tol 3/4, Owl 3/2, Ñala 1/4 short bows (poor);
  Raraguatas 0/4 club, no clothes.
- Raid: Bacchus steel club (melee 9), Gabobrei steel spear, three knives, a club, one archer.
  Neanderthals: robust (~×1.33 health), reduced pain (hard to down), strong melee, 96% of our
  speed; melee skills 2–4 except Bacchus.

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| agent `amove` | bows shoot on approach, melee gangs up | near the start | all 10 downed | 0 dead, 10 down | 116.9 |
| human, attempt 2 (discarded) | loadout; packed squad in the open | open forest | squad down | 2 dead | 99.4 |
| human | loadout; nook; mouth; rotation | nook | repelled t5258 | 0 (1 downed) | 26.0 |
| Claude | the human's plan; breach with 6 pawns; urn cell; rotate below 45% | nook | repelled t6213 | 0 (1 downed) | 10.8 |

## Scenes
- **t0–122** `raid-far` `us-skill-mismatch` → `loadout`: Mabe ↔ Grasshopper (pila to the
  better shooter, ikwa to the better melee pawn).
- **t122–2774** `approach` → `breach`: the nook is closed by a wall at (211, 84). Claude: 6
  pawns hit it (verb gizmo, adjacent, one swing per order, a round every ~90 ticks), 11 rounds.
  The human broke it with drafted melee pawns.
- **t2975** `approach` `raid-strung-out` → `mouth-hold`: all ten inside (radius ~3); the two
  fastest raiders 15 cells ahead of the body.
- **t3221–3702** `melee-contact` → `mouth-hold`: the raid piles up at the entrance; only the
  pawns touching the mouth fight, 2–3 of ours against 1–2 of theirs. Claude broke the urn at
  (212, 85) down to 3% (never fell) and stood a third pawn on that cell.
- **t4371–4803** `melee-contact` `our-downed` → `rotation`: a front pawn at 37–48% steps back, a
  fresh one steps in (Claude swapped below 45%). The one downed (Raraguatas; Claude's game:
  Crica) lay inside, behind the front.
- **t5258 / t6213** `raid-breaking`: Bacchus downed in the breach; the raid flees.
- Attempt 2, for contrast: the same squad packed on open ground; the Neanderthals surrounded
  each fighter and won every exchange (Gabobrei held Trout for 1000+ ticks).

## What the play stood on (observed)
- Site: `nook` (sites.md), 97 cells from the start; open only to the north-west once the wall
  is down; an entrance 1–2 cells wide.
- The raid is all melee and came to us; it arrived one or two at a time.
- ~2800 ticks before contact: enough to walk there and break the wall (~1100 ticks with 6).

## Sources
report `results/human/reports/rand_127.md` · Claude's turns `results/human/raw/rand_127/claude_turns.md` ·
traces `results/human/traces/rand_127_*` (human attempts 1–3, Claude) · rows `results/human/play.jsonl`,
`results/human/discarded.jsonl` · agent row `results/night/router.jsonl`
