# Workflow

## Current stage: evaluation standard changed — baseline-v2 pending

baseline-v1 (tag on GitHub, results/baseline/README.md) was measured on the **Peaceful** difficulty.
The evaluation standard is now **Strive to Survive** (below), so baseline-v1 and every gate run
against it are **exploration data**. Until baseline-v2 exists there is no valid reference:
**no gate verdicts and no behaviour-changing merges**. Measurement-only work (KPIs, drills,
analysis) may continue and merge on passing unit tests. The repo is public on GitHub (origin);
main and tags are pushed after a passing gate (or, for measurement-only work, passing tests);
feature branches may stay local.

## Evaluation standard

Every evaluation battle (baseline, gate, theme batches) uses the same environment. Changing any
item means a new baseline.

| Item | Value |
|---|---|
| Difficulty | **Strive to Survive** (threat scale 100%; the user's normal play). Raids are spawned with explicit points, so threat scale doesn't size them; what differs from Peaceful is enemy death-on-downed (×1.0 vs ×0.5) and colonist mood offset (0 vs +10, mental breaks). Strive allows storyteller threats: the harness must detect unexpected raids and invalidate the episode |
| Scenarios | the 7 theme scenarios (frozen squad of 14, arena_forest, 1500 pt raids) |
| Decision cycle | adaptive 30/120@40 |
| Episode cap | 15000 ticks |
| Game restart | every 100 episodes |
| Runs per cell | 10 |

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
  cell, trade ratio and colonist losses must not get worse beyond noise; exact rule below
  (`tools/gate.py`). The gate runs overnight (one game instance).
- **Version bumps.** Any change an agent's rows could show (behaviour, or report-only signals and
  precondition data) bumps that agent's version, so rows never mix; the gate re-runs every agent
  whose version changed. After a report-only bump the gate is an A/A run (same behaviour on
  both sides), which also checks the gate's own false-alarm rate (feat/signals-preconditions).

- **Saves.** Scenario saves (.rws) are versioned too, gzipped in plain git (~13.5 MB -> ~1.4 MB each;
  a restore script unpacks them into RimWorld's Saves folder; switch to LFS only if saves pile up):
  raids are generated randomly, so scripts alone can't reproduce a scenario. Personal colony saves are used on branches only; adding
  one to the baseline suite is a separate decision.
- **Personal branches stay local (the repo is public, read-only for others).** Branches built on a
  personal colony save (`exp/<save>-...`) are never pushed; personal saves are git-ignored. Only
  what passed the merge gate reaches main, without the personal save. Commits use the GitHub
  noreply email.
- **Traceability.** Result rows record agent version, cycle policy, reflex version, difficulty and
  the commit hash.

### Gate rule (`tools/gate.py`)

```
python3 tools/gate.py results/gate/<branch>.jsonl          # vs results/baseline/core.jsonl
python3 tools/gate.py --simulate                           # false-alarm rate / power
```

- **Rows.** Cells = agent × scenario. Each side: one version per agent (highest in the file, or
  `--base-version` / `--branch-version`), natural options only, the branch's config (cycle,
  reflex) on both sides. A cell with < 5 battles on a side is INCOMPLETE (→ FAIL).
- **Per battle:** `lost` = colonists lost (dead + kidnapped); `trade` = trade share
  E / (E + O) (enemy points lost, our points lost = lost × colonist value; 1 = clean, 0.5 =
  even or nothing lost) — the bounded twin of LER = trade / (1 − trade), so a mean exists when
  LER = ∞.
- **Worsening** d per cell: d_lost = mean(branch) − mean(baseline), d_trade = mean(baseline) −
  mean(branch). Uncertainty: percentile bootstrap, each side resampled on its own, 4000 draws,
  fixed seed.
- **Cell regression:** the 98% interval of d lies wholly above the margin
  (**0.5 colonists per battle**, **0.10 trade share**).
- **Agent regression:** pooled over the agent's scenarios (d = mean of its cells' d, stratified
  bootstrap), the 95% interval lies wholly above a quarter of the margin (0.125 colonists per
  battle, 0.025 trade share).
- **PASS** = no cell regression, no agent regression, no incomplete cell. `watch` cells (90%
  interval above 0 and d > margin) are printed but do not fail the gate.
- **Why these widths** (`--simulate`: A/A resampling of baseline-v1 cells, 60 trials): with 42
  cells × 2 metrics a per-cell "90% interval above 0" rule fails an unchanged branch ~93% of the
  time. This rule: unchanged branch FAILs ~8% (cell rule 5%, agent rule 3%); +0.5 colonists per
  battle in every cell of an agent → FAIL ~100% (agent rule); +1 colonist per battle in one
  median-noise cell only → ~18%. **Limit:** at n = 10 a regression confined to one cell is
  caught only when it is large relative to that cell's noise; a change aimed at one theme
  should add runs for that theme on both sides.
