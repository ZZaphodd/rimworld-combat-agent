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
- **Timers in ticks, not steps.** *Cutting the step from 120 to 30 ticks shrank every step-counted
  rule 4x (a 360-tick stall would have triggered a sally) (execution_report §5).* → Every duration
  is a tick constant, and agents get `now` and `step_ticks`.
- **Pre-registered predictions were mostly wrong.** *4 themes: kite was worst against melee,
  "suicidal" close was 2nd best, and turtle was best against melee (theme_report).* → Route by
  measurement, never by narrative. Keep pre-registering anyway: it exposes wrong models.
- **Batches with the same config differ a lot.** *Two v2 grenadier batches differed by up to
  2.8 lost/ep (threatmap_report §6).* → Use n ≥ 10–20 for any cell a decision depends on, and
  holdout checks on a 2nd squad and a 2nd arena (TODO).
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

Planner algorithm (v3): approach = shortest walkable path from the enemy centre to the anchor.
Enter at the first path cell within 14 of the anchor; the exit = the 8 path cells before it.
enemy_ground = passable cells within range of the exit but > 14 from the anchor. For each cell
reachable within 14: window = approach cells within range with LOS; exposure = enemy_ground cells
that see it. Then filter, pick the best cell, and pack with ≥ 1.5-cell gaps. Range is fixed at 25
(not per weapon).

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

1. **Space `" "` passability disagrees.** `battleground.Grid` and `reflexes.TiledGrid` treat it as
   passable; `threatmap.Terrain` treats it as impassable. `Grid.from_rimmolt` also fills cells it
   never fetched with `" "`. The meaning of `" "` in ascii is UNVERIFIED. Use one terrain module
   with one legend.
2. **Terrain caches go stale.** Fires burn trees and explosions change the map, but turtle builds
   its grid once per episode, close once, and `threatmap.Terrain` is cached **per save per
   process**: tiles fetched mid-episode (possibly after burning) are reused in later episodes of
   the same save. **Design for the rewrite (decided):** keep a cache, but make it correct:
   - Never cache across episodes (at most per episode) — fixes the leak.
   - Event-driven invalidation: re-fetch only the tiles touched by fire cells (already queried),
     `Explosion` things, and buildings added/removed in `wait_for_event`'s `_delta` (destroyed
     walls). UNVERIFIED: whether burned trees (plants) appear in `_delta`; if not, fire cells are
     the signal (trees only burn where there is fire).
   - While in contact, refresh the 2–4 tiles within ~30 cells of the squad every ~600 ticks to
     catch what events miss; keep far tiles cached.
   - Why not drop the cache: a 50×50 ascii tile costs ~17 ms (measured); re-fetching the threat
     map's box (~16 tiles, ~270 ms) every step would make steps 2–3× slower, ~+80–130 s per
     episode at the 30-tick cycle, ~+5–7 h per 210-run matrix. The design above costs ~0.
3. **The weapon range table is guesses** (GAME_FACTS.md §5): "bolt" 30 < "rifle" 35, greatbow =
   bow, no mech weapons (default 25). The planner uses a fixed 25. Read ranges from
   `get_info_card` or the XML.
4. **Two melee classifiers** (`is_melee` keywords vs census `weapon_class`) disagree, e.g. on blade,
   scythe, pike. Use a single classifier.
5. **Rescue reserves a pawn for a disabled option** (§2 doctrine agent).
6. **The doctrine agent undrafts wounded fighters**, who then flee, and may re-draft them as
   "evacuees" in the same step (combat_live logs).
7. **grade() "decisive" ignores our losses** (EVAL_SPEC §5). Stored grade/win fields are stale in
   old rows.
8. **`--resume --agents hold` counts nothing** (canonical-name mismatch; PROCEDURES §11).
9. **engagement_ratio undercounts fire at will.** Replace it with damage-log or attack-verb based
   KPIs.
10. **Kidnap matching is by lowercased short name** from the job text. Two pawns with the same
    short name, or a job naming the pawn differently, would mis-attribute (UNVERIFIED in practice).
11. **Frag-hit KPI** matches `"<short name>'s"`, so short-name collisions are possible. Hits on a
    pawn that dies before a harvest are lost.
12. **The doctrine agent, kite and close have no `versions` map**: their agent_version doesn't change
    with the reflex version. Under reflex v3 they get the threat-map reflex but never call `place`.
    Untested.
13. **frag_check is in scenarios_out/**, so `--scenarios all` includes it. List scenarios
    explicitly.
14. **The `Fire at will` toggle is blind**: the measurement scripts toggle it without reading the
    state back.
15. **theme_report.md is outdated**: it says 113/210 episodes, but theme.jsonl has 210 rows. The
    final table exists only in theme_analysis_final.log (older grade) and DATA.md §7.
16. **The census code comment** blames the 133-pawn mech "raid" on pod leaks, but all-Militor raids
    of 120–133 still appear after the fix (GAME_FACTS.md §2).
17. Two v3b grenadier rows have 9 and 28 lost agent steps (list_things guard, fixed afterwards) and
    were **not re-run**.
