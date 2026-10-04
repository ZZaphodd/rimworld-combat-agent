# Evaluation harness contract

What the harness (`rca/eval/harness.py`, CLI `tools/run_eval.py`) does and promises. It ports
legacy/eval.py; where they differ, the difference is listed here so old and new rows can be
compared. Terms follow GLOSSARY.md: amove = code `amove` (old rows: `b1`), the doctrine agent =
code `doctrine`, turtle = code `turtle` (alias `hold`), plus spread, kite and close. Rows are
read through `rca/eval/results.read_rows`, which maps every alias to its canonical name.

## 1. Time ownership, cycle, sandbox

- **The harness owns game time.** The game is paused while the agent thinks. The agent issues
  orders, then the harness advances `step_ticks` with
  `wait_for_event(maxGameTicks=step, maxSeconds=60, pause="always", force=True)` (client timeout
  90 s), then observes again. `force=True` bypasses RimMolt's 1-hour crisis cap (tool schema);
  the wait can still end early on a letter or message, so elapsed time is always read from
  `get_status.ticksGame`. Agents never call time, save or debug tools (sandbox, RIMMOLT_API.md §6).
- **Adaptive cycle** (default `adaptive:30/120@40`): a step is **30 ticks if any live raider is
  within 40 cells of any squad pawn that has no fate yet, else 120**. This is decided before each
  step from the tracker's last observation, at no extra calls. 30 is the shortest cycle that is a
  whole number of 15-tick quanta, and a frag rests ~90 ticks. `--cycle fixed` = always
  `--step-ticks`. CLI: `--step-ticks 120 --fast-ticks 30 --fast-radius 40 --cycle adaptive|fixed`.
- Policy string stored in every row: `adaptive:<fast>/<calm>@<radius>` or `fixed:<calm>`.
- Episode limit `--max-ticks` (rca CLI default 15000, as every legacy batch used; legacy CLI
  default was 20000). 2500 ticks = 1 in-game hour.
- Episode start: see PROCEDURES.md §9 (load, Never Force Normal Speed, dev mode off).
- **Environment:** every evaluation battle uses the evaluation standard (WORKFLOW.md: difficulty
  Strive to Survive, the theme scenarios, this cycle and cap). baseline-v1 and the calibration
  fits in §2 ran on Peaceful: exploration data, refit on baseline-v2.
- An agent exception costs it that step (`agent_errors += 1`), never the episode. A harness or game
  exception retries the episode once (after the watchdog has checked the game, PROCEDURES §10),
  then logs it to `<results>.errors.jsonl`.
- **Terrain is per episode** (`rca/terrain.py`): the harness creates one `Terrain` per episode,
  hands it to the agent as `agent.terrain`, and feeds it each step's `_delta` and the squad's
  positions (contact refresh); the micro layer feeds fire cells and `Explosion` things.

## 2. Agent interface

```
class Doctrine:                         # rca/tactical/doctrine.py
    name: str                 # canonical code name; stored in rows
    version: int              # bump on any behaviour change (amove starts at 5: b1 rows are 1-4)
    win_condition: str        # prose; the full spec is the module docstring
    preconditions: dict       # {check name: params}, rca/tactical/preconditions.py
    phases_spec: dict         # setup / hold / commit / reset, prose
    option_choices: dict      # {option: (natural value, alternatives...)}, e.g. vs_throwers
    no_progress_ticks: int    # 3000 contested ticks raise the no_progress signal (baseline-v1 fit; refit on v2)
    # set by the harness before reset():
    reflex: bool              # micro layer may act (False: observe and count only)
    rx_version: int           # micro version, stored as reflex_version (rca micro = 4)
    terrain: Terrain          # one per episode
    options: dict             # CLI overrides (--option key=value); see effective_options()
    # set before every step():
    step_ticks: int           # length of the coming step
    now: int                  # episode tick at the start of the coming step
    def reset(self, rm, manifest)   # episode start; builds self.micro (MicroLayer)
    def step(self, rm)              # observe + order; must not advance time
    def kpis(self) -> dict          # stored as row["kpis"]; includes rx_*, terrain_*, phase_log
    signals: list             # "win condition unattainable" history, read by the harness
    def effective_options(self) -> dict   # stored as row["options"]; part of the resume key
```

- **Layer contract (WORKFLOW):** a doctrine owns positioning, targeting, fire control and its own
  phases (setup → hold → commit → reset; a commit such as turtle's sally is a phase, tactical).
  It never switches to another doctrine. It raises **"win condition unattainable"** into
  `signals` — `{tick, reason, phase}` (+ `pause, contested` for no_progress; + `lost, our_pts,
  enemy_pts, ler` for losing_trade) with reason `no_progress` (below), `losing_trade` (below)
  or `precondition:<name>` (a runtime break, e.g. turtle
  `precondition:enemy_approaches` when its idle sally fires, `precondition:no_approach` when the
  raid is already inside). The harness only records it; the strategic layer will consume it
  (roadmap 5).
- **no_progress, rule 2 (contested time; `kpis.no_progress_rule = 2`, from commit 6c041e6).**
  A stalemate is "we are not taking them down **while** we pay for it or are exposed", not a
  quiet pause. Per doctrine, from the first contact step (a live raider within 30 cells of a
  fighter):
  1. *Progress* = the doctrine-side enemy points lost increase (raiders once seen live that are
     no longer live; `data/combat_power.json`; raiders last seen within 12 cells of the map edge
     count 0: walking off is not progress).
  2. Each observation (once per agent step) is *pressed* if **cost** or **threat** holds
     (`rca/eval/progress.pressure`):
     - cost: since the previous observation a squad pawn's summary health (list_colonists
       `health`, %) fell by more than 0.5, a squad pawn became downed, or a squad pawn present
       before is no longer listed (dead or carried off);
     - threat: a live, non-downed raider is within its own weapon range of a squad pawn on the map
       (standing or downed). Range = the XML verb range of its weapon (`rca/game/weapons`; melee
       1.5, unknown 25); a frag/molotov carrier counts within max(range, 12.9 throw + 1.9 blast)
       = 14.8. Distance only: no line of sight.
  3. *Contested time* = the sum of the lengths of pressed steps (the step that ended at the
     observation) since the last progress. Progress resets it to 0 and re-arms the signal.
  4. The signal fires once per stretch when contested time ≥ `no_progress_ticks` = **3000
     (fitted on baseline-v1 and kept; refit on baseline-v2; see the KPIs paragraph below)**. The raw pause (time since the last progress)
     is still measured, but only as a KPI.
  Rule 1 (rows before 6c041e6, `no_progress_rule` absent) fired on the raw pause alone: in the
  phase-2 smoke it fired in 2 of 20 battles (turtle and kite on tribal_melee), both won; in the
  pre-baseline re-check (results/prebaseline/signal_check.jsonl) the same two cells had pauses of
  3164 and 3122 ticks (rule 1 would fire) with 1500 and 418 contested ticks (rule 2: no signal).
  KPIs: `longest_pause_ticks`, `longest_contested_ticks`, `pressure_ticks {cost, threat, either,
  total}` (ticks after first contact). **Fitted on baseline-v1** (Peaceful; refit on baseline-v2; results/baseline/
  calibration.md): at 3000, 82% of fires are in bad battles (defeat/pyrrhic), median lead ~1,800
  ticks, but only 12% of bad battles are caught. Kept at 3000. Known limits: no LOS (a raider behind a wall counts as a
  threat); a carried pawn stays in `list_things` (GAME_FACTS §7) but whether `list_colonists`
  keeps it is UNVERIFIED (if not, it reads as a cost for one step); whether blood loss lowers
  summary health is UNVERIFIED.
- **losing_trade (second signal, report-only; from amove v6, doctrine v6, turtle v9, spread v6,
  kite v6, close v4).** For the fast defeats no_progress misses: "our colonist losses outpace
  the enemy points we take". Per doctrine (`Doctrine.note_trade`), from first contact, on an
  observation whose step was *pressed* (cost or threat, as above):
  1. *pawns gone* = squad pawns listed by `list_colonists` before and missing now (dead or
     carried off); *our points* = pawns gone × colonist value, colonist value =
     `COLONIST_ENEMIES` (4) × the mean combat points of the raiders seen so far (§6);
  2. *enemy points* = the doctrine-side progress meter (points of raiders no longer live;
     edge walk-offs 0);
  3. window: cumulative since first contact; fires **once** when pawns gone ≥ **2** and enemy
     points < **1.0** × our points (running LER < 1).
  Fitted offline on baseline-v1 (Peaceful; refit on baseline-v2; calibration.md, `tools/fit_signals.py`): 87–94% of fires in bad
  battles, 50–56% of bad battles caught (no_progress: 12%), median lead ~2,800–3,100 ticks; the
  enemy curve is a proxy there (baseline rows store only final points). Rows carry
  `kpis.trade_curve` `[[tick, pawns gone, enemy points], ...]` (each change, ≤ 60) and
  `kpis.losing_trade_rule {min_lost, ler, window}`, so the fit can be redone exactly. No
  doctrine acts on it; the strategic layer will.
- **Preconditions** are data on the class, checked by `preconditions.check(doctrine, Context)`
  (terrain + squad `{pos, range, melee}` + enemies `{pos, cls, range}`; a few terrain tiles, no
  planner run). Each result is `{ok, value, need}`. Squad doctrines evaluate them once at reset
  and store them as `kpis.pre_<name>`. A check with `"soft": True` in its params is recorded
  (result `{ok, value, need, soft: true}`) but never makes the doctrine unattainable
  (`preconditions.all_ok` ignores it). Status after the baseline-v1 calibration
  (results/baseline/calibration.md; Peaceful, refit on baseline-v2): only enemy-based checks vary in baseline-v1 (one squad,
  one arena), so squad- and terrain-based thresholds stay UNVERIFIED until the holdout. Checks:
  `ranged_squad`, `defensible_terrain` (wall/rock + ½ tree
  share within 14 of the anchor), `enemy_approaches` (melee/short/thrown share), `enemy_melee_heavy`,
  `enemy_splash_heavy` (census class `explosive` share), `room_to_spread` (passable share within
  10), `enemy_outranges` (raiders with range ≥ our median + 5), `approach_cover` (cover cells
  along the line to the raid).

  | Doctrine | Preconditions | Status |
  |---|---|---|
  | amove, b0 | – | |
  | doctrine | ranged_squad ≥ 0.5 | UNVERIFIED (one squad, 0.93) |
  | turtle | enemy_approaches ≥ 0.5; defensible_terrain ≥ 0.10 **soft** (turtle v9) | enemy_approaches validated; terrain 0.02 on every theme of the one arena and turtle won there vs melee → soft |
  | spread | enemy_splash_heavy ≥ 0.45 (spread v6); room_to_spread ≥ 0.7 | splash fitted (grenadier 0.77 vs ≤ 0.13); room uninformative on one arena (1.00 everywhere) |
  | kite | enemy_melee_heavy ≥ 0.4, ranged_squad ≥ 0.5 | melee_heavy matches its home themes; ranged_squad UNVERIFIED |
  | close | enemy_outranges ≥ 0.4, approach_cover ≥ 0.05 | **inverted for close v3/v4** (loses where the enemy outranges); unchanged until bounding overwatch |
- **Tactical option `vs_throwers`** (positioning vs frag/molotov carriers; TODO phase-2 req. 3),
  offered by doctrine, turtle and spread: `accept_dodge` (natural: stay where the doctrine puts
  the pawn, micro dodges), `stand_off` (a shooter within 12.9 + 1.5 of a thrower steps back to
  15.5 cells from it and holds 300 ticks), `close_in` (a shooter within 25 Auto-attacks the
  thrower for 300 ticks). CLI `--option vs_throwers=stand_off`; rows store `options` (the
  effective values; `{}` for doctrines without options). Not evaluated yet.
- **Casualty options** (both take shooters out of the fight): `rescue=on|off` (doctrine agent:
  Carry downed squadmates to a fallback cell) and `wounded_pullback=on|off` (doctrine agent and
  turtle: pawns below 45% health walk to the fallback cell). `off` = no rescuer is sent / the
  wounded pawn stays where the doctrine puts it. CLI `--option rescue=on`. Compared in
  baseline-v1 (results/baseline/README.md): the doctrine agent lost 1.43 colonists per battle
  with rescue on (v4) vs 1.20 with it off (v5), so its natural value is **off** from doctrine
  v5; wounded_pullback=off showed no effect, so it stays **on** (natural). Resume and reports:
  a key missing from an older row reads as what agents did before the option existed
  (`PRE_OPTION_BEHAVIOUR` in `rca/eval/results.py`: both on), not as today's natural value;
  reports label non-natural variants, e.g. `doctrine@v5[rescue=on]`, so they never pool with
  the natural cell. Checked once each in game (results/prebaseline/
  options_check.jsonl): rescue=off → 0 rescues started (4 pull-backs); wounded_pullback=off →
  0 pull-backs (doctrine, turtle).
- `viscosity` (the micro threshold) is `rca.micro.VISCOSITY[name]` (amove/close 0.15, spread /
  doctrine / kite 0.3, turtle 0.8). The micro layer returns the pawns it owns each step; the
  doctrine skips them and re-issues its order on release, and asks `micro.cell_ok(pid, cell)`
  before sending a pawn somewhere (re-entry hysteresis).
- All agent timers must be in **ticks**, not steps, so that they mean the same at any cycle
  (reflex_report §1).
- Registry (`rca/tactical/__init__.py`): `b0` (does nothing), `amove` v6, `doctrine` v6,
  `turtle` v9, `spread` v6, `kite` v6, `close` v4 (each one above every legacy version, so new
  rows never pool with old ones). baseline-v1 = amove v5, doctrine v5, turtle v8, spread v5,
  kite v5, close v3; the v6/v9/v4 bump (losing_trade, precondition data) is report-only:
  behaviour identical, bumped so rows never mix. Aliases: `b1`/`aggressive` → amove, `hold` → turtle,
  `focus` → doctrine. Specs: module docstrings of `rca/tactical/{focus,turtle,spread,kite,close}.py`.
- Casualties (`rca/tactical/squad.py`): wounded fighters are **never undrafted** (LESSONS bug 6);
  doctrine and turtle pull pawns below 45% health back to a fallback cell 10 behind the squad,
  drafted (option `wounded_pullback`). The doctrine agent carries downed squadmates to that cell
  when `Carry` is enabled (option `rescue`, off by default from doctrine v5) and never reserves a pawn for a disabled option
  (bug 5). The game undrafts a pawn that goes down; when it stands up again every doctrine
  re-drafts it (`kpis.redrafts`; LESSONS §4 "Turtle Go here failures").
- Legacy agents had a `versions` map per reflex version (LESSONS bug 12: doctrine, kite and close
  lacked it). In rca the agent version and the micro version are separate row fields, and the
  resume key requires both, so the map is gone.

## 3. Episode loop and outcome

```
cycle -> agent.step -> wait(step) -> ticks = ticksGame - t0
  -> read _notifications (dedup by text, first tick kept; up to 60 stored)
       " are fleeing" -> raid_fled_tick (first); "satisfied with the damage" -> raid_satisfied_tick
  -> live = tracker.observe(ticks)
  -> progress meter (tracker.lost_points), contact windows for fire_share
  -> engagement counters (legacy, biased)
  -> stop if: no live (non-downed) hostile -> "enemies_cleared"
              no standing squad pawn        -> "squad_down"
              ticks >= max_ticks             -> "timeout"
pause; kpis; squad_state(after); measure; agent.signals; fire_share from the pooled battle log
if squad_kidnapped > 0: outcome = "raid_left_with_captives"
```

`enemies_cleared` also covers a raid that walked off the map. Use the **grade**, not the outcome
or `win`.

**Outcome `invalid`** (2026-10-04). Strive to Survive lets the storyteller send its own threats
during an episode (Peaceful blocked them). Any hostile pawn the tracker sees that was not on the
map at the episode start (`harness.unexpected_hostiles`: a raid, a manhunter, a mech cluster)
ends the episode at once with outcome `invalid` and `invalid {reason: "unexpected_hostiles",
tick, kinds}`. The row is written (traceability) but `read_rows` skips it unless
`invalid=True`, so no summary, gate or resume count sees it; `run_batch` re-runs the same run up
to 3 times, then leaves it to a later `--resume`. Hostiles already in the save are not caught
(the 2026-10-04 Anomaly fleshbeasts were: TODO Now 1). Non-hostile incidents (disease, solar
flare, psychic drone) only show in `game_messages`.

**Difficulty check.** At every episode start the harness reads `get_status.difficulty`; a save
on another difficulty than `--difficulty` (default `strive to survive`; `any` = off) raises
`WrongDifficulty`, which stops the batch (no retry).

## 4. Fate classification (battle_tracker)

Corpses are no evidence (blasts and fire destroy them; walkers leave none).

Each observation:
- Hostiles from `list_things(pawn, hostile, verbose, confirm)` (dead ones excluded). Store name,
  is_mech (`def` starts with `Mech_`), x, z, downed.
- **Leaving-job fetch** (one `get_pawn` per raider, so only where plausible): for a non-mech,
  non-downed raider that is near the edge, or within 3 cells (Chebyshev) of one of our downed
  pawns. Store the job lowercased. A job `kidnapping <name>.` adds the name to `kidnap_targets`.
- **Edge margin** = `round(3 + 0.075 × ticks since the previous observation)`: 12 at 120 ticks,
  5 at 30. "Near edge" = `min(x, z, 249 − x, 249 − z) ≤ margin`.
- A hostile that disappeared gets its fate the first time it is missing:
  1. mech → `destroyed` (mechs never walk off);
  2. its name is in the harvested death names → `killed`;
  3. last seen downed → `killed_inferred`;
  4. last job starts with `kidnapping|fleeing|exiting|stealing|leaving`, or it was last seen near
     the edge → `escaped`;
  5. otherwise → `killed_inferred`.
- A squad pawn that disappeared → `pending`, settled at finish.
- **Log harvest** every 600 game ticks: `get_pawn(tab=log)` for every live hostile and squad pawn.
  Entries matching the death regex (GAME_FACTS.md §3) add names to `dead_names`. Kill records are
  re-read at the same time.

Finish:
- Harvest once more. `killed_inferred` or `escaped` with a name in `dead_names` → upgraded to
  `killed`.
- Pending squad pawns → `kidnapped` if the lowercased short name is in `kidnap_targets` and not in
  `dead_names`, else `dead`.
- Counts: `enemies_seen`, `enemies_active_end` (still on map, not downed), `enemies_downed_end`,
  `enemies_killed` (killed + destroyed), `enemies_killed_inferred`, `enemies_escaped`,
  `squad_dead`, `squad_kidnapped`.
- **Cross-check:** `kills_record` = the sum of the squad's increase in the `Kills` record (only
  stored, not used in grading).
- **rca additions:** each raider's `kind` (PawnKindDef, from `list_things` verbose) and combat
  points (`data/combat_power.json`); finish adds `enemy_seen_points`, `enemy_lost_points` (killed +
  killed_inferred + downed at the end), `enemy_escaped_points` (null if any kind is unknown) and
  `enemy_kinds` ({kind: {fate: n}}). The squad is updated before the kidnapper check, so a pawn
  downed this step already triggers the job fetch (legacy: one step later). Two squad pawns with
  the same short name make a kidnap name ambiguous: listed in `debug_kidnap_ambiguous` (LESSONS
  bug 10), not resolved.
- Debug fields: `debug_kidnap_targets`, `debug_dead_names`, `debug_squad` (name → fate),
  `debug_leaving_jobs` (up to 15).

## 5. measure() and grade()

```
deaths   = squad_dead + squad_kidnapped        # lost to the colony either way
downed_at_end = squad pawns downed at the end
hp_lost_pct   = sum over squad of max(0, health_before - health_after)   # dead -> health 0
new_permanent_injuries = sum over surviving pawns of new (label, part) permanent marks
enemy_neutralized_frac = (killed + killed_inferred + downed_end) / max(1, seen)
```

`grade(m)`, applied **in this order** (n = squad_size, seen = enemies_seen):

1. A row without `enemies_escaped` (pre-tracker) → `decisive` if the stored `win` is true, else `defeat`.
2. `squad_kidnapped > 0` **or** `deaths + downed_at_end ≥ n` → **defeat**.
3. `raid_satisfied_tick` set → **defeat** (they left because they won).
4. `enemies_active_end > 0` → **unresolved**.
5. `enemies_escaped ≤ 0.1 × seen` → **decisive if standing ≥ 0.5, else pyrrhic** (standing as in 7).
6. No `raid_fled_tick` (no message) → fallback: broken = (killed + killed_inferred + downed_end) / seen.
   If **broken < 0.5 → defeat**.
7. standing = (n − deaths − downed_at_end) / n. **≥ 0.5 → repelled**, else **pyrrhic**.

- `win` = decisive or repelled.
- **Evidence for the 0.5 fallback** (results/grade_check.jsonl, 12 runs with messages): satisfied
  raids had broken ≤ 0.46, fleeing raids ≥ 0.71, so 0.5 sits in the gap.
- Lordless pawns (frag_check) never post either message, so they always use the fallback.
- **Stored `grade`/`win`/`score` fields go stale** when grade() changes. Example: grade_check rows
  store `pyrrhic` where the current rule gives `defeat`. Always recompute from raw metrics.
- **Fixed in rca (grade v2):** step 5 used to ignore our losses (a raid fully killed at the cost of
  10/14 pawns was `decisive`). Now a clean sweep with standing < 0.5 is `pyrrhic`. The legacy rule
  is kept as `grade_v1()` for comparisons. Across all legacy results files (1058 rows; 822 distinct,
  since results.jsonl contains pre_tracker.jsonl) the fix changes the grade of 2 rows (exec_v1 and
  exec_v2, 1 each); it matters for doctrines that trade many pawns for a sweep.

## 6. Trade ratio (primary) and the legacy score

**Primary development metric: the trade ratio (LER, loss-exchange ratio)** (`rca/eval/scoring.py`,
TODO roadmap 1):

```
LER = enemy strength lost / our strength lost
enemy strength lost = Σ combatPower of raiders killed, killed_inferred or downed at the end
our strength lost   = (squad_dead + squad_kidnapped) × colonist value
colonist value      = COLONIST_ENEMIES × mean combatPower of a raider in this battle
                      (parameter, default 4: "1 colonist = 4 enemies by points")
```

- **Combat points.** RimMolt does not expose `combatPower` (not on the info card; `get_info_card`
  takes ThingDefs only). `list_things` verbose gives each pawn's PawnKindDef (`kind`), and
  `rca/game/defs.py` reads `combatPower` (with `ParentName` inheritance) from the game XML into
  `data/combat_power.json` (290 kinds, game 1.6.4871). Check: theme raids at 1500 pt sum to
  1000–1485 points of kinds (e.g. pirate_mixed 1455).
- **Old rows** have fate counts only. Their enemy points are `count × the scenario's mean points
  per raider` (manifest kinds; if a manifest stores the race `Human`, spec points / raiders), so
  their LER is count-based: enemy lost / (4 × colonists lost). Pre-tracker rows use
  `round(enemy_neutralized_frac × enemies_seen)`. The row's `ler_basis` says which: `points`,
  `count_x_mean`, `count`.
- **Edge cases.** No colonist lost: LER = ∞ (stored as `"inf"`). Nothing lost on either side:
  undefined, ranked as an even trade (1.0). Escaped raiders are not lost: a raid that leaves
  "satisfied" trades badly by construction.
- **Ordering for superiority:** per run `(LER, enemy points lost)`, so two clean runs are ranked
  by what they took. **Cell summary:** pooled LER = Σ enemy points lost / Σ our points lost
  (∞ if the cell lost nobody), plus the median per-run LER.
- **Reported separately, never folded in:** colonist losses per battle (dead + kidnapped) and the
  grade counts (decisive / repelled / pyrrhic / unresolved / defeat).
- Why: the legacy score charged 1 death = −100 against 150 for the whole raid, which filters out
  high-variance, high-payoff tactics (a local minimum).

**Legacy score** (`score_v1`, kept for comparison with the old reports):

```
score = GRADE_BONUS[grade]
      + 150 × enemy_neutralized_frac
      − 100 × deaths
      −   5 × downed_at_end
      −   1 × hp_lost_pct / n
      −  50 × new_permanent_injuries / n
GRADE_BONUS = {decisive: 50, repelled: 30, pyrrhic: 0, unresolved: 0, defeat: −50}
```

`tools/rescore.py` recomputes both for every results file without touching the raw rows
(results/rescored/, DATA.md §5). The old-vs-new ranking per theme is in
results/rescored/theme.md and DATA.md §7.

## 7. Comparison statistics

- **Superiority** P(A > B) = the share of all (a, b) run pairs where a's score > b's, with ties
  counting ½. 0.5 = no difference; 0.4–0.6 counts as a tie at n=5.
- `tools/report.py` (`rca/eval/report.py`) groups rows by **config** (cycle, reflex on/off, reflex
  version) first, then by (scenario, agent@version): configs and agent versions are never pooled.
  Each agent is compared with `amove` under the same config. Columns: n, grade counts, colonists
  lost per battle, enemy points lost, pooled LER, median LER, P(LER) > amove, median legacy
  score, P(score_v1) > amove, LER basis. Then a headline per agent and the per-scenario ranking
  by pooled LER next to the ranking by median legacy score.

## 8. KPIs currently in use

Most count only **contact steps**: a raider within 30 cells of a fighter.

Legacy KPIs below the rca rows were produced by legacy/reflexes.py and threatmap.py.

| Family | Keys | Meaning / caveat |
|---|---|---|
| engagement (row level) | `engaged_steps, engaged_ours, engaged_theirs, engagement_ratio` | ours = squad pawns with a job starting `attacking`/`melee attacking`; theirs = raiders with `targeting` starting `targeting colonist`/`attacking colonist`. **Biased:** drafted pawns firing at will show "watching for targets" and are not counted (turtle ≈ 0). Don't compare doctrines with it |
| **progress** (row level, rca) | `progress_rate, progress_points, first_contact_tick, longest_no_progress_ticks` | rate = enemy combat points lost (killed, killed_inferred, downed; tracker fates × data/combat_power.json) per 1,000 ticks from first contact (a live raider within 30 of a standing squad pawn) to the end; longest stretch without an increase, from first contact, in or out of contact, up to and including the step that saw the progress (overestimates by ≤ one step). Null before contact |
| **fire share** (row level, rca; replaces engagement for comparisons) | `fire_share, enemy_fire_share, surface_ours, surface_theirs, fire_window_ticks, fire_names_ambiguous, log_entries` | Battle-log based (rca/eval/firelog.py): a pawn *fires* in a 300-tick window if a combat entry in it names the pawn as attacker (shot, shot at, hit, missed, threw, stabbed, beat …); *available* = standing (no fate, not downed) during a contact step in that window. fire_share = fired / available pawn-windows per side; surface = mean firing pawns per contact window. Entries are pooled over all harvested logs (every 600 ticks + at the end; an attack is in the victim's log too). Log ticks are TicksAbs: offset = running max of (newest entry − episode tick at harvest), a lower bound, tight in a fight. Names shared by both sides are dropped (listed); names shared within a side (mechs: every pikeman is "Pikeman") are counted per name. Matching is case-insensitive and ignores a leading "the". Mechs, checked after the fix (results/prebaseline/mech_recheck.jsonl): enemy_fire_share 0.64, 0.59 (doctrine) and 0.63, 0.73 (close) where the smoke had 0.0. Caveats: a pawn that died loses its own log, but its shots survive in victims' logs; per-pawn log length is capped by the game (cap UNVERIFIED) |
| signal (row level, rca) | `signals[{tick, reason, phase, pause?, contested?, lost?, our_pts?, enemy_pts?, ler?}], unattainable_tick, unattainable_reason` | §2; first entry copied to the two flat fields (since losing_trade it can be either signal) |
| losing_trade (kpis, every rca doctrine from amove v6 etc.) | `trade_curve [[tick, pawns gone, enemy points]], losing_trade_rule {min_lost, ler, window}` | §2; the running trade, one entry per change after first contact (≤ 60) |
| no_progress rule (kpis, every rca doctrine) | `no_progress_rule, longest_pause_ticks, longest_contested_ticks, pressure_ticks {cost, threat, either, total}` | §2 rule 2. `longest_pause_ticks` is the doctrine-side twin of the row's `longest_no_progress_ticks` (doctrine view of points lost; it can differ by a step or a late fate) |
| tactical (all rca squad doctrines) | `phase_log [[tick, phase]], pre_<check> {ok, value, need}, rescue_{started,carried,unavailable,failed}, wounded_pullbacks, thrower_moves, thrower_attacks, orders_failed, order_errors, redrafts, redraft_on_error, no_progress_ticks` | phase changes (≤ 30); precondition values at reset; casualty handling; vs_throwers moves; re-drafts of pawns that stood up again / after a "No order matched 'Go here'" |
| spacing (all doctrines) | `gap5_share` | share of fighter-steps whose nearest squadmate is ≥ 5 cells away |
| spread | `mean_gap, step_outs` | nearest-ally distance, capped at 15; spacing moves |
| kite | `shooter_melee_dist, melee_adjacent_share (≤ 1.5), retreat_share` | |
| turtle | `first_shot_tick, on_slot_share, longest_stall_ticks, sally_tick, sally_reason, plan {exit, center, window, best_window, exposure_frac, shooters_placed, shooters, range, enemy_range}, replans` | sally_reason `idle` / `stall` / `no_approach` |
| close | `close_tick_mean, closed_n` | |
| doctrine agent | `assigned_share, targets_per_step, guns_per_target, attacking_share` | |
| reflex `rx_*` | `frags_seen, molotovs_seen, frags_exploded, in_zone_at_landing (≤ 2.5), in_blast_at_landing (≤ 1.9), escaped, stayed_in_blast, lost_track, moves, moves_{frag,predicted,fire,throw,rocket}, nudges, too_late, trapped, ignored_viscous, predictions, predictions_right, observe_steps, frag_hit_pawns, frag_hit_entries, version, revision, enabled, threshold`; v3 adds `stays, map_moves, fire_at, fallback_{kill,back,none}, forbidden_cells, reslots, returns_{auto,map,reflex,other}` | definitions in reflex_report §2 and threatmap_report §3–4 |
| threat map `tm_*` | `returns_fled, entries_known, entries_high, returns_to_danger (= fled + known), high_pawn_ticks, pawn_ticks, high_share, fled_cells, ms_per_step, max_ms, cells_per_step, steps, terrain_calls` | definitions in threatmap.DangerKPI → threatmap_report §4. Caveat: walking *past* a fled cell counts as a return |
| positioning `steps_*` | `steps_auto, steps_map, steps_reflex, steps_other` | who positioned each pawn per contact step |
| micro v4 `rx_*` (rca) | `observe_steps, frags_seen, frags_exploded, in_zone_at_landing, in_blast_at_landing, escaped, stayed_in_blast, lost_track, threatened, threatened_escaped, moves, moves_frag, moves_fire, too_late, trapped, ignored_viscous, reentries, goto_failed, goto_errors, version, enabled, threshold, frag_hit_pawns, frag_hit_entries` | `threatened` = pawns within 1.9 of a frag's final cell at its first sighting (fair across dodge on/off); `reentries` = a pawn found inside a live hazard it fled while no longer owned. No threat map (`tm_*`), no nudges or predictions |
| terrain `terrain_*` (rca) | `fetches, refetches, stale_explosion, stale_building, stale_fire, stale_contact, unknown_chars` | cache cost and invalidations per episode |

**returns_to_danger:** a *fled cell* is one where the pawn stood with hazard ≥ HIGH (3) and was ≥ 2
cells away one step later. A *return* is being back within 1.5 cells of it within 600 ticks while
its hazard is still ≥ LOW (1). A *known entry* is moving onto a cell whose hazard on the previous
step's map was ≥ HIGH and higher than the old cell's.

**Planned (TODO):** `melee_locked_time_share` for our shooters and carries, and
`enemy_melee_locked_time_share`. Melee-lock rules are UNVERIFIED (GAME_FACTS.md §8). Also
first-volley share, overkill shots. Friendly fire (아군 오사): friendly hits (our shot on our
pawn, from the battle log) and lane intrusion (time a pawn stands in an ally's line of fire
beyond the safe radius) — branch `feat/friendly-fire-kpi`, report-only (TODO Now 2).

## 9. Result row schema

Schema 2 (rca rows carry `"schema": 2`; legacy rows have no `schema`):

| Group | Fields |
|---|---|
| identity | `schema, scenario, agent` (canonical), `agent_version, commit` (git HEAD, `+dirty` if rca/ had uncommitted changes), `time` (unix) |
| config | `cycle, step_ticks` (= calm cycle), `reflex, reflex_version` (rca micro = 4; legacy reflexes 1–3), `max_ticks`, `difficulty` (the label `get_status` reports, lowercase, e.g. `strive to survive`; rows without it ran on Peaceful) |
| run | `outcome` (incl. `invalid`, §3), `invalid` (null or `{reason, tick, kinds}`), `ticks, steps, fast_steps, agent_errors, agent_think_s, wall_s` |
| squad | `squad_size, deaths, squad_dead, squad_kidnapped, downed_at_end, hp_lost_pct, new_permanent_injuries` |
| enemy | `enemies_seen, enemies_active_end, enemies_downed_end, enemies_killed, enemies_killed_inferred, enemies_escaped, enemy_neutralized_frac, kills_record`; rca: `enemy_seen_points, enemy_lost_points, enemy_escaped_points, enemy_kinds` |
| verdict (stale-prone, console only) | `grade, win, score_v1, trade_enemy_points, trade_our_points, ler, ler_basis, colonist_enemies` |
| messages | `raid_fled_tick, raid_satisfied_tick, game_messages[{tick, text}]` (≤ 60, text ≤ 160 chars), `building_deltas` (counts of steps whose `_delta` had new/removed buildings) |
| engagement | `engaged_steps, engaged_ours, engaged_theirs, engagement_ratio` — biased (fire at will is not counted; kept for continuity only); use `fire_share, enemy_fire_share, surface_ours, surface_theirs` (+ `fire_window_ticks, fire_names_ambiguous, log_entries`) |
| progress / signal (rca, phase 2) | `progress_rate, progress_points, first_contact_tick, longest_no_progress_ticks, signals, unattainable_tick, unattainable_reason` |
| options (rca, phase 2) | `options` (effective tactical options, e.g. `{"vs_throwers": "accept_dodge", "rescue": "off", "wounded_pullback": "on"}`; `{}` if none; rows before 1403042 lack `rescue`/`wounded_pullback` and read as on, `PRE_OPTION_BEHAVIOUR`) |
| debug | `debug_kidnap_targets, debug_kidnap_ambiguous, debug_dead_names, debug_squad, debug_leaving_jobs` |
| behaviour | `kpis` (dict, §8; rca adds `terrain_*` cache counters) or `{"error": ...}` |

Missing fields in old rows: see DATA.md §5 (legacy formats). Defaults when reading: `cycle` →
`fixed:<step_ticks>`; `reflex` → off; `reflex_version` → 1 if reflex on; agent aliases →
canonical names. Legacy rows store `score` (old formula) instead of `score_v1`; ignore it.

**Resume key** (PROCEDURES.md §11): (scenario, canonical agent) counts only rows with the current
`agent_version`, the same (cycle, reflex, reflex_version) and the same effective `options`
(rows without the field count as `{}`; an option key missing from a row counts as its
pre-option behaviour, `PRE_OPTION_BEHAVIOUR`, else its natural value) and the same
`difficulty` (rows without it = `peaceful`). Invalid rows never count. Both the stored and the requested
agent name are canonicalised, so `--agents hold` and `--agents turtle` count the same rows
(LESSONS bug 8, fixed).
