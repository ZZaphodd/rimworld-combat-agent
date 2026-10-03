# Data files, schemas and summaries

Summaries in §6–§7 were produced on 2026-10-03 with read-only commands (no game): first with the
legacy scripts (`legacy/raid_census.py --report`, `legacy/eval.py --summary`,
`legacy/theme_analysis.py`), then rescored with `python3 tools/rescore.py` (trade ratio + grade v2,
EVAL_SPEC §5–§6) and `python3 tools/census.py --report`. Data files stay where they were; the only
new data directory is `data/` (derived game tables).

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

## 3b. data/

| File | Content |
|---|---|
| `combat_power.json` | `{PawnKindDef: combatPower}` for 290 kinds, read from the game XML (RimWorld 1.6.4871 rev595, all DLC folders under Data/) by `tools/combat_points.py`. Used for point-weighted trade ratios (EVAL_SPEC §6). Re-extract after a game update |
| `weapon_ranges.json` | `{"weapons": {ThingDef: {label, range, min_range, warmup, burst, verb, tags}}, "mech_kinds": {PawnKindDef: {weapons[], range}}}`: 71 weapon ThingDefs (first verb with a `<range>`, `ParentName` inheritance, `weaponTags` appended along the chain) and 24 `Mech_*` kinds (weapons whose tags meet the kind's `weaponTags`; range = the longest). Same game version and tool (`tools/combat_points.py` writes both). Read by `rca/game/weapons.range_source` (GAME_FACTS §5). Mechs without weapons: Scyther, Centurion, Warqueen, work mechs |

## 4. census/

| File | Content |
|---|---|
| `raids.jsonl` | current census, 998 raids: `{faction, points, route: "faction", raiders[] {kind, weapon, class}, t (s per sample)}` |
| `raids.before_recollect.jsonl` | first pass (936). TribeRough:3000 had only 99 samples (lost to the `largeOutput` bug) and Mechanoid:6000 89 (pod leaks). Both configs were re-collected into raids.jsonl |
| `legacy/logs/census_run.log`, `legacy/logs/census_recollect.log` | console logs incl. failures (git-ignored, local only) |

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
| `phase2/smoke.jsonl` | 20 | **rca** phase-2 doctrine smoke (doctrine v4, turtle v8, spread v5, kite v5, close v3; 2 episodes per doctrine on 2 home themes; adaptive + micro v4), `phase2/smoke.sh` + `.log`. Adds progress, fire-share, signal and options fields (EVAL_SPEC §9). Not a baseline |
| `phase2/options.jsonl` | 4 | **rca** one episode per `vs_throwers` option (stand_off, close_in) for spread on pirate_grenadier and turtle on frag_check: exercises the option, not an evaluation. Mech rows in smoke.jsonl have enemy_fire_share 0.0 (parser gap, fixed later) |
| `phase2/shakeout.jsonl` | 1 | first doctrine v4 episode (before the rescue retry cap) |
| `phase2/mech_firelog_check.jsonl` | 1 | doctrine v4 on theme_mechs after the mech-name firelog fix (enemy fire share 0.72) |
| `prebaseline/mech_recheck.jsonl` | 4 | **rca** doctrine and close on theme_mechs, 2 each, after the firelog fix: enemy_fire_share 0.59–0.73 (smoke rows: 0.0). `prebaseline/checks.sh` + `.log` |
| `prebaseline/signal_check.jsonl` | 4 | turtle and kite on theme_tribal_melee, 2 each, with no_progress rule 2 (kpis `longest_pause_ticks`, `longest_contested_ticks`, `pressure_ticks`) |
| `prebaseline/options_check.jsonl` | 3 | one episode each: doctrine rescue=off, doctrine wounded_pullback=off (pirate_mixed), turtle wounded_pullback=off (pirate_melee); exercises the options, not an evaluation |
| `prebaseline/restart_check.jsonl` | 3 | amove on frag_check: planned restart (`--restart-every 1`) before run 2, crash relaunch (game killed) before run 3. `prebaseline/restart.sh` + `.log` |
| `rca_smoke.jsonl` | 2 | **rca** schema 2: amove v5, adaptive + micro v4, on theme_pirate_mixed and theme_frag_check (smoke test of the new harness) |
| `drills/frag_drill*.jsonl` | – | **rca** micro frag drill: one `event` row per exploded frag (`session, dodge, frag, cell, landed_seen, gone_seen, in_blast, in_zone, escaped, stayed, lost_track, hit_pawns, hit_entries, hit_in_blast, moves, false_alarm_moves, fuse_left_at_move[], latency[]`) and one `session` row (`ticks, throwers, standing_end, returns, names_unique, kpis, moves[]`). `_trial` = first shake-out run |
| `rescored/<file>.jsonl` | = source | per-row verdicts recomputed by `tools/rescore.py`: `grade_stored, grade_v1, grade, score_v1, enemy_lost_points, our_lost_points, ler, ler_basis` (+ identity/config). Raw files untouched |
| `rescored/<file>.md`, `rescored/README.md` | – | summary tables per config: grades, lost/battle, pooled/median LER, P vs amove, old vs new ranking |
| `hazards.jsonl` | 7 | measure_hazards: `{kind, tick, weapons, projectiles[] {def, life, moving, resting}, blasts[]}`; measure_blast: `{kind: "frag_blast_radius", rows[] {d, hit}}` |
| `*.sh / *.log / *.done / *.failed` | – | batch scripts, console logs and end markers |
| `*_report.md`, `hazards.md` | – | reports (DOCS.md) |

Early console logs (`eval_*.log`, `combat_live*.log`) moved from the root to `legacy/logs/`
(git-ignored, local only). `combat_live*` is the
standalone doctrine agent on a real colony (with beds).

**Legacy reading rules:** a missing `agent_version` means pre-versioning. A missing `cycle` means
`fixed:<step_ticks>`. Reflex on without `reflex_version` means v1. Agent `hold` = turtle. Always
recompute `grade/win/score`.

## 6. Census summary (`tools/census.py --report`; faction route, arena_open)

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

**Rescored 2026-10-03 (`tools/rescore.py`; full tables in results/rescored/).** Primary metric:
trade ratio (LER, EVAL_SPEC §6), colonist = 4 raiders by points. All legacy rows have only fate
counts, so their LER is count-based (enemy lost × scenario mean points / colonists lost × 4 ×
mean). Grade v2 (decisive needs standing ≥ 0.5) changed the grade of 2 rows across all files
(exec_v1, exec_v2). The legacy score columns below reproduce the old tables exactly, which checks
the port.

**theme.jsonl (theme matrix v1, fixed 120, n=5 per cell)**:

| Doctrine | P(LER)>amove | LER pooled | Lost/battle | Win | legacy P>amove | legacy mean score |
|---|---|---|---|---|---|---|
| amove | – | 2.00 | 1.31 | 20/35 | 0.50 | −98 |
| doctrine agent | 0.46 | 1.58 | 1.54 | 19/35 | 0.46 | −129 |
| turtle | 0.48 | 1.59 | 1.17 | 19/35 | 0.57 | −104 |
| spread | 0.38 | 1.19 | 1.97 | 16/35 | 0.41 | −187 |
| kite | 0.33 | 1.00 | 1.89 | 13/35 | 0.39 | −203 |
| close | 0.50 | 1.84 | 1.31 | 25/35 | 0.54 | −87 |

Ranking per theme, best first (new = pooled LER, old = median legacy score):

| Theme | New (LER) | Old (score) | Top changed |
|---|---|---|---|
| mechs | doctrine agent (∞) > close (10.0) > amove > kite > spread > turtle | close > spread > kite > doctrine > amove > turtle | yes |
| pirate_grenadier | spread (1.66) > amove (0.90) > turtle > close > doctrine > kite | same | no |
| pirate_melee | turtle (∞) > close (∞) > doctrine > spread > amove > kite | same | no |
| pirate_mixed | amove (0.95) > doctrine (0.92) > close > kite > spread > turtle | doctrine > amove > close > turtle > kite > spread | yes |
| pirate_sniper | amove (2.80) > doctrine (2.00) > close > kite > spread > turtle | doctrine > amove > close > kite > turtle > spread | yes |
| tribal_archers | kite (24.5) > turtle (12.1) > doctrine > close > amove > spread | turtle > kite > doctrine > amove > close > spread | yes |
| tribal_melee | turtle (∞) > close (27.8) > amove > doctrine > kite > spread | turtle > close > kite > amove > doctrine > spread | no |

Readings:
- The bottom of every theme is unchanged and the winners of the decision-relevant themes
  (grenadier → spread, melee → turtle) stand. The top changes on mechs, pirate_mixed,
  pirate_sniper and tribal_archers are between near-ties (P within 0.4–0.6 of each other at n=5).
- Under LER, **nothing beats amove on pirate_mixed or pirate_sniper**: the doctrine agent's old
  edge came from grade bonuses and lower HP loss, not from the exchange.
- Turtle drops from the best legacy headline (0.57) to a tie (0.48): its clean wins are already
  clean under both, but its sniper (8% neutralized, LER 0.08) and mixed (0.44) cells are worse
  trades than the legacy score said.
- Kite's tribal_archers cell (1 colonist lost in 5 battles) is now the top trade of that theme.
- These are the old doctrine versions (kite v1, doctrine v1, turtle v3): stale for routing.

**results.jsonl (fixed 120, mostly pre-tracker, n=5–11 per cell, 12 scenarios)**:

| Agent | P(LER)>amove | LER pooled | Deaths/battle | Win | legacy P>amove |
|---|---|---|---|---|---|
| b0 (do nothing) | 0.24 | 0.30 | 4.03 | 0.47 | 0.35 |
| amove (b1) | – | 0.76 | 2.88 | 0.67 | – |
| doctrine agent | 0.49 | 0.89 | 2.47 | 0.61 | 0.57 |
| turtle (hold v1–v3) | 0.59 | 0.73 | 2.92 | 0.46 | 0.53 |

`win` here is the legacy definition for 236/241 rows.

### Legacy summaries (legacy score; kept for reference)

**results.jsonl** notable cells:
- fort_mechs_mid: amove lost 5.0 per battle vs 0.2 for the doctrine agent and 0.0 for b0.
- hard_mechs_mid_open: the doctrine agent had the top median (38.6) at 70% wins vs amove 91%.
- fort_pirate_mirror: the doctrine agent P = 0.96.
- fort_tribe_rush: every agent 0% wins.

**theme.jsonl** under the legacy score: best / worst per theme (median score): mechs close /
turtle (P 0.72); pirate_grenadier spread / kite (0.88); pirate_melee turtle / kite (1.00);
pirate_mixed doctrine agent / spread (0.76); pirate_sniper doctrine agent / spread (0.92);
tribal_archers turtle / spread (0.88); tribal_melee turtle / spread (1.00).

- results/theme_analysis_final.log has the same matrix under the *older* grade
  (wins 33/35, 34/35, ...). The difference comes from the newer no-message fallback: broken < 0.5
  → defeat.
- pirate_sniper: turtle neutralized 8% (it never engages raiders that outrange it).

Other batches are summarised in their reports: execution_report.md (exec_v1/v2),
reflex_report.md (reflex_check), threatmap_report.md (threatmap_check); rescored tables for all
of them are in results/rescored/.

**rca rows (schema 2):** `rca_smoke.jsonl` (2 smoke episodes, results/rescored/rca_smoke.md:
frag_check decisive in 555 ticks with 0 lost, legacy b1 adaptive median 556 ticks and 0 lost;
pirate_mixed defeat with captives, 5 lost, LER 0.52 by points) and the frag drill
(`drills/frag_drill.jsonl`, per-event table in LESSONS.md §1).
