# Game-layer needs from direct play (2026-10-07)

For the game-layer session (branch feat/game-layer), from the experiment session: needs that Claude's
direct base plays turned up, checked against GAME_LAYER_REQUIREMENTS.md (feat/game-layer 28cc04a).
Only partly covered or missing items. The layer session was not reachable when this was written.

Latest play since the check: base2_ith_pirate_4x (repelled 1.5): a room behind a closed door, focus
fire on the toxbomb, Doomsday and incendiary holders at the doorway; one incendiary lit our cells and
was put out by float menu ("Prioritize extinguishing"); burning drafted pawns showed "wandering.".

Sources: the journals for base2_mon_pirate 3x/4x/6x, base2_ith_tribe_3x and base_ith 2x. Below are only the needs that are partly covered or missing.

1. Fire as an event with its cause: fire_started cells, a cause (verb, ability, projectile or explosion def) and the instigator; onFire per pawn. [extends R-EVT-8; ties to R-EVT-6, R-EVT-7]
   Evidence: in mon_pirate_3x at t9545, fires started on (146-148, 79-83) all at once while boss Griffith (Hellcat) stood in the doorway. In 6x at t11088 the same happened with Codex in the
   inner door (145, 86), and Egan had burns by t11148. Both times the cause (the Hellcat mini-burner) was guessed from who stood at the door.
   Gap: fire_started has no cause field, and the instigator appears only in the molotov Accept. A fire started by an ability has to be joined by hand from ability_cast + explosion + fire_started (all P1), and no Accept covers it.

2. Burning pawns: onFire / fleeingFire state, the reason an order is refused, and extinguish by pawn or cell. [extends R-OBS-5, R-ORD-16; an extinguish order for the agent role is new]
   Evidence: in mon_pirate_3x, Pete and Wanda caught fire while drafted and ran off with the job "wandering" (to R1 and R3). The only way to put them out was the float menu "Prioritize
   extinguishing" (Maverick on Wanda, John on Pete, Shar on cells (148, 79-80)). In rand_015/115, "extinguishing fire on ..." looked like wandering. In rand_039, a drafted pawn that was set on fire became undrafted.
   Gap: there is no fleeingFire state and no on_fire refusal code. The only typed extinguish is the admin-only R-ADM-14. Menu passthrough (R-ORD-10) refuses undrafted pawns, and R-ORD-16 prioritize is written for uninstalling.

3. Carry and rescue that work: one carry_to(carrier, downed, cell) that does pickup + walk + drop, with a reply per step and a path that avoids fire and heat. [extends R-ORD-11]
   Evidence: in mon_pirate_6x, a Go here given before pickup cancelled a carry. Rescue (to a bed) sent the carriers back through burning R2. A carry stalled until the carrier
   stood on an orthogonal cell. Willow and Merlicek went down in R2's heat while carrying. In base_ith_pirate_2x, Park stood diagonal to Leslie for 90-135 ticks on "carrying Leslie" and never picked her up.
   Gap: there is no compound carry_to with per-step replies, so the client still chains carry, a wait for pawn_picked_up, move and drop. The diagonal stall is only diagnosed (R-ORD-19), and carry and rescue paths do not avoid fire or heat.

4. Downed crawling (1.6): the crawl target in the snapshot and a way to stop or redirect it. [extends R-OBS-5 crawling; the order part is new]
   Evidence: in mon_pirate_6x, Egan and Kieri were carried to the back (149, 76-77) and then crawled off ("Crawling to bed"), which undid the carry. In ith_tribe_3x, Val crawled
   out into the corridor (133, 182) after the raid broke and bled out there (11 % at t15151).
   Gap: the crawl destination is not a named field (it may show up through job targetA or pather.destination; not checked). No order stops, holds or redirects a crawl, because draft and stop refuse downed pawns.

5. Who can tend and who can fight fire: per-work-type flags (Doctor, Firefighter) for each pawn in the snapshot, and a tend order that reports its result. [extends R-OBS-3/R-OBS-12, R-ORD-11]
   Evidence: in ith_tribe_3x, the tend order for Val never reached her (Pepper cannot doctor), which we only learned mid-fight. In mon_pirate_3x, Rivers turned out to be incapable of
   firefighting while extinguishers were being assigned. In base_ith_pirate_2x, Susumu could tend Leslie only through the float menu "Tend Leslie (without medicine)".
   Gap: only disabled work tags are given, not per-work-type flags. That misses work disabled by traits or genes and leaves the mapping to the client. The tend reply gives only the started job, with no result (hediffs tended, quality) other than the P1 job_ended event.

6. Line of sight and visibility on the server, using live door states; rooms. [extends R-MAP-8, R-MAP-2; the rooms section is new]
   Evidence: every base plan picks "cells that see the doorway but nothing in the corridor" from line of sight on the save map, computed offline (mon_pirate_3x/6x; ith_pirate_4x
   now keeps the door closed instead of held open). In 6x, Kieri went down on a cell visible from the passage. In rand_115, a raider could be seen from inside only through an open door.
   Gap: los(a, b) exists, but there is no visibleFrom(cell, radius) area query and no Accept with held-open vs closed doors. There are no rooms (room id, door cells, enclosed) because get_room/room_graph are not ported.

7. Traps: armed/sprung state, trap cells, a typed spring event and kill attribution. [extends R-MAP-9, R-EVT-4; trap_sprung is new]
   Evidence: in mon_pirate_4x at t6849-7071, Xiatian, Billy and Webb walked down the trap lane (spike traps on x 100) and dropped out of the list without our seeing how.
   In base_ith_pirate_2x, 7 of the 20 dead died on spike traps and the cause is not in the trace. In base_ith_tribe_2x, Scorpion died beside a sprung trap frame.
   Gap: there are no trap fields (armed/rearm, auto-rebuild, which factions know of it) and no trap_sprung {trap id/def/cell, victim, outcome}. A spring that downs nobody can only be pieced together from building_destroyed + damage.

8. Mental break risk: mood, break thresholds and the current mental state for each pawn. [extends R-OBS-12, R-OBS-3]
   Evidence: in base_ith_pirate_2x, raiders John and Evgeny were "panic fleeing" inside the room while John kept hitting us, and we could read this only as text. Base fights now last
   10-20k ticks with deaths, burns and heatstroke in the room (mon_pirate_6x), and nothing shows our own pawns' break risk.
   Gap: there are no minor/major/extreme thresholds (MentalBreaker) and no break-risk level. Active alerts such as "Major break risk" have no load-scoped replacement (get_alerts maps only to R-EVT-2). R-OBS-12 does not say whether mood means the current level or the breakdown of thoughts.

Already covered: R-OBS-13 (abilities/charges), R-OBS-5 (health detail), R-MAP-4 (door holdOpen), R-EVT-2 (stale messages after load), R-OBS-1/R-OBS-7/R-OBS-10 (raider weapon + targeting), R-OBS-6 (fireAtWill), R-ORD-7 (melee by id).
