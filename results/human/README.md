# Human play (observe-only demonstrations)

A person plays a scenario; the harness only watches and grades it like an agent episode
(`tools/run_human.py`, PROCEDURES §15). Roadmap 3: the user plays the problems the agents lose
(`results/night/worst.md`), and what worked is distilled into rules for the agents.

## Files

- `play.jsonl`: one graded row per battle (same schema as agent rows, `agent` = player,
  `cycle` = observed). Since 2026-10-05 a row names its trace in `trace`.
- `traces/<id>_<player>_<time>.jsonl.gz`: every poll (~1 s): each pawn's position, health,
  weapon, job and drafted flag, both sides; fires; thrown projectiles; new game messages
  (`rca/eval/trace.py`, read with `trace.read()`). This is the demonstration itself.
- `reports/<id>.md`: a battle report a person can read later: result vs the agent, a route map,
  labelled frames (`rca/eval/frames.py`), what worked and the lessons with frame references.
- `raw/<id>/`: watcher records from the battles played before traces existed (positions and
  jobs at each screenshot), and `raw/build_reports.py`, which drew their frames.

## Battles

| problem | player | result | lost (actual) | raiders out | vs agent | report |
|---|---|---|---|---|---|---|
| t500_pirate_grenadier | human | pyrrhic, then repelled | 1, then 0 | 6, then 4 | agents 164–239% HP | – (summary in TODO roadmap 3) |
| rand_107 (#1) | human | defeat (captives) | 4 | 4 | doctrine: lost 6, 3 out | [rand_107](reports/rand_107.md) |
| rand_067 (#2) | human | defeat (captives) | 1 | 5 | kite: lost 6, 2 out | [rand_067](reports/rand_067.md) |
| rand_030 (#3) | human_swap | **decisive** | 1 | 9 of 9 | close: lost 7, 3 out | [rand_030](reports/rand_030.md) |

"Lost (actual)": the rows count a kidnapped pawn twice (TODO Now 2); the reports correct it.

## What the human games say so far (hypotheses for the gate)

1. **Kidnapping decides Strive battles.** Every defeat above ended with captives. Keep the downed
   inside the group; when a raider's job becomes "kidnapping X", that carrier is the top target
   and standing pawns move onto its path to the edge (rand_067 frames 7–8, rand_107 frames 6–7).
2. **Isolated pawns go down first** (rand_107 frame 4; rand_067 frame 5).
3. **Short-range squads ambush instead of advancing:** wait behind sight-blocking terrain where
   the raid must come round a corner inside our range (rand_030 frames 3–5).
4. **Loadout is a strategic decision:** guns to the best shooters, throwables to the worst,
   while the raid is still far (rand_030 frame 1).
5. **Bows against melee closers:** kiting stretches the raid, but once the melee arrives the
   archers lose; kill the closers before contact, never charge alone (rand_067 frames 3–6).
6. **The briefing needs skills and weapon quality** (rand_107: the router chose blind).
