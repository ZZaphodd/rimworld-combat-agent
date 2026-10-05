# rand_164 start sheet: savage melee ×9 vs Neanderthal melee ×6, forest, raid from the south edge

`tools/cases.py similar rand_164`: rand_127 (5.37), rand_018 (4.94), rand_115 (1.21).

## 1. rand_127: savage ×10 vs Neanderthals ×7, forest (Claude 10.8, human 26.0)
- **Borrow:** the nook mouth, 2–3 of ours on the 1–2 raiders at the entrance, rotation of the
  wounded, finishing the downed.
- **Differs:** the nook needs its wall broken (~540–1100 ticks). Here walking distance to the nook
  is 85 steps for us and 82 for the raid: no time.

## 2. rand_018: tribal melee ×11 vs Neanderthals ×6, open (Claude lost ×2)
- **Seen:** at rock B's tip, damage was spread over three raiders. In R1/R2, one raider per door
  lost most exchanges. Our pawns went down at 39–58% health; Neanderthals fought on to ~25%.

## Plan
- **Loadout:** the three normal steel spears to the best melee pawns: Hakuja (9), Bacchus (7) and
  Red (6).
- **Site:** the west rock pocket. The raid walks 180 steps to it and we walk 95, so the raid
  should string out.
- **Fight:** everyone on one raider at a time (as many as can touch him), the overflow on a
  second. Pawns under 38% step back to the pocket's west end. Downed raiders next to ours are
  killed (scratchpad `focus164.py`).

## Attempt 2 (2026-10-06): the user's play with the south wall
The user won with a bait and a breach (report `results/human/reports/rand_164.md`, 53.2). Their notes:
- Only three of ours can stand at one wall cell: the breach always goes to the top three melee
  pawns.
- Some weapons break walls better (look each time; no blunt weapon here).
- The same hall's south wall would have kept the bait's way back in open.

Plan:
- **Loadout:** as before (spears to Hakuja, Bacchus, Red).
- **Breach:** the three spears break the south wall cell (209, 167), the cell the user marked for deconstruction, from (208–210, 166). Outside,
  only x 208–213 are open; rock lies at 200–207.
- **Mouth hold:** inside, the mouth cells are (208–210, 168): Hakuja in the middle (209, 168),
  then Bacchus and Red. The rest stand behind in order of melee (Chave, Neabancocan, Marulo, Frog,
  Legua).
- **Rotation:** under ~35%, step back; the next strongest takes the cell.
- **Bait (Lercroi), paced like the user's** (trace `rand_164_human_20261006-044240`):
  - Out south-east to (132, 92) and wait for the raid at ~55 cells.
  - Edge east until the raid's front is ~20 cells off, so some raiders take him as their target.
  - Lead them north-west, north, then east round the ridge, staying 20–30 cells ahead.
  - Come down the hall's east side and in at the south breach once the first group is gone.
