# Docs index

| File | What it is for |
|---|---|
| [README.md](README.md) | What the repo is, requirements, license |
| [TODO.md](TODO.md) | Roadmap, scope principle (overfit to the built-in AI), open work items |
| [GLOSSARY.md](GLOSSARY.md) | Shared vocabulary: layers, doctrine names, threat and positioning terms, words to avoid |
| [WORKFLOW.md](WORKFLOW.md) | Test layers (micro / tactical / strategic) and the post-baseline branch and merge-gate rules |
| [RIMMOLT_API.md](RIMMOLT_API.md) | RimMolt transport, every tool we use with its quirks, debug-menu rules, failure modes, agent sandbox |
| [GAME_FACTS.md](GAME_FACTS.md) | RimWorld mechanics and measured constants, plus the built-in enemy AI behaviour (seed of ENEMY_AI.md) |
| [PROCEDURES.md](PROCEDURES.md) | Runbooks: arenas, fort, load wait, raid spawning, squad and theme building, census, episode start, watchdog, resume |
| [EVAL_SPEC.md](EVAL_SPEC.md) | Harness contract: time and cycle, agent interface, fates, grade/score, KPIs, result row schema |
| [DATA.md](DATA.md) | Every data file and its schema, legacy formats, census and results summaries, what is irreproducible |
| [LESSONS.md](LESSONS.md) | Micro/tactical/strategic lessons with evidence and implications; known bugs to fix in the rewrite |
| [results/baseline/README.md](results/baseline/README.md) | baseline-v1: what was frozen, how it was run, headline numbers (Peaceful difficulty — exploration data since the switch to Strive to Survive) |
| [results/baseline/calibration.md](results/baseline/calibration.md) | Fits on baseline data: no_progress and losing_trade signals, preconditions vs outcomes |
| results/gate/*_gate.md | Gate verdicts, one per branch (per-cell table, PASS/FAIL) |
| [results/rescored/README.md](results/rescored/README.md) | Every legacy results file rescored by trade ratio + grade v2 (tables per config, old vs new ranking) |
| [results/hazards.md](results/hazards.md) | Telegraphed area attacks: reaction windows, frag fuse and blast reach |
| [results/theme_report.md](results/theme_report.md) | Theme × doctrine matrix v1 (first 113 episodes; the full 210-row table, rescored, is results/rescored/theme.md and DATA.md §7) and the pre-registered predictions |
| [results/execution_report.md](results/execution_report.md) | Does each doctrine do what it claims: behaviour KPIs, kite v3, focus v2 (now the `doctrine` agent), hold v4 (now turtle) |
| [results/reflex_report.md](results/reflex_report.md) | Adaptive decision cycle and reflex layer v1/v2: design, cost, validation |
| [results/threatmap_report.md](results/threatmap_report.md) | Threat heatmap and reflex v3a/v3b: design, weights, validation, open issues |
| ENEMY_AI.md (planned) | Built-in enemy AI knowledge base with evidence (TODO roadmap 3); starts from GAME_FACTS.md §8 |

## Code layout

| Path | Layer / role |
|---|---|
| `rca/rimmolt.py` | RimMolt client (RIMMOLT_API.md) |
| `rca/game/` | owning the game: `session` (load, episode start, save guard, watchdog), `debug` (debug-menu helpers), `builders/` (arena, scenario, theme, frag_check), `census`, `weapons` (one classifier, XML ranges), `defs` (combat points and weapon ranges from the XML) |
| `rca/terrain.py` | the one terrain model: legend, LOS, BFS, per-episode cache with event invalidation |
| `rca/micro/` | micro layer: `reflex` (frag dodge, fire step-out, viscosity, ownership, re-entry hysteresis), `drills` (per-event frag drill) |
| `rca/tactical/` | doctrine interface (`doctrine`: phases, signal, options), `preconditions` (cheap checks), `squad` (shared plumbing: casualties, vs-throwers option), `planner` (battleground v4), doctrines `b0`, `amove`, `focus` (code name `doctrine`), `turtle`, `spread`, `kite`, `close`; each spec is its module docstring |
| `rca/strategic/` | placeholder for the router |
| `rca/eval/` | `harness`, `tracker` (fates, pooled battle log), `scoring` (grade, trade ratio), `results` (schema, aliases, resume), `report`, `kpis`, `progress` (progress rate, no-progress stretch), `firelog` (battle-log fire share) |
| `tools/` | CLIs: make_arena, build_scenarios, build_themes, census, combat_points, run_eval, run_drill, report, rescore, gate (merge gate), fit_signals (signal threshold fits), rm (compact game probe) |
| `tests/` | `python3 -m unittest discover -s tests -t .` (offline, no game) |
| `legacy/` | the exploration code and batch scripts (reference only; rca never imports it) |
