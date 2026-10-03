# RimMolt API: what we use and how it behaves

RimMolt is the RimWorld mod that exposes the game as MCP tools. This file is the spec a
client port is checked against. Evidence key: **[code]** = the old client relied on it and it
worked over hundreds of episodes; **[log]** = seen in run logs; **[obs]** = observed during
development; **UNVERIFIED** = assumed, never checked directly.

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
| `get_status` | – | `ticksGame`, `loaded` | Game time source for episodes. Throws NullReferenceException while a load is still settling [log] |
| `game_setup_status` | – | `stage` (`planet`, `starting_site`, ...), `programState` (`Playing` once a map runs) | Raises or times out while the world or map is generating: poll and swallow errors [code] |
| `list_colonists` | – | `colonists[]`: `id, name, downed, mentalState, incapableOf` (string, e.g. contains `Violent`), `job` (text), `health` (%), `inCaravan` | No positions: get them from `list_things` |
| `list_things` | `category` (`pawn`/`item`/`all`), `faction` (`player`/`hostile`), `defName`, `verbose=True`, `summary=True`, `confirm=True`, `limit` | `things[]`: `id, def, kind, label, x, z, downed, dead, targeting, category`; with `summary`: `groups[]` of `{def, count}` | **Output guard:** a large result comes back as a `largeOutput` notice with **no `things` key** unless `confirm=True`. 65 Fire things were enough to trip it (37 agent steps lost, threatmap_report §1.5), and census samples were lost to `KeyError 'things'` the same way [log]. Always pass `confirm=True`. `category="all"` on the forest map is flooded by plants: query projectile defs by name (hazards.md) |
| `get_pawn` | `id`, optional `tab` | Default: `name, x, z, weapon` (label, e.g. `Heavy SMG (good)`, `Biocoded heavy SMG (normal)`), `health, downed, dead, job`; `error` if the pawn is gone. Dead or carried-off pawns have no `x` | Tabs used: `health` → `hediffs[]` of `{label, part, permanent}`; `log` → `entries[]` of `{tick, text}` (battle log, short, and it vanishes with a dead pawn); `records` → `records[]` of `{record, value}` (we read `Kills`). Other tabs: UNVERIFIED |
| `get_area` | `minX, minZ, maxX, maxZ, render="ascii"` | `grid`: list of strings, **north row (max z) first**; also `legend` and `orientation` | One call is capped at about 55×55 cells, so tile in 50×50 [code]. Legend below. Other layers (`layer=roof/buildings/things...`) unused |
| `get_info_card` | `id`, or `x, z`, or `def` (+ `stuff`), or `stat` | `stats[]` of `{category, stats[{label, value}]}` | `def` takes **ThingDefs only** (`Unknown ThingDef: Mercenary_Gunner` for a PawnKindDef) [obs 2026-10-03]. A pawn's card has no combat power; see EVAL_SPEC §6 for where points come from |
| `inspect_thing` | `id` or `x, z` | `actions[]` with `toggle`, `active` for toggle gizmos | Used to read a drafted pawn's `Fire at will` state before toggling it (micro drill) |
| `list_fires` | – | `fireCount`, `bounds`, `fires[{x, z, size}]` | Not used by rca yet (we query `Fire` things); probe only |
| `get_world` | – | `factions[]`: `{def, relation}` | |
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
| `do_thing_action` | `id, label, targetId?` | `ok` | `label="Auto attack (AI)"` + `targetId`: RimMolt's own combat AI for that pawn. It picks its own cover cell and can't see our data (it walks pawns back into danger: threatmap_report). `label="Fire at will"` **toggles** a drafted pawn's fire-at-will (used to make the squad hold fire in measurements; the state is not read back, UNVERIFIED) |
| `say` | `text` | – | On-screen message panel (standalone agent only) |

`order_pawn` option label formats seen [log]:
- `Go here`
- `Auto attack (AI): <target short label>` (e.g. `pikeman`, a raider's nickname)
- `Fire at <target>`; when disabled: `Fire at <target>: Cannot hit target` or `...: Out of range`
- `Melee attack <target>`
- On a downed colonist: `Rescue <name>`, `Carry <name>`, `Tend <name> (without medicine)`, `Strip <name>`,
  `Try to arrest <name> (100% chance)`
- Disabled options keep their text with a reason, e.g.
  `Cannot rescue: No reachable, un-reserved non-prisoner bed in safe temperature.` (no beds in the arenas),
  `Cannot tend X: Will never do doctoring`, `Cannot capture: ...`.
- **Match labels by substring and skip `disabled`.** The old v1 focus code matched "rescue" inside
  "Cannot rescue: ..." and clicked it 41 times (exec_v1.log).

### Time

| Tool | Arguments | Returns | Quirks |
|---|---|---|---|
| `wait_for_event` | `maxGameTicks, maxSeconds, pause="always", force=True` | `_notifications[]`, `cause`, `ticksWaited`, `_delta` | Advances game time and pauses again afterwards. **15-tick quanta**: a 6-tick request advanced 14–16 ticks (hazards.md), 300-tick requests advanced 300–316 [obs]. A letter or notable message, or `threatAppeared`/`threatsCleared`, **ends the wait early**, so read the clock from `get_status`. **`force`** (tool schema): bypasses the crisis cap; without it a wait that starts with hostiles on the map, fire in the home area or a dying colonist is capped at 2500 ticks. `_notifications` carry the game's messages and letters (`{kind, text, label}`); raid fled/satisfied messages are read from here. **`_delta`**: `newItems/removedItems`, `newBuildings/removedBuildings` (`[{def, label, count}]`, **no cells**), `pawnDamage`; keys absent when nothing changed. Verified 2026-10-03: a debug bomb on a ruin wall gave `removedBuildings: [{def: Wall, count: 2}]`; 31,500 ticks of forest fire (trees burning down to stumps, some destroyed) gave **no** `_delta` at all: plants are not reported |
| `set_speed` | `action="pause"` | – | Always pause before teleports and saves: teleport misses walking pawns [obs] |

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
`Explosion... > Bomb|Flame|...` (map tools). `action="list"` with `search` finds entries.

## 4. Known failure modes

| Symptom | When | Handling |
|---|---|---|
| `NullReferenceException` from `get_status` / `load_game` ("RimMolt tool failed on main thread") | Right after loads; frequency grows after about 100+ loads in one session. 29 failed episode attempts across all logs [log] | Retry the episode once. Treat repeated errors as a sign the game is about to crash |
| Native crash (`Verse.SectionLayer_Sand:Regenerate` in `Map.FinalizeInit` while loading) | About 150 loads in one session (theme_report) | Restart RimWorld every ~100 episodes; watchdog (PROCEDURES.md) |
| `ConnectionRefusedError` | Game process gone (57 failed episode attempts across logs) [log] | Watchdog relaunch; `--resume` |
| `largeOutput` without `things` | `list_things` without `confirm=True` and many results | Always pass `confirm=True` |
| Empty `order_pawn` options | Undrafted pawn | Draft first |
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
