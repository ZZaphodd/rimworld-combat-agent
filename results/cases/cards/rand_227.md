# rand_227 · rough outlanders ×9 (guns after the loadout) vs Wasters ×8 with three rifles · forest — repelled by Claude

**Situation:** `forest-arena` `raid-far` `us-skill-mismatch` `raid-strung-out` `raid-holds`
**Plays seen:** `loadout` `skirmish-line` `melee-lock` `close-in`
**Numbers:** ours 9 (short 6, melee 3), range median 25.9 · raid 8 (long 3, short 2, melee 3), outrange share 0.38, no explosives · count ratio 1.12 · raid from the NE corner (219–231, 243–249), ~157 cells

## Sides
- Ours (shooting/melee, weapon):
  - **Mocha** 12/10: steel knife → autopistol (good, Barr's).
  - Cowan 10/3: knife → autopistol (Fernanda's).
  - Roach 10/10: pump shotgun, Fast walker, flak vest.
  - Diana 10/1: revolver (poor).
  - Manning 6/2: knife → autopistol (Pentaryl's).
  - Carol 6/3: revolver (poor 29%).
  - Barr 0/3: autopistol → knife; flak vest + jacket, Careful shooter.
  - Pentaryl 3/0: autopistol → knife; flak pants.
  - Fernanda 0/0: autopistol → knife.
- Raid (Wasters):
  - **Diver:** biocoded bolt-action rifle (poor), 10/9, Psychopath.
  - **Lynx:** autopistol, 9/11, Jogger, flak vest.
  - Smog (rifle, 3) and Banshee (rifle, 4, Tough).
  - Vector: revolver, 0.
  - Melee: Linaly (club, 7, Brawler), Vera (mace, 3), Hexad (knife, 4, Slowpoke).

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| naive agent `doctrine` | – | – | defeat, raid left with 5 captives | 1 dead, 5 kidnapped | 173.5 (123.5 without the kidnap double count) |
| **Claude** | autopistols to the shooters, knives to the rest; one line SW of the start across the raid's approach; the knives locked what reached the line; then the line moved ~8–10 cells forward in one step to bring the rifles (holding just outside 25.9) into range, knives on the rifles | near the start (forest) | **repelled**, 7 of 8 dead | 0 lost (Fernanda downed) | **19.4** |
| Claude, re-measure (orders kept: `hands.Keeper`) | the same plan; each shooter kept its target until it fell or stalled; no re-ranking when the melee raiders reached the line | near the start (forest) | defeat, squad down | 1 dead, 8 downed | 73.8 |
| Claude, re-measure 2 (`Keeper.assign`: expected damage, spread, focus weight, 1.25× switch, friendly-fire radii) | the same plan; fire spread over the arrivals; the close-in rule waited for no raider in reach (t4786) | near the start (forest) | enemies cleared, pyrrhic | 3 dead, 3 downed | 86.6 |
| Claude, re-measure 3 (`Keeper.assign`, close-in by hand) | the same plan, but the line went only to the cells of attempt 1's first, cancelled order, and no knife was sent at the rifles; Barr (behind the old line) and Pentaryl (where he had held Vera) were left and went down to fire | near the start (forest) | defeat, raid left with 2 captives | 4 dead, 2 kidnapped | 132.4 (112.4 without the kidnap double count) |
| Claude, re-measure 4 (`Keeper.assign`, attempt 1's close-in) | the same plan; the line to the cells attempt 1 reached (Mocha and Carol stopped 6–7 short) and the knives sent at Diver and Banshee, as in attempt 1; Lynx still stood | near the start (forest) | **repelled**, 5 dead, 2 downed | 0 lost (2 downed) | **33.5** |

## Scenes
- **Claude, t0–500** `us-skill-mismatch` → `loadout` `skirmish-line`:
  - Three knife-holding shooters (12, 10, 6) took the autopistols.
  - Line from (112, 121) to (124, 111), facing NE; knives 2 cells behind.
- **Claude, t1880–2830** `raid-strung-out` `raid-holds`:
  - Lynx led and stopped at 23 cells. Diver held at 27, Smog at 21–27.
  - The clubs (Linaly, Vera) walked on into the line. Banshee and Hexad came ~100 cells behind.
- **Claude, t2830–4290** `melee-contact` → `melee-lock`:
  - Linaly, Vera and Hexad reached the line and were held by the knives and Roach (shotgun).
  - Lynx was shot dead at 23 cells (t3248). Fernanda went down (t3310).
  - Linaly, Vera and Hexad died (t3466, t4232, t4292).
- **Claude, t4290–5494** `raid-holds` → `close-in`:
  - Diver, Smog, Banshee and Vector held at 20–27 cells, just outside our range ("Fire at"
    disabled). The shooters kept firing at the raider in melee instead.
  - The line moved ~8–10 cells forward in one step (~t4390; an earlier order to ~6 cells was
    cancelled by the controller before anyone moved). Barr (knife, flak) was sent at Diver and
    Pentaryl at Banshee in the same call.
  - Diver died at t5116, Vector at t5494.
- **Claude, t5494–8055** `raid-breaking`: Smog and Banshee (62–64%) backed off east. Barr followed
  Smog and killed him in melee (~t7039); Banshee left.

- **Re-measure 3, t3890–7719** `raid-holds` → `close-in` (to the cells of attempt 1's cancelled first
  order, no knife sent): Barr and Pentaryl were left and went down to fire (t4117, t4349); Lynx
  (t5036) and Vector (t6112) died to focused fire, but Mocha, Carol and Diana were shot dead at
  18–23 cells, and Roach's late rush on Banshee and Smog went down there.
- **Re-measure 4, t3634–5428** `raid-holds` → `close-in`: the line to attempt 1's far cells, Barr sent
  at Diver and Fernanda at Banshee. The holders stayed on their cells and the knives reached them
  (t4100–4515); Diver (t4726) and Lynx (t4768) died, Vector went down; Barr downed Smog as he
  backed off (t5428); Banshee left.

## What the play stood on (observed)
- The two runs that lost none (attempt 1 switching 19.4, re-measure 4 assign 33.5) had the line on
  attempt 1's far cells 100–150 ticks after the last melee arrival died and two knives sent at
  Diver and Banshee. The other three lost 1, 3 and 6 (re-measure 3: 4 dead, 2 kidnapped).
- Re-measure 2 (assign): the melee arrivals died 300–1000 ticks earlier than in the other runs; two
  of three deaths came while the rifles held at 21–27 cells, before a close-in that came 1400 ticks
  after the arrivals died (attempt 1: by hand, ~100 ticks after).
- Re-measure: with the attack orders kept (16 attack runs, median 834 ticks, against 679 runs,
  median 8 ticks, in the first run), the shooters stayed on Lynx at the range edge while the
  clubs and the knife fought the knives at the line. Eight of ours went down.
- Forest near the start; no site. The raid came strung out over ~100 cells, and its melee pawns
  walked into six guns.
- The rifles held 1–2 cells outside the autopistols' 25.9: the gun line did nothing to them until
  it moved forward.

## Sources
journal `journals/rand_227_claude_20261005.md` (run and re-measure) · traces `results/human/traces/rand_227_claude_20261005-204801.jsonl.gz`, `rand_227_claude_20261006-070654.jsonl.gz`, `rand_227_claude_20261006-080127.jsonl.gz`, `rand_227_claude_20261006-112307.jsonl.gz`, `rand_227_claude_20261006-114302.jsonl.gz` ·
naive agent row `results/night/router.jsonl`
