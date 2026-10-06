# base_ith_tribe_2x — Claude, 2026-10-06 (played alone) — civil outlanders vs 10 Neanderthal tribals, Ithfunda base — decisive

Trace `results/human/traces/base_ith_tribe_2x_claude_20261006-175528.jsonl.gz` · row
`results/human/play.jsonl` (player `claude`) · result: **decisive** (enemies_cleared t24014),
**0 lost, 0 downed, 0 permanent**, HP 120% · raiders: Goraxada, Orange, Donkey, Raven, Légua
dead at the door or in the corridor; Enmar, Scorpion, Komodo dead away from us (spike traps or
fire); Jaguar downed far east; Ñabaigo left by the west edge · **badness 4.8** (agent `turtle`
109.7, defeat: 2 dead, 6 downed; `results/base/ladder.jsonl`).
Sheet: `sheets/base_ith_tribe_2x_start.md` (cards base_ith_pirate_2x, rand_127, rand_164: the
east room door, the plug alone in the cell inside the doorway, guns 2+ cells back, and melee pawns
on the two diagonal cells).

Ticks below are the harness's (trace `t`); controller ticks printed in play were game ticks − 383,
harness t ≈ controller t − 21128890 (Goraxada's death: controller 21134140, last seen t5247).

## Card at the start

- Ours: 8 OutlanderCivil (shooting/melee): Graves 8/12 pump shotgun; Semyon 4/11 steel knife
  (Careful shooter); Phat 4/9 molotov (Tough); Wright 8/2 and El 7/0 (Bloodlust) autopistols;
  Vang 1/1 autopistol, flak vest and pants; Tina 1/1 bolt-action rifle, flak vest; Petra 3/1
  revolver. Start: the yard (114–122, 163–166). No loadout (no items in the base).
- Raid: 10 TribeRoughNeanderthal from the south edge (48–52, 2–5), ~165 cells: berserkers
  Orange, Goraxada, Enmar (steel spears); warriors Donkey, Scorpion, Komodo (steel ikwas); chief
  Ñabaigo (steel spear, steel plate armour); penitent Légua (knife); archers Raven (short bow) and
  Jaguar (pila). Shooting 0–4, melee 2–8.
- Tags: `base-arena` `raid-far` `raid-melee` `raid-strong-1v1` (auto: `raid-outnumbers`, count
  ratio 0.8).
- Plan: the east room again (sites.md). New from base_ith_pirate_2x: the two diagonal cells of the
  doorway held by melee pawns (a raider stepped through the empty one there), the pawns next to
  the doorway raider melee him (they cannot shoot him), the guns 2+ cells back. Scratch script
  `base4.py`.

## Scenes

### t0–1087 `approach` → walk in
Front: Semyon on the plug (133, 188), Phat (132, 188), Vang (134, 188). Guns: Graves (133, 189),
Wright (132, 189), El (134, 189), Tina (133, 190), Petra (132, 190). Door held open; Phat's Fire
at will off. All in place at ~t1087.

### t1087–4810 `approach` `raid-wrecking`
The raid walked north smashing and setting fire to furniture on its way (wooden shelves,
hydroponics); in the nook and yard from ~t4100. Goraxada (melee 8) into the corridor at ~t4810.

### t4925–5250 `melee-contact` → `mouth-hold`
Goraxada in the doorway; the three front pawns meleed him and the five guns fired. Semyon (plug)
100 → 47%; swapped for Graves at ~t5216. **Goraxada dead t5247** (~320 ticks in the doorway).

### t5250–9610 `raid-wrecking`
No raider came up for ~4400 ticks (fires in the yard; the archer Raven stood at (133, 169)).

### t9713–10125 `mouth-hold`
Orange (berserker) in the doorway: Phat 100 → 67%. **Orange dead t10125.**

### t13546 Enmar (29%) last seen at (91, 153) "igniting wooden spike trap"; dead there.

### t13926–14222 `mouth-hold`
**Donkey dead t14222** (~140 ticks after reaching the doorway area); Graves 100 → 86%.

### t17529–18271 `mouth-hold`
Raven (archer) came up the corridor first and was shot down in it at (133, 181) (57% there at
~t17730; who hit him not read): **dead t17836**. None of ours lost health while he was in the corridor. Légua (knife) behind him into the doorway: Vang 100 → 88%, Graves
89 → 70%. **Légua dead t18271.**

### t18280 `raid-breaking`
"Neanderthals from Kikbo Nation are fleeing." 6 of 10 out (Goraxada, Orange, Enmar, Donkey,
Raven, Légua).

### t18280–24014 `raid-breaking`
Scorpion died at (85, 153) beside a sprung spike-trap frame (t18916). Komodo and Jaguar, fleeing
east along z 122, lost health cell by cell there (Komodo 64 → 26% over x 177–180, Jaguar 63 → 21%
over x 155–159): Komodo dead at (181, 122) ~t19975; Jaguar was downed at (186, 110) at the end.
Ñabaigo left by the west edge. Raid gone t24014.

## What the play stood on (observed)
- The same door and corridor as base_ith_pirate_2x; this raid came up one at a time, with gaps of
  4000+ ticks while it wrecked the base.
- Each doorway raider had three of ours meleeing him and five guns 2+ cells back firing; the
  raiders in the doorway died in ~140–410 ticks. No raider got into the room.
- Our lowest health in the battle: Semyon 47% (the first plug), Phat 67%, Graves 70%, Vang 88%.
- 3 of the 9 raiders who did not escape died away from us, and Jaguar was downed there: at
  (85–91, 153) and on the row z 122, the stretches where raiders died on spike traps in
  base_ith_pirate_2x.

## New tags / sites
None new; the east room's "used in" in sites.md gains base_ith_tribe_2x.
