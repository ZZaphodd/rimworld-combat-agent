# Data files, schemas and summaries

Summaries in §6–§7 were produced on 2026-10-03 with read-only commands (no game):
`python3 raid_census.py --report`, `python3 eval.py --summary --results results/results.jsonl`,
`python3 theme_analysis.py results/theme.jsonl`, plus counts over themes/*.jsonl.

**Irreproducible data:** raids are generated randomly, so a scenario can't be rebuilt by script,
only re-rolled. **Keep the .rws saves** (RimWorld Saves folder, ~13.5 MB each, ~1.4 MB gzipped;
WORKFLOW.md). The census and theme samples are also one-off draws.

## 1. Saves (in RimWorld's Saves folder, not in the project)

| Save | Built by | Content |
|---|---|---|
| `arena_forest` | make_arena (PROCEDURES §1) | 250×250 temperate forest, observer at (240,240), no animals, no fog, no loose weapons |
| `arena_open` | make_arena | arena_forest with (50,50)–(200,200) cleared |
| `arena_fort` | make_arena `--fort` | arena_open + granite compound (PROCEDURES §2) |
| `theme_base` | theme_builder `--base` | arena_forest + frozen 14-pawn OutlanderRough squad, observer removed |
| `scenario_<id>` (20) | scenario_builder / theme_builder | one per manifest in scenarios_out/ |

## 2. scenarios.json and scenarios_out/

**scenarios.json**: a list of specs.

| Field | Meaning |
|---|---|
| `id` | scenario id (save = `scenario_<id>`) |
| `tier` | `smoke` (regression: even doing nothing should win), `standard`, `hard`, `fort` (A/B with an open-map twin), `theme` (frozen squad vs one raid flavour), `check` (reflex drill) |
| `note` | free text. Some ids are historical: `std_tribe_rush_open` and `fort_tribe_rush` are **archer** raids (27/32 and 33/34 bows), not melee hordes |
| `arena` | `arena_open`, `arena_forest`, `arena_fort` |
| `squad` | `{faction, points, place [x,z], spacing?, width?}`; theme tier: `{base_save: "theme_base", faction, points, place}` |
| `enemy` | method variants: **specifics** `{faction, points, strategy, arrival}` (default ImmediateAttack/EdgeWalkIn); **faction** `{faction, points, method: "faction"}` (game-chosen; mechs); **spawn_pawn** `{method: "spawn_pawn", kind, count, distance, min_frag_share}` (frag_check) |

The 20 scenarios: smoke_pirates_vs_savage_open; std_pirate_mirror_forest, std_tribe_rush_open,
std_outlander_smart_forest (ImmediateAttackSmart), std_pirates_centerdrop_open (CenterDrop),
std_yttakin_groups_forest (PirateYttakin, EdgeWalkInGroups); hard_mechs_mid_open (4000),
hard_pirates_vs_mechs_forest (6000); fort_tribe_rush, fort_pirate_mirror, fort_mechs_mid,
fort_centerdrop; theme_{pirate_mixed, pirate_melee, pirate_grenadier, pirate_sniper,
tribal_archers, tribal_melee, mechs}; theme_frag_check.

**scenarios_out/scenario_<id>.json** (manifest; eval loads every file in the folder, so
`--scenarios all` includes frag_check):

| Field | Content |
|---|---|
| `id, save, spec` | spec = the scenarios.json entry |
| `squad[]` | `{id, name, weapon, x, z, health}` at save time |
| `enemy[]` | non-theme: `{id, def, x, z}`; theme/check: `{id, def (pawn kind), weapon, class, x, z}` |

Squad sizes: 10–18 for the Pirate-squad scenarios, 14 for theme/check. Enemy counts: 5
(frag_check) to 34 (fort_tribe_rush).

## 3. themes/

| File | Schema |
|---|---|
| `base.json` | `{save, arena, spec {faction, points, place, size [12,15], max_top_share 0.5}, attempts, attempt_stats, squad[] {id, name, weapon, x, z, health, class}, slots {id: [x,z]}}` |
| `samples.jsonl` | one per spawned raid: `{faction, points, classes[]}` |
| `build_log.jsonl` | one per theme: `{theme, accepted_at_attempt, faction, points, size, group_attempts, tried{faction: n}}` (or `accepted: false`) |
| `build.log` | console log of the build |

**Frozen squad** (theme_base): OutlanderRough 1500 pt, accepted on the 1st draw. 14 pawns: 6
support (4 heavy SMG, 2 LMG), 5 short, 1 assault rifle, 1 incendiary launcher, 1 longsword. No
long guns.

**Theme predicates and acceptance** (all at 1500 pt; the match rate is the share of samples of
that faction group meeting the predicate, from samples.jsonl):

| Theme | Factions | Predicate | Match rate | Accepted at draw | Raiders |
|---|---|---|---|---|---|
| pirate_mixed | Pirate | no class ≥ 50% | 24/38 (63%) | 1 | 14 |
| pirate_melee | Pirate | melee ≥ 60% | 8/38 (21%) | 4 | 11 |
| pirate_grenadier | Pirate | explosive ≥ 60% | 1/38 (3%) | 26 | 13 |
| pirate_sniper | Pirate | long ≥ 60% | 1/38 (3%) | 38 | 13 |
| tribal_archers | TribeRough/TribeSavage | bow + long ≥ 60% (greatbow is "long") | 4/6 | 2 (TribeSavage) | 26 |
| tribal_melee | TribeRough/TribeSavage | melee ≥ 70% | 1/6 | 6 (TribeSavage) | 27 |
| mechs | Mechanoid | any + assault check | 1/1 spawned (1 of 2 spawn attempts failed) | 1 | 8 (4 pikemen, 3 scythers, 1 termite) |

Every accepted theme passed the assault check on the first try. frag_check: 2nd roll, 4/5 frag
carriers.

## 4. census/

| File | Content |
|---|---|
| `raids.jsonl` | current census, 998 raids: `{faction, points, route: "faction", raiders[] {kind, weapon, class}, t (s per sample)}` |
| `raids.before_recollect.jsonl` | first pass (936). TribeRough:3000 had only 99 samples (lost to the `largeOutput` bug) and Mechanoid:6000 89 (pod leaks). Both configs were re-collected into raids.jsonl |
| `census_run.log`, `census_recollect.log` (project root) | console logs incl. failures |

**Weapon classes** (first match wins, label substring, lowercase): explosive (launcher, grenade,
molotov, emp, inferno, toxbomb, rocket, doomsday, thump cannon, incinerator) → long (sniper,
greatbow, charge lance, bolt-action, marksman, needle gun) → support (lmg, minigun, heavy charge
blaster, heavy smg) → bow (short bow, recurve bow, bow) → thrown (pila, javelin) → short (shotgun,
smg, machine pistol, autopistol, revolver, pistol, chain shotgun, spiner) → medium (assault rifle,
charge rifle, rifle, beam, blaster, gun, cannon) → melee (sword, knife, club, mace, spear, axe,
hammer, ikwa, gladius, horn, claw, blade, fist, bite, scythe, lance, pike) → other. Weapon `none`
→ class by mech kind (GAME_FACTS.md §5). Weapon names are stripped of `(…)` and `Biocoded `.

## 5. results/

| File | Rows | Content / format |
|---|---|---|
| `pilot.jsonl` | 8 | **Legacy, pre-tracker.** First runs (b0/b1/doctrine on smoke + hard mechs), max_ticks 10000. No fates and no grade inputs: grade() falls back to the stored `win` |
| `pre_tracker.jsonl` | 236 | **Legacy.** Fixed 120, max_ticks 15000; b0/b1/doctrine × 12 scenarios + hold (26). Fields: outcome, deaths, downed, hp, perm, `enemies_seen/active_end`, `enemy_neutralized_frac`, ± engagement. The old `win` counted fled raiders as cleared |
| `results.jsonl` | 241 | the 236 pre_tracker rows **plus 5 tracker rows** (max_ticks 20000: fort_tribe_rush b0, hard_mechs_mid_open b1, std_pirates_centerdrop_open b1). The default `--results` file |
| `grade_check.jsonl` | 12 | b1/hold × pirate_grenadier/pirate_mixed with game messages: **evidence for grade() and the 0.5 fallback**. Stored grades are stale (2 rows) |
| `theme.jsonl` | 210 | theme matrix v1: 6 doctrines × 7 themes × 5, fixed 120, no `agent_version`, no `kpis`, **no game_messages** (grade uses the fallback). Old names `hold`, `doctrine`. theme_report.md describes only the first 113 rows |
| `theme.errors.jsonl` | 41 | `{scenario, agent, run, time}` episodes skipped while the game was down (pre-cycle format) |
| `exec_v1.jsonl` | 20 | v1 doctrines with KPIs on their home themes (`agent_version` present, no cycle fields) |
| `exec_v2.jsonl` | 31 | kite v3, doctrine v2, hold v4 home-theme checks (execution_report) |
| `reflex_check.jsonl` | 165 | b1/turtle/spread × frag_check/pirate_grenadier × {fixed:120 no reflex, adaptive no reflex, adaptive + reflex v1 (no `reflex_version`), adaptive + reflex v2} |
| `threatmap_check.jsonl` | 135 | reflex v2 vs v3a vs v3b (agent versions b1 2/3/4, spread 2/3/4, turtle 5/6/7) |
| `hazards.jsonl` | 7 | measure_hazards: `{kind, tick, weapons, projectiles[] {def, life, moving, resting}, blasts[]}`; measure_blast: `{kind: "frag_blast_radius", rows[] {d, hit}}` |
| `*.sh / *.log / *.done / *.failed` | – | batch scripts, console logs and end markers |
| `*_report.md`, `hazards.md` | – | reports (DOCS.md) |

Root logs (`eval_*.log`, `combat_live*.log`) are console logs of early runs. `combat_live*` is the
standalone doctrine agent on a real colony (with beds).

**Legacy reading rules:** a missing `agent_version` means pre-versioning. A missing `cycle` means
`fixed:<step_ticks>`. Reflex on without `reflex_version` means v1. Agent `hold` = turtle. Always
recompute `grade/win/score`.

## 6. Census summary (raid_census --report; faction route, arena_open)

| Config | Raids | Size median (min–max) | Class shares | Dominant class ≥ 60% / ≥ 80% of raid | Melee-heavy (≥ 50%) | Any explosive | Spawn failures |
|---|---|---|---|---|---|---|---|
| Pirate 1000 | 124 | 11 (6–25) | melee 32, short 28, explosive 19, long 13, support 5, medium 2 | 34% / 27% | 17% | 64% | 1 "spawned nobody" |
| Pirate 3000 | 125 | 19 (9–28) | explosive 19, long 19, short 17, melee 17, support 16, medium 12 | 24% / 19% | 12% | 77% | – |
| OutlanderRough 1000 | 125 | 11 (7–15) | short 51, explosive 17, long 12, support 10, medium 5, melee 5 | 26% / 2% | 0% | 86% | – |
| OutlanderRough 3000 | 125 | 18 (9–27) | short 25, melee 25, support 19, medium 17, explosive 10, long 5 | 0% / 0% | 0% | 74% | – |
| TribeRough 1000 | 125 | 13 (11–19) | melee 47, bow 34, long 11, thrown 8 | 38% / 17% | 41% | 0% | – |
| TribeRough 3000 | 125 | 43 (30–59) | melee 44, bow 36, long 10, thrown 10 | 35% / 18% | 30% | 0% | 0% (recollect) |
| TribeSavage 1000 | 124 | 14 (10–20) | melee 45, bow 33, long 12, thrown 9 | 44% / 23% | 40% | 0% | – |
| Mechanoid 6000 | 125 | 14 (10–133) | long 31, melee 22, support 18, short 17, medium 7, explosive 5 | 21% / 10% | 6% | 81% | **42/167 (25%)** |

Readings:
- Pirate raids are bimodal: at 1000 pt, 27% are ≥ 80% one class (melee packs, sniper or
  grenadier squads).
- Outlanders are short-gun heavy and almost never single-class.
- Tribes are melee + bow with no explosives.
- Mech kinds (counts over 125 raids): Scyther 604, Lancer 559, Militor 453, CentipedeBlaster 451,
  Pikeman 284, Termite_Breach 98, Cyclops 84, Tesseron 70, Scorcher 47, Legionary 30, Centurion 14,
  CentipedeGunner 12.
- 3 mech raids of 120–133 Militors (GAME_FACTS.md §2).
- Pirate 3000: 12 raiders with weapon `none` (unclassified).

## 7. Results summaries

**results.jsonl (fixed 120, mostly pre-tracker, n=5–11 per cell)**: headline over 12 scenarios:

| Agent | P>amove | Deaths/battle | Win | eng |
|---|---|---|---|---|
| b0 (do nothing) | 0.35 | 4.03 | 0.47 | 0.00 |
| amove (b1) | – | 2.88 | 0.67 | 0.95 |
| doctrine agent | 0.57 | 2.47 | 0.61 | 0.26 |
| turtle (hold v1–v3) | 0.53 | 2.92 | 0.46 | 0.15 |

Notable cells:
- fort_mechs_mid: amove lost 5.0 per battle vs 0.2 for the doctrine agent and 0.0 for b0.
- hard_mechs_mid_open: the doctrine agent had the top median (38.6) at 70% wins vs amove 91%.
- fort_pirate_mirror: the doctrine agent P = 0.96.
- fort_tribe_rush: every agent 0% wins.

`win` here is the legacy definition for 236/241 rows.

**theme.jsonl (theme matrix v1, fixed 120, n=5 per cell, rescored with the current grade):**

| Doctrine | P>amove | Mean score | Win | Lost/battle |
|---|---|---|---|---|
| amove | 0.50 | −98 | 20/35 | 1.31 |
| doctrine agent | 0.46 | −129 | 19/35 | 1.54 |
| turtle | 0.57 | −104 | 19/35 | 1.17 |
| spread | 0.41 | −187 | 16/35 | 1.97 |
| kite | 0.39 | −203 | 13/35 | 1.89 |
| close | 0.54 | −87 | 25/35 | 1.31 |

Best / worst per theme (median score):

| Theme | Best | Worst | P(best > worst) |
|---|---|---|---|
| mechs | close | turtle | 0.72 |
| pirate_grenadier | spread | kite | 0.88 |
| pirate_melee | turtle | kite | 1.00 |
| pirate_mixed | doctrine agent | spread | 0.76 |
| pirate_sniper | doctrine agent | spread | 0.92 |
| tribal_archers | turtle | spread | 0.88 |
| tribal_melee | turtle | spread | 1.00 |

- results/theme_analysis_final.log has the same matrix under the *older* grade (wins 33/35,
  34/35, ...). The difference comes from the newer no-message fallback: broken < 0.5 → defeat.
- The theme rows are stale for kite, the doctrine agent and turtle, whose versions have changed
  since (execution_report).
- pirate_sniper: turtle neutralized 8% (it never engages raiders that outrange it), and every
  doctrine had P = 0.00 vs amove except the doctrine agent (0.36).

Other batches are summarised in their reports: execution_report.md (exec_v1/v2),
reflex_report.md (reflex_check), threatmap_report.md (threatmap_check).
