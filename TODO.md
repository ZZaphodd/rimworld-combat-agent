# TODO

Scope principle: RimWorld is not PvP. We overfit to the game's built-in enemy AI on purpose —
its rules (targeting, cover seeking, flee/"satisfied" triggers, kidnapping, pathing) are things
to learn, document (ENEMY_AI.md, with evidence) and exploit.

Sections: **Now** (blocking, in order) · **Roadmap** · **Open items by layer** · **Done** (log).

## Now

1. [ ] **Switch the evaluation standard to Strive to Survive and build baseline-v2** (WORKFLOW
   "Evaluation standard"). baseline-v1 and the first gate ran on Peaceful → exploration data.
   * convert arena_/scenario_/theme_ saves to Strive to Survive (raids unchanged); candidate
     route found: a one-line edit of the save (PROCEDURES §1b) — try it on one save first;
   * harness guard: Strive allows storyteller threats — detect unexpected raids mid-episode
     and mark the episode invalid (EVAL_SPEC §3; manhunter animals: later, Evaluation / harness);
   * record the difficulty in every result row (WORKFLOW traceability);
   * baseline-v2: 6 doctrines × 7 themes × 10, overnight; tag `baseline-v2`;
   * re-run the calibration fits (no_progress, losing_trade, preconditions) on v2.
2. [ ] **Friendly fire (아군 오사) measurement — branch `feat/friendly-fire-kpi`, interrupted
   (WIP commit; usage limit).** Measurement-only, so it may merge on passing tests before v2.
   Status:
   * KPIs written (friendly hits from the pooled battle log, lane intrusion) — report-only;
   * 84-episode batch done (Peaceful) — to analyse;
   * **lane drill** (ally on the shooter→target line, assault rifle): 0 hits at 1–6 cells from
     the shooter, a few per 60 shots at 7–11 cells. Consistent with the wiki's ~5-cell safe radius
     around the shooter. The drill's last row hit a shot-count bug (negative shots) — fix;
   * **next: near-target drill** — ally 1–4 cells from the TARGET (beside, behind, adjacent / in
     melee). Hypothesis: missed shots land around the target, so that is the danger zone, which
     fits the user's observation (short-range shooters advancing next to raiders);
   * friendly-fire chance is not a difficulty factor (same at every difficulty — checked in the
     game's difficulty XML); absolute rates still measured at Strive to Survive.

## Roadmap (chosen: long-term quality)

1. Baseline: v1 done (Peaceful, exploration data) → **v2 on Strive to Survive** (Now 1).
2. Friendly fire: measure (Now 2) → zone map as a perception layer → shared positioning rules.
3. Holdout: 2nd squad composition + 2nd arena (e.g. arena_fort) to fit squad/terrain-based
   preconditions (ranged_squad, defensible_terrain, room_to_spread) — before the router.
4. Enemy-AI hypothesis traces + start ENEMY_AI.md (LOS-break relocation, directional cover, fire
   avoidance, berserk vs cover, melee lock details, raiders out of our range).
5. Per-enemy threat profile (chronic / acute).
6. Rule-based router v1 (input structure METT-T) → regret on fresh instances.
7. Lances (asset layer). 8. Flush manoeuvres (if 4 confirms). Later: BaseGen arenas, bait,
   psycasts, mech bosses, LLM router.

Alongside: push only decision-relevant cells to n = 10–20.

## Open items by layer

### Evaluation / harness
- [ ] Gate power at n = 10: a regression confined to one cell is caught only when large (+1
      colonist/battle in a median-noise cell: ~18%). For a change aimed at one theme, run 20 per
      cell on both sides (baseline top-up on the tagged code), or add a per-theme pooled level.
- [ ] losing_trade misses defeats by pawns *downed* (not dead): consider a downed-weighted
      variant (report-only, fit on trade_curve + downed counts — needs downed in the curve).
- [ ] Manhunter animals on Strive: an animal hit by a stray shot turns manhunter 4× as often as
      on Peaceful, and predators hunt humanlikes (GAME_FACTS §6c). A loaded theme map had 0 wild
      animals (`list_wildlife`); check whether any wander in during episodes. If manhunters show
      up in baseline-v2, extend the invalid-episode guard to them or clear wildlife at start.

### Micro
- [ ] Micro drills beyond frags: fire step-out drill (molotov carriers), re-entry under Auto
      attack (amove walking a released pawn back into a live zone).
- [ ] Mech boss telegraphed attacks (Diabolus/War queen/Apocriton charge-ups): measure warmup via
      debug Spawn Pawn and add them to the hazard catalog + reflex layer. Deferred: low payoff
      for now compared to grenades, mortars and doomsday-class rockets.

### Tactical
- [ ] Friendly fire (아군 오사) — model after measuring (Now 2). User observation: the biggest
      friendly-fire damage comes from short-range shooters (shotguns, SMGs) advancing; melee has
      to close in, short-range shooters have far more freedom of position.
      1. KPIs + batch + drills: see Now 2.
      2. Model (shared by all doctrines — positioning by weapon range):
         - short-range roles: wings of the concave, choke-exit ambush from cover beside the exit,
           backline peel, flanking along side lanes; wait for the enemy to come into range instead
           of walking out to it — and (if the near-target drill confirms) stay out of the area
           around the targets our long guns shoot at;
         - fire deconfliction: a long gun whose target has an ally near it (beyond the shooter's
           ~5-cell safe radius) retargets or checks fire briefly;
         - shooting into melee: weigh friendly-fire risk vs leaving a melee-locking enemy alone;
         - danger close: no splash (incendiary launcher, grenades) near our own pawns.
      3. Zone map as a shared PERCEPTION layer (answers queries, decides nothing): enemy zones
         (exposure, throw/rocket reach — reuse legacy threatmap components), hazard zones (resting
         frags, fire — moved out of micro so it's shared), own-fire danger zones (around our
         shooters' targets, beyond each shooter's safe radius; targets from "Fire at" orders, job
         "attacking X", or the last log entry). Each layer/doctrine weighs the answers (turtle:
         slot viscosity high, own-fire zones hard). Lessons from threatmap v3: map ≠ policy,
         change one layer at a time, finish pressure belongs to tactics.
      4. Formation hypothesis (intuition, to test): short-range on the wings (horns of the
         concave, short angled lanes, point-blank on raiders entering the pocket), long-range
         centre-back (straight lanes, max standoff). Exception: raids that don't come in
         (snipers) — short-range held in reserve behind the centre, sent to a wing when raiders
         enter. Test: short-wings / long-wings / current; metrics friendly hits, own-fire zone
         time, trade ratio; split by approaching vs non-approaching themes.
- [ ] Positioning vs throwers (`--option vs_throwers=...`, recorded in rows): test on grenadier
      themes with the doctrine fixed and micro pinned.
- [ ] Fire control from military doctrine (see GLOSSARY "Military doctrine"):
      1. Trigger line + weapons hold for turtle: hold fire (drafted "Fire at will" off) until raiders
         cross a line inside the choke/engagement area, then everyone opens up at once (first volley at
         full engagement surface). KPI: share of first-volley shooters, enemies inside the kill zone at
         trigger time.
      2. Sectors of fire: assign each shooter in the concave its own arc/target set (no gaps, no
         overkill). KPI: distinct targets per step, overkill shots.
      3. Bounding overwatch for `close`: advance in two elements, one moving while the other covers.
         KPI: share of advance steps with an overwatch element in position, losses while advancing.
- [ ] close's enemy_outranges is inverted for the current close: revisit after bounding
      overwatch (fire control item 3). Docstring note only for now.
- [ ] Melee lock (adjacency blocks ranged attacks — both sides). Verify first in traces (roadmap 4,
      ENEMY_AI.md): exact adjacency (diagonals?), weapon exceptions, friendly fire when shooting into
      a melee, mechs. Then model it (roadmap 5):
      * melee-lock threat is per target and valued by what it disables, not by the attacker's damage:
        time-to-reach x DPS of the shooter it would melee-lock. A manhunter guinea pig reaching our carry
        (minigun / sniper / lance user) erases the carry's whole DPS.
      * kill order: any body heading for a carry (animal, small mech, unarmed raider) jumps the queue;
        peel = block every body that heads for the carry; carry stays behind the frontline and its
        approach lanes count as threat on the zone map (melee-lock risk); our shooters adjacent to an enemy
        have ranged fire value 0.
      * offense: our cheap bodies (animals, weak melee) melee-lock enemy carries (snipers, miniguns, rocket
        carriers) — extends the "animals as meat shields" cheese item to "animals as melee lockers".
      * scenario theme: swarms of cheap melee lockers (manhunter packs, insects) vs shooting doctrines.
      * KPIs (verbose names): melee_locked_time_share for our shooters / our carries, and
        enemy_melee_locked_time_share for enemy shooters. Avoid the word "pin" (too open to interpretation).
- [ ] Per-enemy threat profile (roadmap 5), two kinds (user's play intuition):
      chronic/blunt = sustained DPS x time-to-kill (armor, HP, cover, our fire reaching it) —
      e.g. armored minigunner suppressing from cover; acute/sharp = burst lethality x imminence
      (time to contact = distance / speed incl. go-juice; melee DPS, AP) — e.g. go-juiced hussar
      with a monosword. Read gear/armor/hediffs/skills once per raider (get_pawn tabs, info cards).
      Uses: kill order by DPS/TTK (acute overrides); zone map fields (chronic DPS-weighted field,
      acute time-to-contact field along the approach); viscosity applies to chronic only, acute
      bypasses it; router feature (chronic-heavy vs acute-heavy raid). After the zone map, before
      lances (they need this for targeting).
- [ ] Cover-amplified chronic threat -> "flush" manoeuvres: when an enemy's cover makes it a
      high-chronic/high-TTK target, don't trade fire head-on; make it leave cover instead.
      Hypotheses about the vanilla AI to verify with traces first: (a) breaking LOS/range makes
      raiders relocate (cross open ground -> pre-aimed shooters fire); (b) cover is directional,
      so flanking negates it; (c) raiders avoid burning cells / trees burn (area denial);
      (d) berserk (lance) ignores cover. KPIs: enemy share of time in cover, enemy time in open
      under our fire.
- [ ] Lure / bait role (retrievable, not sacrificial) — after the zone map.
      Role inside a doctrine, not a separate doctrine. Pick a tough/fast pawn (armor, shield
      belt, low-value skills); show it at the edge of enemy range, then retreat through the kill
      zone (generalises kite v3's "chased shooter runs through the squad"). On the zone map,
      everyone else avoids high threat; only the bait may enter, up to a cap. Abort on low HP /
      being surrounded; rescue immediately if downed. KPIs: bait survival, damage/grenades drawn,
      share of raiders pulled into the kill zone, kidnappings. First test: turtle + bait on
      pirate_sniper / pirate_mixed (turtle 0/5 there). Risk: a downed bait can be kidnapped and
      the raid leaves "satisfied" (graded defeat) — revisit whether "lost one, saved the rest"
      should really be a defeat.

### Strategic
- [ ] Router input structure = METT-T (Enemy: composition + threat profile; Terrain: arena/fort/OAKOC;
      Troops: our squad composition; Time: prep time before contact; Mission). Roadmap 6.
- [ ] ENEMY_AI.md: knowledge base of built-in enemy behaviour with evidence (raid flee vs
      "satisfied" messages, kidnapping, mechs never walk off, aiming not observable, frag fuse
      ~90 ticks, ...). Feed it to the router (and an LLM router as context). Hypothesis to add:
      what raiders do when our pawns are out of their range (hold? advance? wait for targets?).

### Asset layer ("cheese")
- [ ] An asset-use layer next to doctrine (maneuver); the router also picks assets.
      Priority (user's play experience):
      1. Lances (psychic insanity/berserk lance, shock lance) — tactical-weapon class, on par with
         triple rocket / doomsday: hand them to squad members via debug, use through
         do_thing_action/map_target; first tests on the themes we lose (pirate_sniper, pirate_mixed).
      2. Furniture/chair killbox and trap-maze arena (build with god mode); smoke.
      3. Others: shield belts, animals as meat shields, door dancing.
      4. Psycasts (berserk pulse, skip, wallraise, smokepop, stun) — last.

## Done

- 2026-10-03 — **Rewrite phase 1:** `rca/` foundation (game layer, one terrain module, harness,
  tracker, results, report), micro layer with only the verified reflexes + frag drill, amove.
- 2026-10-03 — **Scoring:** LER (point-weighted loss-exchange ratio) is the primary development
  metric; colonist value is a parameter (default 1 colonist = 4 enemies by points); colonist losses
  + grade shown separately; every results file rescored (EVAL_SPEC §6, results/rescored/). Legacy
  rows are count-based (no per-raider kinds); new rows are point-weighted.
- 2026-10-03 — **Rewrite phase 2** (onto `rca.tactical.Doctrine`): doctrine v4, turtle v8 (planner
  v4 + hold v4 rules), spread v5, kite v5, close v3; specs in the module docstrings; smoke results
  in LESSONS §2 ("Phase-2 smoke"); rescue in bed-free arenas: Carry to a safe cell, never a
  disabled option (bug 5); wounded stay drafted (bug 6); XML weapon ranges (bug 3); battle-log fire
  share (bug 9); phases + commit/reset criteria per doctrine; "win condition unattainable" signal;
  planned game restart every 100 episodes (`--restart-every`).
- 2026-10-03 — **Stalemate clarification requirements:** progress-rate KPI + longest no-progress
  stretch (EVAL_SPEC §8); `no_progress` after 3000 *contested* ticks (rule 2, EVAL_SPEC §2) or a
  runtime precondition break; preconditions as data + `rca/tactical/preconditions.check`;
  `vs_throwers` option selectable (testing still open, see Tactical).
- 2026-10-03 — **Pre-baseline cleanup** (LESSONS §2 / §4): rescue / wounded pull-back as options;
  mech fire share re-checked (0.59–0.73 enemy side); planned restart and crash relaunch ran once
  each; turtle's "No order matched 'Go here'" (undrafted after going down) fixed by re-drafting.
- 2026-10-04 — **Project out of the scratch workspace:** ~/code/rimworld-combat-agent, git, gzipped
  .rws saves + restore script, .gitignore (personal saves), noreply commit email, public GitHub repo
  (ZZaphodd/rimworld-combat-agent), 0BSD license.
- 2026-10-04 — **baseline-v1** (Peaceful; now exploration data): 6 doctrines × 7 themes × 10 +
  casualty options; doctrine v5 = rescue off by default (on 1.43 vs off 1.20 lost/battle);
  4 planned restarts after 100 real loads each; results/baseline/README.md.
- 2026-10-04 — **Calibration on baseline-v1** (results/baseline/calibration.md): no_progress
  keeps 3000; casualty options decided (rescue off, pull-back no effect).
- 2026-10-04 — **feat/signals-preconditions** (merged after an A/A gate PASS): `losing_trade`
  signal (≥ 2 pawns gone and running LER < 1.0; report-only; 85% bad among fires, 56% of bad
  caught); turtle defensible_terrain → soft; spread `enemy_splash_heavy` ≥ 0.45; `tools/gate.py`
  (rule in WORKFLOW, unit-tested, `--simulate`); commit hash in every result row.
