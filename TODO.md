# TODO

## Roadmap (chosen: long-term quality)
1. LER scoring switch + rescore all results (no new runs).
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
- [ ] Scoring: make LER (point-weighted loss-exchange ratio) the primary development metric;
      colonist value as an explicit parameter (default 1 colonist = 4 enemies by points); show
      colonist losses + outcome grade separately. Rescore existing rows (raw metrics are stored).
      Reason: the current 1:9 weight filters out high-variance, high-payoff tactics (local minimum).
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
      judge non-inferiority vs the tagged baseline), commit hash in every result row.
