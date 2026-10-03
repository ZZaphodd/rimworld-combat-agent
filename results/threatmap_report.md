# Threat heatmap + reflex v3

Goal: a pawn that flees a dangerous cell must not walk (or be walked by RimMolt's Auto attack)
straight back into it. The trigger was reflex v2 on theme_pirate_grenadier: molotov-fire step-outs
and rocket-spacing nudges broke Auto attack, Auto attack re-chose the same cover, and losses rose
(aggressive 3.2 → 4.6, turtle 3.2 → 5.4 per episode; `reflex_report.md`).

Raw rows: `results/threatmap_check.jsonl` (135 episodes). Batches: `threatmap_check.sh` (reflex v2 and
v3a, log `threatmap_check.log`) and `threatmap_check_v3b.sh` (v3b, log `threatmap_check_v3b.log`).
Tables: `python3 threatmap_analysis.py`.

## Verdict (short)

- **The map does what it was built for, mechanically.** Time on high-hazard cells fell 2–9x
  everywhere (for example, aggressive on frag_check went from 72% to 10%, and on the grenadier theme
  from 31% to 11–13%). Per pawn-tick, returns to danger fell for aggressive (grenadier 1.25 → 0.46 per
  1000 pawn-ticks) and spread (0.25 → 0.15). On frag_check, frag hits fell from 2–5 per 10 episodes
  to 0–1. Doctrines really hand positioning to the map inside threat areas: map:Auto-attack steps are
  about 2:1 for aggressive, and v2 is 0:all.
- **It did not reduce losses on theme_pirate_grenadier.** v2 → v3b lost/ep: aggressive
  3.4 → 3.2 (wins 2 → 1 of 5), spread 0.8 → 1.6 (wins 5 → 3; two raids left with captives), turtle
  2.6 → 3.4 (wins 1 → 2). The v2 rows here differ a lot from the earlier v2 rows in
  `reflex_check.jsonl` (aggressive 4.6, turtle 5.4). Pooled over both v2 sets (n=10): aggressive
  4.0, spread 1.1, turtle 4.0. Against those, v3 (3a+3b, n=10) gives aggressive 3.4, spread 1.8 and
  turtle 3.8. With n=5 and a per-episode SD of 1.5–2.4 deaths, none of these differences is
  significant. Spread is the only doctrine where v3 looks worse in both batches.
- **Cost: fights take 2–5x longer.** On frag_check, pawns now stay out of the 13-cell throw reach and
  shoot from 25+ cells. The raiders mostly stop throwing (frags seen fell to ~0) and it takes 2200–4500
  ticks instead of 600–800 to clear them, sometimes with a raider escaping (score 150 instead of 200,
  still a win). Wall time per episode went from 7–8 s to 20–38 s (frag_check) and from 32–54 s to
  47–87 s (grenadier).
- **Turtle returns to danger rose versus v2** (grenadier 2.0 → 13.2 per episode, frag_check
  2.6 → 5.9). v2 turtle almost never moved, so it had nothing to return to. On the grenadier theme,
  most v3b turtle returns come after reflex moves (39) or the doctrine's own slot walks ('other', 26),
  not after Auto attack (1). On frag_check, Auto attack during the sally leads (31 of 59). Per
  pawn-tick, frag_check turtle is still lower than v2 (0.29 → 0.20).
- **Recommendation for the 210-run matrix:** don't adopt v3 as the default yet. If it is used,
  use it for aggressive, where it improves every danger KPI and is loss-neutral to slightly better.
  Keep spread on v2. Shorten engagements first (see open issues).

## 1. Code state found / what changed in this session

Found on disk, complete and consistent with the spec: `threatmap.py`, the `HeatReflexes` (v3)
class in `reflexes.py`, v3 hooks in `eval.py` (B1), `doctrines.py` (Spread) and `hold_agent.py`
(turtle), and `threatmap_analysis.py`. The validation batch was **still running** (it had survived
the host session) and was left to finish. It produced the v2 rows and the v3a rows.

Fixes and additions in this session:
1. **Hysteresis neighbourhood** (`reflexes.py`). v3a forbade the exact fled cell, plus only those
   neighbours that were ≥ LOW at flight time, and released each cell on its own hazard. A pawn could
   therefore settle next to a still-hot fled cell, which the KPI counts as a return (d ≤ 1.5). Now
   the fled cell and its 8 neighbours are forbidden until the fled cell's hazard < LOW
   (`HeatReflexes.forbidden()`; Spread uses it too). This was applied before the grenadier v3a block
   started, so the frag_check v3a rows predate it and the grenadier v3a rows have it.
2. **v3b: the rocket clumping term no longer triggers moves** (`reflexes.py`, move gate). v3a made 500
   clump-driven "rocket" moves in 5 aggressive grenadier episodes (100 per episode), which are the v2
   nudges by another name. In v3b, clumping still scores candidate cells (reflex, placement, turtle
   slots, spread step-outs) but never moves a pawn by itself. Rocket moves dropped to 36 (aggressive),
   7 (spread) and 0 (turtle) over 5 episodes; the remaining ones are moves triggered by throw or fire
   whose dominant component at the cell was rocket. Agent versions bumped for v3b:
   b1 3→4, spread 3→4, turtle 6→7 (`versions = {2: …, 3: …}`), plus `rx_revision` in the KPIs.
3. **Turtle initial slot moves respect the map.** At plan and re-plan time, slots are now chosen
   through `_safe_slot` (v2 is unchanged because `slot_ok` is always true there).
4. **Return attribution KPI**: `rx_returns_{auto,map,reflex,other}` records who positioned the
   pawn on the step before each return (`DangerKPI.events`).
5. **Bug: big fires broke the observe step.** `list_things(defName="Fire")` returns
   `largeOutput` with no `things` key once a fire is large (65 fire things on the current map already
   trip it). This cost 37 agent steps in 2 v3b grenadier episodes (aggressive run 1: 9 steps; spread
   run 3: 28 steps; both lost 1 pawn). It never happened in the v2/v3a rows. Fixed afterwards with
   `confirm=True` on the projectile and fire queries. Those two rows were **not** re-run.

## 2. Heatmap design (`threatmap.py`)

threat(cell) = hazard + exposure + cover, in "how bad is standing here" units. HIGH = 3 is the
"dangerous" watermark and LOW = 1 the "safe again" watermark. ELEVATED = 1.5 is where doctrines stop
using Auto attack.

| component | weight | where |
|---|---|---|
| resting frag | 10 inside d ≤ 1.9 (measured blast), 5 out to 2.5 | until its fuse ends (first sighting − half step + 90 ticks); not remembered |
| grenade/molotov throw zone | 3.0 (= HIGH) | ≤ 12.9 + 2 cells (a raider walks ~2.4 cells per 30-tick step), then tapered to 0 over 3 cells; ×0.3 without LOS from the thrower |
| rocket carrier (doomsday / triple) | 0.5 (low) | within 36 cells |
| clumping (with a carrier in reach) | 0.6 per squadmate (or reserved destination) within 3 cells | per pawn; scores cells only (v3b) |
| fire | 6 on a burning cell, 1.5 adjacent | |
| exposure | 0.35 per live raider with the cell in weapon range and LOS | |
| cover | −0.8 wall/rock, −0.3 tree, next to the cell on the side facing the 3 nearest raiders | sandbags don't render in `get_area` ascii |

- **Memory/decay:** the pawn-independent hazard (throw, rocket base, fire) of every queried cell is
  remembered and decays with a half-life of 240 ticks. threat uses max(now, remembered). A throw zone
  the thrower has left stays above LOW for about 380 ticks. Frags are exact and not remembered.
- **Bounded box:** the squad's bounding box + 12 cells (max 90 per side). Terrain is fetched
  lazily in 50×50 `get_area` tiles out to 40 cells beyond the box and cached per save for the whole
  process, with a blocker prefix sum that makes LOS on open ground O(1). Cells are evaluated lazily
  and memoised per step, so only cells somebody queries cost anything.
- **Queries:** `threat(cell, pid)`, `hazard(cell, pid)`, `best_cell_near(pid, p, radius,
  must_see=raider, rng, forbid, taken, budget)` (BFS over passable cells; score = −threat + fire
  value (0.5 per raider we can shoot from there, cap 3, +1 if must_see is visible) − 0.08 × walk),
  `local_hazard`, `dominant`, `frag_deadline`.
- **Cost** (wall time inside map code only, per decision step, real episodes):

| config | map ms/step (max) | cells evaluated/step | whole agent step (think) |
|---|---|---|---|
| v3, aggressive | 19–21 (max 161) | 510–630 | 165–185 ms |
| v3, spread | 9–12 (max 82) | 350–500 | 140–175 ms |
| v3, turtle | 5–16 (max 55) | 130–340 | 160–210 ms |
| v2 (passive: feed + KPIs) | 0–8, but 29–65 on frag_check aggressive/spread | 9–15 | 135–225 ms |

  So the map adds roughly 5–20 ms to a 150–200 ms agent step. The game calls dominate. A synthetic
  benchmark (5 pawns, 5 raiders, both searches per pawn per step) runs at 45 ms/step. Open: v2
  frag_check aggressive rows show one ~500–800 ms spike in every episode. It does not reproduce
  offline (0.6 ms/step with the v2 call pattern) and does not appear in v3. It is probably wall-clock
  noise in this timer (the eval process runs niced next to the game), not map work.

## 3. Reflex v3 rule, hysteresis, thresholds (`reflexes.py: HeatReflexes`)

- **Gate (v3b):** hazard(here) without rockets (no rocket base, no clumping) must reach the doctrine
  threshold.
- **Move iff** threat(here) − threat(best) > threshold + move_cost. The best cell comes from
  `best_cell_near` within 8 steps. It excludes forbidden cells and cells taken by or reserved for
  squadmates, and it only includes cells the pawn reaches before the dominant threat lands: with a
  resting frag over it, 15 + walk / 0.07 ticks must fit into the remaining fuse.
  move_cost = 0.5 + 0.5 if the pawn is shooting + the fire value it gives up (raiders it can shoot
  from here but not from there).
- **Viscosity thresholds (threat units, `VISCOSITY_V3`):** aggressive/close 0.5, spread/focus/kite
  1.0, turtle 3.0. Turtle leaves its line for a frag (5–10) or fire under it (6), not for a throw zone
  (3), adjacent fire (1.5) or clumping; its slots handle those. The v2 severity thresholds
  (`VISCOSITY`) are kept for v2.
- **After a move** the reflex owns the pawn until it arrives (≤ 150 ticks), or until the frag blows
  (+10) if that is later. It is released early if its destination becomes ≥ HIGH.
- **Hysteresis:** the fled cell becomes a forbidden centre for that pawn. That cell and its 8
  neighbours are excluded from the reflex search, map placement, turtle slot choice/return and
  spread step-outs until the centre's (remembered, decaying) hazard < LOW (1.0).
- **No rocket nudges** (v3b: clumping only shapes where pawns go). Rocket carriers are handled by
  targeting instead: `threat_target` = the nearest thrower we can hit (range + LOS), else the
  nearest rocket carrier in reach.
- **Doctrine positioning** (`place`, used by aggressive, spread and turtle when sallying or with
  raiders inside): the area is elevated when hazard ≥ 1.5 on the pawn's cell or 4 cells around it
  (rocket base excluded), or when a fled cell is within 6. If it is not elevated, the pawn gets Auto
  attack as before. If it is, the map picks a cell within 6 steps that sees the target
  (Go here), unless staying is within threshold + 0.5. From there the pawn fires: Fire at the
  thrower or carrier if it can hit one, else fire at will. If no cell is below HIGH, the doctrine
  fallback applies. Aggressive and turtle use 'kill' (Fire at the nearest thrower/carrier we can
  hit, else step back). Spread uses 'back': step back up to 12 cells, out of the zone, keeping the
  target in weapon range (rifles 25–31 vs throw 12.9), else shoot it. Turtle line pawns on their
  slot Fire at throwers/carriers in reach (`focus_danger`). Slots that are ≥ HIGH or forbidden are
  swapped for a cell within 4 that is at least 1 lower (`better_slot`).

## 4. Validation (adaptive 30/120@40 cycle; frag_check n=10, pirate_grenadier n=5)

Returns to danger = returns to a fled cell (back within 1.5 of a cell the pawn left while it was
≥ HIGH, within 600 ticks, while that cell is still ≥ LOW) + known entries (the pawn moved onto a cell
that was ≥ HIGH and above its old cell on the previous step's map). High-threat time = pawn-ticks on
cells with hazard ≥ HIGH. A throw zone with LOS counts as HIGH, so every v2 pawn within ~15 cells of
a grenadier counts.
v2 = b1 v2 / spread v2 / turtle v5 run fresh in this batch. The old-version agents still run
(`--reflex-version 2` picks them). v3a = first map version (exact-cell hysteresis on frag_check;
clumping in the gate). v3b = final code.

| scenario | doctrine | rx (agent v) | n | wins | lost/ep | hp lost/ep | returns to danger/ep (fled + known entries) | raw high entries/ep | time in high threat | moves/ep (reflex / map / nudge) | Auto attack : map steps | frags in blast / escaped / stayed | frag hit entries | ticks/ep | wall s/ep |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| frag_check | aggressive | v2 (2) | 10 | 10 | 0.0 | 31 | 5.4 (1.1 + 4.3) | 11.2 | 72.2% | 6 (6 / 0 / 0) | 2089:0 | 7 / 4 / 3 | 3 | 593 | 7 |
| frag_check | aggressive | v3a (3) | 10 | 10 | 0.0 | 0 | 1.6 (0.5 + 1.1) | 15.2 | 9.5% | 182 (140 / 43 / 0) | 1151:3591 | 0 / 0 / 0 | 0 | 3322 | 34 |
| frag_check | aggressive | v3b (4) | 10 | 10 | 0.0 | 0 | 3.2 (1.3 + 1.9) | 15.4 | 10.4% | 182 (140 / 42 / 0) | 1447:3734 | 0 / 0 / 0 | 0 | 3387 | 36 |
| frag_check | spread | v2 (2) | 10 | 10 | 0.1 | 47 | 3.5 (0.4 + 3.1) | 6.3 | 47.6% | 10 (10 / 0 / 0) | 23:0 | 23 / 14 / 8 | 2 | 804 | 8 |
| frag_check | spread | v3a (3) | 10 | 10 | 0.0 | 4 | 1.3 (0.4 + 0.9) | 10.3 | 7.8% | 71 (68 / 3 / 0) | 99:243 | 0 / 0 / 0 | 0 | 3055 | 26 |
| frag_check | spread | v3b (4) | 10 | 10 | 0.0 | 0 | 0.8 (0.1 + 0.7) | 9.0 | 5.2% | 73 (69 / 4 / 0) | 237:287 | 0 / 0 / 0 | 0 | 4549 | 38 |
| frag_check | turtle | v2 (5) | 10 | 10 | 0.0 | 48 | 2.6 (0.9 + 1.7) | 5.7 | 60.5% | 5 (5 / 0 / 0) | 0:0 | 19 / 9 / 10 | 5 | 672 | 8 |
| frag_check | turtle | v3a (6) | 10 | 10 | 0.0 | 18 | 6.8 (4.1 + 2.7) | 6.6 | 18.2% | 27 (25 / 2 / 0) | 75:1724 | 25 / 19 / 6 | 0 | 3139 | 25 |
| frag_check | turtle | v3b (7) | 10 | 10 | 0.0 | 9 | 5.9 (3.3 + 2.6) | 5.7 | 23.9% | 23 (22 / 1 / 0) | 74:1322 | 15 / 11 / 4 | 1 | 2192 | 20 |
| pirate_grenadier | aggressive | v2 (2) | 5 | 2 | 3.4 | 709 | 49.8 (8.4 + 41.4) | 55.2 | 30.6% | 69 (40 / 0 / 29) | 2624:0 | 5 / 5 / 0 | 0 | 3871 | 35 |
| pirate_grenadier | aggressive | v3a (3) | 5 | 3 | 3.6 | 716 | 36.8 (5.0 + 31.8) | 59.4 | 10.8% | 239 (198 / 41 / 0) | 1352:1967 | 1 / 0 / 1 | 0 | 7485 | 69 |
| pirate_grenadier | aggressive | v3b (4) | 5 | 1 | 3.2 | 754 | 32.4 (3.6 + 28.8) | 52.6 | 12.6% | 215 (131 / 84 / 0) | 1501:2818 | 1 / 1 / 0 | 0 | 7940 | 76 |
| pirate_grenadier | spread | v2 (2) | 5 | 5 | 0.8 | 389 | 18.6 (4.6 + 14.0) | 16.2 | 9.8% | 16 (16 / 0 / 0) | 1711:0 | 5 / 2 / 3 | 1 | 6653 | 54 |
| pirate_grenadier | spread | v3a (3) | 5 | 5 | 2.0 | 444 | 17.8 (3.6 + 14.2) | 31.8 | 5.6% | 124 (108 / 16 / 0) | 1395:722 | 2 / 2 / 0 | 0 | 9368 | 87 |
| pirate_grenadier | spread | v3b (4) | 5 | 3 | 1.6 | 477 | 13.0 (1.6 + 11.4) | 23.8 | 4.8% | 95 (75 / 20 / 0) | 1276:870 | 2 / 1 / 1 | 1 | 8539 | 76 |
| pirate_grenadier | turtle | v2 (5) | 5 | 1 | 2.6 | 861 | 2.0 (0.2 + 1.8) | 2.0 | 17.6% | 4 (4 / 0 / 0) | 0:0 | 0 / 0 / 0 | 0 | 5328 | 32 |
| pirate_grenadier | turtle | v3a (6) | 5 | 1 | 4.2 | 912 | 20.0 (5.2 + 14.8) | 23.2 | 7.4% | 43 (43 / 1 / 0) | 36:223 | 0 / 0 / 0 | 0 | 7126 | 46 |
| pirate_grenadier | turtle | v3b (7) | 5 | 2 | 3.4 | 811 | 13.2 (1.4 + 11.8) | 17.8 | 6.1% | 23 (21 / 2 / 0) | 63:219 | 0 / 0 / 0 | 0 | 6862 | 47 |

Returns to danger per 1000 pawn-ticks (episodes differ 2–5x in length), and who positioned the pawn on the step before a return (only rows written after attribution was added):

```
  ('frag_check', 'b1', 2, 2): 0.69 /1000 pawn-ticks; by mode {'auto': 0, 'map': 0, 'reflex': 0, 'other': 0}
  ('frag_check', 'b1', 3, 3): 0.03 /1000 pawn-ticks; by mode {'auto': 0, 'map': 0, 'reflex': 0, 'other': 0}
  ('frag_check', 'b1', 3, 4): 0.07 /1000 pawn-ticks; by mode {'auto': 7, 'map': 4, 'reflex': 21, 'other': 0}
  ('frag_check', 'spread', 2, 2): 0.32 /1000 pawn-ticks; by mode {'auto': 0, 'map': 0, 'reflex': 0, 'other': 0}
  ('frag_check', 'spread', 3, 3): 0.03 /1000 pawn-ticks; by mode {'auto': 0, 'map': 0, 'reflex': 0, 'other': 0}
  ('frag_check', 'spread', 3, 4): 0.01 /1000 pawn-ticks; by mode {'auto': 0, 'map': 1, 'reflex': 6, 'other': 1}
  ('frag_check', 'turtle', 2, 5): 0.29 /1000 pawn-ticks; by mode {'auto': 0, 'map': 0, 'reflex': 0, 'other': 0}
  ('frag_check', 'turtle', 3, 6): 0.16 /1000 pawn-ticks; by mode {'auto': 0, 'map': 0, 'reflex': 0, 'other': 0}
  ('frag_check', 'turtle', 3, 7): 0.20 /1000 pawn-ticks; by mode {'auto': 31, 'map': 4, 'reflex': 8, 'other': 16}
  ('pirate_grenadier', 'b1', 2, 2): 1.25 /1000 pawn-ticks; by mode {'auto': 0, 'map': 0, 'reflex': 0, 'other': 0}
  ('pirate_grenadier', 'b1', 3, 3): 0.51 /1000 pawn-ticks; by mode {'auto': 19, 'map': 22, 'reflex': 143, 'other': 0}
  ('pirate_grenadier', 'b1', 3, 4): 0.46 /1000 pawn-ticks; by mode {'auto': 21, 'map': 61, 'reflex': 80, 'other': 0}
  ('pirate_grenadier', 'spread', 2, 2): 0.25 /1000 pawn-ticks; by mode {'auto': 0, 'map': 0, 'reflex': 0, 'other': 0}
  ('pirate_grenadier', 'spread', 3, 3): 0.17 /1000 pawn-ticks; by mode {'auto': 36, 'map': 5, 'reflex': 45, 'other': 3}
  ('pirate_grenadier', 'spread', 3, 4): 0.15 /1000 pawn-ticks; by mode {'auto': 10, 'map': 7, 'reflex': 42, 'other': 6}
  ('pirate_grenadier', 'turtle', 2, 5): 0.04 /1000 pawn-ticks; by mode {'auto': 0, 'map': 0, 'reflex': 0, 'other': 0}
  ('pirate_grenadier', 'turtle', 3, 6): 0.34 /1000 pawn-ticks; by mode {'auto': 1, 'map': 1, 'reflex': 57, 'other': 41}
  ('pirate_grenadier', 'turtle', 3, 7): 0.21 /1000 pawn-ticks; by mode {'auto': 1, 'map': 0, 'reflex': 39, 'other': 26}
```

Reflex v3 move kinds and fallbacks (sums over the batch; `forbidden_cells` counts forbidden cells in
v3a and fled centres, each worth 9 cells, in v3b):

```
  ('frag_check', 'b1', 3, 3): moves_frag=0 moves_throw=1399 moves_fire=0 moves_rocket=0 stays=1623 too_late=0 trapped=0 fire_at=770 fallback_kill=0 fallback_back=2 fallback_none=130 reslots=0 forbidden_cells=8823 ignored_viscous=2956
  ('frag_check', 'b1', 3, 4): moves_frag=0 moves_throw=1393 moves_fire=6 moves_rocket=0 stays=1507 too_late=0 trapped=0 fire_at=849 fallback_kill=0 fallback_back=1 fallback_none=126 reslots=0 forbidden_cells=1303 ignored_viscous=3682
  ('frag_check', 'spread', 3, 3): moves_frag=0 moves_throw=682 moves_fire=2 moves_rocket=0 stays=216 too_late=0 trapped=0 fire_at=41 fallback_kill=0 fallback_back=0 fallback_none=3 reslots=0 forbidden_cells=5152 ignored_viscous=2563
  ('frag_check', 'spread', 3, 4): moves_frag=0 moves_throw=692 moves_fire=1 moves_rocket=0 stays=216 too_late=0 trapped=0 fire_at=45 fallback_kill=0 fallback_back=1 fallback_none=12 reslots=0 forbidden_cells=647 ignored_viscous=5031
  ('frag_check', 'turtle', 3, 6): moves_frag=76 moves_throw=168 moves_fire=9 moves_rocket=0 stays=1762 too_late=12 trapped=0 fire_at=607 fallback_kill=117 fallback_back=1 fallback_none=10 reslots=318 forbidden_cells=1998 ignored_viscous=5217
  ('frag_check', 'turtle', 3, 7): moves_frag=36 moves_throw=181 moves_fire=8 moves_rocket=0 stays=1443 too_late=4 trapped=0 fire_at=592 fallback_kill=85 fallback_back=0 fallback_none=6 reslots=282 forbidden_cells=218 ignored_viscous=3554
  ('pirate_grenadier', 'b1', 3, 3): moves_frag=3 moves_throw=415 moves_fire=72 moves_rocket=500 stays=563 too_late=1 trapped=0 fire_at=278 fallback_kill=14 fallback_back=7 fallback_none=47 reslots=0 forbidden_cells=926 ignored_viscous=2912
  ('pirate_grenadier', 'b1', 3, 4): moves_frag=1 moves_throw=526 moves_fire=93 moves_rocket=36 stays=390 too_late=0 trapped=0 fire_at=345 fallback_kill=45 fallback_back=6 fallback_none=54 reslots=0 forbidden_cells=562 ignored_viscous=3033
  ('pirate_grenadier', 'spread', 3, 3): moves_frag=5 moves_throw=465 moves_fire=8 moves_rocket=61 stays=116 too_late=0 trapped=0 fire_at=108 fallback_kill=0 fallback_back=3 fallback_none=25 reslots=0 forbidden_cells=484 ignored_viscous=5342
  ('pirate_grenadier', 'spread', 3, 4): moves_frag=2 moves_throw=332 moves_fire=32 moves_rocket=7 stays=110 too_late=0 trapped=0 fire_at=127 fallback_kill=0 fallback_back=6 fallback_none=12 reslots=0 forbidden_cells=342 ignored_viscous=4055
  ('pirate_grenadier', 'turtle', 3, 6): moves_frag=0 moves_throw=100 moves_fire=25 moves_rocket=88 stays=39 too_late=0 trapped=0 fire_at=172 fallback_kill=9 fallback_back=0 fallback_none=2 reslots=113 forbidden_cells=200 ignored_viscous=2798
  ('pirate_grenadier', 'turtle', 3, 7): moves_frag=0 moves_throw=94 moves_fire=10 moves_rocket=0 stays=87 too_late=0 trapped=0 fire_at=185 fallback_kill=4 fallback_back=1 fallback_none=1 reslots=159 forbidden_cells=96 ignored_viscous=2335
```

For comparison, the earlier v2 rows (`reflex_check.jsonl`, n=5, same cycle) on the grenadier
theme were: aggressive 0/5 wins, 4.6 lost; spread 5/5, 1.4; turtle 0/5, 5.4. Cycle-only (no
reflex): aggressive 3/5, 3.2; spread 4/5, 0.6; turtle 0/5, 3.2.

## 5. Does throwing need line of sight?

**Yes, by the defs.** `Weapon_GrenadeFrag` and `Weapon_GrenadeMolotov`
(`Data/Core/Defs/ThingDefs_Misc/Weapons/RangedIndustrialGrenades.xml`) use `Verb_LaunchProjectile`
with range 12.9 and do not override `requireLineOfSight`. The defs that do not need LOS (mortars,
some turrets, a few abilities) set `<requireLineOfSight>false</requireLineOfSight>` explicitly,
which is consistent with the engine default being true. So a thrower needs the same LOS a rifleman
does, including leaning around corners. This was not measured in game. The map therefore cuts the
throw zone by LOS but keeps a 0.3 factor without LOS (≈ 0.9 < LOW): the thrower can step around the
obstacle within a step or two. A cheap in-game check if wanted: a grenadier behind a 1-wide wall
with a target 8 cells on the other side, and see whether he throws or repositions.

## 6. Open issues

- **Engagements are 2–5x longer** because the squad now holds outside the 13-cell throw reach.
  Against frag throwers that is free (0 losses either way on frag_check). Against rocket carriers
  (36 cells, undodgeable) a longer fight means more rocket volleys, and that probably offsets the
  gain on the grenadier theme. Next step: a time/exposure term (a "finish them" bias when our fire
  value is high, or priority focus on rocket carriers with every free gun), rather than more
  avoidance.
- **Aggressive still makes ~100–140 reflex throw moves per episode** (threshold 0.5 against a 3.0 throw
  zone). Every advancing grenadier pushes the line back. A per-pawn move cooldown, or a threshold
  ≥ 1.0 for throw-only hazard, should cut the churn. Not tried.
- **Spread looks worse under v3 on the grenadier theme in both batches** (2.0 and 1.6 lost vs
  0.8/1.4). Its own MIN_GAP step-outs and the map's moves add up (95–124 moves per episode vs 16).
  Consider spread = v2 + map hysteresis only.
- **Turtle returns on the grenadier theme are mostly reflex and doctrine slot walks**, not Auto attack. The KPI also
  counts a pawn walking *past* a fled cell en route (the position is sampled every step). A
  path-aware check (does the planned path cross a forbidden disc?) would separate real returns from
  transits.
- **"Known entries" dominate returns on the grenadier theme** (aggressive 28.8 per episode). Most
  are moves into a ≥ HIGH throw zone that has drifted onto the destination while the pawn walked, or
  transit cells. A throw zone at exactly HIGH makes this KPI sensitive. Consider W_THROW slightly
  below HIGH, with only throw + LOS + approach counted as high.
- n=5 on the grenadier theme; the two v2 batches already differ by up to 2.8 lost per episode. The
  loss comparisons above are not significant.
- The 2 v3b grenadier rows with observe errors (bug 5) were kept, not re-run.
- Map cost timer: unexplained once-per-episode spike in the v2 frag_check aggressive rows (§2).

## Files

`threatmap.py` (map + DangerKPI), `reflexes.py` (HeatReflexes v3/3b, `attach`), `eval.py`
(B1 v3/v4), `doctrines.py` (Spread v3/v4), `hold_agent.py` (turtle v6/v7), `threatmap_analysis.py`,
`results/threatmap_check.{sh,log,jsonl,done}`, `results/threatmap_check_v3b.{sh,log,done}`.
