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
| §14 threat montage | `tools/build_montage.py` | `rca/game/builders/montage.py` |
| §15–16 human / Claude play | `tools/run_human.py`, `tools/hands.py` | `rca/eval/harness.run_observed_episode` |
| combat points | `tools/combat_points.py` | `rca/game/defs.py` |

**Save guard:** `session.save` refuses any name not starting with `arena_`, `scenario_`,
`theme_base` or `drill_`, so a builder can never overwrite a personal colony save.

## 1. Arena creation (`arena_forest`, `arena_open`)

1. `tools/make_arena.py --new-game` (`arena.new_game`): quit to title, new colony →
   **The Rich Explorer** → Phoebe, **Strive to Survive** (the evaluation standard, WORKFLOW) →
   "Create world" page. Both selection pages have a review gate (the first call only lists the
   choices), so each is called up to twice. The pre-2026-10-04 arenas were Peaceful
   (archived).
2. **By hand:** on the planet page, make sure the factions **Pirate gang, Rough outlander union,
   Fierce tribe, Savage tribe, Mechanoid hive** are listed. Biotech swaps the first four for
   xenotype variants, and the `Add...` float menu vanishes unless the real mouse is over it.
   Script check: `get_window_ui` on `Page_CreateWorldParams`, labels between `Factions` and `Add...`.
3. `tools/make_arena.py` does steps 3–11: map size **250×250** (`arena.set_map_size`: Advanced
   settings → `Edit...` → radio `250x250`, verified, `--map-size` to change), then
   `create_world(coverage=0.3, rainfall/temperature/population=Normal, pollution=0)`; poll
   `game_setup_status` until `stage == "starting_site"`.
4. Tile: `find_world_tiles(TemperateForest, Flat, coastal=False, river=False, temp 10–20, limit=60)`.
   For each tile, preview `select_starting_site(tile)` and take the first one with no
   `nearbyObjects` where every surrounding biome is temperate forest. Then confirm it.
5. `choose_ideoligion(classic)`; rename the starting pawn **Arena 'Observer' Keeper**; `start_game`;
   poll until `programState == "Playing"`; wait 3 s; refuse to go on unless
   `get_status.difficulty` is `strive to survive`.
6. Close the intro letter (`Dialog_NodeTree` → OK). Wait (120-tick waits, up to 30) until no
   `DropPodIncoming`/`ActiveDropPod` remains.
7. Pause; dev mode on; run `Destroy factionless animals`, `Destroy player animals`, `Clear All Fog`.
8. Teleport the observer to **(240, 240)**. Use the 3-call teleport and verify with `get_pawn`,
   retrying up to 5 times.
9. `Clear area (rect)` over the landing spot ±8 cells (the explorer's kit), `Destroy factionless
   animals` again, then destroy every loose `Gun_*`/`MeleeWeapon_*`/`Weapon_*` item (ruins) with
   `T: Destroy`, and strip Anomaly content (`arena.strip_anomaly`: "Dark entities" pawns,
   cryptosleep caskets, the Void Monolith; GAME_FACTS §7). Saves built before this step:
   `make_arena.py --strip-anomaly save1,save2,...` (load, strip, save; done for the 10 t500
   saves on 2026-10-04).
10. `save_game("arena_forest")`.
11. `Clear area (rect)` over (50,50)–(200,200), then `save_game("arena_open")`.

## 1b. Difficulty conversion (superseded 2026-10-04: the saves are rebuilt instead; UNVERIFIED)

No RimMolt tool changes the difficulty of a loaded game: `select_storyteller` works only on the
new-game page (RIMMOLT_API §2). Candidate route, keeping every raid exactly as saved:

1. A save stores only the difficulty's name, in the storyteller block:
   `<storyteller><def>Phoebe</def><difficulty>Peaceful</difficulty>…` (theme_base.rws; no
   per-value block for a preset difficulty, so the values come from the DifficultyDef).
2. Back up the save, replace that one line with `<difficulty>Rough</difficulty>` (Rough = Strive
   to Survive), load it, and check `get_status.difficulty` reads `strive to survive`.
3. Same edit for every `arena_*`, `scenario_*` and `theme_base` save, then refresh the gzipped
   copies in `saves/` (`restore_saves.sh` unpacks them). The block also holds a Peaceful-only
   `studyEfficiencyFactor` 2 (Anomaly research, no effect on battles).

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

rca check (2026-10-03): `tools/build_scenarios.py --specs <tmp spec> --out <scratch dir>` built
the throwaway `scenario_tmp_phase2_check` (Pirate 1000 squad of 11 vs TribeSavage 400, 8
raiders, arena_open) and passed the assault check (gap 131 → 19). The save is left in the Saves
folder (saves are never deleted).

## 7. Theme building (theme_builder)

Scenario sets (`--set`, `theme.SETS`): **t500** (the evaluation standard: squad from
OutlanderRough 500 pt with 7–10 pawns, raids 500 pt, mech ladder 500/600/700/800/1000; ids and
saves `t500_<theme>` / `scenario_t500_<theme>`, base `theme_base_t500`, files in `themes/t500/`)
and **theme** (1500 pt, squad 12–15, baseline-v1; `theme_<name>`, `themes/`). The steps below
are written for the 1500 set; t500 is the same with its numbers. `themes/t500/build.sh` runs
the whole set with a fresh game before each load-heavy stage (base + pirates, then tribes, mechs
and frag_check).

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

1. Load + ready wait (§3). This leaves dev mode on. The harness reads `get_status.difficulty`,
   stops the batch unless it is `--difficulty` (default `strive to survive`), and stores it in
   the row. During the episode, a hostile that was not there at the start ends it as `invalid`
   (EVAL_SPEC §3); the run is repeated up to 3 times.
2. `debug_menu run tab=settings path="Never Force Normal Speed" value=True`, then `close`.
3. `dev_mode(devMode=False, godMode=False)`. The agent runs with no dev mode and a sandboxed client.
4. Read the squad state, create the tracker, `observe(0)`, create the episode's `Terrain`,
   `agent.reset`, then the loop (EVAL_SPEC.md).
5. `--scenarios all` excludes check-tier scenarios (frag_check): name them explicitly.
6. Tactical options: `--option vs_throwers=accept_dodge|stand_off|close_in` (doctrine, turtle,
   spread), `--option rescue=off|on` (doctrine; off from doctrine v5), `--option
   wounded_pullback=on|off` (doctrine, turtle); natural values first; ignored by doctrines that
   don't offer them. Rows store the effective `options`; `--resume` counts only rows with the
   same options (a key missing from an older row counts as what agents did before the option
   existed, `PRE_OPTION_BEHAVIOUR`: on). Example (phase-2 smoke): `results/phase2/smoke.sh`;
   one run per casualty option: `results/prebaseline/checks.sh`.

## 10. Crash watchdog and planned restarts (legacy/results/threatmap_check*.sh; rca: `session.Watchdog`)

rca runs the same logic in-process before every episode attempt (`run_batch`) and drill
session: alive → go; process exists but silent → wait 60 s, then **stop** (never launch a second
instance); no process → `open steam://rungameid/294100`, poll every 5 s for up to 5 min, then
20 s grace; more than 2 crash relaunches in a batch → stop. The process is found with
`pgrep -f "RimWorld by Ludeon Studios"` (the macOS process name).

**Planned restart cadence** (WORKFLOW evaluation standard: every 100 episodes): `run_batch` counts episode attempts (each is a
load); after `--restart-every` attempts (default **100**; 0 = never) the next `ensure()` quits the
game (`pkill -f "RimWorld by Ludeon Studios"`, SIGKILL after 60 s if it is still there), waits
until the process is gone, relaunches it as above and resets the counter. Planned restarts don't
count against the 2-relaunch limit; a crash relaunch also resets the counter. Why: NullReference
errors grow after ~100 loads and a native crash came at ~150 loads in one session (RIMMOLT_API
§4). Episodes never save, so nothing is lost.

**Verified once in rca (2026-10-03, `results/prebaseline/restart.sh`, amove on frag_check):**
planned restart with `--restart-every 1` (log: "watchdog: planned restart after 1 episodes";
the game quit, relaunched and loaded the next scenario; ~45 s between episodes, load included),
and crash relaunch (game killed with `pkill`, then a new batch: "watchdog: relaunching RimWorld
(restart 1)", ~42 s). Both episodes completed normally; one game process afterwards. Not yet
seen: a real crash mid-episode, and a planned restart after 100 loads (the default).
`tools/run_eval.py` passes its flushing logger to the watchdog, so these lines reach a detached
log as they happen. Legacy shell version:

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
  **agent_version equals the current class's version**, **and** (cycle policy, reflex on/off,
  reflex version) equal the current run's settings, **and** its effective `options` equal the
  requested ones (no field = `{}`; a missing key = its pre-option behaviour, §9), **and** the same
  `difficulty` (no field = `peaceful`). Invalid rows never count. Rows from other versions or
  settings are kept in the file but ignored.
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

## 14. Threat montage (`montage_threats`, 2026-10-04)

A save to look at raid sizes in game: one raid per (type, points) cell in a 2D grid of walled
pens (results/montage/legend.md for the counts).

1. **New game, all automated except two clicks:** `return_to_title(confirm=True)` →
   `main_menu(new_colony)` → `select_scenario("The Rich Explorer")` →
   `select_storyteller(Phoebe, Rough, reloadAnytime=True)` (Rough = Strive to Survive).
   By hand on the planet page: add Pirate gang, Rough outlander union, Fierce tribe, Savage
   tribe (`Add...` still closes without the real mouse). Map size: the planet page's Advanced
   settings → `Edit...` opens `Dialog_AdvancedGameConfig` (radios `200x200` … `325x325`,
   readable with `get_window_ui`; the site page itself is not scriptable). Then
   `create_world`, tile by `arena.pick_tile` (tile 55, flat temperate forest), confirm,
   classic ideoligion, `start_game`. 300×300 map.
2. Map prep as §1 steps 6–9 (observer to (292, 292)).
3. `python3 tools/build_montage.py --samples 3`: for each of 4 types × 7 point levels,
   3 sample raids (spawn, record, `Destroy non-colonists`); then `Clear area` over the
   montage (it removes natural rock too), god mode: floors `GoldTile` / `SilverTile` in a
   checkerboard per pen and a granite `Wall` outline (`build fill=outline`); one raid per
   pen, raiders in rows sorted by weapon class; mech cells first (pods need settle waits);
   human raids are placed with no time passing (`spawn_raid(instant=True)`: EdgeWalkIn
   raiders exist as soon as the last pick returns, even paused); a final pass re-places
   raiders that moved.
4. Layout: pens 14×12 inside, pitch 18 × 16, south-west corner (114, 94); columns west →
   east pirates, outlanders, tribe (fierce), mechanoids; rows south → north 100, 200, 300,
   500, 700, 1000, 1500 points.

Found while building: raid generation fails now and then even for humans (Pirate 100 once:
retry, up to 3 tries); Mechanoid 700 failed 4 tries in a row before one worked. Settle waits
cost the observer (gone after the mech fill; a "Game Over" letter remains): view the save
paused. Dismiss raid letters with `read_letter(id, dismiss=True)` (117 had piled up).

## 15. Human play and the router night run (roadmap 3: failure mining)

**Human play** (`tools/run_human.py --scenario <id>` or `--manifest <file>`;
`harness.run_observed_episode`): the scenario loads paused and a person plays; the harness
never pauses or advances time. It polls every second (fates, contact windows, the storyteller
guard, stop conditions; game messages from `get_alerts.recentMessages`, skipping the toasts
left from before the load) and writes the usual row with agent `human`, cycle `observed`, to
`results/human/play.jsonl`. Every poll also goes to a trace (`rca/eval/trace.py`,
`results/human/traces/`, named in the row's `trace`; `--no-trace` skips it): each pawn's
position, health, weapon, job and drafted flag on both sides, fires, thrown projectiles and new
messages, ~0.25 s per poll. Screenshots for a watcher: `screenshot(include_ui=false, x, z, w,
h)` renders offscreen and never moves the player's camera; `tools/watch.py` (in the background, one look per run) waits for game time or contact, prints both sides (position, health, weapon, job) and draws a labelled frame; copy its output to `results/human/raw/<id>/` for the report. A battle report
(`results/human/reports/<id>.md`) uses them: `rca/eval/frames.annotate()` labels a screenshot
with who stood where (blue ours, red enemies, dashed downed) and draws route maps (macOS:
Quick Look + ffmpeg).

**Router night run** (`tools/night.py`): `new` builds a random problem
(`rca/game/builders/problem.py`: arena_forest_night or arena_open_night × our squad = a raid of
a random human faction at 500 pt, recruited and placed at (125, 125) × the enemy = a raid of
a random faction at 500 pt, mechanoids included; no assault check) and prints the briefing
(`rca/strategic/briefing.py`: both sides' composition and ranges, each doctrine's
preconditions on the map). The router (a person or Claude) picks a doctrine and options and
runs `night.py run <id> --agent <d> [--option k=v] --why "<reason>"`; the row (+ `router`,
`problem`, `badness`) goes to `results/night/router.jsonl`. `night.py rank --top 100` writes
`results/night/worst.md` (badness: `rca/eval/ranking.py`). The game restarts after 80 loads
(`results/night/state.json`). The night arenas are copies of the evaluation arenas with the
Empire and the civil outlanders made hostile (debug goodwill), saved as `arena_*_night`.

## 16. Claude plays directly, with the case library (2026-10-05)

Claude fights the whole battle itself (strategic: loadout and site; tactical: the play; micro:
each order), turn by turn through `tools/hands.py`, and looks back at past battles in
`results/cases/` while doing it. The Python agents are frozen as the baseline. The library and
the retrieval prompts are in `results/cases/README.md`.

**After a context compaction, read first:** `results/cases/README.md`, this section,
`tools/hands.py` (docstring and helpers), the operating facts in RIMMOLT_API.md
(`do_thing_action`, `order_pawn` float menu, `manage_gear`) and the last journal in
`results/cases/journals/`.

1. **Pick** the next problem in `results/night/worst.md` that has no card in
   `results/cases/cards/` (#9 `rand_011` onward), unless the user names one.
2. **Load:** `python3 tools/run_human.py --manifest scenarios_rand/scenario_<id>.json --player
   claude`, in the background. It loads paused and only watches; the trace goes to
   `results/human/traces/`, the row to `results/human/play.jsonl`. Time moves only with
   `hands.wait(ticks)` (it pauses again after).
3. **Battle card:** `hands.brief("player")` and `hands.brief("hostile")` (shooting/melee, combat
   traits, weapon, armour, smoke packs, positions; read them before the battle, skills grow
   during it), the raid's edge and distance, `briefing.features(manifest)`, situation tags from
   `results/cases/tags.md`. Show the user a short card in chat.
4. **Retrieval (start):** the subagent prompt in `results/cases/README.md` writes
   `results/cases/sheets/<id>_start.md`. Read it, decide (loadout, site, play), and tell the
   user the plan in a few lines.
5. **Loadout** before anyone is drafted (drafting cancels the pick-up job): `manage_gear` drop,
   then equip by ThingID (RIMMOLT_API.md), ~100–200 ticks.
6. **Play:** draft and order with `go`, `attack`, `melee`, `hit` (walls, urns), float-menu
   `Carry`/`Melee attack … to death`, gizmos `Pop smoke`/`Drop <name>`; `st()` and
   `shot()` to look; `wait()` 45–150 ticks per decision (shorter in contact). At a turning point
   the start sheet did not cover, run the scene retrieval. Keep key frames with
   `shot(..., keep="<id>_t<tick>.jpg")`.
7. **End:** the harness stops when the raid is gone (or 6000 ticks after squad down; the man in
   black is removed). Compute badness (`rca.eval.ranking.badness(row)`) and compare with the
   agent's row in `results/night/router.jsonl` (the worst-list rows stopped at squad down:
   EVAL_SPEC §3).
8. **Records:** the journal (`results/cases/journals/`, format in the README), the card (new,
   or a Claude row and scenes added), new sites in `sites.md`, new tags in `tags.md` marked
   *(new, date)*, the README's card table. Observations only: no lessons from one battle (ask
   the user before LESSONS.md).
9. **Commit** on a branch and merge into main; don't push.

**Never advance time blind:** every loop that moves time uses `hands.guard()` or `hands.wait_safe()` (they stop when a raider comes near or one of ours goes down). Two plain `wait()` loops let the raid arrive unseen (rand_015 attempt 2, rand_023). Check that a repeated order works (a wall's %, a target's health) after the first rounds.

A battle in which the context was compacted is discarded, not resumed: move its row to
`results/human/discarded.jsonl` with `discarded.why`, and play it again from the start. The
user may also take over or ask for a restart at any time.
