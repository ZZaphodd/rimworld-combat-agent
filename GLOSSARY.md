# Glossary

Shared vocabulary for code, reports and discussion. Borrowed from RTS (StarCraft) and MOBA
(League of Legends) where a term already bundles "situation + response"; RimWorld community
terms win when they exist (killbox, cheese, door dancing). Scope: we fight the built-in
RimWorld enemy AI, not other players (see TODO.md, scope principle).

## Architecture

| Term | Meaning here | Source |
|---|---|---|
| **micro** | Battle drills and reflexes: dodging a skillshot, stepping out of fire, not re-entering a fled cell. Judged per event, not per battle | RTS |
| **tactical** | Doctrine execution: positioning (concave, choke, standoff), fire control, focus, commit/reset timing. Judged per battle with the doctrine fixed | military |
| **strategic / decision** | Choosing doctrine and assets for this raid, terrain and squad, and when to transition (the router). Judged over a scenario distribution | RTS/military |
| **precondition** | What a doctrine needs to be able to win (turtle: defensible terrain — choke/concave — and an enemy that will come to it). Checked by the router before choosing | ours |
| **win condition unattainable** | The signal a doctrine raises (no progress for 3000 ticks, or a precondition broken at runtime); the strategic layer decides what to do with it | ours |
| **stalemate / progress rate** | Progress rate = enemy combat points lost per 1,000 ticks. A **pause** is any stretch with no progress; a **stalemate** is a stretch with no progress while we pay a cost (damage, downed, lost pawns) or are under threat (a raider in its weapon range of us): only that *contested* time raises "win condition unattainable" (EVAL_SPEC §2). Tactical KPI and the trigger for commit/reset | ours |
| **layer discipline** | Change and test one layer at a time with the others held fixed; a micro win must not be judged by tactical outcomes | ours |
| **doctrine** | A posture with a **win condition**, plus **commit** and **reset** criteria | ours + MOBA |
| **win condition** | How a doctrine wins, e.g. turtle: "they come through our choke" | MOBA |
| **commit / reset** | Fully engage / pull out, regroup and re-engage (doctrine transitions) | MOBA |
| **asset layer** | Item and ability use next to doctrine: lances, smoke, EMP, psycasts ("cheese") | ours |
| **viscosity** | A doctrine's threshold for leaving its position; applies to sustained threat, not burst | ours |

## Doctrines (code name → meaning)

| Name | Meaning | Previous name |
|---|---|---|
| **amove** | Baseline: draft everyone, Auto attack the nearest enemy, no control | b1, aggressive |
| **doctrine** | Rally, then focus fire by priority, avoiding **overkill**. Kept as the code name for now; in prose say "the `doctrine` agent" to keep it apart from doctrine the concept | — (briefly called focus in reports) |
| **turtle** | Pick the battleground, man a **concave** behind a **choke**, high viscosity | hold |
| **spread** | Keep spacing to mitigate **splash** (burst damage over a small area) | — |
| **kite** | Shoot while backing off from melee (stutter step) | — |
| **close** | Close the distance fast against **poke** (snipers, archers) | — |

Renames keep the old names as aliases so earlier result rows still read correctly.

## Threat

| Term | Meaning here | Source |
|---|---|---|
| **burst threat** | Acute: high lethality soon. time-to-contact × burst damage | RTS/MOBA |
| **sustained threat** | Chronic: sustained DPS × time-to-kill (armor, HP, cover) | RTS |
| **dive** | A burst threat closing in (go-juiced hussar with a monosword) | MOBA |
| **poke** | Sustained damage from range (snipers, suppressive fire) | MOBA |
| **stim** | Temporary buff (go-juice, yayo): raises burst threat | RTS |
| **splash** | Area damage: grenades, rockets, molotovs | RTS |
| **skillshot** | A telegraphed attack that can be dodged after it is seen (frag: ~90-tick fuse) | MOBA |
| **undodgeable** | Too fast once fired (rockets); counter only by prevention | ours |
| **telegraph** | The warning signal before an attack lands | RTS/MOBA |
| **zone / zoning** | Area denied by threat; our **zone map** is the threat heatmap | MOBA |
| **CC** | Crowd control: stun, EMP, smoke, berserk | MOBA |
| **clump / deathball** | Massed squad: strong against single-target, weak against splash | RTS |

## Positioning and engagement

| Term | Meaning here | Source |
|---|---|---|
| **concave** | Arc where all of our shooters can fire on the same front | RTS |
| **choke** | Narrow entry that limits how many enemies engage at once | RTS |
| **engagement surface** | How many units on each side can trade fire at the same time | RTS |
| **killbox** | Built choke + concave (RimWorld community term) | RimWorld |
| **frontline / backline** | Absorbing line vs damage-dealing line | MOBA |
| **carry** | Our key pawn to protect: best shooter, lance user, doctor | MOBA |
| **peel** | Intercepting a dive before it reaches the carry/backline | MOBA |
| **pull / bait / tank** | Lure enemies into the kill zone / absorb fire | RTS/MOBA |
| **flank** | Attack from an angle; RimWorld cover is directional, so it negates cover | RTS |
| **flush** | Make an enemy leave cover (break LOS, area denial, lance) | ours |
| **pick / catch** | Kill an isolated enemy first | MOBA |
| **snipe (priority)** | Remove key enemy units first (rocket carriers; kill order by DPS ÷ TTK) | RTS |
| **scout** | Read the raid early (composition, gear); router input | RTS |
| **dodge** | Step out of a skillshot's area (reflex layer) | RTS/MOBA |
| **vs throwers: accept-and-dodge / stand off / close in** | The tactical option `vs_throwers` (doctrine, turtle, spread): stay put and let micro dodge frags / step back out of throw range (12.9) while staying in gun range / go kill the thrower. Positioning, so tactical, not micro | ours |
| **melee lock / melee-locked time** | An enemy (or ours) adjacent to a ranged pawn blocks its ranged attack; KPI name `melee_locked_time_share`. Value is set by what gets locked, not by the attacker (a manhunter guinea pig on our minigunner) | ours |
| **cooldown trading** | Engage when the enemy's key weapon has just fired | MOBA |

## Outcomes and metrics

| Term | Meaning here | Source |
|---|---|---|
| **trade / trade ratio** | Loss-exchange ratio (LER): enemy strength lost ÷ ours; >1 is a good trade | RTS |
| **snowball** | Early kills compounding (Lanchester square law) | MOBA |
| **overextend** | Pushing past support into an enemy concave (KPI candidate) | MOBA |
| **throw** | Losing a won fight by misplay, e.g. chasing a fleeing raid (KPI candidate) | MOBA |
| **face-check** | Walking into unseen fire unprepared (KPI candidate) | MOBA |
| **hard / soft counter** | Strong / mild doctrine–theme advantage (router table) | RTS/MOBA |
| **decisive / repelled / pyrrhic / defeat** | Outcome grades (game raid messages decide) | ours |

## Military doctrine

| Term | Meaning here | Source |
|---|---|---|
| **METT-T** | Decision inputs: Mission, Enemy (raid composition, threat profile), Terrain (arena/fort), Troops (our squad composition), Time (prep time before contact). The router's input structure | military |
| **OODA loop** | Observe-Orient-Decide-Act; the harness decision cycle (adaptive cycle = faster loop in contact) | military |
| **OAKOC** | Terrain analysis: Observation & fields of fire, Avenues of approach, Key terrain, Obstacles, Cover & concealment; the battleground planner's checklist | military |
| **engagement area / kill zone** | Planned area where the enemy is engaged (killbox, turtle's fire zone) | military |
| **trigger line** | Line the enemy must cross before we open fire, so the first volley lands at full engagement surface | military |
| **weapons hold / tight / free** | Fire-control states; drafted "Fire at will" toggle is the tool | military |
| **sectors of fire** | Each shooter's assigned arc: covers the concave without gaps or overkill | military |
| **mutual support / interlocking fields of fire** | Positions that cover each other; names turtle v1's failure (split squad beaten one half at a time) | military |
| **enfilade / defilade** | Fire along the long axis of an enemy line / a position out of enemy direct fire (a zone-map cell category) | military |
| **cover vs concealment** | Cover protects (walls, sandbags); concealment only hides (smoke lowers accuracy) | military |
| **dead space** | Area a position cannot cover with fire (planner blind spots) | military |
| **friendly fire (아군 오사) / fratricide** | Our own shot or splash hitting our own pawn (shooting into a melee, a short-range shooter inside a long gun's lane, our grenades/incendiary). Korean term kept on purpose: precise nuance, cheap as a single word | military/ours |
| **danger close** | Using splash near our own pawns | military |
| **battle drill** | Trained immediate response: the reflex layer ("react to contact", "break contact" = disengage) | military |
| **bounding overwatch / fire and maneuver** | One element moves while the other covers it; how `close` should advance | military |
| **overwatch** | A position waiting to fire on whatever appears (turtle's line, the bait's kill zone) | military |
| **phase line / fallback position** | Pre-agreed lines and fallback cells: concrete reset criteria | military |
| **culminating point** | Where an attack can no longer continue: the raid's flee threshold (theirs), commit/reset (ours) | military |
| **force ratio** | Combat-power ratio (threat points); router feature | military |
| **economy of force / mass** | Minimum force on secondary efforts, concentration on the main one (Lanchester); one bait pawn is economy of force | military |
| **CASEVAC / triage** | Casualty evacuation and treatment priority (rescue logic) | military |

## Avoid

| Term | Why | Use instead |
|---|---|---|
| **siege** | RimWorld has a raid strategy named Siege (mortars) | sustained threat, poke |
| **sustain** | In MOBA it means healing | sustained threat / sustained DPS |
| **harass** | In RTS it usually means economic raiding | poke |
| **macro, build order, timing attack** | No economy in scope | — |
| **high ground** | No elevation mechanics in RimWorld | — |
| **suppression** | Vanilla RimWorld has no suppression mechanic (Combat Extended does) | sustained threat, poke |
| **center of gravity** | Too abstract to operationalise | snipe priority |
| **split** | In MOBA it means splitting the team (side-lane push vs main teamfight); too strong a "divide in two" sense for small-area splash mitigation | spread |
| **pin** | Concise but open to interpretation (suppression? root? melee contact?) | melee lock |
| **친선 사격** | Reads as a 'friendly exchange of fire'; too open to interpretation | friendly fire (아군 오사) |
| **split push, vision/ward, last hit** | Lanes, minimap and economy are out of scope | — |
