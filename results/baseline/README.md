# baseline-v1

The frozen reference point (WORKFLOW.md). Later branches are judged against it (no-regression gate).

| What | Value |
|---|---|
| Code | tag `baseline-v1` (doctrine v5 commit 31283f1; matrix runner at 845c4a7 for the other agents — no agent changed in between) |
| Agents | amove v5, doctrine v5 (rescue off), turtle v8, spread v5, kite v5, close v3 |
| Micro | reflex v4 (frag dodge + fire step-out), drill-verified |
| Cycle | adaptive 30/120@40, max 15000 ticks |
| Difficulty | **Peaceful** (the arenas' setting at the time). The evaluation standard is now Strive to Survive (WORKFLOW), so baseline-v1 is **exploration data**; baseline-v2 will be the reference |
| Scenarios | the 7 theme scenarios (frozen OutlanderRough squad of 14, arena_forest, 1500 pt raids); saves in `saves/` |
| Runs | 10 per agent × theme (`core.jsonl`); doctrine **v4** rows in the same file are superseded and kept for the rescue comparison |
| Options | `options.jsonl`: doctrine rescue=off (v4) and turtle wounded_pullback=off, 5 per theme |
| Report | `core_report.md` (`python3 tools/report.py results/baseline/core.jsonl`) |

Headline (lost colonists per battle / wins of 70): kite 1.06/43, amove 1.14/36, doctrine v5 1.20/41,
close 1.27/38, turtle 1.43/42, spread 1.81/30. Oracle routing (best doctrine per theme) 0.64/56.
Known limits: one squad composition and one arena (holdout check still open); n=10 per cell;
the no_progress, losing_trade and precondition thresholds were fitted on this data
(calibration.md), so they are refit on baseline-v2.
