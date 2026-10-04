# Calibration on baseline-v1 (analysis only — no agent behaviour changed)

Data: results/baseline/core.jsonl, current agent versions (doctrine v5), 420 battles.
"bad" = grade defeat or pyrrhic (189/420).

## no_progress signal (rule 2: contested time without enemy points lost)

| threshold (ticks) | fires | share bad among fires | share of bad battles caught | fires in good battles |
|---|---|---|---|---|
| 1000 | 217 | 0.61 | 0.70 | 85 |
| 2000 | 78 | 0.72 | 0.30 | 22 |
| 2500 | 42 | 0.81 | 0.18 | 8 |
| **3000 (current)** | 28 | **0.82** | 0.12 | 5 |
| 4000 | 12 | 0.83 | 0.05 | 2 |

- At 3000 it is a reliable stalemate detector (82% of fires are in battles that end badly), with a
  median lead of ~1,800 ticks before the battle ends — enough time for a doctrine switch. Keep 3000.
- It catches only 12% of bad battles: most defeats are not stalemates but fights lost quickly.
  → A second signal is needed for those ("losing trade": our losses outpace enemy losses while
  contested). TODO.
- By doctrine: spread 16 fires (13 bad) — spread stalls against everything but grenadiers.

## Preconditions vs where each doctrine actually beat amove

| doctrine | precondition | varies across themes? | verdict |
|---|---|---|---|
| turtle | defensible_terrain (≥0.10) | no — 0.02 on every theme (one forest arena) | Not calibratable here; turtle won on open forest when the enemy came (melee themes). Make it soft, not required. |
| turtle | enemy_approaches (≥0.5) | yes | **Validated.** Good where ≥0.5 (pirate melee 0.91, tribal melee 1.00, mixed 0.50); bad where 0 (grenadier, sniper). Keep 0.5. |
| kite | enemy_melee_heavy (≥0.4) | yes | **Matches** its home themes (0.91, 1.00). Keep. |
| kite / doctrine | ranged_squad (≥0.5) | no — one squad (0.93) | Not calibratable until a 2nd squad. |
| spread | room_to_spread (≥0.7) | no — 1.00 everywhere | Uninformative. Spread only beats amove vs grenadiers → **add an enemy splash-heavy precondition**. |
| close | enemy_outranges (≥0.4) | yes | **Inverted for the current close:** it loses where the enemy outranges (sniper 1.00) and wins where it doesn't (mixed, tribal melee). Its approach is too costly until bounding overwatch. |
| close | approach_cover (≥0.05) | slightly | Unclear. |

Main limit: squad- and terrain-based preconditions are constant in baseline-v1 (one squad, one
arena), so only enemy-based ones can be fitted. Fitting the rest needs the holdout (2nd squad
composition + 2nd arena, e.g. arena_fort).

## Follow-up fits (branch feat/signals-preconditions; `python3 tools/fit_signals.py`)

### losing_trade (second "win condition unattainable" signal, report-only)

Rule (rca/tactical/doctrine.py): from first contact, on a contested step, once **≥ 2 squad pawns
are gone** (dead or carried off) and **enemy points lost < pawns gone × colonist value**
(running trade ratio LER < 1.0; colonist value = 4 × mean raider points; window = cumulative
since first contact), fire once.

Offline data: baseline rows have exact colonist-loss ticks ("Funeral opportunity" and
"kidnapped" messages: they match squad_dead / squad_kidnapped on all 420 rows) but only the
final enemy points, so the enemy curve is bracketed by two proxies: **linear** (points spread
evenly from first contact to the raid's end) and **final** (all points from first contact on:
the fewest fires).

| min pawns gone | LER < | fires (lin / final) | share bad among fires | share of bad caught | fires in good | median lead, ticks |
|---|---|---|---|---|---|---|
| 1 | 1.0 | 166 / 109 | 0.78 / 0.94 | 0.68 / 0.54 | 37 / 6 | 3894 / 3005 |
| 2 | 0.5 | 91 / 65 | 0.91 / 1.00 | 0.44 / 0.34 | 8 / 0 | 3098 / 2557 |
| 2 | 0.75 | 111 / 85 | 0.88 / 0.99 | 0.52 / 0.44 | 13 / 1 | 3062 / 2604 |
| **2** | **1.0** | 121 / 101 | **0.87 / 0.94** | **0.56 / 0.50** | 16 / 6 | **3098 / 2751** |
| 2 | 1.5 | 133 / 129 | 0.82 / 0.83 | 0.58 / 0.57 | 24 / 22 | 3073 / 3051 |
| 3 | 1.0 | 80 / 80 | 0.94 / 0.94 | 0.40 / 0.40 | 5 / 5 | 2344 / 2269 |

- Chosen: **2 pawns, LER < 1.0** ("after two losses we are trading worse than even"). It is as
  precise as no_progress at 3000 (0.87–0.94 vs 0.82) and catches 4–5x more bad battles
  (50–56% vs 12%), with a median lead of ~2,800–3,100 ticks before the episode ends. One pawn
  fires too often in good battles (a single early loss); LER 1.5 adds mostly good battles.
- Together: no_progress catches 23 bad battles, losing_trade 95–105, both 17–18, **either
  101–110 of 189**. What neither catches: defeats by pawns *downed* (not dead) at the end,
  which the trade ratio does not count.
- Lead time is measured to the episode end, not to the moment the battle was decided, so it
  overstates the time a router would have.
- The fit uses proxies; rows from the signal's introduction on carry `kpis.trade_curve`, so the
  fit can be redone exactly (`tools/fit_signals.py <file>` replays them).

### enemy_splash_heavy (spread precondition)

Share of raiders with census class `explosive` (from the scenario manifests; constant per theme):
grenadier 10/13 = **0.77**; mechs 1/8 = 0.13; pirate_mixed 1/14 = 0.07; melee, sniper, archers,
tribal melee 0. Spread beat amove only on grenadier (P(LER) 0.88; ≤ 0.37 elsewhere,
core_report.md). Threshold **0.45**, the middle of the gap 0.13–0.77. One grenadier raid only:
the fit separates the themes, it does not say where between 0.13 and 0.77 spread starts to pay.
Caveat: the class counts a smoke launcher as explosive (1 of the 10 grenadier raiders).

### Exact check on the gate rows (results/gate/signals-preconditions.jsonl, 420 battles, 178 bad)

The gate rows carry `kpis.trade_curve`, so the rule is replayed exactly
(`python3 tools/fit_signals.py results/gate/signals-preconditions.jsonl`):

| min pawns gone | LER < | fires | share bad among fires | share of bad caught | fires in good | median lead |
|---|---|---|---|---|---|---|
| 1 | 1.0 | 174 | 0.75 | 0.74 | 43 | 3795 |
| 2 | 0.75 | 109 | 0.85 | 0.52 | 16 | 3128 |
| **2** | **1.0** | **117** | **0.85** | **0.56** | **17** | **3132** |
| 2 | 1.5 | 124 | 0.85 | 0.59 | 19 | 3150 |
| 3 | 1.0 | 72 | 0.93 | 0.38 | 5 | 2818 |

The proxy fit holds: the chosen rule fires in 117 battles, 85% of them bad, and catches 56% of
bad battles (no_progress on the same rows: 11; either signal: 106 of 178). In-game signal ticks
match the replay. Kept at 2 pawns, LER < 1.0. Precondition values in game equal the manifest
values (enemy_splash_heavy 0.769 on grenadier only; defensible_terrain 0.02, soft).
