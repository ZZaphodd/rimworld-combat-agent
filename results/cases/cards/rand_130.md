# rand_130 · civil outlanders ×9 (one ace) vs civil outlanders ×9 with two grenadiers · open — repelled

**Situation:** `open-arena` `raid-far` `raid-throwers` `raid-low-skill` `us-low-skill` `us-skill-mismatch`
**Plays seen:** `loadout` `skirmish-line` `focus-top-threat` `frag-dodge` `carry-downed`
**Numbers:** ours 9 (short 8, melee 1), range median 25.9 · raid 9 (short 6, explosive 2, melee 1), 465 pt · count ratio 1.0 · raid from the NE corner (212–226, 242–249), ~150 cells

## Sides
- Ours: Sammy 18/19 good revolver (Trigger-happy, Tough, flak), Rae 9, Zhang 4, Beatriz 3, Petra
  2, Hakuja 2, Missy 0, Dave 0, Lady 0 (the raid's target); revolvers, autopistol, machine pistol,
  two shotguns, a knife.
- Raid (everyone shooting ≤ 5): Athequart molotovs, Daiki frags, autopistols, revolvers, a
  machine pistol, Evans knife.

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| naive agent `doctrine` | focus fire | open ground | defeat (captives) | 16 (incl. kidnap count) | 206.0 |
| Claude (alone) | loadout; two rows across the lane; the ace on the grenadiers; grenade sidesteps; carry the downed | open ground near the start | **repelled** | 1 dead, 3 downed | 35.4 |
| Claude, re-measure 2026-10-06 | the same plan; ranged fire by `Keeper.assign` (Sammy weighted onto the grenadiers); guard changed (grenade memory across calls, a step-away from a lying grenade, dodgers held through the Keeper so a fire order no longer cancels a sidestep; in the first play no sidestep moved a pawn more than 1 cell) | open ground near the start | **repelled** | 1 dead, 1 downed | **21.8** |

## Scenes
- **t1772–3392**: the ace (shooting 18) on Daiki from 30 cells in; both grenadiers died within
  their throwing range; a lone knife died in our line.
- **t3392–5403** `raid-holds`: the gunners held at 16–22 cells and lost three, one at a time,
  before the rest left.

- **Re-measure t1937–3116** `focus-top-threat` `thrower-close`: Sammy on Daiki from t1937;
  both grenadiers died 10–11 cells out (t2459, t3116). The step-away from a lying frag moved Zhang
  4 cells clear (it fired while the frag paused in flight). A molotov thrown just before Athequart
  died: guard sent Sammy (nearest where it was first seen), then stopped watching when Athequart
  fell; it landed next to Rae (two guard gaps, changed after).
- **Re-measure t3116–5370** `raid-holds`: Cali held at 13–14 cells, the rest at 18–23; Cali,
  Loser, Lui died; Zhang was shot dead at t3447, Beatriz down at t5262; the raid fled at t5370.

## What the play stood on (observed)
- One shooting-18 pawn did 288 of 458 damage read in the first play (Beatriz, dead, not read);
  170 of 510 read in the re-measure (Zhang, dead, not read).
- The pump shotguns fired 8 and 6 shots in both plays.
- Our losses were in the front row. In the first play the gunners stopped at 16–22 cells; in the
  re-measure Cali stood at 13–14 from t2061 until he died at t3617, the rest at 18–23.

## Sources
journal `journals/rand_130_claude_20261005.md` · trace `results/human/traces/rand_130_claude_20261005-165810.jsonl.gz` ·
re-measure: journal `journals/rand_130_claude_20261006.md` · trace `results/human/traces/rand_130_claude_20261006-094522.jsonl.gz` ·
sheet `sheets/rand_130_start.md` · naive agent row `results/night/router.jsonl`
