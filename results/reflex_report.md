# Adaptive decision cycle + shared reflex layer

Goal: a frag grenade we could have stepped away from must not decide a fight.
Raw rows: `results/reflex_check.jsonl` (165 episodes, 0 harness errors). Batches:
`reflex_check.sh` (before vs after, reflex v1), `reflex_ablation.sh` (cycle without reflex),
`reflex_v2.sh` (reflex v2 + 5 more frag_check runs per setting).

## Verdict (short)

- **The adaptive cycle helps on its own.** On theme_pirate_grenadier, cycle-only won 3/5 (aggressive)
  and 4/5 (spread) vs 1/5 and 1/5 at fixed 120. Cost: about 1.5x wall time per episode.
- **The frag reflex works mechanically.** In frag_check under reflex v2, 32 of 60 pawns caught inside a
  resting frag's blast walked out before it blew. With the cycle but no reflex, 3 of 29 got out on their own.
  Logged frag hits did not consistently drop, though. They fell for aggressive (12 to 2 per 10
  episodes), stayed level for turtle (9 to 9) and rose for spread (3 to 5).
- **On the real grenadier theme the reflex layer did not help, and it probably hurt.** With the reflex
  (v1 or v2), aggressive won 0/5 against 3/5 for cycle-only, and turtle lost 5.4 pawns per episode
  under v2 against 3.2. Spread kept 5/5 wins but lost 1.4 pawns per episode against 0.6. Frags are
  rare in that raid (0–3 seen per 5 episodes). The reflex's activity there is almost all
  molotov-fire step-outs and rocket-spacing nudges, and each one breaks the pawn's Auto attack.
  n=5, so treat this as a warning, not a measurement.
- **Recommendation for the 210-run matrix:** run with the adaptive cycle. Either leave the reflex off
  (`--no-reflex`, which still records its KPIs), or first build v3 = frag-only (no fire-adjacency
  moves, no nudges) and check it on the grenadier theme (see open issues).

## 1. Decision cycle (eval.py)

- Rule, the same for every agent: the cycle is **30 ticks while any live hostile is within 40 cells
  of any squad pawn, else 120**. The harness decides this from the tracker data it already reads,
  so it costs no extra calls. CLI options: `--fast-ticks 30 --step-ticks 120 --fast-radius 40
  --cycle adaptive|fixed`.
- The wait tool advances in 15-tick quanta, so 30 is the shortest cycle that is a whole number of
  quanta.
- Before each step, agents get `agent.step_ticks` (the coming step) and `agent.now` (episode tick).
- Every row stores `cycle` (e.g. `adaptive:30/120@40` or `fixed:120`), `reflex`, `reflex_version`,
  `fast_steps` and `step_ticks` (= calm cycle). `--resume` only counts rows with the same agent
  version **and** the same (cycle, reflex on/off, reflex version). `--summary` labels agents with
  their setting whenever a file mixes settings, and compares against b1 under the same setting.
  Old rows are read as `fixed:<step_ticks>`, reflex off.

### Settings counted in steps, now in ticks (every item from execution_report.md section 5)

At a fixed 120-tick cycle, the converted values are identical to the old ones, so fixed:120 rows
reproduce the old behaviour.

| where | old | now |
|---|---|---|
| turtle | STALL 12 / IDLE 40 / REPLAN_COOLDOWN 10 steps | 1440 / 4800 / 1200 ticks; stall and idle accumulate elapsed ticks |
| turtle KPIs | sally_tick, first_shot_tick = steps x step | episode tick |
| kite | calm >= 3 contact steps | CALM_TICKS 360 (contact ticks) |
| kite | reach = 0.08 x step + 3 | unchanged: already scales with the current step |
| kite | REAR 5, PRESS 40 | unchanged: these are distances in cells, not durations |
| focus | retarget_every 10 steps | retarget_ticks 1200 |
| focus | idle re-issue every step | at most once per reissue_ticks 120 per pawn (stops re-issue spam at 30 ticks) |
| spread | HOLD_STEPS 4 | HOLD_TICKS 600 (the move step + 4 held steps); STEP_OUT 5 cells is a distance |
| close | 10-cell bound every step | 10-cell bound at most every ADVANCE_TICKS 120 per pawn |
| close KPI | close_tick = steps x step | episode tick |
| tracker | harvest every 5 steps | every 600 ticks (log harvest is the expensive call) |
| tracker | EDGE 12 cells | 3 + 0.075 x (ticks since last sample): 12 at 120, 5 at 30 |
| trace.py | (no clock) | feeds `now`/`step_ticks` so the agents' timers run |

Agent versions: b1 v2, focus v3, turtle v5, spread v2, kite v4, close v2. Reflex changes carry their
own `REFLEX_VERSION` (now 2) in each row, so rows from different reflex versions are kept apart.

### Cost

Wall time per episode, excluding the ~8.7 s per episode for loading and setup:

| scenario | fixed:120 | adaptive (cycle only) | adaptive + reflex v2 |
|---|---|---|---|
| frag_check (n=30 each) | 5.2 s | 7.8 s | 8.1 s |
| pirate_grenadier (n=15 each) | 25.2 s | 38.3 s | 45.9 s |
| all 45 episodes per setting | 11.9 s | 18.0 s | 20.7 s |

- Wall time per step falls from 0.61 s to about 0.40 s, because a short step has less game time to
  simulate. Steps per episode rise 2–3x. Agent think time is about 40% of wall time with the reflex
  on, against 32% at fixed 120.
- Reflex cost: 3 extra `list_things` calls (frag, molotov, fire; about 20 ms each) on steps with a
  raider within 30 cells, plus one `get_pawn` per raider per episode (weapon cache). The terrain grid
  is fetched in 50x50 tiles only when a dodge is needed. The battle-log reads for the hit KPI happen
  once at the start, after each nearby blast, and once at the end.
- **210-run matrix projection.** The v1 matrix averaged 31 s wall per episode at fixed 120, which
  is about 2.3 h including loads. The grenadier theme's measured ratios give about **3.3 h** with
  the adaptive cycle and no reflex (x1.52), and about **3.8 h** with reflex v2 (x1.82). A fixed
  30-tick cycle would take about 7 h.
- RimWorld did not crash this session, across about 180 save loads. Still plan for a restart
  around every 100–150 episodes.

## 2. Reflex layer (reflexes.py)

Every doctrine calls `Reflexes.step(fighters, hostiles, now, step_ticks)` right after its own
observation. The call returns the pawns the reflex owns this step: those it moved now, and those
still dodging (up to the fuse + 10 ticks, at most 120). Each doctrine skips those pawns and re-issues
its normal order once they are released: aggressive, focus, spread, kite and close re-attack, and
turtle walks back to its slot. With `--no-reflex`, the layer only observes and counts; it never
moves a pawn or changes a target.

### Frag grenades (ground-fused)

- `Proj_GrenadeFrag` is tracked by id. The fuse runs from the **first sighting at the grenade's
  current cell**, minus half a step. The layer does not wait for a second sighting to confirm the
  grenade is at rest: that left about 45 ticks, which is too little time to walk 3 cells (seen in
  the smoke tests).
- Danger radius is **2.5 cells**. `measure_blast.py` (in hazards.md) found hits at d ≤ 1.4 (6 of 7
  pawns) and none at 2.2 or beyond (0 of 32 pawns), which matches the XML blast radius of 1.9.
- A threatened pawn walks to a walkable cell outside every danger zone that no squadmate holds or
  is heading for. Cells are searched by BFS up to 8 steps on the ascii terrain. Among cells it can
  reach before the deadline (15 ticks to start + distance / 0.07 cells per tick), it prefers one
  not closer to the raiders, then the nearest. If no cell is reachable in time, it does not move and
  the case is counted as `too_late` or `trapped`.

### Grenades and molotovs in flight

- Implemented: the predicted landing spot is the squad pawn nearest the forward ray of two
  sightings.
- **Not reliable.** Scored per projectile in the v2 rows, the prediction was right (within
  2.5 cells) for 51 of 130 frags and molotovs (39%).
- v1 acted on predictions: 74 of its 155 frag_check moves were moves of this kind, mostly false alarms. v2 only
  scores the prediction.
- So molotovs get **no reflex before impact**; only the fire they leave triggers one.

### Fire

- A pawn on a `Fire` cell steps out (severity 0.9).
- Next to a fire, severity is 0.2 in v2 (0.4 in v1), so only aggressive and close react to it.
  Standing next to fire does no damage in RimWorld; only the fire's spread does.

### Rocket carriers

- A live raider whose weapon label contains "doomsday" or "rocket launcher" counts as a carrier.
  Weapons are cached from `get_pawn`.
- Spacing: while a carrier is within 45 cells of the squad, pawns with a squadmate closer than
  4.5 cells are nudged 3 cells apart. The rule only applies when the doctrine's viscosity allows
  0.3, and each pawn is nudged at most every 600 ticks (300 in v1). It is skipped for spread, which
  keeps its own 5-cell gap.
- Targeting: `priority_target(p, hostiles, fallback, reach=35)` returns the nearest carrier within
  35 cells. aggressive, spread, kite, close and turtle (when it attacks) use it for shooters. focus
  ranks carriers at priority 6, above Lancers.

### Viscosity

- Severity is 1.0 inside a resting frag's blast (d ≤ 1.5) and 0.3 in the 2.5-cell margin.
  Predicted threats are worth x0.6, but v2 no longer acts on them.
- Fire on the pawn's cell is 0.9; next to one, 0.2. Rocket spacing is 0.3.
- The reflex fires when severity ≥ the doctrine's threshold:

| doctrine | threshold | reacts to |
|---|---|---|
| aggressive (b1) | 0.15 | everything: blast, margin, fire on or next to the cell, spacing |
| close | 0.15 | same as aggressive |
| spread | 0.30 | blast, margin, fire on the cell (no spacing nudge: it spaces itself) |
| focus (doctrine) | 0.30 | blast, margin, fire on the cell, spacing |
| kite | 0.30 | same as focus |
| turtle | 0.80 | only a grenade inside its blast reach, or fire under it; never leaves the line for the margin or spacing |

### Reflex KPIs (in `kpis`, prefixed `rx_`)

- `frags_seen`: frag grenades seen.
- `in_zone_at_landing`: pawns within 2.5 cells at the first sighting on the grenade's final cell.
- `in_blast_at_landing`: the same, within 1.9 cells (2.0 in v1).
- `escaped`: of the pawns in blast at landing, those outside the blast at the last sighting
  before it blew.
- `stayed_in_blast`: those still inside it.
- `moves`, split into `moves_frag` / `moves_predicted` / `moves_fire`.
- `nudges`.
- `too_late` / `trapped`.
- `ignored_viscous`: pawn-steps under threat below the doctrine's threshold.
- `predictions` / `predictions_right`.
- `frag_hit_pawns` / `frag_hit_entries`: new battle-log entries where a frag grenade damaged that
  squad pawn. Logs are also harvested right after each nearby blast, because a pawn that dies later
  has no log left to read.

## 3. Validation

### Scenarios

- **`theme_frag_check`** (tier "check"; built with `theme_builder.py --frag-check`): 5
  `Grenadier_Destructive` spawned with debug Spawn Pawn about 27 cells east of the frozen 14-pawn
  theme squad.
  - The build kept the 2nd roll: 4 of 5 carry frags. The 1st roll had 1 of 5.
  - These are lordless pawns, so the game posts no fleeing or "satisfied" message and grading
    falls back to fates.
  - The fights are short (about 600 ticks) and always won. The scenario measures grenade exposure,
    not outcomes.
- **`theme_pirate_grenadier`**: mostly doomsday, triple rocket and molotov weapons, with 1 frag
  thrower.

### Outcomes

- "before" = fixed:120 with the reflex observing only (the pre-change behaviour).
- "cycle" = adaptive cycle, reflex off.
- "after" = adaptive + reflex v2.
- Wins = decisive or repelled. "Lost" = dead + kidnapped.

| scenario | doctrine | setting | n | wins | lost (sum) | lost/ep | hp lost/ep | frag-hit pawns/ep | frag hit entries (sum) | wall s/ep |
|---|---|---|---|---|---|---|---|---|---|---|
| frag_check | aggressive | before | 10 | 10 | 0 | 0.0 | 53 | 0.4 | 4 | 4 |
| frag_check | aggressive | cycle | 10 | 10 | 0 | 0.0 | 70 | 1.0 | 12 | 6 |
| frag_check | aggressive | after (rx2) | 10 | 10 | 1 | 0.1 | 38 | 0.2 | 2 | 7 |
| frag_check | spread | before | 10 | 10 | 0 | 0.0 | 72 | 0.7 | 7 | 6 |
| frag_check | spread | cycle | 10 | 10 | 0 | 0.0 | 47 | 0.3 | 3 | 9 |
| frag_check | spread | after (rx2) | 10 | 10 | 0 | 0.0 | 32 | 0.5 | 5 | 9 |
| frag_check | turtle | before | 10 | 10 | 0 | 0.0 | 96 | 1.8 | 19 | 5 |
| frag_check | turtle | cycle | 10 | 10 | 1 | 0.1 | 57 | 0.9 | 9 | 8 |
| frag_check | turtle | after (rx2) | 10 | 10 | 0 | 0.0 | 51 | 0.8 | 9 | 8 |
| pirate_grenadier | aggressive | before | 5 | 1 | 11 | 2.2 | 753 | 0.2 | 1 | 17 |
| pirate_grenadier | aggressive | cycle | 5 | 3 | 16 | 3.2 | 722 | 0.8 | 5 | 36 |
| pirate_grenadier | aggressive | after (rx2) | 5 | 0 | 23 | 4.6 | 873 | 0.0 | 0 | 41 |
| pirate_grenadier | spread | before | 5 | 1 | 9 | 1.8 | 672 | 0.0 | 0 | 32 |
| pirate_grenadier | spread | cycle | 5 | 4 | 3 | 0.6 | 360 | 0.0 | 0 | 42 |
| pirate_grenadier | spread | after (rx2) | 5 | 5 | 7 | 1.4 | 528 | 0.0 | 0 | 61 |
| pirate_grenadier | turtle | before | 5 | 0 | 17 | 3.4 | 980 | 0.0 | 0 | 27 |
| pirate_grenadier | turtle | cycle | 5 | 0 | 16 | 3.2 | 967 | 0.2 | 1 | 37 |
| pirate_grenadier | turtle | after (rx2) | 5 | 0 | 27 | 5.4 | 1068 | 0.2 | 1 | 36 |

Reflex v1 (adaptive + v1, 5 runs each):

| scenario | doctrine | wins | lost/ep | frag hit entries (sum) |
|---|---|---|---|---|
| frag_check | aggressive | 5/5 | 0.0 | 0 |
| frag_check | spread | 5/5 | 0.0 | 1 |
| frag_check | turtle | 5/5 | 0.0 | 5 |
| pirate_grenadier | aggressive | 0/5 | 3.6 | 1 |
| pirate_grenadier | spread | 5/5 | 1.6 | 0 |
| pirate_grenadier | turtle | 0/5 | 3.6 | 2 |

### Reflex KPIs (sums)

| scenario | doctrine | setting | frags seen | in blast at landing | escaped | stayed | moves (frag / fire) | nudges | too late | ignored (viscous) |
|---|---|---|---|---|---|---|---|---|---|---|
| frag_check | aggressive | cycle | 17 | 5 | 0 | 5 | 0 | 0 | 0 | 0 |
| frag_check | aggressive | after rx2 | 16 | 15 | 7 | 8 | 72 (49 / 23) | 0 | 5 | 0 |
| frag_check | spread | cycle | 15 | 12 | 2 | 10 | 0 | 0 | 0 | 46 |
| frag_check | spread | after rx2 | 22 | 15 | 8 | 7 | 63 (46 / 17) | 0 | 10 | 21 |
| frag_check | turtle | cycle | 13 | 12 | 1 | 11 | 0 | 0 | 0 | 147 |
| frag_check | turtle | after rx2 | 19 | 30 | 17 | 13 | 61 (43 / 18) | 0 | 9 | 96 |
| pirate_grenadier | aggressive | after rx2 | 0 | 0 | 0 | 0 | 166 (0 / 166) | 113 | 0 | 0 |
| pirate_grenadier | spread | after rx2 | 5 | 3 | 2 | 1 | 60 (8 / 52) | 0 | 0 | 324 |
| pirate_grenadier | turtle | after rx2 | 3 | 2 | 1 | 1 | 49 (2 / 47) | 0 | 1 | 242 |
| pirate_grenadier | aggressive | after rx1 | 5 | 2 | 1 | 1 | 207 (2 / 167, +38 predicted) | 248 | 3 | 0 |

The "before" rows are not shown here. At a 120-tick cycle a grenade is seen once at most, so
in-blast and escaped counts are undercounted there; compare them through the battle-log hits
instead.

### Reading the numbers

- **Escapes.** In frag_check, under the cycle with no reflex, 3 of 29 pawns in a frag's blast were out by
  the last sighting. Under reflex v2, 32 of 60 were.
- **Why the rest stayed.**
  - About half of the pawns that stayed were `too_late`: the grenade was first seen at its cell
    with under about 60 ticks of fuse left. Escaping takes 15 + about 40 ticks.
  - Most of the rest were the turtle's margin cases, which its viscosity ignores by design, and
    pawns still walking out at the last sighting (up to 30 ticks before the blast).
- **Hits.** Log-based frag hits are low-count and noisy (0–19 per 10 episodes). They fall clearly
  only for aggressive: 12 to 2 against cycle-only, 4 to 2 against before.
- **The cycle alone.** In frag_check, the adaptive cycle already halves hits and HP lost for turtle
  and spread against fixed 120. More frequent re-orders mean pawns stand still less.
- **The grenadier theme.** It is decided by rockets and molotov fire, not frags. The reflex there
  mostly does fire step-outs (166 per 5 episodes for aggressive) and nudges. Its outcomes are
  equal or worse than cycle-only for every doctrine. v1 to v2 cut the nudges and dropped the
  predicted moves, but outcomes did not recover.

## 4. Open issues

- **Fire step-outs and spacing nudges cost more than they save** on the grenadier theme, especially
  for aggressive. Each one replaces Auto attack with a Go here, and Auto attack then walks the pawn
  back into the same cover. Next step (v3): fire only when the pawn's own cell burns, no nudges; or
  nudge only pawns that are not currently shooting. Validate on theme_pirate_grenadier before the
  matrix.
- **Not dodgeable:**
  - doomsday and triple rockets (30–60 ticks in flight, aiming not observable);
  - molotovs (they burst on impact, and the in-flight prediction is right only ~39% of the time);
  - frags first seen with less than ~55 ticks of fuse left, about 1 in 4 of in-blast cases at
    30 ticks;
  - frags landing while a pawn is boxed in (trapped: 0 so far).
  A 15-tick fast cycle (the minimum) would rescue some late frags, at about 2x the fast-step cost.
- **False alarms.**
  - A frag seen mid-flight is treated as possibly resting, so pawns under its path move needlessly.
    Accepted: about 1 in 3 such sightings has already landed at a 30-tick cycle.
  - v1's predicted moves were mostly false alarms (74 moves).
- **Dodging into worse spots:**
  - Safe cells only avoid known hazards: no cover or line-of-sight check.
  - "Not closer to the enemy" is only a preference.
  - Turtle pawns that dodge are re-sent to their slot afterwards, which can be inside a fire.
  - We have not measured how often a dodge exposed a pawn to fire.
- **KPI caveats.**
  - Hits on a pawn that dies before any harvest are lost. Harvest runs after each nearby blast.
  - "Escaped" uses the last sighting, up to 30 ticks before the blast.
  - The 1.9-cell blast radius rests on 39 pawn observations from only 4 blasts.
- **Theme scenario note.** frag_check is lordless, so it never produces a "fleeing" message, and its
  outcomes are trivial wins. It is only useful for exposure and hit counts. It lives in
  `scenarios_out/`, so `--scenarios all` would include it; the matrix should list scenarios
  explicitly.
- **Sample sizes** are n=5 on the grenadier theme. The cycle-only improvement (aggressive 1/5 to 3/5,
  spread 1/5 to 4/5) should be confirmed in the matrix.
- **Untested here:** kite, focus and close were converted to tick timers and given the reflex, but
  were not validated in this round. Their versions were bumped, so the old matrix rows are stale.
