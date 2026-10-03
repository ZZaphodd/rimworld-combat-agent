# TODO

## Roadmap (chosen: long-term quality)
0. **Rewrite, phase 1 — done (2026-10-03):** `rca/` foundation (game layer, one terrain module,
   harness, tracker, results, report), micro layer with only the verified reflexes + frag drill,
   amove. **Phase 2 — done (2026-10-03):** doctrine v4, turtle v8, spread v5, kite v5, close v3 on
   the doctrine interface with preconditions, phases, the "win condition unattainable" signal and
   the `vs_throwers` option; progress-rate and battle-log KPIs; bugs 3/5/6/9 fixed; planned game
   restarts (see "Phase 2" below). Next: roadmap 2.
1. ~~LER scoring switch + rescore all results (no new runs).~~ Done: EVAL_SPEC §6,
   results/rescored/, DATA.md §7.
2. Baseline checkpoint: full 210-run matrix at current versions + adaptive cycle (+ heatmap if it
   helped), overnight, with auto game restart every ~100 episodes.
3. Enemy-AI hypothesis traces + start ENEMY_AI.md (LOS-break relocation, directional cover,
   fire avoidance, berserk vs cover).
4. Per-enemy threat profile (chronic / acute).
5. Rule-based router v1 -> regret on fresh instances.
6. Lances (asset layer). 7. Flush manoeuvres (if 3 confirms). Later: BaseGen arenas, bait, psycasts,
   mech bosses, LLM router.
Alongside: holdout check on a 2nd squad composition + 2nd arena before trusting any router/doctrine
claim; push only decision-relevant cells to n=10-20.

Scope principle: RimWorld is not PvP. We overfit to the game's built-in enemy AI on purpose —
its rules (targeting, cover seeking, flee/"satisfied" triggers, kidnapping, pathing) are things
to learn, document (ENEMY_AI.md, with evidence) and exploit.


- [ ] Mech boss telegraphed attacks (Diabolus/War queen/Apocriton charge-ups): measure warmup via
      debug Spawn Pawn and add them to the hazard catalog + reflex layer. Deferred: low payoff
      for now compared to grenades, mortars and doomsday-class rockets.
- [ ] Lure / bait role (retrievable, not sacrificial) — after the threat heatmap lands.
      Role inside a doctrine, not a separate doctrine. Pick a tough/fast pawn (armor, shield
      belt, low-value skills); show it at the edge of enemy range, then retreat through the kill
      zone (generalises kite v3's "chased shooter runs through the squad"). On the heatmap,
      everyone else avoids high threat; only the bait may enter, up to a cap. Abort on low HP /
      being surrounded; rescue immediately if downed. KPIs: bait survival, damage/grenades drawn,
      share of raiders pulled into the kill zone, kidnappings. First test: turtle + bait on
      pirate_sniper / pirate_mixed (turtle 0/5 there). Risk: a downed bait can be kidnapped and
      the raid leaves "satisfied" (graded defeat) — revisit whether "lost one, saved the rest"
      should really be a defeat.
- [x] Scoring: LER (point-weighted loss-exchange ratio) is the primary development metric;
      colonist value is a parameter (default 1 colonist = 4 enemies by points); colonist losses +
      grade shown separately; every results file rescored (EVAL_SPEC §6, results/rescored/).
      Legacy rows are count-based (no per-raider kinds); new rows are point-weighted.
- [x] Phase 2 of the rewrite (onto `rca.tactical.Doctrine`), done 2026-10-03:
      * doctrine v4, turtle v8 (planner v4 + hold v4 rules), spread v5, kite v5, close v3;
        specs in the module docstrings; smoke results in LESSONS §2 ("Phase-2 smoke");
      * rescue in beds-free arenas: Carry to a safe cell, never a disabled option (bug 5); wounded
        stay drafted (bug 6); XML weapon ranges (bug 3); battle-log fire share (bug 9);
      * phases + commit/reset criteria per doctrine; "win condition unattainable" signal;
      * planned game restart every 100 episodes (`--restart-every`).
- [x] Pre-baseline cleanup (2026-10-03, LESSONS §2 / §4):
      * no_progress rule 2: only contested time (cost or threat) counts (EVAL_SPEC §2);
      * rescue / wounded pull-back are options (`rescue=on|off`, `wounded_pullback=on|off`,
        natural on), in rows, resume key and report labels;
      * mech fire share re-checked (0.59–0.73 enemy side);
      * planned restart and crash relaunch ran once each in rca;
      * turtle's "No order matched 'Go here'": undrafted after going down; re-draft fix.
- [ ] Open before / with the baseline matrix (roadmap 2):
      * calibrate the precondition thresholds against outcomes (values are in every row;
        UNVERIFIED, `defensible_terrain` failed on every theme while turtle won on melee);
      * fit T for no_progress rule 2 (3000 contested ticks, UNVERIFIED) and check that it fires
        on a real stalemate (e.g. turtle vs pirate_sniper), not only that it stays quiet in wins;
      * put the casualty options in the matrix (doctrine × rescue on/off × pull-back on/off on the
        themes where pawns go down; turtle × pull-back on/off) — decide the natural value after;
      * a planned restart after 100 real loads (the default) has not happened yet.
- [ ] Micro drills beyond frags: fire step-out drill (molotov carriers), re-entry under Auto
      attack (amove walking a released pawn back into a live zone).
- [ ] "Cheese" track = an asset-use layer next to doctrine (maneuver); the router also picks assets.
      Priority (user's play experience):
      1. Lances (psychic insanity/berserk lance, shock lance) — tactical-weapon class, on par with
         triple rocket / doomsday: hand them to squad members via debug, use through
         do_thing_action/map_target; first tests on the themes we lose (pirate_sniper, pirate_mixed).
      2. Furniture/chair killbox and trap-maze arena (build with god mode); smoke.
      3. Others: shield belts, animals as meat shields, door dancing.
      4. Psycasts (berserk pulse, skip, wallraise, smokepop, stun) — last.
- [ ] NEXT after the heatmap: per-enemy threat profile, two kinds (user's play intuition):
      chronic/blunt = sustained DPS x time-to-kill (armor, HP, cover, our fire reaching it) —
      e.g. armored minigunner suppressing from cover; acute/sharp = burst lethality x imminence
      (time to contact = distance / speed incl. go-juice; melee DPS, AP) — e.g. go-juiced hussar
      with a monosword. Read gear/armor/hediffs/skills once per raider (get_pawn tabs, info cards).
      Uses: kill order by DPS/TTK (acute overrides); heatmap fields (chronic DPS-weighted field,
      acute time-to-contact field along the approach); viscosity applies to chronic only, acute
      bypasses it; router feature (chronic-heavy vs acute-heavy raid). Before lances (they need
      this for targeting).
- [ ] Cover-amplified chronic threat -> "flush" manoeuvres: when an enemy's cover makes it a
      high-chronic/high-TTK target, don't trade fire head-on; make it leave cover instead.
      Hypotheses about the vanilla AI to verify with traces first: (a) breaking LOS/range makes
      raiders relocate (cross open ground -> pre-aimed shooters fire); (b) cover is directional,
      so flanking negates it; (c) raiders avoid burning cells / trees burn (area denial);
      (d) berserk (lance) ignores cover. KPIs: enemy share of time in cover, enemy time in open
      under our fire.
- [ ] ENEMY_AI.md: knowledge base of built-in enemy behaviour with evidence (raid flee vs
      "satisfied" messages, kidnapping, mechs never walk off, aiming not observable, frag fuse
      ~90 ticks, ...). Feed it to the router (and an LLM router as context).
- [ ] Melee lock (adjacency blocks ranged attacks — both sides). Verify first in traces (roadmap 3,
      ENEMY_AI.md): exact adjacency (diagonals?), weapon exceptions, friendly fire when shooting into
      a melee, mechs. Then model it (roadmap 4):
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
- [ ] Fire control from military doctrine (see GLOSSARY "Military doctrine"):
      1. Trigger line + weapons hold for turtle: hold fire (drafted "Fire at will" off) until raiders
         cross a line inside the choke/engagement area, then everyone opens up at once (first volley at
         full engagement surface). KPI: share of first-volley shooters, enemies inside the kill zone at
         trigger time.
      2. Sectors of fire: assign each shooter in the concave its own arc/target set (no gaps, no
         overkill). KPI: distinct targets per step, overkill shots.
      3. Bounding overwatch for `close`: advance in two elements, one moving while the other covers.
         KPI: share of advance steps with an overwatch element in position, losses while advancing.
- [ ] Router input structure = METT-T (Enemy: composition + threat profile; Terrain: arena/fort/OAKOC;
      Troops: our squad composition; Time: prep time before contact; Mission). Goes into roadmap 5.
- [ ] Before the baseline checkpoint: move the project out of the session scratch workspace into a
      permanent folder (scratch is deleted with the session), git init, gzipped .rws saves + restore
      script, relative paths in scripts/logs, .gitignore (personal saves), noreply commit email,
      public GitHub repo (read-only for others), optional license.
- [ ] After the baseline is frozen (WORKFLOW.md): gate.py (re-run the baseline suite on a branch and
      judge non-inferiority vs the tagged baseline). Commit hash in every result row: done (rca
      rows carry `commit`).
- [ ] Phase 2 requirements from the stalemate clarification (WORKFLOW layer contracts):
      1. [x] Progress-rate KPI + longest no-progress stretch (EVAL_SPEC §8); every doctrine raises
         "win condition unattainable" (`signals`) after 3000 *contested* ticks without progress
         (rule 2, EVAL_SPEC §2) or on a runtime precondition break.
      2. [x] Preconditions as data on each doctrine + `rca/tactical/preconditions.check` (EVAL_SPEC
         §2); the router (roadmap 5) will call it. Thresholds UNVERIFIED.
      3. [~] Positioning vs throwers is selectable (`--option vs_throwers=...`, recorded in rows);
         still to test on grenadier themes with the doctrine fixed and micro pinned.
      4. [ ] ENEMY_AI hypothesis (roadmap 3): what raiders do when our pawns are out of their range
         (hold? advance? wait for targets?).
