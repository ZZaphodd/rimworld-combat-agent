# TODO

Scope principle: RimWorld is not PvP. We overfit to the game's built-in enemy AI on purpose —
its rules (targeting, cover seeking, flee/"satisfied" triggers, kidnapping, pathing) are things
to learn, document (ENEMY_AI.md, with evidence) and exploit.

Sections: **Now** (blocking, in order) · **Roadmap** · **Open items by layer** · **Done** (log).

## Now

1. [ ] **Switch the evaluation standard to Strive to Survive and build baseline-v2** (WORKFLOW
   "Evaluation standard"). baseline-v1 and the first gate ran on Peaceful → exploration data.
   * **rebuild instead of converting** (2026-10-04): old saves archived (repo copies at tag
     baseline-v1); threat size **500 pt** chosen from the montage; new arena_forest (250×250,
     Strive) done; scenario set t500 done (squad of 9, 6 themes + frag_check; no sniper theme
     at 500 pt — back with the 1500 set);
   * doctrine parameters were tuned on a squad of 14 (formation widths, kite fan-out, turtle
     cluster radius, max guns per target): check them on the squad of 9 before baseline-v2;
   * [x] harness guard: a hostile not on the map at the start → outcome `invalid`, re-run
     (EVAL_SPEC §3); difficulty checked at every start and stored in every row;
   * [x] Anomaly contamination (2026-10-04): an "ancient danger" ruin (6 cryptosleep caskets,
     4 fleshbeast guards) and the Void Monolith were in every t500 save; stripped from all 10
     (`arena.strip_anomaly`, also part of arena prep now). Anomaly playstyle stays "standard":
     a later Anomaly event would end an episode as invalid;
   * baseline-v2: 6 doctrines × 6 t500 themes × 10 (`--scenarios tier:t500`); tag `baseline-v2`;
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
3. **Failure mining + human demonstrations** (user, 2026-10-04; absorbs the holdout). The
   loop: generate many problems → agents solve them → the user plays only the ones they fail →
   distil what worked into rules → the gate checks they generalise.
   1. Scenario generator: random raids around 500 pt on varied squads and arenas (new saves
      on demand, not 7 frozen ones); doubles as the holdout (2nd squad composition, 2nd arena)
      for the squad/terrain preconditions (ranged_squad, defensible_terrain, room_to_spread).
   2. Failure miner: every agent once per problem; rank by loss, HP lost, permanent injuries
      and downed; group by cause (fire, melee rush, out-ranged, flank) — spend human time only
      where all agents fail and the cause is unclear (a human battle costs ~8 min).
   3. Human demonstrations in observe-only mode (`tools/run_human.py`, branch
      feat/human-observe; merge after baseline-v2), plus a trace (every pawn's position, job
      and target each second) so "what the human did differently" can be measured: distance
      to the enemy, cover use, group spacing, when to pull back, who stands where (roster).
   4. Distil into rules the agents can observe (not the human's pausing or whole-screen view),
      as a doctrine change or tactical option on a branch; the gate (branch vs baseline-v2)
      decides. One demonstration is a hypothesis: human rounds 1 and 2 differed completely.
   First demonstrations (t500_pirate_grenadier, results/human/play.jsonl on the branch):
   round 1 pyrrhic (6 killed, 1 lost, 4 downed, 313% HP, 7 permanent injuries); round 2
   repelled with 0 lost, 0 downed, 48% HP (agents 164–239%): hold behind rock lines, keep the
   throwers at 13–37 cells, two groups 11 apart, weakest shooter in reserve, the molotov fire
   between the sides as a wall → test `vs_throwers=stand_off` + cover first.
4. Enemy-AI hypothesis traces + start ENEMY_AI.md (LOS-break relocation, directional cover, fire
   avoidance, berserk vs cover, melee lock details, raiders out of our range).
5. Per-enemy threat profile (chronic / acute).
6. Rule-based router v1 (input structure METT-T) → regret on fresh instances.
7. Lances (asset layer). 8. Flush manoeuvres (if 4 confirms). Later: BaseGen arenas, bait,
   psycasts, mech bosses, LLM router, and the 1500-pt scenario set on Strive (squad of ~14:
   the scale of baseline-v1) once the doctrines are mature at 500.

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
      animals (`list_wildlife`), but a wild **cougar wandered in during a baseline-v2 episode**
      (t500_mechs, 2026-10-04): animals do enter battles. A manhunter is a new hostile, so the
      invalid guard already ends such an episode; a predator hunting a pawn is not (not hostile
      by faction) — count wild-animal entries per episode and look at baseline-v2's invalid rows.

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
- [ ] **Minimum-range pocket ("hug")** (user, watching baseline-v2 on t500_mechs, 2026-10-04:
      melee-locking the Tesseron looked worth it even for shooters). A hard rule, not AI
      behaviour: a weapon cannot fire inside its XML `min_range` (`data/weapon_ranges.json`):
      beam graser (Tesseron) 3.9, incinerator and hellsphere cannon (Diabolus) 5.9. Our guns have
      none, so a short-range shooter inside the pocket keeps firing point blank while the enemy's
      gun is silent — no melee pawn needed (the t500 squad has none: 3 revolvers + a machine
      pistol are the natural huggers; revolver 25.9 ≈ beam graser 24.9, so only the approach is
      exposed).
      1. Drill first (friendly-fire drill harness): 1 Tesseron vs one pawn at 2, 3, 4, 5 cells —
         does it stop firing, step back to regain range, or switch to melee? Same for incinerator
         carriers. Facts → GAME_FACTS / ENEMY_AI.md.
      2. Perception: per-enemy threat profile (roadmap 5) gets min_range; the zone map's enemy
         zone becomes a ring (min_range, range) with a safe pocket inside (safe from that gun only:
         not from its melee, other enemies, or splash — the Pikeman's needle gun 44.9 has no pocket).
      3. Tactical primitive shared by all doctrines: who hugs (short range, HP/armour), when
         (value of the silenced gun — a 5-shot beam sweeping a clumped squad — vs exposure on the
         approach), and fire deconfliction: long guns pick other targets while our huggers stand
         next to the target (near-target friendly fire, Now 2). KPIs: pocket time per hugger,
         enemy shots silenced, friendly hits on huggers.
- [ ] Melee lock, behavioural kind (adjacency makes an enemy fight in melee instead of shooting —
      both sides; for weapons without a min_range: Pikeman, Lancer, humanlike raiders). UNVERIFIED.
      Verify first in traces (roadmap 4, ENEMY_AI.md): exact adjacency (diagonals?), weapon
      exceptions, friendly fire when shooting into a melee, mechs. Any of our pawns can melee (gun
      butt, fists): the lock matters, not the damage. Then model it (roadmap 5):
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
- 2026-10-04 — **Docs review** for the Strive to Survive standard (every doc; RIMMOLT_API checked
  against the live tool list) and **`tools/rm.py`**: compact game probe for hand checks (status
  ~120 bytes vs ~7 KB raw; `rca/probe.py`, tests/test_probe.py).
- 2026-10-04 — **Threat montage** (`montage_threats`, PROCEDURES §14): new Strive to Survive
  world (300×300), 4 raid types × 7 point levels (100–1500) in walled gold/silver pens, plus
  3 sample draws per cell (results/montage/legend.md). Old project saves archived.
