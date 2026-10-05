# rand_011 · Waster pirates ×9 (four good shooters) vs low-skill outlanders ×9 with two grenadiers · open

**Situation:** `open-arena` `raid-far` `raid-throwers` `raid-low-skill` `us-outrange` `us-melee-pawns` `us-skill-mismatch`
**Plays seen:** `loadout` `skirmish-line` `melee-tieup` `melee-charge` `ability` `gang-melee`
**Numbers:** ours 9 (short 4, melee 3, long 2), range median 25.9 (max 36.9) · raid 9 (short 6, explosive 2, melee 1), 495 pt, outrange share 0, closer share 0.78 · count ratio 1.0 · raid from the west edge (0–16, 47–67), ~140 cells

## Sides
- Ours (shooting/melee, start weapon → after the loadout): Schlitzer 13/10 bolt-action rifle;
  **Boss** 13/10 granite club (28%) → bolt-action rifle; **Diver** 10/8 marble club → revolver
  (poor); Strangler 8/1 pump shotgun; Wanya 4/10 biocoded revolver, steel flak helmet, ability
  *Animal warcall*; Olaf 3/3 revolver → marble club; **Mila** 3/4 steel club, Bloodlust, ability
  **Fire spew**; Far 1/4 biocoded autopistol, Jogger; Bagad 0/3 bolt-action rifle → granite club.
- Raid (everyone shoots 1–5): Shaw and Maggie frags; Cali pump shotgun (melee 6, Nimble, Tough,
  flak vest); Reid, Zach machine pistols; Navarro, Dennis (full flak) autopistols; Cameron
  revolver (poor); Pablo steel knife, Jogger.

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| agent `close` (no loadout) | closed in by ~t1130, then held | open ground | defeat, captives (kidnapping from t4930) | 3 kidnapped, 4 downed | 106.4 |
| human (Claude's loadout) | two lines on open ground west of the start, guns in front; small steps east | open ground (x 114–131, z 105–135) | decisive, raid broke t4666, 9 of 9 out | 1 dead (Bagad) | 25.8 |

## Scenes
- **t0–121** `raid-far` `us-skill-mismatch` → `loadout`: Boss ↔ Bagad (rifle to the 13),
  Diver ↔ Olaf (revolver to the 10); the biocoded guns can't move.
- **t873** `approach` → `skirmish-line`: two lines 4–6 cells apart, the four guns in front at
  x 114–116, the clubs and weak guns 6 cells behind. Nobody moved until contact.
- **t1524–2117** `approach` `us-outrange`: the raid's front four at 38 cells, grenadiers behind.
  The two rifles and Diver hit Navarro (twice), Maggie, Dennis and Cameron at 17–28 cells; the
  raid's first hit came at t1956.
- **t2244–2805** `thrower-close` `raid-holds`: Shaw inside 13; the raid's gunners stopped at
  15–27 cells. Olaf (club) went alone to the south-west towards Shaw and was shot up by the
  machine pistols (from t2512). Pablo (knife) ran in to Diver.
- **t2912–3304** `melee-contact` → `melee-tieup`: Bagad (club) held Pablo; Diver's revolver
  killed him. The line stepped ~6 cells east.
- **t3552–3979** `thrower-close` `our-downed`: both grenadiers within 13; Olaf downed in the
  middle at t3817 (Reid's machine pistol). Shaw killed (Strangler's shotgun, Wanya) at t3939.
- **t3896–4515** → `melee-charge` `ability`: Bagad and Mila charged through the raid to its
  wounded back pair (Navarro 44%, Cameron 68%). Bagad took a liver shot (Dennis) on the way and
  died ~360 ticks later. Mila's Fire spew killed Navarro and seared Cameron; fire on the ground.
- **t4433–4711** `raid-breaking`: Maggie (Diver), Dennis (Boss), Cameron (Boss), Zach (Far) dead
  within 300 ticks; the raid broke at t4666. Reid downed (Boss, spine).
- **t4900–6420** → `gang-melee`: Cali ran, then turned on Mila; all seven standing finished him
  in melee. Olaf carried to the group.

## What the play stood on (observed)
- No site: open ground (the cleared square), 5–15 cells west of the start, across the raid's
  lane (it walked north-east past the west lake: (76, 113) at ~t1524).
- Four of ours shoot 8–13 after the loadout; the raid shoots 1–5 with a median range of 20.
- The raid's gunners held at 15–27 cells; only the knife and the grenadiers came closer.
- Losses: the two who left the line (Olaf alone on the flank, Bagad in the charge).
- The fight was short (raid broke at t4666), so no kidnapping began.

## Retrieval check
Start sheet `sheets/rand_011_start.md` (rand_029, rand_107, rand_039), opened after the battle:
the raid's lane and timing from rand_029 (same edge) matched within ~200 ticks; it misread
Boss's club condition (28%) as his health; its sites were not used.

## Sources
report `results/human/reports/rand_011.md` · trace `results/human/traces/rand_011_human_loadout_20261005-092131.jsonl.gz` ·
watcher records `results/human/raw/rand_011/` · agent row `results/night/router.jsonl`
