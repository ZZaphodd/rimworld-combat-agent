# rand_115 start sheet: Waster throwers ×8 (no guns) vs Neanderthal melee ×6, open arena, raid from the NNW edge

New battle: 8 PirateWaster, no guns. Seven carry tox grenades; Hizak (8/8) carries molotovs. Best melee: Hizak 8, Levy 6, Fizzman 5 (moving 82%), Ambush 4 with a drill arm and flak vest. Skalder (0) and Albert (2) have elbow blades. Flak on Levy, Ambush, Faz, Blurkap and Skalder.
Raid: 6 Neanderthals, all melee, 285 pt, from (37–49, 242–247), ~146 cells. Antelope ikwa 8, Crocodile knife 6 (Jogger), Alobi ikwa 5 (82%), Jackal club 5, Stinkbug club 2, Nebar spear 1. Agent `kite`: squad down t7796, 0 kills, 84.8.
Geometry (from sites.md coordinates):
- The raid's line to the start enters the cleared square at ~(71, 203), then crosses ~96 open cells. Its line to the nook mouth (211, 84) is ~232 cells, passes ~42 cells north of the start, and reaches the mouth from the NW, the side the nook opens to.
- Pace: rand_118's NW-corner raid (~260 cells, faster Yttakin) queued at the mouth at t3972; Neanderthals walk at 96% of our speed (rand_127). So the body arrives at ~t3700–4300, Crocodile earlier, Alobi later.
- Ours to the nook: 97 cells. Most arrive ~t1650 (rand_118 reached the wall at t1661); Fizzman (82%) ~t2000.

## 1. rand_127: the same raid race against the nook mouth. Claude 10.8, human 26.0, agent 116.9
- **Close:** 6 Neanderthal melee + 1 archer (310 pt), against 6 Neanderthal melee here (285 pt). Tags in common: `raid-far` `raid-melee` `raid-strong-1v1` `us-outnumber` (1.43 there, 1.33 here). Their raid came from the north edge (130 cells), contact t3221. Their melee skills were 2–4 except Bacchus 9; here Antelope 8, Crocodile 6, the rest 1–5.
- **Differs (it matters):**
  - There, four melee weapons held the front (Barracuda 10/11, Crica 10 ikwa, Mabe 7 ikwa, Trout 6 ikwa) and 5 bows shot the raider in the mouth. Here the front fights with fists, two elbow blades and a drill arm (best melee 8); the damage from behind the front must come from tox gas, one molotov stock and any ability.
  - Forest arena there. The nook is outside the cleared square (x > 203), so it is forest on both arenas.
- **Borrow:**
  - Site: inside (212–214, 81–87), mouth (211, 84). Breach the marble wall at (211, 84): one swing per order, a round every 90 ticks (Claude: 6 pawns, 11 rounds; the human: ~1100 ticks with 6).
  - Everyone inside (radius ~3); only the pawns touching the mouth fight, 2–3 of ours against 1–2 of theirs. Rotate a front pawn out below 45%. The downed lay inside behind the front, and nobody could carry them off.
  - The raid fled when Bacchus, its best melee pawn, went down: t5258 human (5 raiders out), t6213 Claude.
- **Went wrong:** the urn (212, 85) fell only to 3%; one of ours was downed in each game. Human attempt 2 put the same squad, packed, on open ground: the Neanderthals surrounded each fighter and won every exchange (Gabobrei held Trout for 1000+ ticks), squad down, 99.4. The agent's `amove` in the open: all 10 downed.

## 2. rand_118: the nook on the open arena against a mostly-melee raid from the NW. Claude 28.2, agent `kite` 93.2
- **Close:** `open-arena` `raid-far` `raid-melee`. The raid came from the NW corner (0–14, 242–249), ~170 cells, just west of this edge. No explosives. The agent's `kite` also ended in squad down (t4600 there, t7796 here). That squad had no melee weapons either (bows used as clubs, one pila).
- **Differs:**
  - Yttakin (melee 3–9), not Neanderthals; 9 v 8. **Tail's machine pistol and Gecko's autopistol, firing in from 1–4 cells outside the mouth, downed most of ours who went down in both attempts.** This raid has no ranged weapon, so that cause is gone.
  - The 7 bows did much of the killing at the mouth: damage dealt Crouca 182 (in melee), Verea 175, Crab 151. Here throwers take the bows' place.
- **Borrow:**
  - Timings: loadout t75; at the wall t1661. Nine pawns broke the marble wall in 6 rounds (91 → 88 → 68 → 32 → 26 → 3 → broken), open at t2246 with the raid ~100 cells off. The raid came along z 84–85 down the lane, straight at its target (Wolf), and queued at the mouth at t3972. Six melee pieces died one at a time in the mouth cell (t4433–6486), each with 2 front pawns and 6 bows on it. Raid gone t7954.
  - Cells: with the urn standing, only (212, 83) and (212, 84) touch the mouth from inside; a column stands at (214, 84). Only (212–214, 84) see far down the lane, to (189–205, 85). The south pocket (209–212, 78–82) is out of the lane's sight and served as the rest spot: Carmen out at 38% (t4868), Crouca at 41% (t6126).
  - Loop: `journals/rand_118_mouth_loop.py`. The front melees the raider in the mouth and rotates below 45%; archers re-pick their target when their shot count stalls. Its archer block would become the throwers.
- **Went wrong:** Babodor stepped into the mouth cell (211, 84) itself, was hit from several sides, and went down at t4150. Bows given attack orders on Tail (verb-gizmo orders) sat "attacking Tail" for ~1000 ticks without firing; the float menu's "Fire at" (`hands.fire`) worked. Attempt 1 (discarded): the bows stood at the least-visible cells, and the pistols outlasted the front.

## 3. rand_015: the same two factions with sides swapped, open arena. Claude 61.4 (best of 3), agent 105.2
- **Close:** Neanderthal melee ×6 against Wasters whose throwables were molotovs (Rubisum) and tox grenades (Horror). `open-arena` `raid-far`, from a corner at ~142 cells (NE there, NNW here).
- **Differs (it matters):** there the Wasters were the raid and carried 7 guns; the Neanderthals were ours. What it shows of Neanderthal melee against Wasters: three of ours on Seizz (melee 11), dead in ~150 ticks; pairs locked and downed Tasya, Horror and Tooth within ~1200 ticks, none of ours down.
- **Tox and fire there:**
  - Horror was locked before he threw: no tox gas was seen in the battle.
  - Five molotovs were sidestepped, but the grass fire reached pawns who had already stepped aside. Alpaca and Mallard burned; their "extinguishing fire on …" read like wandering.
  - Seizz had Fire spew (a Waster gene). In attempt 3 he spewed into a doorway and set three of ours burning.
- **Site:** the west rock pocket (25–35, 140–144) is open to the north. From this edge it is ~103 cells from the raid and 96 from our start, and the raid would walk in through its open north side (~10 cells wide), not round rock B's tip.
- **Went wrong:** the fights drifted into gunners' view (no gunners here). Kidnap at the end: Bilegoda was carried off the west edge past two wounded chasers. Attempt 2 moved the squad with a plain `wait()` loop: 3 lost. Attempt 3 (big-ruin rooms): the raid shot in through every door.

## Also: tox, molotovs, abilities, kite, weak locks (cards outside the three)
- **rand_126 (our Wasters, won 13.6):**
  - JC threw tox at three raiders at (37–39, 153–159): "no gas cloud seen". With rand_015's unthrown tox, these are the library's only tox records; nothing is recorded on what tox gas does to raiders.
  - Dtchrath's Fire spew on two raiders standing together: Storch 87 → 40%, Fudiao set burning. rand_011: range 7.9, ~40 ticks to cast, aims at a cell. Wasters had Fire spew in rand_011, rand_015 and rand_126; `hands.brief()` lists abilities.
  - Gang-melee: Wes, 3 on 1, dead in ~400 ticks; Oahnip (13/14), 4 on 1, "slow with weak clubs".
- **Molotovs and our own grenades:** rand_058: our frag, thrown at a raider our pawns were locking, landed on them (Poinlaoik died); a molotov at the group north of the pocket lit grass fire there, away from ours. rand_104: one molotov burned in front of the line all battle. rand_084: a molotov on Claula at 8 cells killed him.
- **rand_128 (`raid-strong-1v1` `us-outnumber`, open, no site), kite:**
  - `journals/rand_128_kite_loop.py`: shoot until the chaser is 6 cells away, throw at ≤ 11 cells, step back 12. It killed Theodore (3.1 cells/s against our 3.75) in six cycles. Lekapenos (4.2) kept up and had to be fought.
  - Here: Fizzman (82%) and Ambush (92%) are at or below the Neanderthals' 96%, and Crocodile is a Jogger. In rand_128, Squiggle (the slowest) fell behind and went down. Agent kites lost in rand_067, rand_039 and rand_118.
- **Weak locks:** rand_011, two clubs with melee 3 lost their exchanges. rand_058, lockers with melee 1 kept missing until Trev (10) joined.

## Other sites (sites.md) for this battle
- **Nook** (above): 97 ESE of the start, ~232 from the raid's edge, opens NW towards it. The only mouth tested against a melee raid.
- **NE walled hall**, one-cell mouth at (213, 167): ~98 cells from the start, ~187 from the raid's edge, so contact comes sooner (~t3100). Granite: rand_023's breach failed at the 45-tick cadence (95 → 93% in ~3000 ticks); untested at the 90-tick cadence.
- **Big-ruin rooms** R1 (104–107, 43–44) and R2 (104–107, 46–47): ~82 SSW of the start, ~209 from the raid's edge; ~8 cells each.
  - Doors: R1 W (103, 44), S (106, 42), gap (105, 42); R2 W (103, 46), N (105, 48); R1–R2 (106, 45). Five ways in for 8 pawns.
  - rand_015 attempt 3 lost there to gunners; this raid has none.
- **Not suited:** the west rock pocket and west notch (~103 cells from the raid, open to the north); the rock hill (bare ground on this arena); the small ruin (26 ESE, low walls, no mouth); the SE pocket (127 SE, where rand_067's kite ended against the edge and the lake).
