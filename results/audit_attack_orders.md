# Attack-order cadence audit (2026-10-06)

The user noticed that our code gives attack orders far more often than a player. A player orders
an attack only to change target. This file checks that against the code and the traces.

Method:
- Three readers went through `tools/hands.py` and Claude's per-battle controllers (session
  scratchpad, plus the committed `results/cases/journals/rand_118_mouth_loop.py` and
  `rand_128_kite_loop.py`), the agents' micro layer (`rca/micro/`), and the agents' upper layers
  and harness (`rca/tactical/`, `rca/strategic/`, `rca/eval/`).
- A skeptic re-checked every finding against the code. 37 findings were made; 36 held, and one
  was re-rated higher (room.py).
- Run counts come from the traces: an "attacking X" run is the polls in a row whose job names the
  same target.

## Measured in the game

**Same target, ordered again (rand_227 map, autopistols).**
- One shooter got "Fire at" once; the other got it again every 30 or every 10 ticks.
- Shots fired were equal in all four phases: 4/4, 6/6, 4/4 and 3/3, over 230–540 ticks.
- Long-aim weapons (bolt-action, greatbow) were not tested.

**Dummy targets (rand_227 map, 2026-10-06, no harness row).**
- Setup with the debug menu (dev mode, turned off afterwards). The raiders were killed. Two
  `Tribal_Farmer` pawns were spawned 10–16 cells in front of the six shooters and given:
  - Neanderthal, Tough, a painstopper and two peg legs;
  - `T: Toggle Movement`, and the faction set to a pirate faction;
  - a deep-water ring (2 cells wide) around them (the user's idea).
- Each way was run for 600 ticks, with a poll every 8 ticks. The dummies were healed when below
  70%. "Shots fired" and "Damage dealt" come from the pawn records.
- The max is ticks / (aim + cooldown).
- Warm-up (aim) times: autopistol 18 ticks, revolver 18 ticks, pump shotgun 54 ticks.

| way | orders | shots (max 38.4) | shotgun (max 4.7) |
|---|---|---|---|
| no order (fire at will) | 0 | 39 | 5 |
| one "Fire at" each | 6 | 39 | 5 |
| same target again every 24 ticks | 156 | 39 | 5 |
| the other dummy every 60 ticks | 60 | 36 | 5 |
| the other dummy every 24 ticks | 156 | 31 | **0** |
| the other dummy every 8 ticks | 456 | **0** | 0 |
| `Keeper.assign` (run 1) | 6 | 41 | 5 |
| `Keeper.assign` (run 2) | 6 | 39 | 5 |

- A switch restarts the aim; the cooldown carries on. A pawn switched faster than its
  weapon's aim time never fires.
- Its job still reads "attacking <name>" all the time: only "Shots fired" shows the loss.
- Repeating the same target costs nothing (as in the autopistol test above).
- In both runs, `assign` gave one order per shooter and split them three and three.
- Damage per run (66–134) swung with the dice more than with the ordering, apart from the
  8-tick switch.

**Hold fire (same dummies, Barr and Pentaryl teleported 2 cells from each).**
- Fire at will kept shooting: 18 shots in 300 ticks. No hit on ours in that sample.
- `assign` found nothing worth shooting (friendly-fire risk 1 for every shooter):
  - The first version stopped a shooter with a Go here on its own cell. The float menu does not
    offer that ("No order matched 'Go here'"), so the shooter kept firing on its order.
  - Now the order is ended (undraft and draft again, `hands.stop`) and Fire at will is turned off
    after it, because drafting turns it back on.
  - Result: the six shooters were ordered onto a dummy, then stopped at the first step (tick 8):
    0 shots in 300 ticks.
  - After the two were teleported away, the same Keeper ordered targets again, three and three,
    and Fire at will was back on. 20 shots in 300 ticks (max ~20).
- No failed stop shows in the rand_227 `assign` re-measure's output: the old branch did not run
  there.

**Wall (rand_164 map, `Command_VerbTarget`).**
- One swing per pawn (11 damage), then nothing for 450 ticks. This held whether the order was
  given once, again every 90 ticks, or after the pawn stepped away and back.
- The float menu on a wall is empty.

## What the audit found

The costly pattern is **switching**, not repeating: a pawn is moved A → B → A, and each switch
starts a new aim or swing.

| where | what makes it switch | measured in the trace |
|---|---|---|
| Claude: `gun227.py`, `duel150.py`, `duel.py` | stall rule ("Shots fired" unchanged for 3 steps = 18–24 ticks, shorter than an aim + cooldown cycle). Priority targets in range of the squad but out of the shooter's own range, so "Fire at" is disabled and it falls through to another raider every step | rand_227: 663 of 679 attack runs ended in a switch, median run 16 ticks. rand_150: Lover (bolt-action) went Lawman ↔ Paul ~30 times and fired 5 shots in the fight |
| Claude: `focus190.py` (bows) | "stalled" = no new shot in one 15-tick step | rand_190: 77 of 80 runs ended in a switch, median 15 ticks; Bee switched 40 times |
| Claude: `pocket.py`, `mouth2.py` / `rand_118_mouth_loop.py` | stall rule; nearest-raider and distance-to-mouth orders flip | rand_179: median run 134 ticks (old 15–30-tick waits) |
| Claude: `focus164.py`, `mark23b.py`, `mark190.py`, `hall164.py` | a "Go here" to a touch cell replaces a melee job that was still chasing, then the melee order again; two raiders in reach give alternating orders | rand_164 attempt 1: median melee run 34 ticks; rand_023 attempt 3: 15 melee → moving → melee cycles |
| Claude: `room.py` | a kidnap-response order followed in the same step by a "Go here" back to the cell (stale job text), then undraft/redraft | (rand_115) |
| Claude: `hands.guard(keep=())` (gun227, duel150, duel) | a grenade sidestep "Go here" cancels a shot; nothing resumes it | – |
| Agents: `rca/tactical/focus.py` | job-text "idle" test re-orders every 120 ticks, plus a full re-target every 1200 | baseline_v2 doctrine attacking share 0.66 |
| Agents: `replay.py` breach step | a wall order every step, no gate (30 ticks in contact) | rand_127 v2: 62 breach hits, wall never broken in 8536 ticks |
| Agents: `turtle.py`, `kite.py`, `close.py`, `spread.py` | nearest-raider flips re-ordered every 30-tick step | – |
| Low: `amove.py`, `thrower_step`, `hands.fire/melee` themselves | order only on death or change | – |

The agents are the frozen baseline: listed here, not changed.

## Not covered
`legacy/` and `.worktrees/human/`: the skeptic noted the same 120-tick idle re-order in
`legacy/combat_agent.py`.

## Re-measures with the fix

| problem | first run | re-measure (`hands.Keeper`) | what changed |
|---|---|---|---|
| rand_227 | 19.4, repelled. Ranged runs 679, median 8 ticks, 665 switches | **73.8, squad down**. Ranged runs 16, median 834 ticks, 8 switches | The switching was gone, but the shooters stayed on the priority raider at their range edge (Lynx, 21–23 cells) while the melee arrivals fought the knives at the line. Nothing re-ranked targets when the threat changed |

| rand_227 | (as above) | **86.6, pyrrhic** with `Keeper.assign` (expected damage, spread, focus weight, 1.25× switch, friendly-fire radii). Ranged runs 30, median 335 ticks, 20 switches | The melee arrivals died 300–1000 ticks earlier than in either other run. Two of three deaths came while the rifles held out of reach before a rule-timed close-in (1400 ticks after the arrivals died; by hand in attempt 1, ~100 ticks after) |

| rand_150 | 36.4, repelled, 2 dead. Lover (bolt-action, aim 102 ticks) 5 shots all fight | **6.4, repelled, none lost or downed** with `Keeper.assign` (after the hold-fire fix). Lover 12 shots, 134 damage; damage dealt ≥405 → 536 | The same plan and line. Lawman (the raid's best pistol, weight 1.5) died at t2842; in the first play he lived past t5224. The raid's knives died 4–6 cells out, so our knives never went out and there was no rush |

Each row is one draw.

So keeping a target is not enough. A player re-targets when the threat picture changes (the
user: an order only "when I want to change target"); a re-target rule is needed before more
re-measures.
