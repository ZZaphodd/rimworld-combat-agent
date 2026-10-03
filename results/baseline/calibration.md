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
