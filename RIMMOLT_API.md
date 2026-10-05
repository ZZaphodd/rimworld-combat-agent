# RimMolt API: what we use and how it behaves

RimMolt is the RimWorld mod that exposes the game as MCP tools. This file is the spec a
client port is checked against. Evidence key: **[code]** = the old client relied on it and it
worked over hundreds of episodes; **[log]** = seen in run logs; **[obs]** = observed during
development; **UNVERIFIED** = assumed, never checked directly. Checked against RimMolt's own
tool list (117 tools) and live replies on 2026-10-04: argument names below match the schemas.
**Probing by hand:** `python3 tools/rm.py` (status, pawns, pawn, area, wait, debug, tools, call)
prints one line per thing and drops the `get_status` bundle, colour tags and long lists
(`rca/probe.py`): ~120 bytes for a status vs ~7 KB raw.

## 1. Transport

- Endpoint `http://localhost:8787/mcp`. It is stateless JSON-RPC 2.0 over HTTP POST: no session
  handshake, one POST per call [code].
- Headers: `Content-Type: application/json`, `Accept: application/json, text/event-stream` [code].
- Request body: `{"jsonrpc":"2.0","id":N,"method":"tools/call","params":{"name":TOOL,"arguments":{...}}}`.
- Response handling, in order:
  1. A top-level `error` means a protocol error, so raise.
  2. `result.content[]`: concatenate the `text` fields.
  3. `result.isError == true`: raise with that text. Tool failures arrive this way, e.g.
     `Error: RimMolt tool failed on main thread: NullReferenceException: ...` [log].
  4. Parse the text as JSON. If it is not JSON, wrap it as `{"text": ...}`.
- Many tools also report failure in-band: `{"ok": false, "error": "..."}` or a payload with an
  `error` key (for example `get_pawn` on a pawn that no longer exists). Callers check `ok`/`error`
  themselves [code].
- The client timeout must be longer than any `maxSeconds` passed to `wait_for_event`. The old
  client used 30 s by default and `maxSeconds + 30` for waits (60→90, 20→60, 300→330) [code].
- Liveness probe for watchdogs: call `get_status` and look for `"result"` in the reply (curl,
  10 s timeout) [code, results/*.sh].

## 2. Tools we use

Coordinates are map cells `(x, z)`, with z pointing north. Pawn and thing ids are strings such as
`Human51406`.

### Observation

| Tool | Arguments we pass | Returns (fields we read) | Quirks |
|---|---|---|---|
| `get_status` | – | `ticksGame`, `loaded`, `paused`, `storyteller` (label, e.g. `Phoebe Chillax`), `difficulty` (label, e.g. `peaceful`) | Game time source for episodes. Throws NullReferenceException while a load is still settling [log]. **Bundle:** by default every reply also carries the full output of `list_colonists` and `get_alerts` under `bundled` (6.3 of 7 KB with 14 colonists); `bundle_set=""` clears it, and the bundle list is saved with the save game [obs 2026-10-04] |
| `game_setup_status` | – | `stage` (`planet`, `starting_site`, ...), `programState` (`Playing` once a map runs) | Raises or times out while the world or map is generating: poll and swallow errors [code] |
| `list_colonists` | – | `colonists[]`: `id, name, health` (%), `mood, downed, job` (text), `topSkills, mapIndex`; only when present: `mentalState, incapableOf` (string, e.g. contains `Violent`), `inCaravan, hint` | No positions: get them from `list_things` |
| `list_things` | `category` (`pawn`/`item`/`all`), `faction` (`player`/`hostile`), `defName`, `verbose=True`, `summary=True`, `confirm=True`, `limit` (default 300); unused: anchor `nearId` or `nearX, nearZ` (+ `radius`) sorts nearest-first with `distance` | `things[]`: `id, label, def, kind, x, z, category, faction, hostile, rotation, downed, dead`, `drafted` (player pawns), `targeting` (live hostiles; shown only while the mod setting "Reveal hostile targeting" is on, the default); the compact form (no `verbose`) drops default-valued fields; with `summary`: `groups[]` of `{def, count}` | **Output guard:** a large result comes back as a `largeOutput` notice with **no `things` key** unless `confirm=True`. 65 Fire things were enough to trip it (37 agent steps lost, threatmap_report §1.5), and census samples were lost to `KeyError 'things'` the same way [log]. Always pass `confirm=True`. `category="all"` on the forest map is flooded by plants: query projectile defs by name (hazards.md) · `targeting` text seen [obs 2026-10-05, rand_011]: `targeting colonist <name>` (far off, every raider showed the same colonist), `targeting cell (x,z)` = the cell it is walking to (its firing position; they stopped there), `attacking colonist <name>` (a melee runner); absent while it just watches |
| `wait_for_event` (via `rm.wait(n)`) | `maxGameTicks` | `ticksWaited` | **Granularity [obs 2026-10-05]:** time runs at the mod's *wait speed* (a mod setting), so `wait(3)` advanced 15–30 ticks and `wait(10)` 14 at the setting in use: micro finer than ~15 ticks needs a slower wait speed (which also slows every agent run). Each short wait took ~0.1 s of wall time |
| `get_pawn` | `id`, optional `tab` | Default: `name, x, z, weapon` (label, e.g. `Heavy SMG (good)`, `Biocoded heavy SMG (normal)`), `health, downed, dead, job`; `error` if the pawn is gone. Dead or carried-off pawns have no `x`. Also `mood, hostilityResponse`; `name=` works instead of `id` | Tabs used: `health` → `hediffs[]` of `{label, part, permanent}`; `log` → `entries[]` of `{tick, type, text, battle}` (`type` `combat`/`social`; `tick` is **TicksAbs**, not `ticksGame` [obs 2026-10-03]; short, and it vanishes with a dead pawn); `records` → `records[]` of `{record, value}` (we read `Kills`; `Shots fired` shows whether a pawn is shooting: its own misses are not in its `log`, and its job stays `watching for targets` while it fires at will [obs 2026-10-05]); `bio` → `skills[]` `{skill, level, passion, disabled}`, `traits[]`; `gear` → `equipment[]`, `apparel[]`, `inventory[]` (`hands.brief()`). Other tabs (`needs, social, training, all`; `detail=true` adds tooltip text): unused |
| `get_area` | `minX, minZ, maxX, maxZ, render="ascii"` | `grid`: list of strings, **north row (max z) first**; also `legend` and `orientation` | One call is capped at about 55×55 cells, so tile in 50×50 [code]. Legend below. Other layers (`layer=roof/buildings/things...`) unused |
| `get_info_card` | `id`, or `x, z`, or `def` (+ `stuff`), or `stat` | `stats[]` of `{category, stats[{label, value}]}` | `def` takes **ThingDefs only** (`Unknown ThingDef: Mercenary_Gunner` for a PawnKindDef) [obs 2026-10-03]. A pawn's card has no combat power; see EVAL_SPEC §6 for where points come from |
| `inspect_thing` | `id` or `x, z` | `actions[]` with `toggle`, `active` for toggle gizmos | Used to read a drafted pawn's `Fire at will` state before toggling it (micro drill). Draft state: an undrafted pawn shows `Draft` (toggle, active false), a drafted one `Undraft` (active true) [obs 2026-10-03]. The reply also has `drafted` directly, and so does `list_things` (cheaper: one call for the squad); `list_colonists` and `get_pawn` have none [obs 2026-10-04] |
| `list_fires` | – | `fireCount`, `bounds`, `fires[{x, z, size}]` | Not used by rca yet (we query `Fire` things); probe only |
| `get_world` | – | `factions[]`: `{def, relation}` | |
| `list_wildlife` | – | `count, kinds[], animals[]` (id, kind, position; `mentalState` = manhunter; `revengeOnHarmPercent`) | Unused; the tool for the manhunter check (TODO). A loaded theme map had 0 wild animals [obs 2026-10-04] |
| `list_windows` / `get_window_ui` / `window_action` | `index`, `option` | `windows[]`: `{type, index}`; `labels[]` | Planet page: `Page_CreateWorldParams`; the faction list is the labels between `"Factions"` and `"Add..."`. Intro letter: `Dialog_NodeTree`, close with `option="OK"` |
| `set_hostility_response` | none (query) | `colonists[]`: `{response}` | Read-only use in trace.py |

**`get_area` ascii legend** (only the characters the code relies on):

| Char | Meaning | Passable | Blocks LOS | Evidence |
|---|---|---|---|---|
| `#` | wall (built) | no | yes | [code], fort build printout |
| `%` | natural rock | no | yes | [code] |
| `~` | deep water / marsh | treated as no | no | [code]; whether marsh is really impassable is UNVERIFIED |
| `*` | tree | yes | no (counted as half cover) | [code] |
| `+` | door or gate | yes | yes in rca (closed doors block; open-door state not checked) | legend |
| `.` | open ground (grass and low plants render as ground) | yes | no | legend |
| `V` | steam geyser | yes | no | legend |
| `?` | fogged / unknown | treated as yes | no | legend; arenas are fog-free |
| ` ` (space) | **never returned** | – | – | [obs 2026-10-03]: 0 of 62,500 cells on a whole arena_forest map (all 25 tiles). It was only the legacy canvas fill for unfetched cells |
| sandbags | **do not render** in ascii | – | – | [obs] (threatmap_report §2) |

The reply carries the full legend (`#` "constructed wall / impassable building", `%` "natural rock",
`+` "door or gate", `*` "tree", `~` "water, marsh or terrain you cannot build on (slow/blocked
movement)", `.` open ground, `V` geyser, `?` fogged). Whole forest map counts: `.` 54,874,
`%` 4,103, `*` 2,531, `~` 630, `#` 348, `+` 14. Burned trees (`BurnedTree` stumps) still render
as `*` (GAME_FACTS §6). rca/terrain.py is the one implementation of this legend.

### Orders

| Tool | Arguments | Returns | Quirks |
|---|---|---|---|
| `draft` | `action` (`draft`/`undraft`), `ids` (comma-separated) | – | Drafted pawns standing still fire at will at anything in range. Undrafted pawns follow their hostility response (flee) [code/obs] |
| `order_pawn` (list) | `id` plus a target: `targetId` or `x, z` | `options[]` of `{label, disabled}` | Float-menu labels, see below. **An undrafted pawn gets an empty option list** (no "Go here") [log] |
| `order_pawn` (by index) | same target + `index` | `ok` | The index refers to the list just fetched for the same target |
| `order_pawn` (direct) | `id, x, z, command="Go here"` / `id, targetId, command="Fire at"` | `ok` / `error` | No list round trip needed. A Go here onto an unwalkable cell fails, so retry the neighbours [code] |
| `do_thing_action` | `id, label, targetId?` | `ok` | `label="Drop <name>"` on a pawn carrying a downed squadmate puts it down [obs 2026-10-03]. `label="Auto attack (AI)"` + `targetId`: RimMolt's own combat AI for that pawn. It picks its own cover cell and can't see our data (it walks pawns back into danger: threatmap_report). `label="Fire at will"` **toggles** a drafted pawn's fire-at-will (used to make the squad hold fire in measurements). The reply's `nowActive` is the state after the click; `inspect_thing` reads it before (micro drill, PROCEDURES §12) |
| `do_thing_action` (verb) | `id, label="Command_VerbTarget", targetId` | `executed` | The weapon's own attack gizmo: fires/swings at a pawn **or a building** (walls, urns: how a drafted squad breaks cover). On a building it is **one swing/shot per order** (re-issue every ~45–90 ticks) and needs the pawn adjacent for a melee weapon; `executed: false` when out of reach or without line of sight (a rock between). Thrown weapons (frags, molotov) are thrown at the target pawn this way [obs 2026-10-05, rand_127/030] |
| `do_thing_action` `Command_VerbTarget` on a building — cadence | `id, label, targetId` | `executed` | **[obs 2026-10-05]** one swing per order: re-issuing it every 45 ticks cancelled the swings (rand_023: a granite wall 95 → 93% in ~3000 ticks with three pawns), every ~90 ticks worked (rand_127: a marble wall down in 11 rounds). Check the wall's % after the first rounds |
| `do_thing_action` (gizmos) | `id, label` (+ `targetId` or `targetX, targetZ` for a targeted gizmo) | `executed`; a refused target: `rejected`, `reason`, and `targeting {range, canTarget, validTargets}` | Apparel/ability gizmos by their label, e.g. `"Pop smoke"` (smokepop pack, drafted wearer); `"Drop <name>"` puts down a carried pawn. Gene abilities show **only on drafted pawns** (`hands.brief()` drafts for a moment to list them). `"Fire spew"`: range 7.9, targets a pawn, a building or a cell; ~40 ticks to cast; the cast replaces the pawn's current order [obs 2026-10-05] |
| `manage_gear` | `id, op (drop/equip/wear/force/unforce), item` | `itemId, ordered` | `item` = ThingID or **defName** (a label like "Autopistol" is rejected; `rca.game.weapons.weapon_def()` maps a gear label to a defName). `drop` is instant, also while paused, and returns the dropped `itemId`; `equip` with that id is a walk-over job that runs when time moves and is **cancelled by drafting** [obs 2026-10-05] |
| `say` | `text` | – | On-screen message panel (standalone agent only) |

`order_pawn` option label formats seen [log]:
- `Go here`
- `Auto attack (AI): <target short label>` (e.g. `pikeman`, a raider's nickname)
- `Fire at <target>`; when disabled: `Fire at <target>: Cannot hit target` or `...: Out of range`
- `Melee attack <target>`
- On a downed colonist: `Rescue <name>`, `Carry <name>`, `Tend <name> (without medicine)`, `Strip <name>`,
  `Try to arrest <name> (100% chance)`
  In the bed-less arenas `Rescue` is disabled and **`Carry <name>` is enabled**: executing it makes a
  drafted pawn pick the victim up and carry it under later `Go here` orders until `Drop <name>`
  [obs 2026-10-03; rca/tactical/squad.py].
- On a raider: `Fire at <name>`, `Melee attack <name>` (the way to send a knife at a shooter or tie a
  grenadier up in melee: throwers can't throw in melee); on a **downed** raider `Melee attack <name>
  to death` (finishing), `Carry <name>`, `Strip <name>`, `Tend <name>`. On a downed squadmate
  `Carry <name>`, then `Go here` walks the carrier with it [obs 2026-10-05]. The carrier's job reads
  `carrying <name>` already while it walks to the victim: a `Go here` before the victim's own job
  reads `being carried by …` cancels the carry (twice in rand_011, Claude's game) [obs 2026-10-05].
- `Cannot go here: No path` for a cell behind a wall: break the wall first (verb gizmo above).
- Disabled options keep their text with a reason, e.g.
  `Cannot rescue: No reachable, un-reserved non-prisoner bed in safe temperature.` (no beds in the arenas),
  `Cannot tend X: Will never do doctoring`, `Cannot capture: ...`.
- **Match labels by substring and skip `disabled`.** The old v1 focus code matched "rescue" inside
  "Cannot rescue: ..." and clicked it 41 times (exec_v1.log).

### Time

| Tool | Arguments | Returns | Quirks |
|---|---|---|---|
| `wait_for_event` | `maxGameTicks, maxSeconds, pause="always", force=True` | `_notifications[]`, `cause`, `ticksWaited`, `_delta` | Advances game time and pauses again afterwards. **15-tick quanta**: a 6-tick request advanced 14–16 ticks (hazards.md), 300-tick requests advanced 300–316 [obs]. A letter or notable message, or `threatAppeared`/`threatsCleared`, **ends the wait early**, so read the clock from `get_status`. **`force`** (tool schema): bypasses the crisis cap; without it a wait that starts with hostiles on the map, fire in the home area or a dying colonist is capped at 2500 ticks. `_notifications` carry the game's messages and letters (`{kind, text, label}`); raid fled/satisfied messages are read from here. Also returns `event, cause, ticksWaited, time` and `pausedAfter` (what really happened: a mod setting can override `pause`); `crisisCap` says why a wait was capped. **`_delta`**: `newItems/removedItems`, `newBuildings/removedBuildings` (`[{def, label, count}]`, **no cells**), `pawnDamage`; keys absent when nothing changed. Verified 2026-10-03: a debug bomb on a ruin wall gave `removedBuildings: [{def: Wall, count: 2}]`; 31,500 ticks of forest fire (trees burning down to stumps, some destroyed) gave **no** `_delta` at all: plants are not reported |
| `set_speed` | `action="pause"` | – | Always pause before teleports and saves: teleport misses walking pawns [obs]. Only `pause`/`unpause`: no speed setting; to advance a fixed number of ticks use `wait_for_event` (`rm.wait(ticks)`), which is how Claude plays turn by turn (tools/hands.py) |

### Game lifecycle

| Tool | Arguments | Returns | Quirks |
|---|---|---|---|
| `load_game` | `name, confirm=True` | `ok`/`error` | Returns before the map is up. See the ready wait in PROCEDURES.md. Fails with `Load failed: Object reference not set...` after many loads [log] |
| `save_game` | `name, overwrite=True` | `ok` | Pause first |
| `dev_mode` | `devMode` bool, `godMode` bool | – | God mode makes `build` instant and free. Turn both off before an episode (the agent must not have them) |
| `build` | `def, stuff?, minX, minZ, maxX, maxZ, fill="filled"` | `rejected, reasons, failedCells` | Used with god mode for the fort walls (`Wall`, `BlocksGranite`) and `Sandbags` |
| `create_world` | `coverage, rainfall, temperature, population, pollution` | – | World generation takes a while: poll `game_setup_status` |
| `find_world_tiles` | `biome, hilliness, coastal, river, tempMin, tempMax, limit` | `tiles[]` of `{tile}` | |
| `select_starting_site` | `tile`, `confirm` | `surroundings`: `nearbyObjects`, `biomes[]` of `{biome}` | Without `confirm` it only previews |
| `choose_ideoligion` | `mode="classic"` | | |
| `edit_starting_pawn` | `action="rename", index, first, nick, last` | | |
| `select_storyteller` | `storyteller, difficulty, reloadAnytime` (all required) | | **New-game page only.** No tool changes the difficulty of a loaded game; a save stores it as `<difficulty>Peaceful</difficulty>` in its storyteller block (conversion: PROCEDURES §1b). Refused to agents (§6) |
| `start_game` | – | | |

## 3. Debug menu (`debug_menu`)

Needs `dev_mode(devMode=True)`. Actions:

| Action | Arguments | Meaning |
|---|---|---|
| `run` | `path`, optional `tab`, `value` | Open an entry. Returns `optionList.options` if it asks for choices, or `armedTool` if it waits for map clicks |
| `pick` | `option` (exact label) | Choose from the open option list |
| `click` | `x, z` or `cells="x,z;x,z;..."` | Click the armed tool on one cell or several cells. `Clear area (rect)` takes its two corners as `cells="x0,z0;x1,z1"` |
| `close` | – | Close the menu. Do it before saving and before handing the game to an agent |

Every reply has `ok`, and on failure `error`. It may also carry `_notifications` and `log[]`
(`{text}` lines of the game log).

**Rules (all learned by failure):**
1. **Chains break on any other call.** An open option list closes if any other tool is called in
   the middle of a chain, so issue all `pick`s back to back [code].
2. **Armed tools disarm on any other call.** Look things up (pawn positions) *before* `run`, never
   between `run` and `click` [code].
3. **Paths are bare entry labels** with no category prefix (`"T: Teleport"`, not `"Pawns/T: Teleport"`) [code].
4. **Settings tab:** `run(tab="settings", path="Never Force Normal Speed", value=True)` [code].
5. **Submenu syntax:** `"Spawn Pawn... > Grenadier_Destructive"` (entry `>` PawnKindDef) [code].
6. **Option label formats** [code]:
   - a faction is `"<name> (<FactionDef>)"`, matched by its `(<FactionDef>)` suffix;
   - a label ending in `[NO]` is unusable, so never pick it;
   - points are `"<N> points"`: pick the nearest N;
   - strategy and arrival use def names (`ImmediateAttack`, `ImmediateAttackSmart`, `EdgeWalkIn`,
     `EdgeWalkInGroups`, `CenterDrop`);
   - trailing extras (age, ...) are answered with `-Random-`.
7. **Teleport is 3 calls:** `run("T: Teleport")`, `click(pawn cell)`, `click(destination)`. The
   first click sometimes misses (the pawn is walking, or another pawn stands on the same cell):
   check that the reply to the first click still has `armedTool`, then **verify the position with
   `get_pawn` and retry** (up to 4–5 rounds) [code].
8. **Vanilla float menus vanish without the real mouse.** `Set Faction Rect` and the planet page's
   `Add...` faction menu close unless the physical mouse is over them. So squads are converted with
   `T: Recruit`, and factions are added by hand [obs].
9. **Silent failure of "Execute raid with faction...":** the reply looks fine but nothing spawns.
   Detection: no `_notifications` entry with `kind == "letter"` **and** a `log[]` line containing
   `"empty collection"` (the game found no usable strategy or arrival). Independently, always diff
   hostiles before and after the raid; "spawned nobody" is a failure [code, log].

Entries used: `Execute raid with specifics...`, `Execute raid with faction...`, `Spawn Pawn... > <Kind>`,
`T: Recruit`, `T: Teleport`, `T: Destroy`, `Clear area (rect)`, `Clear All Fog`,
`Destroy factionless animals`, `Destroy player animals`, `Destroy non-colonists` (about 1 s),
settings `Never Force Normal Speed`. Probes only: `T: Attach Fire` (map tool, `cells` works),
`Explosion... > Bomb|Flame|...` (map tools), `T: Damage Until Down` (GAME_FACTS §7). `action="list"` with
`search` finds entries.

Unused tools that may help later: `get_alerts`, `read_debug_log` (game log, e.g. to spot a
NullReferenceException streak), `get_map` (coarse whole-map ascii), `screenshot`, `list_wildlife`.

## 4. Known failure modes

| Symptom | When | Handling |
|---|---|---|
| `NullReferenceException` from `get_status` / `load_game` ("RimMolt tool failed on main thread") | Right after loads; frequency grows after about 100+ loads in one session. 29 failed episode attempts across all logs [log] | Retry the episode once. Treat repeated errors as a sign the game is about to crash |
| Native crash (`Verse.SectionLayer_Sand:Regenerate` in `Map.FinalizeInit` while loading) | About 150 loads in one session (theme_report) | Restart RimWorld every ~100 episodes; watchdog (PROCEDURES.md) |
| `ConnectionRefusedError` | Game process gone (57 failed episode attempts across logs) [log] | Watchdog relaunch; `--resume` |
| `largeOutput` without `things` | `list_things` without `confirm=True` and many results | Always pass `confirm=True` |
| Empty `order_pawn` options; direct `Go here` → `{ok: false, error: "No order matched 'Go here'.", available: []}` | Undrafted pawn, including one the game undrafted when it went down and that stood up again [obs 2026-10-03]. Occupied, impassable and far cells still accept `Go here` (the game picks a cell nearby) | Draft first; rca re-drafts pawns that were downed and retries once on this error |
| Planet page `Add...` menu closes | Any scripted click | Manual faction edit |

## 5. RimMolt's own messages (strings we match)

- `RimMolt tool failed on main thread: <Exception>: <message>`: a tool failed on the game thread.
- `Load failed: <message>` in `load_game` errors.
- `largeOutput` notice from `list_things` (see above). Its exact text is UNVERIFIED; detect it by
  the missing `things` key.
- `tool '<name>' is not available to agents` is *our* sandbox message, not RimMolt's.

## 6. Agent sandbox

Agents get a wrapper client that refuses these tools (it raises before sending):
`dev_mode, debug_menu, load_game, save_game, return_to_title, main_menu, set_speed, wait_for_event,
select_scenario, select_storyteller, create_world, select_starting_site, choose_ideoligion,
edit_ideoligion, edit_starting_pawn, start_game, reform_ideoligion, rename_pawn`.
The harness owns time, saves and debug. Everything else (observe, draft, order, do_thing_action,
get_area, ...) is allowed. See EVAL_SPEC.md §1.
