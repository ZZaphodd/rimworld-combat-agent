# Game facts: RimWorld mechanics and measured constants

Vanilla RimWorld with Biotech, played through RimMolt (RIMMOLT_API.md). Each fact lists its
evidence. **UNVERIFIED** = assumed or guessed, never measured or checked against the XML.

Scope principle (TODO.md): RimWorld is not PvP. We overfit to the built-in enemy AI on purpose, and
its rules are things to learn and exploit. Section 8 collects them and is the seed of ENEMY_AI.md.

## 1. Factions

| FactionDef (debug menu suffix) | World-page label | Notes |
|---|---|---|
| `Pirate` | Pirate gang | |
| `OutlanderRough` | Rough outlander union | The theme squad is drawn from it |
| `TribeRough` | Fierce tribe | |
| `TribeSavage` | Savage tribe | |
| `Mechanoid` | Mechanoid hive | Must be reachable by "Execute raid with faction" (see §2) |
| `PirateYttakin` | (xenotype pirates, used in std_yttakin_groups_forest) | label UNVERIFIED |

- **Biotech default swap:** the planet page's default faction list replaces Pirate gang, Rough
  outlander union, Fierce tribe and Savage tribe with xenotype variants. They must be added back by
  hand before creating the world (make_arena.py docstring; observed).
- Debug raid menus list factions as `"<faction name> (<FactionDef>)"`.

## 2. Mech raid quirks

- **Faction route only.** "Execute raid with specifics" filters mechanoids out before their
  earliest raid day, so mechs come only through "Execute raid with faction...". That route lets
  the game choose strategy and arrival [code].
- **Generation failures:** 42 of 167 attempts (25%) at 6000 pt produced nothing (census_recollect.log).
  The theme build at 1500 pt failed 1 of 2 tries. TODO speaks of ~25–30%. Failures are silent (see
  RIMMOLT_API.md §3 rule 9).
- **Low points fail more.** The theme builder walks a ladder of 1500 → 2000 → 2500 → 3000 → 4000 pt.
  1500 pt worked on the 2nd try. The exact threshold is UNVERIFIED.
- **Late pods.** Mech drop pods can land long after the raid fires, and `Destroy non-colonists`
  does not touch pods still in flight. Settle up to 60×60 ticks and wait until no
  `DropPodIncoming` / `ActiveDropPod` remains [code].
- **Loitering.** Mech raids sometimes do not assault (game-chosen strategy), so every built
  scenario must pass the assault check (PROCEDURES.md) [code/obs].
- **Never walk off the map.** A mech that disappears was destroyed. The fate tracker relies on this
  (observed; ENEMY_AI.md candidate). Seen 2/5 times in theme_mechs: mechs parked 13–28 cells from a
  turtle line, out of sight and not attacking (execution_report §3).
- **Militor swarms:** 3 of 125 mech census raids at 6000 pt were 120–133 Militors only. A code
  comment blamed leaked pods, but they still appear after the fresh-arena fix, so they are probably
  a genuine composition (UNVERIFIED).

## 3. Labels, names and log phrasing

| What | Format | Evidence |
|---|---|---|
| Pawn label in `list_things` | `"<Short name>, <more>"` or `"<name> <...>"`; short name = text before the first `,` or `<` | [code] |
| Weapon label in `get_pawn` | `"<Weapon> (<quality> [hp%])"`, possibly prefixed `Biocoded `; mechs carry none (`weapon` empty) | [code] |
| Pawn kind | `list_things` verbose `kind` = PawnKindDef (e.g. `Mercenary_Gunner`, `Grenadier_Destructive`, `Mech_Scyther`); `def` is the race (`Human`, `Mech_Scyther`) | [obs 2026-10-03] |
| Death (battle log) | `"<Name> perished\|expired\|died\|was killed\|succumbed\|bled out ..."` at the start of an entry | [code] |
| Leaving / special jobs | job text starting with `kidnapping <name>.`, `fleeing`, `exiting`, `stealing`, `leaving` | [code]; full list UNVERIFIED |
| Raider targeting | `targeting` field: `"targeting colonist <name>"` (aiming) / `"attacking colonist <name>"` | [code] |
| Our jobs | `"attacking ..."`, `"melee attacking ..."`, `"moving."`; drafted fire-at-will shows `"watching for targets"` | [code, execution_report] |
| Raid broken | notification containing `" are fleeing"` (e.g. `Pirates from The Lance Leopards are fleeing.`) | grade_check.jsonl |
| Raid won | notification containing `"satisfied with the damage"` (`... are satisfied with the damage done and are leaving`) | grade_check.jsonl |
| Frag throw | `"X flung her frag grenade at Y"`; throw verbs `launched, flung, threw, tossed, lobbed, hurled` | hazards.md, [code] |
| Frag damage | `"X's frag grenade(s) <verb> Y's <parts>"` / `"The blast\|shockwave from X's frag grenade ..."` | hazards.md |
| Permanent injury | hediff `permanent=true`, or label contains `missing, cut off, shot off, torn off, bitten off, destroyed` | [code] |

## 4. Time and movement

| Constant | Value | Evidence |
|---|---|---|
| Ticks per second at 1x | 60 | game constant |
| In-game hour | 2500 ticks | eval CLI help |
| Smallest `wait_for_event` step | 15 ticks (quantised) | hazards.md |
| Humanlike raider speed | ~0.075–0.08 cells/tick (~4.6 c/s); covers ~9 cells per 120 ticks, ~2.4 per 30 ticks | execution_report, threatmap.py; some raiders are faster (UNVERIFIED which) |
| Walking colonist with trees around | 0.07 cells/tick | reflex constant (estimate) |
| Go here start-up delay | ~15 ticks before a fresh order moves the pawn | reflex constant (estimate, UNVERIFIED) |
| **Combat slowdown** | Vanilla forces 1x speed whenever combat starts, which made runs ~10x slower. Debug setting **"Never Force Normal Speed"** (settings tab) disables it; set it every episode | eval.py, [obs] |

## 5. Weapons

**Range table: UNVERIFIED.** These are guesses written into code, not read from the XML. Check
them against `Data/Core/Defs` before reuse. Keys are matched by substring of the weapon label, in
this order:

| Key | Range (cells) | Suspicion |
|---|---|---|
| sniper | 44 | |
| charge lance | 30 | |
| bolt | 30 | lower than generic "rifle" (35)? |
| assault | 31 | |
| charge rifle | 27 | |
| rifle | 35 | also catches every other "... rifle" |
| lmg | 26 | |
| minigun | 30 | |
| heavy smg / smg | 23 | |
| machine pistol | 19 | |
| chain shotgun | 15 | |
| shotgun | 16 | |
| autopistol / revolver / pistol | 26 | |
| bow | 25 | greatbow gets the same value |
| launcher | 23 | |
| (anything else, incl. all mech weapons) | 25 | pikeman needle gun, lancer charge blaster missing |

Measured or read from the XML (more reliable):

| Fact | Value | Evidence |
|---|---|---|
| Frag/molotov throw range | 12.9 (`Weapon_GrenadeFrag` / `Weapon_GrenadeMolotov` verb range) | XML read, threatmap_report §5 |
| Throws need LOS | yes: `Verb_LaunchProjectile` without `requireLineOfSight=false` | XML read, not measured in game |
| Rocket carrier reach used | 36 cells | code constant (UNVERIFIED) |
| Frag fuse at rest | 88–91 ticks | measure_grenade, hazards.md |
| Frag blast reach | hit 6/7 pawns at d ≤ 1.4, 0/32 at d ≥ 2.2; XML radius 1.9 | measure_blast (4 blasts only), hazards.md |
| Aiming times (info card) | frag/molotov 1.5 s; doomsday/triple rocket 4.5 s; incendiary/EMP/smoke launcher 3.5 s | hazards.md |
| Flight times | frag 75–122 ticks, molotov ~90–105, doomsday 30–45, triple rocket 30–60 | hazards.md |
| Aiming observable? | no: the carrier's job stays "watching for targets" | hazards.md |

Projectile defs: `Proj_GrenadeFrag` (rests, then blows), `Proj_GrenadeMolotov` (bursts on impact,
leaves `Fire`), `Bullet_DoomsdayRocket`, `Bullet_Rocket`, `Proj_GrenadeEMP`, `Proj_GrenadeTox`,
`Proj_GrenadeSmoke`, `Bullet_IncendiaryLauncher`, `Bullet_EMPLauncher`, `Bullet_SmokeLauncher`.
Blasts show up as short-lived `Explosion` things.

**Melee keyword list** (is_melee, weapon label substring): `sword, horn, hammer, mace, spear, knife,
axe, club, gladius, ikwa, fist, claw`. The census classifier uses a different, longer list
(adds `blade, scythe, lance, pike, bite`) and puts it last after explosive, long, support, bow,
thrown, short and medium (DATA.md §4). Both lists are UNVERIFIED against the actual weapon set; the
rewrite should use one classifier.

**Mech kill priority** (doctrine agent, higher first; unknown kinds 2; rocket carriers 6):

| Kind | Priority |
|---|---|
| Mech_Lancer, Mech_Pikeman | 5 |
| Mech_Scyther | 4 |
| Mech_Centurion | 3 |
| Mech_CentipedeBlaster | 2 |
| Mech_Warqueen | 1 |

The doctrine agent's melee pawns only go for Lancer/Pikeman/Scyther unless something is within
20 cells. This table is a design choice, not a measurement.

**Mech weapon class** (no weapon label, so classed by kind): Lancer medium, Pikeman long, Scyther
melee, Centurion/CentipedeBlaster/CentipedeGunner/Warqueen support, CentipedeBurner/Termite/
Scorcher/Diabolus explosive, WarUrchin/Militor short, Tesseron/Legionary medium.

## 6. Hazards

See results/hazards.md (reaction windows) and results/reflex_report.md. Additions:

- **Fire:** standing *next to* fire does no damage; only spread does (reflex_report §2). Burning
  forest makes `list_things(defName="Fire")` large (65+ things → output guard).
- **Rockets are undodgeable:** 30–60 ticks in flight and aiming can't be seen. Counter them only by
  spacing, cover and killing the carriers first.
- **Molotov in-flight landing prediction** was right for 51 of 130 frags+molotovs (39%), so we don't
  act on it.
- **Frags first seen with < ~55–60 ticks of fuse left** cannot be escaped (15 + ~40 ticks to walk
  3 cells). That is ~1 in 4 in-blast cases at a 30-tick cycle.
- Fire and explosions **change terrain**, but less than assumed. Verified 2026-10-03 on
  arena_forest (12 trees set alight with `T: Attach Fire`, a debug bomb on a ruin wall, then
  25×300 + 40×600 ticks):
  - A **burning tree becomes a `BurnedTree` stump** ("burned stump", `StumpBase`), which still
    renders as **`*`** in get_area ascii. Only 1 of the 12 ignited cells became `.` (stump
    destroyed). Stump fillPercent 0.20 vs tree 0.25 (XML), both PassThroughOnly: cover changes
    slightly, passability and LOS (by our legend) do not.
  - Trees burn slowly: after 7,500 ticks every ignited tree was still `*` and burning; the fire
    kept spreading through grass (17 → 113 Fire things over 31,500 ticks, outside any home area).
  - **Burned trees never appear in `wait_for_event`'s `_delta`** (no `_delta` at all during the
    fire). A destroyed wall does: `removedBuildings: [{def: Wall, count: 2}]`, without cells
    (RIMMOLT_API §2). So fire cells are the only signal for plant changes, and building deltas need
    a cell guess (rca/terrain.py marks every fetched tile with a structure char).
  - Plants also grow: 3 cells went `.` → `*` over the same time (saplings). Terrain is not static
    even without combat.
- Mech boss telegraphed attacks: not measured (TODO).

## 6b. Combat points

| Fact | Value | Evidence |
|---|---|---|
| Source | `combatPower` of the PawnKindDef (XML, with `ParentName` inheritance); not exposed by RimMolt | `rca/game/defs.py` → `data/combat_power.json` (290 kinds, game 1.6.4871 rev595) |
| Examples | Mercenary_Gunner 85, Mercenary_Sniper 110, Grenadier_Destructive 70, Tribal_Warrior 50, Town_Guard 60, Mech_Militor 45, Mech_Pikeman 110, Mech_Termite_Breach 110, Mech_Scyther 150, Mech_Lancer 190, Mech_CentipedeBlaster 400, Mech_Warqueen 600, Warg 160 | XML |
| Raid points vs kind points | theme raids spawned at 1500 pt sum to 1260–1485 points of kinds (pirate_mixed 1455, tribal_archers 1485); theme_mechs 1000 (4 Pikeman, 3 Scyther, 1 Termite_Breach) | manifests × table |
| Mean points per raider | tribal 54–59, pirates 104–115, frag_check grenadiers 70, mechs 125–248 by scenario | `scoring.manifest_mean_points` |

## 7. Arena facts

- Scenario: **The Rich Explorer** (one colonist arrives by drop pod with a kit: charge rifle,
  meds, ...), storyteller Phoebe/Peaceful. The kit must be cleared from the landing area or squads
  pick it up [code].
- **Ruins hold weapons**, even persona weapons. Remove every `Gun_*`, `MeleeWeapon_*`, `Weapon_*`
  item before saving [code].
- Map size **250×250** [code]. Map tile: flat temperate forest, inland, no river, 10–20 °C, no
  world objects within 5 tiles.
- `arena_open` = `arena_forest` with the rect (50,50)–(200,200) cleared (no trees, no cover).
- Arenas have **no beds**: "Rescue" is always disabled ("Cannot rescue: No reachable ... bed") [log].
- Equal raid points ≠ equal headcount: tribal raids at 1500 pt are ~26 pawns vs our 14 (theme_report).

## 8. Built-in enemy AI behaviour (becomes / merges into ENEMY_AI.md)

| Behaviour | Evidence | Confidence |
|---|---|---|
| A raid leaves when broken (**"... are fleeing"**) or after enough damage dealt (**"... satisfied with the damage done and are leaving"**). Satisfied raids had lost ≤ 46% of their pawns, fleeing ones ≥ 71% | grade_check.jsonl (12 runs) | measured, small n |
| A raid can turn "satisfied" without fighting a passive defender: turtle vs pirate_mixed, 14/14 escaped, 0 killed | grade_check.jsonl | measured, n=3 |
| Raiders kidnap downed colonists (job `kidnapping <name>.`) and leave the map with them | tracker, theme_report (3/5 kite runs left with captives) | observed |
| Mechs never walk off the map | tracker design | observed, not counted |
| Mechs may park out of sight 13–28 cells from a static line and not attack | execution_report §3 (hold v3 traces) | observed |
| Mech raids sometimes don't assault at all (strategy chosen by the game) | assault check rejects | observed |
| Grenade aiming is not observable (job stays "watching for targets") | hazards.md | measured |
| Melee raiders show their target: `targeting = "attacking colonist <name>"` (kite v3 uses it) | [code], execution_report | observed |
| Raiders mostly stop throwing frags when we hold beyond 13 cells (frags seen fell to ~0) | threatmap_report verdict | measured, n=10 |
| Throwers need LOS (by defs) | threatmap_report §5 | XML read, not measured |
| Melee lock: a pawn with an adjacent enemy can't use its ranged attack (both sides). Adjacency rule (diagonals?), weapon exceptions, friendly fire into melee and mech behaviour are **UNVERIFIED** | TODO | belief |
| Directional cover; LOS-break relocation; fire avoidance; berserk ignoring cover | TODO hypotheses | **UNVERIFIED** |

Our own colonists: undrafted pawns follow the hostility response (flee). Drafted pawns that stand
still fire at will. A pawn that is moving does not shoot [code, obs].
