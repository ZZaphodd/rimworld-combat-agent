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
3. **[phase 2] The weapon range table is guesses.** Still in `rca/game/weapons.RANGE_GUESS` for the
   doctrines that need it; read verb ranges from the XML (the XML reader exists now:
   `rca/game/defs.py`) when the planner is ported.
4. **[fixed] Two melee classifiers.** `rca/game/weapons.py` is the only classifier; `is_melee` =
   class `melee` (so blade, scythe, pike, lance, bite count as melee everywhere). The class
   keyword lists themselves are still UNVERIFIED against the full weapon set.
5. **[phase 2] Rescue reserves a pawn for a disabled option** (no beds in the arenas). The doctrine
   agent is not ported yet; TODO "Phase 2" has the fix (check `disabled`, carry to a safe cell).
6. **[phase 2] The doctrine agent undrafts wounded fighters**, who then flee. Fix with the port.
7. **[fixed] grade() "decisive" ignored our losses.** grade v2: a clean sweep with standing < 0.5
   is `pyrrhic`; `grade_v1` kept for comparisons. Changes 2 of the legacy rows (exec_v1, exec_v2).
   Stored grade/win fields stay stale in old rows: reports recompute (EVAL_SPEC §5).
8. **[fixed] `--resume --agents hold` counted nothing.** `rca/eval/results.read_rows` canonicalises
   stored names and `run_batch` canonicalises CLI names (`b1`→amove, `hold`→turtle,
   `focus`→doctrine); tests/test_results.py.
9. **[partly] engagement_ratio undercounts fire at will.** Still recorded (for continuity) and
   flagged as biased in EVAL_SPEC §8/§9; the damage-log / attack-verb KPI is phase 2.
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
