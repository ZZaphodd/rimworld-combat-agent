# Lessons (micro / tactical / strategic)

Knowledge that so far lived only in parameters, docstrings and reports. Each entry has three
parts: **lesson** → *evidence* → **implication for the rewrite**. Layer terms are from
GLOSSARY.md and WORKFLOW.md. Report names refer to results/*.md. Numbers are n=5 per cell unless
stated otherwise; with a per-episode SD of 1.5–2.4 deaths, most differences in losses are not
significant.

## 0. Cross-layer

- **Change one layer at a time.** *Threat map v3 changed micro (dodging, hysteresis) and tactical
  (standing outside throw range) together and was judged by battle losses, so neither effect could
  be read (threatmap_report; WORKFLOW).* → Micro gets drills judged per event. Tactical is
  judged with micro pinned to a drill-verified version.
- **The "turtle + grenade" stalemate was three problems, not one.** *Threat map v3: pawns stood
  outside the 13-cell throw range, raiders stopped throwing, fights took 2–5x longer and gave
  rockets more volleys (threatmap_report).* Split by layer:
  micro — dodging a resting frag: solved (97.9% escape in the frag drill), cost = false-alarm moves;
  tactical — where to stand vs throwers (accept-and-dodge / stand off / close in) was slipped in
  as "avoidance", and nothing detected the lack of progress;
  strategic — turtle's preconditions were not met (forest arena, no choke; our 25–31 range vs their
  13 gives raiders no reason to come in);
  enemy AI — why raiders out of range didn't advance is unknown.
  → Layer contracts in WORKFLOW; preconditions in doctrine specs; progress-rate KPI; positioning
  vs throwers is an explicit tactical option; ENEMY_AI hypothesis "raiders out of range".
- **Timers in ticks, not steps.** *Cutting the step from 120 to 30 ticks shrank every step-counted
  rule 4x (a 360-tick stall would have triggered a sally) (execution_report §5).* → Every duration
  is a tick constant, and agents get `now` and `step_ticks`.
- **Pre-registered predictions were mostly wrong.** *4 themes: kite was worst against melee,
  "suicidal" close was 2nd best, and turtle was best against melee (theme_report).* → Route by
  measurement, never by narrative. Keep pre-registering anyway: it exposes wrong models.
- **Batches with the same config differ a lot.** *Two v2 grenadier batches differed by up to
  2.8 lost/ep (threatmap_report §6).* → Use n ≥ 10–20 for any cell a decision depends on, and
  holdout checks on a 2nd squad and a 2nd arena (TODO).
- **A gate with one test per cell fails unchanged code.** *42 cells × 2 metrics at n = 10: a
  "90% interval above 0 and worse by the margin" rule fails an A/A comparison ~93% of the time
  (tools/gate.py --simulate). The real A/A run (feat/signals-preconditions, report-only bump)
  had 2 such cells (amove × mechs 0.0 → 0.5 lost/battle, doctrine × grenadier trade share 0.43 →
  0.27) with identical code; per-agent lost/battle moved by up to 0.34 (spread 1.81 → 1.47).* →
  The gate uses a strict per-cell interval (98%, above the margin) plus a pooled per-agent check
  (WORKFLOW "Gate rule"); single-cell regressions need more runs to be seen. Never read one cell
  of n = 10 as a regression or an improvement.
- **Moving pawns don't shoot.** *Kite v1 retreat_share 0.48–0.60; the doctrine agent v1 had 12–13
  of 14 pawns "moving" at contact (execution_report).* → Count the shooting time a move costs in
  every layer (v3 move_cost does this).

## 1. Micro (reflexes, battle drills)

**Decision cycle**
- **The adaptive cycle helps on its own.** *Grenadier theme, cycle-only vs fixed 120: amove 3/5 vs
  1/5 wins, spread 4/5 vs 1/5. On frag_check, HP lost was halved for turtle and spread
  (reflex_report).* → Keep it: 30 ticks while a raider is within 40 cells, else 120. A 15-tick fast
  cycle would save some late frags at ~2x the cost.

**Frag dodge**
- **Start the fuse clock at the first sighting at the current cell, minus half a step.** *Waiting
  for a 2nd sighting at the same cell left ~45 ticks, too little to walk 3 cells (smoke tests).
  About 1 in 3 mid-flight sightings has already landed at a 30-tick cycle.* → deadline =
  first_seen_here − step/2 + 90. Accept the false alarms from pawns under a grenade's flight path.
- **Danger radius 2.5; blast reach 1.9.** *0/32 pawns hit at d ≥ 2.2, 6/7 at d ≤ 1.4, but from only
  4 blasts (hazards.md).* → Keep a 0.6-cell margin. Re-measure with more blasts.
- **Safe cell = walkable, outside every zone, not held or targeted by a squadmate, reachable before
  the deadline** (15 + d / 0.07 ticks). Use an 8-step BFS and prefer cells not closer to the
  raiders. *Escapes rose from 3/29 (cycle, no reflex) to 32/60 (reflex v2) on frag_check.* → Same
  rule. Add cover/LOS checks: dodges are not checked for exposure.
- **About half of the failed escapes were `too_late`** (first seen with < ~60 ticks left). *reflex_report §3.*
  → Unfixable at a 30-tick cycle. Count it separately; don't tune against it.
- **Don't act on in-flight landing predictions.** *Prediction right for 51/130 (39%); 74 of v1's
  155 frag_check moves were prediction moves, mostly false alarms.* → Score predictions only.
  Molotovs get no pre-impact reflex; their fire does.

- **Drill-verified (rca micro v4, 2026-10-03, results/drills/frag_drill.jsonl).** Frag drill
  (PROCEDURES §12): theme squad frozen on its slots, fire at will off, 1–3 frag-only
  `Grenadier_Destructive` at 12 cells, fixed 30-tick cycle, 5 sessions per mode, alternating.
  Judged per event:

  | | dodge off | dodge on |
  |---|---|---|
  | frags exploded | 75 | 76 |
  | pawns threatened (≤ 1.9 of the final cell at first sighting) | 120 | 145 |
  | … escaped (outside 1.9 at the last sighting) | 0 (0%) | 142 (97.9%) |
  | … hit (battle log) | 43 (35.8%) | 1 (0.7%) |
  | events where every threatened pawn escaped | 0 / 73 | 69 / 72 |
  | pawns in blast at landing / escaped | 117 / 0 | 96 / 93 (96.9%) |
  | squad pawns hit, all frags | 44 (0.59 per frag) | 1 (0.01 per frag) |
  | squad standing at session end | 6–8 / 14 | 14 / 14 (all 5) |
  | moves / false alarms (not inside 1.9 of the final cell when ordered) | 0 | 377 / 205 (54%) |
  | moves ordered before the frag's landing sighting | – | 168 |
  | too_late / trapped | – | 1 / 0 |
  | fuse left at the order (median) | – | 75 ticks |

  → The frag dodge works as a reflex when nothing else moves the pawn: ~36% of threatened pawns
  are hit without it, ~1% with it. Its price is movement: ~5 moves per frag, half of them false
  alarms (in-flight sightings and the 1.9–2.5 margin). In a battle every move costs shooting time
  (§0), so the tactical layer must be judged with this micro version pinned, not this drill
  number. Compare legacy reflex v2 in frag_check battles: 32/60 escaped, because Auto attack and
  the doctrine move pawns too.
- The 2.5 margin and the in-flight trigger are now the tunable part (false-alarm rate); the
  next drill should vary them one at a time.

**Fire and rockets**
- **Fire step-outs and spacing nudges cost more than they save.** *Grenadier theme, reflex v2 vs
  cycle-only: amove 0/5 vs 3/5 wins, 4.6 vs 3.2 lost/ep; turtle 5.4 vs 3.2. Each move replaced Auto
  attack with Go here, and Auto attack then walked the pawn back into the same cover.* → React only
  to fire on the pawn's own cell, never nudge for rockets, and never break a shooting pawn for a
  low-severity threat.
- **Standing next to fire does no damage.** → Adjacent-fire severity stays low (v2 0.2, v1 0.4).
- **Rockets can't be dodged** (30–60 ticks in flight, aiming not observable). → Counter rockets in
  targeting (carriers first: doctrine agent priority 6, `priority_target` within 35 cells) and in
  spacing (tactical), never with reflex moves. *v3a's clump-driven moves (500 in 5 amove episodes)
  were the v2 nudges again (threatmap_report §1).*

**Viscosity and ownership**
- **Viscosity per doctrine.** v2 severity thresholds: amove/close 0.15, spread/doctrine agent/kite
  0.30, turtle 0.80. v3 threat-unit thresholds: amove/close 0.5, spread/doctrine agent/kite 1.0,
  turtle 3.0. Turtle leaves its slot only for a frag (5–10) or fire under it (6). *Turtle ignored
  147 threatened pawn-steps on frag_check by design.* → Keep viscosity a doctrine parameter that the
  micro layer reads.
- **Ownership timing.** v2 owns a pawn until min(deadline + 10, now + 120). v3 owns it until it
  arrives (≤ 150 ticks) or until the frag blows + 10, whichever is later, and releases it early if
  the destination becomes ≥ HIGH. The doctrine skips owned pawns and re-issues its order on release
  (turtle walks back to its slot). → Same contract. Turtle must not return to a slot that is still
  hot (v6+ checks `slot_ok`).

**Threat map (v3)**
- **Hysteresis must cover the neighbourhood.** *v3a forbade only the exact fled cell, so pawns
  settled next to a still-hot fled cell, which counts as a return.* → Forbid the fled cell and its 8
  neighbours until the fled cell's remembered hazard < LOW (1.0).
- **Move gate (v3b):** hazard(here) without rockets ≥ threshold, then move iff threat(here) −
  threat(best) > threshold + move_cost, where move_cost = 0.5 + 0.5 if shooting + the fire value
  given up. *Throw moves stayed high for amove (~100–140/ep): a 0.5 threshold against a 3.0 throw
  zone means every advancing grenadier pushes the line back.* → Add a per-pawn move cooldown or a
  threshold ≥ 1.0 for throw-only hazard (untried).
- **Doctrine positioning (`place`)** takes over from Auto attack when hazard ≥ 1.5 on or 4 cells
  around the pawn, or a fled cell is within 6. It picks the best cell within 6 that sees the
  target; fallbacks are `kill` (Fire at the thrower/carrier) or `back` (≤ 12 cells, target kept in
  range). *Time in high threat fell 2–9x and returns to danger fell for amove and spread, but losses
  on the grenadier theme did not improve.* → This is a tactical decision in disguise (standoff
  range). Put it in the tactical layer and test it there.

## 2. Tactical (doctrine execution)

**RimMolt "Auto attack (AI)"**
- **Auto attack walks off to find cover and stops shooting.** It also re-chooses cover we just fled.
  *Doctrine agent v1: 12–13/14 pawns "moving" at contact. Reflex v2: pawns returned to fled
  cells.* → If a target is in range and LOS, use **Fire at** (stand and shoot). Use Auto attack
  only to close the distance or in calm areas.

**Battleground planner (turtle)**

| Version | Failure | Fix |
|---|---|---|
| v1 | Split the squad into a crossfire; raiders that got inside beat each half alone (Lanchester against us; GLOSSARY "mutual support") | Pack the squad around the single best cell |
| v2 | Ranked cells by window ÷ (1 + exposure) alone: a corner seeing ONE approach cell with no exposure won ("hiding is not holding") | Only cells with window ≥ 0.6 × best window compete on the ratio |
| v2 | Cluster radius capped at 5, which left 8/18 shooters without a cell | Widen the radius by 2 until every shooter has a cell (fall back to any scored cell beyond 2 × search radius) |
| v2 | Raid already inside (drop pods): picked a corner with window 1 | Approach < 3 cells → `no_approach`: don't hold, fight |
| v3 | – | Cells < 8 from the funnel exit are excluded (standoff), so raiders cross open ground under fire |
| v4 | One guessed range (25) for every gun, while the theme squad spans 12.9 (chain shotgun) to 30.9 (assault rifle) | Per-pawn XML ranges; shortest range picks first (rca/tactical/planner.py) |

Planner algorithm (v3): approach = shortest walkable path from the enemy centre to the anchor.
Enter at the first path cell within 14 of the anchor; the exit = the 8 path cells before it.
enemy_ground = passable cells within range of the exit but > 14 from the anchor. For each cell
reachable within 14: window = approach cells within range with LOS; exposure = enemy_ground cells
that see it. Then filter, pick the best cell, and pack with ≥ 1.5-cell gaps. Range was fixed at
25 (not per weapon). **v4 (rca, phase 2):** same rules on rca/terrain.py (8-neighbour paths);
site chosen with the shooters' median XML range, exposure with the raid's median range (every 2nd
enemy-ground cell), and each shooter, shortest range first, takes the free cell with the largest
window for its own range.

**Turtle (hold) parameters and why**

| Parameter | Value | Why |
|---|---|---|
| GRID_MARGIN | 60 | analysed rectangle around the anchor |
| MELEE_TRIGGER | 7 | melee pawns stand behind the line and charge only raiders this close |
| INSIDE_RADIUS | 10 | a raider this close to the anchor = the fight is inside, everyone engages |
| IDLE_SALLY_TICKS | 4800 | nobody within 30 cells this long → go get them |
| STALL_SALLY_TICKS | 1440 | v4: in contact but no raider lost this long → go get them. *Mechs parked 13–28 cells out; the idle rule never fired; 2/5 timeouts. With it: mechs 4/4 wins, 0.2 lost; it never fired on melee themes (stalls ≤ 360)* |
| RETREAT_HP | 45 | below it, step off the line (stay drafted) |
| REPLAN_ANGLE / COOLDOWN | 45° / 1200 ticks | re-plan when the raid's bearing swings; the cooldown stops a split raid making the line dance |

- **A passive line loses to raids that won't come.** *pirate_sniper: turtle neutralized 8%,
  P = 0.00 vs amove. In grade_check, pirate_mixed raids turned "satisfied" and left with 14/14
  escaped and 0 killed.* → Turtle needs a reset/commit criterion for out-ranging raids (sally, or
  route snipers elsewhere). An unbroken line is not a win.
- **Terrain is cached once per episode** ("terrain doesn't change mid-fight"), which is wrong once
  things burn — a turtle trusting a choke that has been blown open. See the decided cache design
  in §4 item 2.

**Doctrine agent (focus) v1 → v3**
- Rally 3 cells apart (2 packed the squad for one grenade). engage_radius 45, exposed_radius 30,
  retreat_hp 45, max 4 guns per target, full re-assignment every 1200 ticks, idle re-issue at most
  every 120 ticks per pawn.
- Target score = priority × 10 − distance × (2.0 melee / 0.5 ranged) + 15 if in range. Melee pawns
  only take Lancer/Pikeman/Scyther unless something is within 20.
- **Split-raid rule:** only hostiles within engage_radius + 15 of the anchor are assigned, so a split
  raid doesn't drag the squad to both edges.
- v2 fixes: Fire at when in range; drop assignments whose pawn is no longer attacking or moving
  (v1's `assigned_share` fell to 0.21 in the 8-loss run); skip disabled options.
- *Outcome: a tie on both home themes (P 0.62, 0.53). Guns per target barely moved (2.6 → 2.7). It
  is catastrophic vs grenadiers (5.2 lost).* → Focus fire on its own is not shown to help. Combine
  it with spread's spacing. Pull wounded pawns back instead of undrafting them: an undrafted pawn
  flees (hostility response).
- **Rescue bug:** arenas have no beds, so "Rescue" is always disabled. The rescuer still stays
  reserved in `rescues` and is removed from focus fire while the victim is down; v1 even clicked
  the disabled option (41x, exec_v1.log). → Check that an option is enabled before reserving a pawn
  for it; a beds-free arena needs carry-to-safe-cell instead.

**Kite v1 → v3**
- *v1: everyone Auto-attacked forward before contact (doubling closing speed), then every threatened
  shooter backed off 8 cells directly away; with equal speeds that buys nothing. retreat_share
  0.48–0.60, squad scattered over 50–160 cells, 1/8 wins vs pirate_melee. v2a (anyone a raider could
  reach before the next decision runs): at 120 ticks that was nearly everyone; 12/14 were moving and
  7 went down.*
- **v3 rule:** nobody advances while melee raiders come (drafted, standing, fire at will). **Only the
  chased shooter runs**: the victim comes from the raider's `targeting` ("attacking colonist
  <name>"), falling back to the nearest shooter, and only if the raider is within reach =
  0.08 × step_ticks + 3. The runner goes **through the squad's centre** to 5 cells past it (at
  least `reach`), fanned sideways by ((i mod 5) − 2) × 3. Melee pawns take the raider nearest any
  shooter, one each, engaging within 8. Auto attack sweep starts once no melee raider has been
  within 40 for 360 contact ticks.
- *Result: 5/5 on both melee themes (P 0.97 / 0.93). retreat_share 0.14–0.27, but distance and
  adjacency KPIs were flat and gap5 was 0.10–0.16.* → The win came from **shooting time and
  cohesion**, not distance. Kite v3 is "stand and fire, peel the hunted pawn through the group".
  The bait role (TODO) generalises it. It is compact, so never route it against explosives. At a
  30-tick cycle reach is ~5.4 cells; MARGIN needs re-tuning (untested).

**Spread**
- MIN_GAP 5, STEP_OUT 5 cells, HOLD 600 ticks on the new cell. The step-out direction is the sum of
  unit vectors away from close neighbours; if they nearly cancel (|v| < 0.3, i.e. stacked pawns),
  **fan out by index**: angle = i × 2.4 rad. Each pawn Auto-attacks the raider nearest to *itself*
  (a shared focus target would pull everyone onto one line).
- *gap5_share 0.71–0.79 vs 0.1–0.4 for the others. Best vs grenadiers (P 0.76 vs amove).* → A
  spacing primitive other doctrines should reuse (the doctrine agent and kite pack too tightly).
- *Spread + threat-map v3 looked worse in both batches (1.6–2.0 lost vs 0.8–1.4; 95–124 moves/ep vs
  16): its own step-outs and the map's moves add up.* → Choose one owner for spacing moves.

**Close**
- CLOSE_DIST 14, a bound of ADVANCE 10 cells at most every 120 ticks per pawn. hop = min(10,
  d − 14 + 2) toward the nearest raider, ending at the nearest free cell within 3 that touches cover
  (`*`, `#`, `%`). Once inside 14, Auto attack for good.
- *Home: 4/5 sniper, 5/5 mechs; all 14 inside 14 cells by tick ~1380. Best overall win count in the
  theme matrix (25/35 under the current grade). Losses come during the approach.* → Next step:
  bounding overwatch (TODO).

**Threat map weights (what went wrong)**
- Weights: frag 10 (d ≤ 1.9) / 5 (≤ 2.5); throw zone 3.0 = HIGH within 12.9 + 2, tapered over 3,
  × 0.3 without LOS; rocket base 0.5 within 36; clump 0.6 per mate within 3; fire 6 / adjacent 1.5;
  exposure 0.35 per raider with range + LOS; cover −0.8 wall/rock, −0.3 tree facing the 3 nearest
  raiders. Memory half-life 240 ticks. Positioning value 0.5 per shootable raider (cap 3), +1 if
  the target is seen, −0.08 per cell walked.
- **Holding outside throw range makes fights 2–5x longer.** *On frag_check, raiders stopped
  throwing, but kills took 2200–4500 ticks instead of 600–800. Against rocket carriers, a longer
  fight means more volleys.* → Add a time/exposure term ("finish them" when our fire value is high,
  all free guns on carriers) rather than more avoidance.
- **W_THROW = HIGH makes the returns KPI hypersensitive.** *Known entries dominate (amove 28.8/ep):
  zones drift onto destinations while pawns walk.* → Set W_THROW slightly below HIGH, and use a
  path-aware return check (transits count as returns today).

**Phase-2 smoke (rca, 2026-10-03; results/phase2/smoke.jsonl, n=2 per cell, adaptive + micro v4).**
Smoke runs check that each doctrine does what its spec says, not which doctrine is better.

| Doctrine | Theme | Grades | Lost (dead+kidn.) | LER | progress_rate | fire_share ours/theirs | Spec KPIs |
|---|---|---|---|---|---|---|---|
| doctrine v4 | pirate_mixed | defeat, defeat | 0, 8 (5 kidnapped) | ∞, 0.23 | 120, 107 | 0.44/0.58, 0.42/0.45 | guns/target 2.4, 1.8; rescues started 19, 13 (carried 10, 6) |
| doctrine v4 | mechs | decisive ×2 | 1, 0 | 2.0, ∞ | 266, 333 | 0.47, 0.50 | guns/target 3.3 ×2 |
| turtle v8 | pirate_melee | decisive ×2 | 1, 0 | 2.5, ∞ | 303, 309 | 0.69/0.41, 0.66/0.49 | on_slot 1.0; surface 9.0 vs 3.6–4.3; no sally |
| turtle v8 | tribal_melee | repelled, decisive | 0, 0 | ∞, ∞ | 182, 677 | 0.53/0.31, 0.73/0.24 | run 1: replan → raid centre inside → no_approach sally |
| spread v5 | pirate_grenadier | repelled ×2 | 2, 1 | 1.3, 2.6 | 176, 201 | 0.34/0.39, 0.19/0.27 | gap5 0.81, 0.87; 80–88 step-outs |
| spread v5 | frag_check | decisive ×2 | 0, 0 | ∞ | 646, 554 | 0.64, 0.43 | gap5 0.0–0.03 (fight over in ~600 ticks) |
| kite v5 | pirate_melee | decisive ×2 | 0, 0 | ∞ | 306, 347 | 0.68/0.43, 0.67/0.27 | retreat_share 0.09, 0.04; adjacent 0.04, 0.0 |
| kite v5 | tribal_melee | decisive ×2 | 0, 0 | ∞ | 309, 178 | 0.62/0.18, 0.50/0.22 | retreat 0.17; run 2 raised no_progress (stall 5159) |
| close v3 | pirate_sniper | defeat ×2 | 5, 5 | 0.35, 0.30 | 137, 103 | 0.56/0.45, 0.51/0.46 | all 14 closed, mean tick 1134, 1228 |
| close v3 | mechs | decisive ×2 | 2, 1 | 1.0, 2.0 | 379, 319 | 0.60, 0.63 | all 14 closed, mean tick ~1700 |

(Mech-side enemy fire share was 0.0 in these rows: a parser gap, fixed afterwards. Re-run of both
cells, 2 episodes each (results/prebaseline/mech_recheck.jsonl): enemy fire share 0.64, 0.59
(doctrine) and 0.63, 0.73 (close); ours 0.53, 0.49 / 0.68, 0.64; all 4 decisive.)
- **Turtle and kite still win their home themes** (8/8 decisive or repelled, 1 colonist lost in
  8 battles); turtle's concave shows as engagement surface 9–10 of ours vs 3.6–4.3 of theirs.
  → The ports keep the v3/v4 behaviour; the baseline matrix can measure them.
- **The `defensible_terrain` check failed on every theme (0.02 vs 0.10) while turtle won 4/4 on
  melee themes.** Against raiders that charge, turtle's edge was the standing line, not cover.
  → The precondition "defensible terrain" is either miscalibrated or not needed against melee;
  calibrate against outcomes before the router uses it (UNVERIFIED either way, n=4).
- **The doctrine agent lost both pirate_mixed battles** (one with 0 dead but 11 downed and a
  satisfied raid, one with 5 kidnapped) while rescuing 13–19 times per battle; on mechs it won
  both. Carrying works mechanically, but a carrier walks ~1 cell per 30 ticks (one probe) and stops shooting.
  → Rescue is not shown to pay; keep it doctrine-agent-only. It is now an option
  (`rescue=on|off`, and `wounded_pullback=on|off` for doctrine and turtle; natural on); the
  baseline compares them. One episode each ran as designed (rescue=off: 0 rescues; pull-back off:
  0 pull-backs), n=1, no verdict.
- **close loses to snipers in this squad** (5 lost per battle, all 14 closed by tick ~1200): the
  losses come during the approach, as in v2. → Bounding overwatch (TODO) before reading close's
  sniper cell as a doctrine verdict.
- **The no_progress signal fired twice, both in won battles** (kite tribal_melee: stall 5159
  ticks while the last raiders were slow to die/leave; turtle tribal_melee after its sally; plus
  one `precondition:no_approach` in the same turtle row, so 3 signal entries in 2 of 20 rows).
  Rule 1 said "no points lost for 3000 ticks": a pause, not a stalemate. → **Rule 2** (EVAL_SPEC
  §2): count only *contested* time, i.e. steps in which we took damage / lost or downed a pawn, or
  a raider had one of us in its weapon range (throw zone for grenadiers). Offline, the smoke rows
  only bound it (contested ≤ pause, so the 18 rows with a pause < 3000 cannot fire; the per-step
  data needed for the 2 others is not stored). Re-run of the two cells (results/prebaseline/
  signal_check.jsonl, n=2 each, all won): pauses 3164 (turtle) and 3122 (kite) ticks, so rule 1
  would have fired twice again; contested 1500 and 418 ticks, rule 2 fired 0 times. Threat
  dominates the pressure: in the 14 rule-2 rows so far, 31–100% of post-contact time was
  pressed (100% in all 4 mech battles: Pikemen reach 44.9 cells). Whether rule 2 fires when it should (a real stalemate: snipers out-ranging a turtle)
  is untested. → T = 3000 contested ticks stays a first value (UNVERIFIED), to be fitted on
  baseline data.
- **Most bad battles are lost fast, not stalled.** *no_progress (3000 contested ticks) is
  precise (82% of fires in bad battles) but catches 12% of them on baseline-v1. losing_trade
  (≥ 2 pawns gone and running LER < 1) catches 56% at 85% precision with ~3,100 ticks median
  lead (exact replay on the gate rows; the baseline proxy fit gave 50–56% / 87–94%); together
  106 of 178 bad battles (calibration.md).* → The router gets two signals; defeats by pawns
  downed (not dead) are still unflagged.
- **Only enemy-based preconditions can be fitted on one squad and one arena.** *In baseline-v1
  ranged_squad (0.93), defensible_terrain (0.02) and room_to_spread (1.00) are constant; turtle
  won on the "indefensible" forest vs melee. enemy_approaches (turtle), enemy_melee_heavy (kite)
  and the new enemy_splash_heavy (spread: grenadier 0.77 vs ≤ 0.13) separate the themes; close's
  enemy_outranges points the wrong way for the current close.* → defensible_terrain is soft;
  squad/terrain thresholds wait for the holdout.
- **`$(grep -c x f || echo 0)` is "0\n0" when nothing matches** (grep -c prints 0 and exits 1).
  *The gate script's crash-count stop never worked (no crash happened).* → `n=$(grep -c ...);
  n=${n:-0}`.
- **vs_throwers options run** (results/phase2/options.jsonl, 1 episode each, not an evaluation):
  stand_off made 15 thrower moves (spread, grenadier) and close_in 24 thrower attacks; on
  frag_check turtle's on_slot_share fell from ~1.0 to 0.64 (stand_off) and 0.14 (close_in), as
  designed.
- Spread on frag_check never spread (gap5 ≤ 0.03): the fight ends in ~600 ticks, before 5-cell
  step-outs complete. Not a defect, but frag_check says nothing about spread's spacing.

## 3. Strategic (selection / router)

- **Provisional routing** (theme matrix v1, fixed 120, n=5, current grade; DATA.md §7):

| Raid | Route to | Avoid | Evidence |
|---|---|---|---|
| explosive-heavy | spread | kite, doctrine agent | P(spread > amove) 0.76 |
| melee-heavy (pirate or tribal) | turtle, close 2nd | kite v1 (fixed in v3, not re-run in the matrix) | P 1.00 |
| mechs | close / kite / doctrine agent (≈ tie) | turtle v3 (stall fixed in v4) | |
| mixed pirates | doctrine agent ≈ amove | spread | nothing clearly beats amove |
| snipers | doctrine agent, amove | turtle (8% neutralized), spread | P = 0.00 for 4 doctrines |
| tribal archers | turtle, kite | spread | |

  Rows are stale for kite, the doctrine agent and turtle. The squad has no long guns, so the
  sniper and archer themes partly measure the squad, not the doctrine.
- **Equal points ≠ equal headcount** (tribal 1500 pt ≈ 26 pawns vs our 14). → Use a force ratio by
  points *and* by count as router features (METT-T).
- **"win" overstates outcomes vs pirates.** *Fled raiders counted as cleared: grenadier/hold had 0
  killed, 12 escaped, 9/14 downed and was still "win".* → Grade by the game's flee/satisfied
  message (EVAL_SPEC §5).
- **The scoring weight is a local minimum.** *1 death = −100 vs 150 for the whole raid filters out
  high-variance, high-payoff tactics (TODO).* → Use LER with colonist = 4 enemies by points.
- **Census:** pirate raids are often single-class (27% are ≥ 80% one class at 1000 pt) and tribes
  are ~40% melee-heavy, so a router that reads composition has real variety to exploit. Outlanders
  are almost never single-class (DATA.md §6).

## 4. Known bugs and inconsistencies to fix in the rewrite

Status after rewrite phase 1 (2026-10-03): **[fixed]** = done in rca with the fix named;
**[partly]** = mitigated, rest open; **[phase 2]** = belongs to a module not ported yet;
**[data]** = a fact about old data, nothing to fix in code.

1. **[fixed] Space `" "` passability disagreed** (`battleground.Grid` / `reflexes.TiledGrid`:
   passable; `threatmap.Terrain`: impassable; `Grid.from_rimmolt` filled unfetched cells with
   `" "`). Verified in game: get_area never returns `" "` (0 of 62,500 cells of a whole forest map);
   its legend is `# % + * ~ . V ?`. One module, `rca/terrain.py`, with that legend; every cell is
   fetched on first use, so `" "` cannot occur. Tests: tests/test_terrain.py.
2. **[fixed] Terrain caches went stale** (turtle/close cached per episode, `threatmap.Terrain` per
   save per process). `rca/terrain.py` implements the decided design: one `Terrain` per episode
   (the harness creates it; nothing is module-level), stale tiles re-fetched lazily on
   `Explosion` things (radius 6), building `_delta`s (every fetched tile with a structure char,
   since `_delta` gives no cells), fire cells and contact refresh (tiles within 30 cells of the
   squad, both when older than 600 ticks). **Verified: burned trees do not appear in `_delta`**;
   a burned tree becomes a `BurnedTree` stump that still renders `*` (GAME_FACTS §6), so fire
   barely changes the ascii terrain; destroyed walls do appear (`removedBuildings`). In the smoke
   episode the cache made 1 fetch and 2 re-fetches on pirate_mixed (cost ≈ 0).
3. **[fixed, phase 2] The weapon range table was guesses.** `data/weapon_ranges.json` holds the
   XML verb ranges of 71 weapons and the weapons of 24 mech kinds (`rca/game/defs.extract_weapons`);
   `rca/game/weapons.range_source` looks them up by label or mech kind. The guesses were off where
   it mattered: rocket launchers 23 → 35.9 (matched "launcher"), Pikeman 25 → 44.9, Lancer
   25 → 32.9, hellcat rifle 35 → 26.9, bolt-action 30 → 36.9, chain shotgun 15 → 12.9, every
   bow 25 → 22.9–29.9 (GAME_FACTS §5). Turtle's planner v4 uses per-pawn ranges.
4. **[fixed] Two melee classifiers.** `rca/game/weapons.py` is the only classifier; `is_melee` =
   class `melee` (so blade, scythe, pike, lance, bite count as melee everywhere). The class
   keyword lists themselves are still UNVERIFIED against the full weapon set.
5. **[fixed, phase 2] Rescue reserved a pawn for a disabled option** (no beds in the arenas).
   `rca/tactical/squad.rescue_choice` takes only enabled options: Rescue if a bed exists, else
   **Carry** (verified in game: enabled in the arenas; the carrier keeps the pawn under Go here,
   `Drop <name>` puts it down), carried to a fallback cell 10 behind the squad. No enabled option
   → nobody reserved. Shake-out: a flat 300-tick pickup budget timed out and the same victim was
   retried every step (21 starts for 8 downed); now the budget is 60 + distance / 0.06 ticks and
   2 tries per victim.
6. **[fixed, phase 2] The doctrine agent undrafted wounded fighters**, who then fled. rca never
   undrafts: below 45% health the doctrine agent and turtle walk the pawn, drafted, to a fallback
   cell behind the squad (it still fires at will from there); test: tests/test_tactical.py.
7. **[fixed] grade() "decisive" ignored our losses.** grade v2: a clean sweep with standing < 0.5
   is `pyrrhic`; `grade_v1` kept for comparisons. Changes 2 of the legacy rows (exec_v1, exec_v2).
   Stored grade/win fields stay stale in old rows: reports recompute (EVAL_SPEC §5).
8. **[fixed] `--resume --agents hold` counted nothing.** `rca/eval/results.read_rows` canonicalises
   stored names and `run_batch` canonicalises CLI names (`b1`→amove, `hold`→turtle,
   `focus`→doctrine); tests/test_results.py.
9. **[fixed, phase 2] engagement_ratio undercounted fire at will.** Replaced for comparisons by
   `fire_share` / `enemy_fire_share` / `surface_*` from the pooled battle log (rca/eval/firelog.py,
   EVAL_SPEC §8): attack entries per pawn per 300-tick contact window, so a drafted pawn firing at
   will counts like one under Fire at. The old fields stay in rows for continuity.
10. **[partly] Kidnap matching by lowercased short name.** The tracker now updates the squad before
    the kidnapper check (a kidnapping is caught one step earlier) and lists ambiguous names
    (`debug_kidnap_ambiguous`) instead of guessing; matching itself is still by short name
    (UNVERIFIED whether job text ever names a pawn differently).
11. **[partly] Frag-hit KPI by `"<short name>'s"`.** The drill records whether squad short names are
    unique (`names_unique`, true for theme_base) and harvests logs right after each blast, per
    event; collisions in other squads remain possible.
12. **[fixed] No `versions` map for doctrine/kite/close.** The map is gone: agent version and micro
    (reflex) version are separate row fields and the resume key needs both. amove starts at v5 so
    its rows never pool with legacy b1 v1–v4.
13. **[fixed] frag_check in `--scenarios all`.** `load_manifests("all")` excludes tier `check`.
14. **[fixed] The `Fire at will` toggle was blind.** The drill reads `inspect_thing`
    (`actions[label="Fire at will"].active`) before and after toggling and aborts the session if
    a pawn is still on.
15. **[fixed, docs] theme_report.md is outdated** (113 of 210 rows). The full 210-row matrix,
    rescored, is results/rescored/theme.md and DATA.md §7; theme_report.md now says so.
16. **[fixed] The census comment** blaming the Militor swarms on pod leaks is gone with
    legacy/raid_census.py; GAME_FACTS §2 has the right statement.
17. **[data] Two v3b grenadier rows** have 9 and 28 lost agent steps and were not re-run. Legacy
    data; ignore those two rows when reading threatmap_check v3b.

New in phase 2 (found while porting):
- **Battle-log ticks are TicksAbs**, not `ticksGame` (318,941 vs ~2,300 in the same scenario):
  anything that joins log entries to episode time needs an offset (firelog estimates it).
- **Mech names in the log are lowercase with "the"** ("the termite's head") and several mechs
  share one label, so log KPIs are per name for mechs (EVAL_SPEC §8).
- **[fixed] Turtle Go here failures:** 11 failed orders ("No order matched 'Go here'") in one
  tribal_melee episode after the sally. Cause, reproduced in game on theme_tribal_melee
  (2026-10-03): the error (with an empty option list) means the pawn is **undrafted**; occupied,
  impassable and far cells still accept Go here. The game undrafts a pawn when it goes down, and
  it stands up undrafted; the doctrine kept it in its own `drafted` set and never drafted it
  again (that row has "McClain ... is no longer incapable of walking" at tick 7912, and the
  wounded pull-back retried the failed Go here every step; an undrafted pawn also follows the
  flee response — bug 6 by another road). Fix: squad doctrines and amove forget the draft of a
  downed/broken pawn and re-draft it when it is able (`kpis.redrafts`); goto() drafts and retries
  once on this error (`redraft_on_error`). Tests: tests/test_tactical.py (DraftingGame). In the
  11 squad-doctrine episodes since: 0 failed orders, 1 re-draft (close on mechs), 0 retries on
  the error. The 2 turtle tribal_melee re-runs had no pawn standing up again, so the original
  episode was not reproduced end to end; the cause was reproduced with a direct probe.

New in phase 1 (found while porting):
- **Kidnapper check lagged one step**: the squad's downed state was read from the previous
  observation (fixed, item 10).
- **A failed Go here cost the dodge**: 1 failed order in each smoke episode (fire step-outs). The
  micro layer now tries the next two best safe cells and keeps the last errors in
  `rx_goto_errors`.
- **"In blast at landing" is not a fair denominator across dodge on/off**: a dodging squad leaves
  on in-flight sightings, so fewer pawns are in the blast when the frag lands (trial drill: 4 vs
  12). The drill also scores the frag's final cell against pawn positions at its first sighting
  (`threatened`), which does not depend on the mode.
