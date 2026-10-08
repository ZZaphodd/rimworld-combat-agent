# Claude's battle loops for the v2 bases (2026-10-07/08), saved from the session scratchpad

These are the control loops Claude wrote while playing directly (`tools/hands.py`, PROCEDURES §16):
the Ithfunda 6× battles (p6, p7) and the 34 Cawalia staircase battles
(card `results/cases/cards/base2_caw_staircase.md`, journal
`results/cases/journals/base2_caw_staircase_claude_20261008.md`). They are kept as written during
play, as a record: battle constants are module-level globals that were set per battle (some with
`sed` between battles), nothing here has tests, and they speak RimMolt only. Promoting the useful
parts into `tools/` is separate work.

**The game is used for rimcockpit from 2026-10-08: run none of this without the user's word.**

## Use

The modules import each other in a chain, so import them from this folder:

```bash
cd results/cases/journals/base2_claude_loops && python3 - <<'EOF'
import pk
pk.NAMES = ["...", "..."]                    # the squad, set per battle
from pk import *
print(kite_arc(120, "N", maxt=4000, trig=30))
EOF
```

`p.py` and `swap.py` put the repo's `tools/` on the path themselves.

## Files

| file | what | used in |
|---|---|---|
| `p.py` | base helpers on top of hands: `tick`, `s()` compact view, `msgs`, `until`, `fight` (melee whoever is adjacent), `carry_out` (approach, Carry, walk, Drop), `watch`, `focus`, `hold` | Ithfunda; `carry_out` in Cawalia 10, 13, 14 |
| `p6.py`, `p7.py` | Ithfunda east-room loop; the rock/ground frag barrage | base2_ith_tribe_6x |
| `spectate.py` | watcher used while the user played (light reads, frames) | the user's games |
| `pc.py` | Cawalia basics: `T0` (41226471, the start tick of every Cawalia save), `lg`, `up`, `centroid`, `line`, `place`, `nearest`, `traps`, `kite` (step a line back) | from Cawalia 1 |
| `pc2.py` | `watchline`: stop on a raider close or one of ours hurt | 2 |
| `pc3.py` | `hold3`; **`fire_id(name, thing_id)`**: fire at a hostile by thing id (mech labels repeat; `hands.fire` is keyed by short name) | from 3 |
| `pc4.py` | `watch4`: melee-aware stop (weapon cache by id) | 4 |
| `pc5.py` | `watch5(team, close, low)`: the general watcher | from 5 |
| `pc6.py` | `focus_loop(order, keep)`: rifles (`RIFLES`) fire down a list of ids, a pawn within `keep` steps back `STEP` cells | 6, 9, 12, 13 |
| `pk.py` | **`kite_arc`**: the zigzag across a trap arc against melee raids; `NAMES`, `NORTH_Z`/`SOUTH_Z` (south arc 66/42, north arc 207/183), `group_cells`, `ours()` (skips broken pawns), `dirn` | 10 (buggy), 11, 24, 25, 26, 29 |
| `pl.py` | `leash`: lead slow mechs along waypoints (did not work: they closed while the rifles stood) | 13 |
| `pm.py` | `melee_fight`: stand and shoot point blank at the raider on the weakest pawn | 10 |
| `pz.py` | **`zone`**: kite-and-shoot with per-kind safe distances (`SAFE`: Centipede 29.5, Lancer 34, Centurion 34, Apocriton 46, …; `Pikeman` 0 = accept its fire) and 7-cell step-backs; rifles in `R` | 14, 17, 22, 28, 31, 34 |
| `room.py` | the block's east room cells (`ROOM`, `room_cells`), `food(name)`, **`feed(names, below)`**: order "Consume" on a survival meal (drafted pawns do not eat) | 28, 31, 34 |
| `swap.py` | `swap(pairs, maxt=1200)`: weapon swap that waits until both hold the new weapon before anyone is drafted (drafting cancels the walk; battle 23 lost two rifles that way) | from 24 |

## Known traps

- `kite_arc` re-orders a crossing only after the group has arrived (centroid within 4 of its cells) or
  400 ticks have passed. Battle 10 ran the earlier version, which re-sent the crossing every 20 ticks
  and turned the group back and forth inside the band (one dead).
- `pc6.focus_loop` stepped back every poll at first; that kept interrupting the rifles' aim (2–3 shots
  in 4,000 ticks in battle 12). `STEP = 8` and `pz.zone`'s 7-cell steps came after.
- A fire order given while a pawn is walking stops it there (battle 26: three pawns down mid-retreat).
- "Go here" is not offered for a blocked cell; `go()` prints `go fail` and the pawn stays put.
- Short names repeat (22 "Lancer"s): use thing ids (`fire_id`, `up()` entries), not `hands.ids()` for
  enemies.
