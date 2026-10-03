# Doctrine execution report (axis B: does each doctrine do what it claims?)

All runs: frozen OutlanderRough squad of 14 in `arena_forest`, 1500-pt theme raids,
harness step **120 ticks**, max 15000 ticks. Grading and scoring are unchanged (`eval.grade/score`).

## 1. Home themes and intended behaviour

| doctrine (agent) | home themes | intended behaviour (one line) |
|---|---|---|
| spread (`spread`) | pirate_grenadier | keep >= 5 cells between pawns so one blast hits one pawn; each fights its own nearest raider |
| kite (`kite`) | pirate_melee, tribal_melee | shooters never stand in melee; the raid crosses open ground under fire; melee pawns intercept |
| hold (`hold`) | pirate_melee, tribal_melee, tribal_archers | man a planned firing line and let the raid come to it; sally only when the raid won't come / won't die |
| close (`close`) | pirate_sniper, mechs | get inside the enemy's effective range fast (cover to cover), then fight up close |
| focus (`doctrine`) | pirate_mixed, mechs | concentrate fire: few targets, many guns on each, priority kinds first |

Kept as suggested. Note: on mechs, hold (not home) had the known stall problem; it was
fixed too because it is an execution bug, not a concept mismatch.

## 2. Behaviour KPIs (new)

Agents keep a `kpis.Tally` fed from data they already read each step (no extra game
calls); `eval.run_episode` stores `agent.kpis()` as `kpis` and `agent.version` as
`agent_version` in each result row. `--resume` now only counts rows whose version and
`step_ticks` match the current implementation, and `theme_analysis.py` warns if a cell pools
versions and prints a KPI table. Most KPIs count only **contact steps** (a raider within
30 cells of a fighter).

| doctrine | KPIs |
|---|---|
| all doctrine agents | `gap5_share`: share of fighter-steps whose nearest squadmate is >= 5 cells away |
| spread | `mean_gap` (nearest-ally distance, capped at 15) |
| kite | `shooter_melee_dist` (mean distance shooter -> nearest melee raider, when within 30), `melee_adjacent_share` (<= 1.5 cells), `retreat_share` (shooter-steps spent running instead of shooting) |
| hold | `first_shot_tick` (first step a raider is in weapon range of a shooter on its slot), `on_slot_share` (while holding), `longest_stall_ticks` (contact with no raider lost), `sally_tick`, `sally_reason` |
| close | `close_tick_mean` (tick each pawn first gets inside CLOSE_DIST, averaged), `closed_n` |
| focus | `assigned_share`, `targets_per_step`, `guns_per_target`, `attacking_share` (fighters whose job is an attack; v2 only) |

"Before" KPIs come from re-running the v1 code with KPIs on (`results/exec_v1.jsonl`,
2-3 runs per cell). "After" = `results/exec_v2.jsonl`. Outcome "before" pools v1 rows from
`results/theme.jsonl` (n=5) and `exec_v1.jsonl`.

## 3. Per doctrine

### kite: v1 -> v3 (home: pirate_melee, tribal_melee)

**Problem (traced, pirate_melee).** Before contact, v1 gave every shooter an Auto attack
because nothing was in range, so the whole squad walked toward a raid ~95 cells away.
That doubled the closing speed. Once raiders were within 10 cells, every threatened
shooter backed off 8 cells *directly away from its own threat*. With equal speeds that
buys no free shots. Shooters spent ~half their contact steps walking (`retreat_share`
0.48-0.60), the squad scattered over 50-160 cells, and in the end everyone chased one
lingering raider across the map (2 timeouts). A first fix (v2: anticipate by raider
speed x step, run through the squad) made it worse: at 120 ticks, "can reach you before
the next decision" (~12.6 cells) covered nearly every shooter, so the whole squad ran
and nobody fired (traced: 12/14 "moving", 7 downed). That version was not kept.

**Fix (v3).**
- Nobody advances while melee raiders are coming. Drafted pawns standing still fire at will.
- Only the shooter a melee raider is actually after runs. That shooter is taken from the raider's own `targeting` "attacking colonist <name>", falling back to the nearest shooter, and only if the raider is within reach (RAIDER_SPEED x step_ticks + MARGIN).
- The runner goes *through* the squad to its far side, so the chaser is dragged past everyone else's guns.
- Melee pawns intercept the raider nearest any shooter.
- Auto attack ("sweep") starts only once no melee raider has pressed for 3 contact steps, or none exist.

| | pirate_melee v1 | v3 | tribal_melee v1 | v3 |
|---|---|---|---|---|
| wins | 1/8 | **5/5** | 3/8 | **5/5** |
| mean lost | 1.5 | 0.2 | 1.5 | 0.4 |
| median score | -108 | 135 | -117 | 134 |
| P(v3 > v1) | | 0.97 | | 0.93 |
| median ticks | 10526 | 5404 | 8656 | 7337 |
| retreat_share | 0.48 | **0.14** | 0.60 | **0.27** |
| shooter_melee_dist | 11.8 | 10.7 | 10.0 | 9.4 |
| melee_adjacent_share | 0.06 | 0.05 | 0.08 | 0.14 |
| gap5_share | 0.57 | 0.10 | 0.67 | 0.16 |

Read faithfully: the win came from **more shooting time and cohesion**, not from keeping
melee raiders farther away. Distance and adjacency KPIs are flat or slightly worse on
tribal_melee, and the squad is much tighter (gap5 0.1-0.16). In effect kite v3 is
"stand and fire, peel the hunted pawn through the group". That tightness would be a
liability against explosives.

### focus: v1 -> v2 (home: pirate_mixed, mechs)

**Problem (traced, pirate_mixed and pirate_grenadier).**
1. Focus orders were always "Auto attack (AI)". At the moment of contact that makes pawns walk off for cover: 12-13 of 14 were "moving" exactly when the raid arrived.
2. Assignments were only refreshed every 10 steps. A pawn whose attack job had ended kept a stale assignment and was never re-ordered (`assigned_share` dropped to 0.21 in the 8-loss run).
3. The rally grid had 2-cell spacing.

The "implausibly low engagement vs grenadiers" is mostly a **measurement artefact**.
`engagement_ratio` counts only "attacking ..." jobs. Drafted pawns firing at will show
"watching for targets" and are not counted, which is also why hold scores ~0.0. The real
grenadier loss was the packed squad: 8 pawns downed in ~4 steps once the raid was at 2-4 cells.

**Fix (v2).**
- A ranged pawn whose focus target is in weapon range gets vanilla "Fire at" (stand and shoot). Auto attack is used only when out of range.
- Target picking prefers in-range targets (+15).
- Assignments whose pawn is no longer attacking or moving are dropped and re-issued.
- Disabled float-menu options ("Fire at: Out of range") are skipped.
- Rally spacing is 3 cells.

| | pirate_mixed v1 | v2 | mechs v1 | v2 |
|---|---|---|---|---|
| wins | 4/8 | 3/5 | 8/8 | 5/5 |
| mean lost | 2.5 | 1.4 | 0.2 | 0.2 |
| median score | -143 | -23 | 140 | 103 |
| P(v2 > v1) | | 0.62 (tie) | | 0.53 (tie) |
| assigned_share | 0.54 | 0.67 | 0.66 | 0.73 |
| targets_per_step / guns_per_target | 2.9 / 2.6 | 3.5 / 2.7 | 2.9 / 2.9 | 3.2 / 3.3 |
| attacking_share | n/a | 0.55 | n/a | 0.40 |

**Verdict: not shown to help.** Outcomes are a tie on both home themes. The KPIs show more
fighters with an assignment, but concentration (guns per target) barely moved. The
pirate_mixed v2 loss was again a kidnapping/rout (4 lost). Grenadier check (not home,
n=3): still 0/3 wins, 5.0 lost (v1 5.2), `gap5_share` ~0.4. Rally spacing 3 was not enough.

### hold: v3 -> v4 (home: pirate_melee, tribal_melee, tribal_archers; fix targeted mechs)

**Problem (traced, mechs).** After the first exchange, 4-5 mechs parked 13-28 cells from
the line, out of sight or not attacking. The idle-sally rule resets whenever *any* raider is
within 30 cells, so it never fired. The line sat 40+ steps while pawns were picked off
(1 -> 3 downed) and 2/5 runs timed out.

**Fix (v4).** Added a stall sally: in contact with no raider lost for 12 steps (1440 ticks),
go get them. The idle rule is kept.

| | mechs v3 | v4 | tribal_melee v3 | v4 | pirate_melee v3 | v4 |
|---|---|---|---|---|---|---|
| wins | 5/7 | **4/4** | 7/7 | 2/2 | 5/5 | 2/2 |
| mean lost | 0.7 | 0.2 | 0.0 | 0.5 | 0.0 | 0.0 |
| median score | 70 | 125 | 139 | 74 | 142 | 159 |
| P(v4 > v3) | | 0.68 | | 0.21 (n=2) | | 0.60 |
| sally_reason | never | stall in 4/4 (mean tick 7950) | - | none | - | none |
| on_slot_share | 0.36 | 0.38 | 0.86 | 0.89 | - | 0.83 |
| first_shot_tick | 4380 | 4290 | 2040 | 2040 | - | 1680 |

The rule never fired on the melee home themes (stalls there <= 360 ticks), so the
tribal_melee dip (one pawn lost in one of 2 runs) is not caused by the change. Treat it as noise.

### spread (home: pirate_grenadier): no change (v1)
Already wins at home (4/5 in v1). KPIs confirm it does what it claims: `gap5_share`
0.71-0.79 (focus 0.4, kite v3 0.1, hold 0.1-0.25), `mean_gap` 5.7-6.9. 2 KPI runs: 1
repelled, 1 pyrrhic (3 lost).

### close (home: pirate_sniper, mechs): no change (v1)
4/5 and 5/5 at home in v1. KPIs (sniper, n=2): all 14 pawns close inside 14 cells, mean
close tick 1380 (~11 steps). The 2 KPI runs went 1 defeat / 1 repelled with 1 lost each, so
sniper is its weaker home theme. Not changed because no execution fault was traced. Its
losses are taken during the approach, which is the concept's cost.

## 4. v2 matrix: NOT RUN (by instruction)

The coordinator relayed a change of plan: the harness step will be shortened for all
agents (~30 ticks in close combat), so the 210-run matrix at 120 ticks was cancelled before
it started. `results/theme_v2.jsonl` does not exist (0 rows). Only home-theme verification
runs exist (above). The v1 matrix (`results/theme.jsonl`) stays the reference, but **it is now
stale for kite, focus and hold**, whose versions changed.

## 5. Things that assume a 120-tick step (retune for the shorter cycle)

> Done: all items below are now in ticks (adaptive 30/120 cycle); see `results/reflex_report.md` section 1.

- **kite**:
  - `reach = RAIDER_SPEED (0.08 c/tick) x step_ticks + MARGIN (3)` already scales with `agent.step_ticks` (eval now sets it). At 30 ticks reach is ~5.4 cells, which is probably too tight given path start-up. Re-tune `MARGIN`.
  - The v2a failure mode ("everyone in reach runs") came from 120 ticks. At 30 ticks the hunted-only rule may become unnecessary, or the anticipation version may work. Re-test both.
  - `calm >= 3` steps before sweeping, `REAR = 5`, `PRESS = 40`.
- **hold**: `STALL_SALLY_STEPS = 12`, `IDLE_SALLY_STEPS = 40` and `REPLAN_COOLDOWN = 10` are counted in *steps*. Convert them to ticks, or they shrink 4x at 30 ticks (a 360-tick stall would trigger a sally).
- **focus**:
  - `Doctrine.retarget_every = 10` steps (full re-assignment) is step-based too.
  - Stale-assignment re-issue runs every step, so a 4x shorter step means ~4x more `order_pawn` calls.
  - `Doctrine.step_ticks` is unused under the harness.
- **spread**: `HOLD_STEPS = 4` and `STEP_OUT = 5` cells are sized per 120-tick step.
- **close**: `ADVANCE = 10` cells per step.
- **battle_tracker**: `EDGE = 12` ("a walker covers ~9 between 120-tick samples") and `harvest_every = 5` steps.
- **KPIs**: `first_shot_tick` / `sally_tick` resolution is one step. "calm" and "stall" counters are in steps, but the stall KPI is reported in ticks.
- **Cost**: wall time is ~0.5 s per step, mostly harness observation; agent think time is 18-26% of it. A 30-tick step is about 4x the steps, so ~2 min per episode and **~7 h for 210 runs** instead of ~1.7 h. RimWorld crashed after ~150 loads last time, so plan restarts around every 100 episodes.

## 6. Open issues

- `engagement_ratio` undercounts every doctrine that relies on fire at will (hold ~0.0, kite, focus). Do not use it to compare doctrines. A KPI from the game's attack verbs or damage log would be needed.
- focus on pirate_mixed is still a coin flip (3/5). The fix improved the assignment KPIs but not concentration or outcome, and the failures are routs with kidnappings. A next attempt could pull wounded pawns back and rescue them instead of undrafting them (undrafted = Flee hostility response).
- focus vs grenadiers remains catastrophic (5 lost/battle). That is a selection problem (route grenadiers to spread), but focus could also adopt spread's spacing.
- kite v3 is very compact (gap5 0.1-0.16). Selection should never send it against explosive raids. Its distance KPIs did not improve; the gain is shooting time.
- hold v4 tribal_melee dip and all other v2 cells: n=2-5 only. Needs the full matrix at the new step.
- tribal_archers (a hold home theme) was not re-verified after hold v4. The stall rule could fire against archers holding at bow range; check it in the next matrix.
- No game restarts were needed in this session (about 45 save loads).

## Files

- New: `kpis.py`, `results/execution_report.md`, `results/exec_v1.{sh,log,jsonl,done}` (v1 KPI baselines), `results/exec_v2.{sh,log,jsonl,done}` (home-theme verification).
- Changed:
  - `eval.py`: `version` on B0/B1/focus, `step_ticks` passed to agents, `kpis`/`agent_version` in rows, version-aware `--resume`, focus KPIs.
  - `combat_agent.py`: focus v2.
  - `doctrines.py`: shared KPI plumbing, kite v3, spread/close KPIs, version attrs.
  - `hold_agent.py`: v4 stall sally + KPIs.
  - `theme_analysis.py`: multiple files, version-pool warning, KPI table, crash fix when no aggressive rows.
