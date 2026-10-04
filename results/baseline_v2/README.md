# baseline-v2

The reference for gate verdicts from 2026-10-05 on (WORKFLOW "Evaluation standard"). baseline-v1
(Peaceful, 1500 pt, squad of 14) is exploration data and not comparable.

| What | Value |
|---|---|
| Code | tag `baseline-v2` = commit c5f94a1 (every row): amove v6, doctrine v6, turtle v9, spread v6, kite v6, close v4; micro v4 (reflex) |
| Difficulty | Strive to Survive (all 360 rows; 0 invalid episodes, 0 harness errors) |
| Scenarios | set t500 (`--scenarios tier:t500`): squad of 9 (OutlanderRough 500 pt: 4 bolt-action rifles, 3 revolvers, machine pistol, frag grenades) on arena_forest 250×250 vs 500-pt raids: mechs, pirate_grenadier, pirate_melee, pirate_mixed, tribal_archers, tribal_melee |
| Cycle | adaptive 30/120@40, max 15000 ticks, game restart every 100 episodes |
| Runs | 10 per doctrine × theme (`core.jsonl`, 360 rows); `run.sh` |
| Report | `core_report.md` (`python3 tools/report.py results/baseline_v2/core.jsonl`) |
| Wall time | median 37 s per battle, 3.9 h of battles in all (vs 50 s median at 1500 pt) |

Colonists lost per battle (dead + kidnapped) / wins of 10 (decisive + repelled):

| Theme | amove | doctrine | turtle | spread | kite | close | best |
|---|---|---|---|---|---|---|---|
| mechs | 0.10/10 | 0.10/10 | **0.00/10** | 1.10/9 | 0.20/10 | 0.50/10 | turtle |
| pirate_grenadier | 0.40/8 | 0.30/9 | 0.50/9 | 0.90/7 | 0.40/10 | **0.10/9** | close |
| pirate_melee | 3.20/4 | 0.60/0 | 0.60/10 | 1.10/4 | **0.10/10** | 1.00/1 | kite |
| pirate_mixed | 2.90/5 | 1.00/8 | 0.70/10 | 1.10/5 | 0.50/10 | **0.20/10** | close |
| tribal_archers | 1.70/7 | 0.70/8 | 0.20/10 | 0.80/7 | **0.10/10** | 0.50/9 | kite |
| tribal_melee | 0.50/3 | 0.80/4 | 0.40/10 | 1.20/1 | **0.00/10** | 1.40/6 | kite |

Overall (lost per battle, wins of 60, median HP lost %, permanent injuries per battle): kite
0.22 / 60 / 142 / 0.7; turtle 0.40 / 59 / 174 / 1.1; doctrine 0.58 / 39 / 275 / 2.0; close
0.62 / 45 / 213 / 1.6; spread 1.03 / 33 / 259 / 1.7; amove 1.47 / 37 / 345 / 2.3. Oracle
routing (best doctrine per theme) 0.08 lost per battle.

Readings (n = 10 per cell; single cells are noisy, see the gate's limits):
- With this squad (4 bolt-action rifles, no melee pawn) kite and turtle — stand and fire, peel
  the chased pawn / hold a line — win almost everything. spread loses on every theme
  (scattered pawns are picked off; flamers and molotovs set the grass alight around them).
- On Strive, raiders kidnap downed colonists: amove's 3.2 and 2.9 lost per battle on the
  pirate melee and mixed themes are mostly captives.
- Grades miss injuries: a human round on pirate_grenadier (results/human, branch
  feat/human-observe) was "repelled" with 48% HP lost vs 142–345% for the agents.
- Squad/terrain preconditions still can't be fitted (one squad, one arena): roadmap 3.
