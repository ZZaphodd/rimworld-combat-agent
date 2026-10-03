# Procedures (runbooks)

How each kind of save, scenario and episode was built and run. Tool details are in
RIMMOLT_API.md, game constants in GAME_FACTS.md. Every step here worked in practice unless it is
marked UNVERIFIED. Code: `rca/game/` (session, debug, builders, census) behind the CLIs in
`tools/` (README.md); legacy/ holds the scripts these runbooks were first written for.

| Runbook | CLI | Code |
|---|---|---|
| §1–2 arenas | `tools/make_arena.py [--resume\|--fort]` | `rca/game/builders/arena.py` |
| §3 load + ready wait | – | `rca/game/session.load` |
| §4 raid spawning | – | `rca/game/debug.py` |
| §5–6 squad, scenarios, assault check | `tools/build_scenarios.py` | `rca/game/builders/scenario.py` |
| §7 themes, frag_check | `tools/build_themes.py` | `rca/game/builders/theme.py` |
| §8 census | `tools/census.py` | `rca/game/census.py` |
| §9 episodes | `tools/run_eval.py` | `rca/eval/harness.py` |
| §10 watchdog | (in-process) | `rca/game/session.Watchdog` |
| §12 micro drills | `tools/run_drill.py` | `rca/micro/drills.py` |
| combat points | `tools/combat_points.py` | `rca/game/defs.py` |

**Save guard:** `session.save` refuses any name not starting with `arena_`, `scenario_`,
`theme_base` or `drill_`, so a builder can never overwrite a personal colony save.

## 1. Arena creation (`arena_forest`, `arena_open`)

1. **By hand:** new colony → scenario **The Rich Explorer** → storyteller Phoebe, Peaceful → open
   "Create world".
2. **By hand:** on the planet page, make sure the factions **Pirate gang, Rough outlander union,
   Fierce tribe, Savage tribe, Mechanoid hive** are listed. Biotech swaps the first four for
   xenotype variants, and the `Add...` float menu vanishes unless the real mouse is over it.
   Script check: `get_window_ui` on `Page_CreateWorldParams`, labels between `Factions` and `Add...`.
3. `create_world(coverage=0.3, rainfall/temperature/population=Normal, pollution=0)`; poll
   `game_setup_status` until `stage == "starting_site"`.
4. Tile: `find_world_tiles(TemperateForest, Flat, coastal=False, river=False, temp 10–20, limit=60)`.
   For each tile, preview `select_starting_site(tile)` and take the first one with no
   `nearbyObjects` where every surrounding biome is temperate forest. Then confirm it.
5. `choose_ideoligion(classic)`; rename the starting pawn **Arena 'Observer' Keeper**; `start_game`;
   poll until `programState == "Playing"`; wait 3 s.
6. Close the intro letter (`Dialog_NodeTree` → OK). Wait (120-tick waits, up to 30) until no
   `DropPodIncoming`/`ActiveDropPod` remains.
7. Pause; dev mode on; run `Destroy factionless animals`, `Destroy player animals`, `Clear All Fog`.
8. Teleport the observer to **(240, 240)**. Use the 3-call teleport and verify with `get_pawn`,
   retrying up to 5 times.
9. `Clear area (rect)` over the landing spot ±8 cells (the explorer's kit), `Destroy factionless
   animals` again, then destroy every loose `Gun_*`/`MeleeWeapon_*`/`Weapon_*` item (ruins) with
   `T: Destroy`.
10. `save_game("arena_forest")`.
11. `Clear area (rect)` over (50,50)–(200,200), then `save_game("arena_open")`.

## 2. `arena_fort` layout (derived from `arena_open`, god mode)

- Granite walls (`Wall`, stuff `BlocksGranite`) on the outline x 110–140, z 110–140: north, south
  and west sides complete. The east wall at x = 140 has a **3-cell gap at z 124–126** (segments
  z 110–123 and z 127–140).
- `Sandbags` line inside at **x = 128, z 118–132** facing the gap.
- God mode off, pause, print the ascii area as a check, then `save_game("arena_fort")`.
- Fort scenarios place the squad at (120, 125). legacy/trace.py uses gate = (140, 125).

## 3. Load and ready wait (every load)

1. `load_game(name, confirm=True)`; raise on `error`.
2. Poll `game_setup_status` once a second (swallow errors; up to 180 s) until
   `programState == "Playing"`.
3. "Playing" flips before the map is up. Poll (up to 30 s) until `get_status.loaded` **and**
   `list_colonists` is non-empty.
4. Sleep 2 s, `set_speed(pause)`, `dev_mode(devMode=True)`. The builders need dev mode, and the
   episode start turns it off again.

## 4. Raid spawning

**Specifics route** (`Execute raid with specifics...`): you choose strategy and arrival.

1. Snapshot the hostile ids (`list_things pawn hostile confirm`).
2. `run` the entry, then back to back: pick the faction (`endswith("(<Def>)")`, skip `[NO]`), the
   points (nearest `"N points"`), the strategy, the arrival, then `-Random-` until no options are
   left.
3. Settle (below).

**Faction route** (`Execute raid with faction...`): the game chooses strategy and arrival. It is
the only route for mechs, and the census uses it for the natural mix.

1. Snapshot the hostiles; `run`; pick the faction; pick the points; then pick option 0 until no
   options are left.
2. Silent-failure check: no `letter` notification **and** "empty collection" in `log[]` → not
   generated (raise and retry).
3. Settle with max 20 steps (60 for mechs).

**Settle:** repeat `wait_for_event(maxGameTicks=60, pause=always, force)` until the set of new
hostiles is non-empty, its size equals the previous sample, and no drop pod is in flight
(`list_things(category=all, summary, confirm)` groups starting `DropPodIncoming`/`ActiveDropPod`).
Then pause. No new hostiles = failure ("spawned nobody").

**Lordless spawn** (frag_check): `run("Spawn Pawn... > <Kind>")`, `click(cells="x,z;...")`,
`close`. These pawns have no raid lord, so no fleeing or satisfied message is ever posted.

## 5. Squad build

1. Remember the observer ids (`list_colonists`) on the freshly loaded arena.
2. Spawn a raid of the squad faction (specifics route, ImmediateAttack/EdgeWalkIn).
3. `T: Recruit` + click on each raider. Verify that every id is now in `list_colonists`.
4. Placement: a formation of rows of `width` 5 with `spacing` 2, centred on `place` (rows go
   toward −z). Then `place()`: up to 4 rounds of "teleport every pawn not on its slot, re-check
   positions". Stacked pawns make clicks grab the wrong pawn.
5. Observer removal: for each observer, check that no squad pawn shares its cell, then
   `T: Destroy` at its cell. Verify that the colony equals the squad exactly.

## 6. Scenario build and assault check (scenario_builder)

Per spec in scenarios.json:
1. Load the arena.
2. Build the squad (§5).
3. Spawn the enemy by `method` (faction route if `"faction"`, else specifics).
4. `debug_menu close`, save `scenario_<id>`, write the manifest (DATA.md).
5. **Assault check:** reload the save and take the median distance from the squad centroid to the
   hostiles (d0). Wait 3000 ticks with no orders and measure again (d1). The check passes if any
   hostile's `targeting` starts with `targeting colonist`/`attacking colonist`, **or** any squad
   pawn is dead/downed/gone, **or** d1 ≤ 0.7 × d0. Otherwise the raid is loitering: rebuild, up to
   3 builds.

## 7. Theme building (theme_builder)

1. **Frozen base** (`--base`): load `arena_forest` and spawn OutlanderRough 1500 pt until the raid
   has 12–15 pawns and no weapon class ≥ 50% (up to 40 tries; the first draw passed). Recruit,
   place at (125,125), remove the observer, save `theme_base` and write `themes/base.json` (squad
   and slots).
2. **Rejection sampling** per faction group: reload `theme_base` for every attempt so the squad is
   identical. Tribal groups alternate TribeRough/TribeSavage. Spawn 1500 pt (= squad points, no
   relaxing). Classify each raider's weapon (one `get_pawn` each), append the sample to
   `themes/samples.jsonl`, and offer the raid to every still-missing theme of that faction (the
   predicates are disjoint). Max 150 attempts.
3. **Mechs:** the faction route with the points ladder 1500/2000/2500/3000/4000, 3 tries per level,
   always reloading the base.
4. **On a match:** teleport the squad back onto its base slots (it wandered while the raid
   settled), close the debug menu, save `scenario_theme_<name>`, run the assault check (reject
   loiterers), write the manifest, and upsert the spec into scenarios.json.
5. **frag_check** (`--frag-check`): load the base and put 5 `Grenadier_Destructive` at
   (cx + 27, cz − 6 + 3i), shifting each by 0, ±1, ±2, +3 in x to a passable cell. Accept if
   ≥ 60% carry frag grenades (2nd roll: 4/5), place, save, run the assault check. Up to 15 tries.
   Tier `check`.

Theme predicates and acceptance rates: DATA.md §3.

## 8. Census sampling (raid_census)

- Configs `Faction:points`; default 8 configs × 125 raids, faction route, from `arena_open`.
- Reload the arena every 100 samples and after any failed sample. Otherwise batch
  `Destroy non-colonists` + close every 5 samples (it costs ~1 s; raids barely move between
  samples).
- **Mechs:** every sample starts from a freshly loaded arena and settles up to 60 steps (late pods
  would leak into the next sample).
- Up to 2 × per_config attempts; failures are counted and printed. One JSON line per raid.
- About 2.6 s per sample.

## 9. Episode start (`session.start_episode`, `harness.run_episode`)

1. Load + ready wait (§3). This leaves dev mode on.
2. `debug_menu run tab=settings path="Never Force Normal Speed" value=True`, then `close`.
3. `dev_mode(devMode=False, godMode=False)`. The agent runs with no dev mode and a sandboxed client.
4. Read the squad state, create the tracker, `observe(0)`, create the episode's `Terrain`,
   `agent.reset`, then the loop (EVAL_SPEC.md).
5. `--scenarios all` excludes check-tier scenarios (frag_check): name them explicitly.
6. Tactical options: `--option vs_throwers=accept_dodge|stand_off|close_in` (doctrine, turtle,
   spread; ignored by the others). Rows store the effective `options`; `--resume` counts only rows
   with the same options. Example (phase-2 smoke): `results/phase2/smoke.sh`.

## 10. Crash watchdog and planned restarts (legacy/results/threatmap_check*.sh; rca: `session.Watchdog`)

rca runs the same logic in-process before every episode attempt (`run_batch`) and drill
session: alive → go; process exists but silent → wait 60 s, then **stop** (never launch a second
instance); no process → `open steam://rungameid/294100`, poll every 5 s for up to 5 min, then
20 s grace; more than 2 crash relaunches in a batch → stop. The process is found with
`pgrep -f "RimWorld by Ludeon Studios"` (the macOS process name).

**Planned restart cadence** (TODO roadmap 2): `run_batch` counts episode attempts (each is a
load); after `--restart-every` attempts (default **100**; 0 = never) the next `ensure()` quits the
game (`pkill -f "RimWorld by Ludeon Studios"`, SIGKILL after 60 s if it is still there), waits
until the process is gone, relaunches it as above and resets the counter. Planned restarts don't
count against the 2-relaunch limit; a crash relaunch also resets the counter. Why: NullReference
errors grow after ~100 loads and a native crash came at ~150 loads in one session (RIMMOLT_API
§4). Episodes never save, so nothing is lost. The relaunch path itself is UNVERIFIED in rca (no
crash and no 100-episode batch since phase 1). Legacy shell version:

```
alive(): POST get_status (curl -m 10); ok if the reply contains "result"
ensure_game():
  if alive: return
  if a RimWorld process exists: sleep 60; if alive: return      # busy, not dead
  if RESTARTS >= 2: touch <batch>.failed; exit 1
  RESTARTS += 1; open steam://rungameid/294100
  poll alive every 5 s, up to 60 times; when alive: sleep 20, return
  else recurse
for each (scenario, runs) block: run it TWICE with --resume, calling ensure_game before each pass
touch <batch>.done
```

- The 2nd `--resume` pass fills episodes lost to a crash. Run batches detached:
  `nohup python3 tools/run_eval.py ... --resume > results/<batch>.log 2>&1 &` and wait with an
  until-loop (a single background tool call dies after ~1 h). Legacy batches wrote a `.done` /
  `.failed` marker file.
- The watchdog does not restart a game that is alive but degraded (NullReferenceException streak);
  the planned restart every 100 episodes is the mitigation.

## 11. Resume rules

- `--resume` counts the existing rows per (scenario, canonical agent). A row counts only if
  **agent_version equals the current class's version for this reflex version**, **and**
  (cycle policy, reflex on/off, reflex version) equal the current run's settings, **and** its
  effective `options` equal the requested ones (missing = `{}`). Rows from other
  versions or settings are kept in the file but ignored.
- It then runs runs [done, runs) for each cell.
- An episode that fails twice is written to `<results>.errors.jsonl` and skipped; `--resume`
  ignores that file, so the next pass retries it.
- Aliases (`b1`, `hold`, ...) work on both sides: stored names and CLI names are canonicalised
  before counting (`rca/eval/results.py`; tests/test_results.py). Legacy eval.py counted nothing for
  `--resume --agents hold` (rows keyed `turtle`, looked up as `hold`), fixed in rca. Old rows
  without a `cycle` field read as `fixed:<step_ticks>` with the reflex off, and rows with reflex
  on but no `reflex_version` read as v1.
- The agent version is per class (no per-reflex-version map any more): the resume key needs the
  agent version **and** the reflex version, separately.

## 12. Micro drills (frag drill)

Per WORKFLOW test layers: micro is judged per event, with positioning and targeting held fixed.

1. Load `theme_base` (Never Force Normal Speed, dev mode on only for spawning).
2. Spawn `count` (3) `Grenadier_Destructive` at `range` (12) cells east of the squad centroid,
   3 cells apart (passable cell nearest the wanted one); destroy every one without a frag grenade.
   Dev mode off.
3. Draft the squad and set **fire at will off**, reading the toggle state with `inspect_thing`
   (`actions[label="Fire at will"].active`) before and after toggling (fails the session if any
   pawn is still on).
4. Fixed 30-tick steps. Each step the micro layer observes and (mode `on`) dodges; a released pawn
   walks back to its slot unless the slot is inside a live hazard (`cell_ok`).
5. A session ends after `events` exploded frags, when fewer than half the squad stands, or at
   `max_ticks` (6000); the next session reloads the base. Modes alternate per session.
6. Output: `results/drills/<name>.jsonl`, one `event` row per exploded frag + one `session` row.
