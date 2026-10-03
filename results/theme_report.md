# Theme x doctrine matrix

> **Outdated (2026-10-03):** this report covers the first 113 of the 210 rows in
> `results/theme.jsonl` and uses the legacy score. The full matrix, rescored by trade ratio and
> grade v2, is [rescored/theme.md](rescored/theme.md) (summary in DATA.md §7).

Same frozen OutlanderRough squad (arena_forest) against one raid per enemy theme,
every doctrine x every theme x 5 runs, max 15000 ticks. Results: `results/theme.jsonl`.

Doctrines (agent names in `eval.AGENTS`):

| doctrine   | agent      | idea |
|------------|------------|------|
| aggressive | `b1`       | draft all, Auto attack nearest |
| focus      | `doctrine` | combat_agent.CombatAgent: rally, priority focus fire, retreat/rescue |
| hold       | `hold`     | hold v3: firing-position planner (battleground.plan_positions) |
| spread     | `spread`   | anti-explosive: keep >= 5 cells apart, Auto attack individually |
| kite       | `kite`     | anti-melee: shooters back off from melee raiders, melee pawns screen |
| close      | `close`    | anti-standoff: bound cover-to-cover to short range, then Auto attack |

## Pre-registered predictions (written before any theme run)

| theme | predicted best | predicted worst | reason |
|-------|----------------|-----------------|--------|
| pirate_grenadier | spread | hold | blasts hit everyone within a few cells; hold packs the line with 1-cell gaps, a grenade magnet |
| pirate_sniper | close | hold | snipers out-range everything we carry and are helpless up close; a static line just trades at their range |
| pirate_melee | kite | close | shooters that keep their distance get free volleys; rushing forward hands melee raiders the contact they want |
| pirate_mixed | focus | close | no single counter applies; killing raiders one at a time (square law) is the generic edge, rushing a mixed raid eats shotguns and blades |
| tribal_melee | kite | close | as pirate_melee, with more and weaker raiders: free volleys during the long approach matter even more |
| tribal_archers | close | hold | bows are weak, short-ranged volume fire and tribals are unarmoured: close and win the gunfight; a static line takes arrows from 20 bows |
| mechs | focus | close | tanky mechs need concentrated fire on the dangerous kinds (lancers/pikemen first); charging centipedes and scythers is suicide |

## Status: INCOMPLETE (113 of 210 episodes)

RimWorld crashed natively during the batch (Player.log: native crash in
`Verse.SectionLayer_Sand:Regenerate` inside `Map.FinalizeInit`, i.e. while
loading a save, after ~150 loads this session; it was preceded by intermittent
`NullReferenceException` from `get_status`/`load_game`, which the retry
absorbed). The game process is gone and the batch was stopped. Done:
mechs, pirate_grenadier, pirate_melee (6x5 each), pirate_mixed (all but
kite runs 4-5 and close x5). Not run: pirate_sniper, tribal_archers,
tribal_melee. Resume after restarting the game with:

    python3 eval.py --agents b1,doctrine,hold,spread,kite,close \
      --scenarios theme_pirate_grenadier,theme_pirate_sniper,theme_pirate_melee,theme_pirate_mixed,theme_tribal_melee,theme_tribal_archers,theme_mechs \
      --runs 5 --max-ticks 15000 --results results/theme.jsonl --resume
    python3 theme_analysis.py

(`results/theme.errors.jsonl` only lists the episodes skipped while the game
was down; `--resume` ignores it.)

## Setup actually built

- Squad (`theme_base`, `themes/base.json`): OutlanderRough 1500 pt, accepted on
  the first draw: 14 pawns = 6 support (4 heavy SMG, 2 LMG), 5 short
  (chain shotgun, machine pistol, autopistol, 2 revolvers), 1 assault rifle,
  1 incendiary launcher, 1 longsword. Largest class 43% (< 50%), but note it
  is a close/mid-range squad: no long guns at all.
- Themes (all 1500 pt = squad points, ImmediateAttack/EdgeWalkIn except mechs;
  every save passed the builder's assault check on the first try):

| theme | raiders | composition | accepted at draw | match rate in this session |
|---|---|---|---|---|
| pirate_mixed | 14 | short 6, medium 3, support 2, melee/long/explosive 1 each | 1 | 24/38 Pirate draws |
| pirate_melee | 11 | 10 melee (maces, warhammers, blades) + 1 hellcat rifle | 4 | 8/38 |
| pirate_grenadier | 13 | 10 explosive (4 molotov, 3 doomsday, 1 triple rocket, 1 frag...) + minigun, rifle | 26 | 1/38 |
| pirate_sniper | 13 | 13 sniper rifles | 38 | 1/38 |
| tribal_archers | 26 | 12 bows + 5 greatbows (65%), 8 melee, 1 pila (TribeSavage) | 2 | 4/6 tribal draws |
| tribal_melee | 27 | 27 melee (TribeSavage) | 6 | 1/6 |
| mechs | 8 | 4 pikemen, 3 scythers, 1 termite | 1 | 1500 pt worked (1 of 2 spawns failed) |

  Equal points != equal headcount: tribal raids at 1500 pt are ~26 pawns vs our
  14. Mechs at 1500 pt DID spawn (2nd try), so no point mismatch was needed.
  No thresholds were relaxed.

## Results (n=5 unless noted; P = P(random run beats a random aggressive run), 0.4-0.6 = tie)

### mechs
| doctrine | win | mean lost | enemy neutralized | median score | P(>aggressive) |
|---|---|---|---|---|---|
| aggressive | 5/5 | 0.4 | 100% | 126 | - |
| focus | 5/5 | 0.0 | 100% | 140 | 0.64 |
| hold | 3/5 | 0.6 | 95% | 70 | 0.36 |
| spread | 5/5 | 0.6 | 100% | 154 | 0.52 |
| kite | 5/5 | 0.4 | 100% | 146 | 0.64 |
| close | 5/5 | 0.2 | 100% | 168 | 0.64 |

### pirate_grenadier
| doctrine | win | mean lost | enemy neutralized | median score | P(>aggressive) |
|---|---|---|---|---|---|
| aggressive | 5/5 | 2.6 | 72% | -250 | - |
| focus | 5/5 | 5.2 | 48% | -508 | 0.04 |
| hold | 5/5 | 1.6 | 37% | -246 | 0.56 |
| spread | 5/5 | 1.6 | 82% | -76 | 0.76 |
| kite | 5/5 | 4.2 | 32% | -590 | 0.24 |
| close | 5/5 | 4.0 | 46% | -397 | 0.24 |

### pirate_melee
| doctrine | win | mean lost | enemy neutralized | median score | P(>aggressive) |
|---|---|---|---|---|---|
| aggressive | 5/5 | 0.6 | 76% | -25 | - |
| focus | 5/5 | 0.2 | 89% | 109 | 0.84 |
| hold | 5/5 | 0.0 | 85% | 162 | 1.00 |
| spread | 4/5 | 0.4 | 80% | 91 | 0.68 |
| kite | 0/5 | 1.6 | 58% | -111 | 0.20 |
| close | 5/5 | 0.0 | 85% | 133 | 1.00 |

### pirate_mixed (partial: kite n=3, close not run)
| doctrine | win | mean lost | enemy neutralized | median score | P(>aggressive) |
|---|---|---|---|---|---|
| aggressive | 4/5 | 2.2 | 60% | -121 | - |
| focus | 5/5 | 2.4 | 63% | -131 | 0.52 |
| hold | 5/5 | 2.4 | 30% | -254 | 0.40 |
| spread | 4/5 | 3.0 | 43% | -304 | 0.32 |
| kite (n=3) | 2/3 | 2.3 | 50% | -302 | 0.27 |

## Prediction vs measured

| theme | predicted best / worst | measured best / worst (median) | verdict |
|---|---|---|---|
| mechs | focus / close | close 168 (but close vs focus P=0.64, vs aggressive 0.64: close, kite, focus are a 3-way near-tie) / hold 70 (3/5 wins; P(close>hold)=0.72) | best: tie (focus not beaten clearly); worst: WRONG, close was the top median, hold was worst |
| pirate_grenadier | spread / hold | spread -76 (P>aggr 0.76, P>hold 0.84) / kite -590 (focus -508 close behind) | best: HELD; worst: WRONG by score (hold mid-pack, P(hold>kite)=0.80) though hold neutralized only 37% |
| pirate_melee | kite / close | hold 162 (P>aggr 1.00; hold vs close 0.80) / kite -111 (0/5 wins) | both WRONG: the anti-melee doctrine was the worst, the "suicidal" close was 2nd best |
| pirate_mixed | focus / close | aggressive -121 ~ focus -131 (P=0.48, tie) / spread -304 (P 0.32; close not run) | best: tie with aggressive (focus no better); worst: untested |
| pirate_sniper | close / hold | not run | - |
| tribal_melee | kite / close | not run | - |
| tribal_archers | close / hold | not run | - |

## Overall (provisional, 3 complete themes: mechs, grenadier, melee)

| doctrine | mean P(>aggressive) | mean score | lost/battle |
|---|---|---|---|
| spread | 0.65 | 22 | 0.87 |
| hold | 0.64 | 12 | 0.73 |
| close | 0.63 | -38 | 1.40 |
| focus | 0.51 | -92 | 1.80 |
| aggressive | 0.50 | -35 | 1.20 |
| kite | 0.36 | -153 | 2.07 |

Best default so far: **spread** or **hold** (statistically tied, both beat
aggressive on ~2/3 of pairings with the fewest losses); hold is the
lower-loss one, spread the more robust one (never below 0.52). This is on 3
themes only and must be re-checked once sniper/tribal themes are in.

Provisional routing (measured themes only; others default to spread):

| theme | route to | evidence |
|---|---|---|
| explosive-heavy raid | spread | P>aggr 0.76, P>hold 0.84 |
| melee-heavy raid | hold (close as 2nd) | P>aggr 1.00 both; hold vs close 0.80 |
| mechs | close / kite / focus (tie); avoid hold | hold 3/5 wins, 2 timeouts with 1 mech left |
| mixed | aggressive or focus (tie) | nothing beat aggressive |
| snipers, tribal melee, tribal archers | not measured | - |

## Issues found

- **Game crash** (see Status). Likely load-related instability after many
  loads; consider restarting RimWorld every ~100 episodes.
- **kite is broken against melee**: 0/5 wins vs pirate_melee, engagement ratio
  0.02-0.12, 3/5 raids left with captives. At 120 ticks/step a melee raider
  covers ~9 cells per step, so a 10-cell trigger means shooters spend most
  steps walking backwards (moving pawns don't shoot) and get caught anyway.
  It needs a smaller step or a "back off only if you can't kill it this step" rule.
- **"win" overstates outcomes vs pirates**: raids flee once broken and fled
  raiders count as cleared. E.g. grenadier/hold run 5: 0 killed, 12 escaped,
  9 of 14 squad downed and 2 dead is scored win=True; every doctrine is 5/5
  "wins" vs grenadiers with 32-82% neutralized. Read score / lost / neutralized,
  not win. "Escaped" is also an edge heuristic: raiders burning in molotov fires
  near the edge may be miscounted.
- **hold leaves the last mech alive**: 2/5 mech runs timed out with one mech
  still active (probably a termite/slow mech out of range); the idle-sally rule
  needs "nobody within 30 cells" for 40 steps and never fired. It should
  sally once few raiders remain.
- **focus doctrine engagement looks implausibly low** (0.02-0.13 vs grenadiers)
  while losing 5.2 pawns/battle: its rally-then-engage cycle keeps pawns moving.
  Worth a trace.
- The squad has no long guns; long-range themes (snipers, archers) will
  partly measure that, not only the doctrine.
- Tribal themes are ~2x our headcount at equal points.
