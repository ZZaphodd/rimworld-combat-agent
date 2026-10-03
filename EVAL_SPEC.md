# Evaluation harness contract

What the harness (eval.py) does and promises. A port must reproduce it, or the old result rows
can't be compared with new ones. Terms follow GLOSSARY.md: amove = code `b1`, the doctrine agent =
code `doctrine`, turtle = code `turtle` (alias `hold`), plus spread, kite and close.

## 1. Time ownership, cycle, sandbox

- **The harness owns game time.** The game is paused while the agent thinks. The agent issues
  orders, then the harness advances `step_ticks` with
  `wait_for_event(maxGameTicks=step, maxSeconds=60, pause="always", force=True)` (client timeout
  90 s), then observes again. Agents never call time, save or debug tools (sandbox, RIMMOLT_API.md §6).
- **Adaptive cycle** (default `adaptive:30/120@40`): a step is **30 ticks if any live raider is
  within 40 cells of any squad pawn that has no fate yet, else 120**. This is decided before each
  step from the tracker's last observation, at no extra calls. 30 is the shortest cycle that is a
  whole number of 15-tick quanta, and a frag rests ~90 ticks. `--cycle fixed` = always
  `--step-ticks`. CLI: `--step-ticks 120 --fast-ticks 30 --fast-radius 40 --cycle adaptive|fixed`.
- Policy string stored in every row: `adaptive:<fast>/<calm>@<radius>` or `fixed:<calm>`.
- Episode limit `--max-ticks` (CLI default 20000; every batch used 15000). 2500 ticks = 1 in-game hour.
- Episode start: see PROCEDURES.md §9 (load, Never Force Normal Speed, dev mode off).
- An agent exception costs it that step (`agent_errors += 1`), never the episode. A harness or game
  exception retries the episode once, then logs it to `<results>.errors.jsonl`.

## 2. Agent interface

```
class Agent:
    name: str                 # canonical code name; stored in rows
    version: int              # bump on any behaviour change
    versions: {rx_version: agent_version}   # optional; per reflex version
    # set by the harness:
    reflex: bool              # reflex layer may act (False: observe and count only)
    rx_version: int           # 2 = one-shot rules, 3 = threat-map reflex
    step_ticks: int           # length of the coming step
    now: int                  # episode tick at the start of the coming step
    def reset(self, rm, manifest)   # rm = sandboxed client; manifest = DATA.md §2
    def step(self, rm)              # observe + order; must not advance time
    def kpis(self) -> dict          # optional; stored as row["kpis"]
```

- Before `reset`, the harness sets `reflex`, `rx_version`, `version = versions.get(rx_version,
  version)` and `now = 0`. Before every `step` it sets `step_ticks` and `now`.
- All agent timers must be in **ticks**, not steps, so that they mean the same at any cycle
  (reflex_report §1).
- Registry: `b0` (does nothing), `b1` amove, `doctrine`, `turtle` (+ alias `hold`), `spread`,
  `kite`, `close`.

## 3. Episode loop and outcome

```
cycle -> agent.step -> wait(step) -> ticks = ticksGame - t0
  -> read _notifications (dedup by text, first tick kept; up to 60 stored)
       " are fleeing" -> raid_fled_tick (first); "satisfied with the damage" -> raid_satisfied_tick
  -> live = tracker.observe(ticks)
  -> engagement counters
  -> stop if: no live (non-downed) hostile -> "enemies_cleared"
              no standing squad pawn        -> "squad_down"
              ticks >= max_ticks             -> "timeout"
pause; kpis; squad_state(after); measure
if squad_kidnapped > 0: outcome = "raid_left_with_captives"
```

`enemies_cleared` also covers a raid that walked off the map. Use the **grade**, not the outcome
or `win`.

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
5. `enemies_escaped ≤ 0.1 × seen` → **decisive**.
6. No `raid_fled_tick` (no message) → fallback: broken = (killed + killed_inferred + downed_end) / seen.
   If **broken < 0.5 → defeat**.
7. standing = (n − deaths − downed_at_end) / n. **≥ 0.5 → repelled**, else **pyrrhic**.

- `win` = decisive or repelled.
- **Evidence for the 0.5 fallback** (results/grade_check.jsonl, 12 runs with messages): satisfied
  raids had broken ≤ 0.46, fleeing raids ≥ 0.71, so 0.5 sits in the gap.
- Lordless pawns (frag_check) never post either message, so they always use the fallback.
- **Stored `grade`/`win`/`score` fields go stale** when grade() changes. Example: grade_check rows
  store `pyrrhic` where the current rule gives `defeat`. Always recompute from raw metrics.
- Known gap: step 5 ignores our losses. A raid fully killed at the cost of 10/14 pawns is
  `decisive` (as long as 2 + 3 don't fire).

## 6. score()

```
score = GRADE_BONUS[grade]
      + 150 × enemy_neutralized_frac
      − 100 × deaths
      −   5 × downed_at_end
      −   1 × hp_lost_pct / n
      −  50 × new_permanent_injuries / n
GRADE_BONUS = {decisive: 50, repelled: 30, pyrrhic: 0, unresolved: 0, defeat: −50}
```

Deaths dominate on purpose. Per-capita terms keep large squads from being punished for their size.
Score is always recomputed from raw metrics.

**Planned switch (TODO.md):** the primary metric becomes **LER / trade ratio** (point-weighted:
enemy strength lost ÷ ours), with colonist value an explicit parameter (**default 1 colonist = 4
enemies by points**), plus colonist losses and grade shown separately. Then every row is rescored
(raw metrics are stored). Reason: 1 death = −100 vs 150 for a whole raid filters out
high-variance, high-payoff tactics.

## 7. Comparison statistics

- **Superiority** P(A > B) = the share of all (a, b) run pairs where a's score > b's, with ties
  counting ½. 0.5 = no difference; 0.4–0.6 counts as a tie at n=5.
- `--summary` groups rows by (scenario, agent). If the file mixes configs, the agent name gets
  `[<cycle>+rx<v>]` and is compared with `b1` under the same setting. Table columns: n, win%, mean
  deaths, median score, P>b1, eng.
- Never pool agent versions in one cell (theme_analysis warns).

## 8. KPIs currently in use

Most count only **contact steps**: a raider within 30 cells of a fighter.

| Family | Keys | Meaning / caveat |
|---|---|---|
| engagement (row level) | `engaged_steps, engaged_ours, engaged_theirs, engagement_ratio` | ours = squad pawns with a job starting `attacking`/`melee attacking`; theirs = raiders with `targeting` starting `targeting colonist`/`attacking colonist`. **Biased:** drafted pawns firing at will show "watching for targets" and are not counted (turtle ≈ 0). Don't compare doctrines with it |
| spacing (all doctrines) | `gap5_share` | share of fighter-steps whose nearest squadmate is ≥ 5 cells away |
| spread | `mean_gap` | nearest-ally distance, capped at 15 |
| kite | `shooter_melee_dist, melee_adjacent_share (≤ 1.5), retreat_share` | |
| turtle | `first_shot_tick, on_slot_share, longest_stall_ticks, sally_tick, sally_reason` | |
| close | `close_tick_mean, closed_n` | |
| doctrine agent | `assigned_share, targets_per_step, guns_per_target, attacking_share` | |
| reflex `rx_*` | `frags_seen, molotovs_seen, frags_exploded, in_zone_at_landing (≤ 2.5), in_blast_at_landing (≤ 1.9), escaped, stayed_in_blast, lost_track, moves, moves_{frag,predicted,fire,throw,rocket}, nudges, too_late, trapped, ignored_viscous, predictions, predictions_right, observe_steps, frag_hit_pawns, frag_hit_entries, version, revision, enabled, threshold`; v3 adds `stays, map_moves, fire_at, fallback_{kill,back,none}, forbidden_cells, reslots, returns_{auto,map,reflex,other}` | definitions in reflex_report §2 and threatmap_report §3–4 |
| threat map `tm_*` | `returns_fled, entries_known, entries_high, returns_to_danger (= fled + known), high_pawn_ticks, pawn_ticks, high_share, fled_cells, ms_per_step, max_ms, cells_per_step, steps, terrain_calls` | definitions in threatmap.DangerKPI → threatmap_report §4. Caveat: walking *past* a fled cell counts as a return |
| positioning `steps_*` | `steps_auto, steps_map, steps_reflex, steps_other` | who positioned each pawn per contact step |

**returns_to_danger:** a *fled cell* is one where the pawn stood with hazard ≥ HIGH (3) and was ≥ 2
cells away one step later. A *return* is being back within 1.5 cells of it within 600 ticks while
its hazard is still ≥ LOW (1). A *known entry* is moving onto a cell whose hazard on the previous
step's map was ≥ HIGH and higher than the old cell's.

**Planned (TODO):** `melee_locked_time_share` for our shooters and carries, and
`enemy_melee_locked_time_share`. Melee-lock rules are UNVERIFIED (GAME_FACTS.md §8). Also LER,
first-volley share, overkill shots.

## 9. Result row schema (current)

| Group | Fields |
|---|---|
| identity | `scenario, agent, agent_version, time` (unix) |
| config | `cycle, step_ticks` (= calm cycle), `reflex, reflex_version, max_ticks` |
| run | `outcome, ticks, steps, fast_steps, agent_errors, agent_think_s, wall_s` |
| squad | `squad_size, deaths, squad_dead, squad_kidnapped, downed_at_end, hp_lost_pct, new_permanent_injuries` |
| enemy | `enemies_seen, enemies_active_end, enemies_downed_end, enemies_killed, enemies_killed_inferred, enemies_escaped, enemy_neutralized_frac, kills_record` |
| verdict (stale-prone) | `grade, win, score` |
| messages | `raid_fled_tick, raid_satisfied_tick, game_messages[{tick, text}]` (≤ 60, text ≤ 160 chars) |
| engagement | `engaged_steps, engaged_ours, engaged_theirs, engagement_ratio` |
| debug | `debug_kidnap_targets, debug_dead_names, debug_squad, debug_leaving_jobs` |
| behaviour | `kpis` (dict, §8) or `{"error": ...}` |

Missing fields in old rows: see DATA.md §5 (legacy formats). Defaults when reading: `cycle` →
`fixed:<step_ticks>`; `reflex` → off; `reflex_version` → 1 if reflex on.

**Resume key** (PROCEDURES.md §11): (scenario, canonical agent) counts only rows with the current
`agent_version` and (cycle, reflex, reflex_version). WORKFLOW.md asks for the commit hash in
every row after the baseline freeze (not implemented).
