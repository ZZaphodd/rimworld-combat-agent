# rand_094 · Yttakin ×8 (4 melee, 3 short guns, a rifle) vs Neanderthal melee ×7 · open — repelled by Claude

**Situation:** `open-arena` `raid-far` `raid-melee` `raid-strong-1v1` `us-melee-pawns` `us-skill-mismatch`
**Plays seen:** `loadout` `breach` (by deconstruction) `mouth-hold` `rotation` (agent: `kite`)
**Numbers:** ours 8 (melee 4, short 3, long 1), range median 8.7 (max 36.9) · raid 7 (melee 7), 300 pt, closer share 1.0 · count ratio 1.14 · raid from the north edge (130–140, 242–248), ~121 cells

## Sides
- Ours (PirateYttakin; shooting/melee, weapon at the start): Yeark 0/1 bolt-action rifle; Yoen 4/12
  machine pistol (Frail, Dementia, moving and manipulation 42%; Inject go-juice); Koersh 9/6 pump
  shotgun; Hysen 0/2 steel mace; Woyon 11/7 steel knife; Dur 7/2 biocoded revolver; Wyn'koersh 0/5
  and Kin'wakul 0/5 clubs. All have Animal warcall; the map had no wild animals.
- Raid (Neanderthal tribals): Humps ikwa 9 (Tough), Braña knife 9, White knife 6, Lion ikwa 5
  (Fast walker, Tough), Miñoca knife 3, Rhino knife 1, Wolle club 0. All targeting Woyon.

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| agent `kite` | pack kite | open ground | squad down, 0 kills | 0 dead, 8 downed, 8 permanent | 69.2 |
| Claude (2026-10-18) | loadout (rifle to Woyon, mace to Yoen); the nook's mouth wall deconstructed by one undrafted pawn, the job given at the start; two melee pawns on the front cells, four guns on the raider in the mouth; one rotation | nook | **repelled** (t5515): 3 dead, 2 downed, 2 fled; raid fled t4640 | 0 lost, 0 downed, 0 permanent | **5.2** |

## Scenes
- **t0–255** `us-skill-mismatch` → `loadout` `breach`: weapons swapped by t150; the mouth wall
  (211, 84) designated for deconstruction. Yeark (construction 4), undrafted, wandered until he was
  drafted and undrafted again (t255), then walked the ~96 cells with the job.
- **t1740–2680** `approach` → `breach`: Yoen, frail, walked ~34 ticks a cell until his "Inject
  go-juice" gizmo (t1790; moving 42% → 111%). The wall was gone at t2530 (~790 ticks of work), the
  raid 27 cells out; all eight in place at t2680. The raid came south along x 206–210, not along
  the lane z 84–85 as in rand_118.
- **t3000–4640** `melee-contact` → `mouth-hold` `rotation`: Lion, Miñoca, Wolle, White and Braña
  came into the mouth one at a time and died or went down there; Yoen (front) 77% → 45%, swapped
  for Kin'wakul at t4360–4500 (both stood on the front cell for ~60 ticks; Yoen left at 36%).
  Damage dealt: Yeark 169 (machine pistol, shooting 0), Dur 129, Koersh 126, Woyon 89, Yoen 83.
- **t4640–5515** `raid-breaking`: with four of seven out, Humps and Rhino walked east off the map.

## What the play stood on (observed)
- The nook mouth again took an all-melee raid one raider at a time (rand_118, rand_127).
- With four guns on the mouth cell and two melee pawns touching it, nobody of ours went down.
- Deconstruction finished ~470 ticks before the first raider reached the mouth.

## Sources
journal `journals/rand_094_claude_20261018.md` · trace `results/human/traces/rand_094_claude_20261018-051552.jsonl.gz` ·
sheet `sheets/rand_094_start.md` · agent row `results/night/router.jsonl`
