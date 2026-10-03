# Workflow

## Current stage: pre-baseline (exploration)

The baseline is not stable yet: doctrines, harness, grading and scoring still change, and results
from different agent versions / cycle policies are kept apart by version fields rather than by
branches. The rules below take effect once the baseline checkpoint (TODO roadmap step 2) is frozen
and tagged.

## Test layers (applies now)

Three layers, tested separately; a change touches one layer and the others are held fixed.

| Layer | Question | Suite | Metrics | Held fixed |
|---|---|---|---|---|
| micro | Does it dodge what can be dodged? | Isolated drills (fixed squad, throwers at fixed range), judged per event | dodge success when inside a blast at landing, damage avoided, false-alarm moves, reaction latency | positioning, targeting |
| tactical | Does a given doctrine win locally? | Theme battles | trade ratio, time to resolve, engagement surface, high-threat time, melee-locked time | doctrine choice; micro at its verified version |
| strategic | Right doctrine/asset at the right time? | Scenario-distribution suite | regret vs oracle, outcome grade, colonist losses | tactical implementations (versions) |

Layer contracts (who owns what):

| Layer | Owns | Must not | Reports upward |
|---|---|---|---|
| micro | Short-lived moves for one hazard event (temporary ownership of a pawn) | Change where the doctrine stands pawns; keep a pawn after its event | Cost KPIs: moves, false-alarm share, time not firing |
| tactical | Positioning, targeting, fire control, the doctrine's own phases (setup → hold → commit → reset), stalemate detection | Switch to another doctrine | "Win condition unattainable" (no progress for T ticks, preconditions broken) |
| strategic | Doctrine/asset choice (METT-T), checking doctrine **preconditions**, switching between doctrines | Control individual pawns | — |

Boundary rule: a phase change inside a doctrine (turtle's commit, a sally) is tactical; moving to a
different doctrine (turtle → close) is strategic. Tactical raises the signal, strategic decides.

Pyramid: many cheap micro drills, a moderate number of tactical battles, a costly strategic suite.
The baseline suite measures tactical + strategic; micro is pinned to its drill-verified version.
Tools: micro = `tools/run_drill.py` (frag drill, PROCEDURES §12); tactical/strategic =
`tools/run_eval.py` + `tools/report.py`. Unit tests (`python3 -m unittest discover -s tests -t .`)
cover the offline logic of every layer and run before any game batch.
Lesson that motivated this: threat map v3 changed micro (dodging, hysteresis) and tactical
(standing outside throw range) at once and was judged by battle losses, so neither effect could be
read (results/threatmap_report.md).

## After the baseline is frozen

- **main = baseline.** Code, the scenario suite and the baseline evaluation results live together;
  every frozen point gets a tag (`baseline-v1`, ...).
- **Branches per experiment.** `exp/<save>-...` for tuning on a specific save (e.g. the user's own
  colony), `feat/<name>` for new capabilities.
- **Merge gate.** A branch is never merged on its own results. Re-run the baseline scenario suite on
  the branch and compare with the tagged baseline; merge only if it passes.
- **Gate per layer.** Run the suites of the layer the branch changed plus the layers above it.
- **Pass criterion: no regression (non-inferiority), not "proven better".** Per doctrine × scenario
  cell, P(branch > baseline) must not fall below the noise band, and trade ratio and colonist losses
  must not get worse beyond noise. The gate runs overnight (one game instance).
- **Saves.** Scenario saves (.rws) are versioned too, gzipped in plain git (~13.5 MB -> ~1.4 MB each;
  a restore script unpacks them into RimWorld's Saves folder; switch to LFS only if saves pile up):
  raids are generated randomly, so scripts alone can't reproduce a scenario. Personal colony saves are used on branches only; adding
  one to the baseline suite is a separate decision.
- **Personal branches stay local (the repo is public, read-only for others).** Branches built on a
  personal colony save (`exp/<save>-...`) are never pushed; personal saves are git-ignored. Only
  what passed the merge gate reaches main, without the personal save. Commits use the GitHub
  noreply email.
- **Traceability.** Result rows record agent version, cycle policy and reflex version, plus the
  commit hash.
