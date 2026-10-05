# rand_118 start sheet: tribal bows ×9 vs Yttakin blades + boar, open arena, raid from the NW corner

New battle: 9 TribeRough bows, no armour, no melee weapons: Sam 11 greatbow (30), Crouca 9/14 and Crab 7 recurve, Wolf 7 short bow, Trigger-happy (the raiders' target), Babodor 4/11, Red, Barra, Verea short bows, Carmen 3/8 pila. 5 of 9 shoot ≤ 4.
Raid: 8 Yttakin (360 pt) = 5 knives/clubs (melee 3–8), a boar, and 2 pistols in shooting-0 and shooting-3 hands, from (0–14, 245–249), ~170 cells. Agent `kite`: squad down t4600, 1 killed, 93.2.
Geometry (computed from sites.md): the raid walks straight at its target (rand_015 ×3, rand_023, rand_126). From the corner to (125, 124) it enters the cleared square at ~(50, 202), then crosses ~110 open cells. At ~17 ticks/cell (rand_126: ~245 cells, contact t4142) its body reaches the start at ~t2900; runners come sooner. Away from it is ESE, where the small ruin, the rock hill's east side and the nook lie in a row.

## 1. rand_067: the same matchup. Human kite 58.7 (lost 1), agent `kite` 130.5
- **Close:** tribal bows vs Yttakin at 360 pt with clubs and a wild boar; `raid-melee` `us-bows` `raid-far`; a pack kite was the play, and the agent's kite lost both times.
- **Differs:** Forest there: contact came close and the walk was ~30 ticks/cell. Here the bows see the chasers across ~110 open cells at 23–30. The raid there came from the south edge at 129 cells. Their raid had 4 ranged raiders (Hadyott molotovs, shotgun, revolver, machine pistol). Here there are 2 weak pistols, so nearly all the danger is contact. Their squad had melee weapons (Val 12/10 ikwa, Toad 11/11 pila, Stork spear, Mole pila), and Toad was Slowpoke. Here nobody is slow, but Crouca 14 and Babodor 11 would fight with bows in hand. This matters at contact.
- **How the kite went:**
  - t454–1122: the drifter Kottytt ran 40 cells ahead of the raid into the whole squad and was killed, the kite's one clean kill.
  - t1777: the squad went east in a pack. The boar and Kelerk (club) had already caught up; the gunners trailed.
  - t2751: it turned south near the east edge into the strip between the SE ruins (west) and the lake (east), just north of the SE pocket (212–216, 28–40). The raid was strung out over 50 cells with Kelerk in front.
  - The squad stopped there. By t3520 it stood in two clumps ~10 cells apart: north Val, Stork, Hawke (greatbow), Toad; south Banve, Ape, Mole, Irodo.
- **Where the melee caught the bows:** at the north clump, t3520. The raid came down the squad's own trail from the north-west, so that clump was the rear. Hadyott, Ryan and the boar (Kin'kovysh close behind) hit it together; Kelerk took Banve in the south clump. Molotov fire burned between the clumps. Val charged alone and was down at t3652. Toad, Stork and Val were down in one spot by t4300 while Hawke fought two; five were down by t4700.
- **Why** (report, frames 3–6): the pack moved at Toad's Slowpoke pace through forest, slower than the boar and Kelerk. The kite ran out of room (east edge, lake, ruins), so the stopped squad met the front four together, not one at a time. The closers were not focused before contact.
- **Borrow:** the runner picked off by all nine. In frame 8, three archers happened to stand on the kidnapper's south exit and killed him, saving Mole; Toad was carried off east. Note that a kite away from this NW raid heads for that same corner: the SE pocket is ~127 cells from (125, 124).

## 2. rand_127: the nook's mouth against an all-melee raid. Claude 10.8, human 26.0
- **Close:** 6 of 7 raiders were melee and reached the mouth one or two at a time; we had 5 bows; `raid-far`. The nook is open only to the north-west, the raid's direction here.
- **Differs:** Neanderthals (robust, reduced pain, 96% of our speed) there; Yttakin with melee 3–8 here. 10 v 7 there, 9 v 8 here. Their raid came from the north edge (130 cells, contact t3221). Four melee weapons (ikwas, pila) held their mouth. Here it would be Crouca, Babodor and Carmen with bows or the pila. This matters: the front loses more exchanges and needs more rotation. The nook is outside the cleared square (x > 203), so it is in forest on both arenas: the last ~8 cells before the mouth are trees.
- **Site:** inside (212–214, 81–87), mouth (211, 84), urn (212, 85).
  - Distance: 95 cells from (125, 124), ~1600–1700 ticks of walking.
  - Raid's approach: ~261 cells from the NW corner, ~34 off the corner→start line, with the mouth facing the corner, so the raid's straight line to Wolf ends at the mouth. Its body would arrive at ~t4400, runners earlier.
  - Not checked: whether the bows inside see out of the mouth to the north-west (needs an `rca.terrain` LOS check).
- **Play:**
  - Breach the marble wall at (211, 84): 6 pawns adjacent, one swing per order, a round every ~90 ticks. Claude needed 11 rounds (~1100 ticks), so the mouth would be open at ~t2800. In rand_023, re-issuing every 45 ticks cancelled the swings (95 → 93% in 3000 ticks).
  - Everyone inside (radius ~3). Only the pawns touching the mouth fight: 2–3 of ours vs 1–2 of theirs.
  - Rotation: a front pawn below 45% steps back and a fresh one steps in. The downed lay inside, behind the front.
  - The raid fled when Bacchus (its best melee pawn) went down: t5258 (human), t6213 (Claude).
- **Went wrong:** The urn fell only to 3% and never broke. One of ours was downed in each game. Human attempt 2: the same squad, packed on open ground, was surrounded, each fighter outnumbered (Gabobrei held Trout 1000+ ticks): squad down. In rand_023, the breach loop did not watch the raid, and the raid caught the squad outside the wall.

## 3. rand_039: stepped withdrawal east from the small ruin. Human 8.0, Claude 48.4, agent `kite` 108.0
- **Close:** the raid came from a corner at 169 cells (~170 here); `raid-far` `us-low-skill`; the agent's pack kite lost. Bounds made whoever followed arrive alone: Takuya, Cynapse and Blake were killed that way.
- **Differs:** That raid came from the SW, so bounds east ran sideways to its line; here the same bounds go straight away. Forest hid that squad; here the raid sees us all the way, and we walk at 16–18 ticks/cell. There the gunners and throwers held at 22–45 cells; only two knives and the grenadier followed. Here 6 of 8 will follow. Whether they arrive one at a time depends on their speed against ours; this matters most.
- **Speeds seen elsewhere:**
  - rand_128's loop (shoot until the chaser is 6 cells away, step back 12) killed Theodore (3.1 cells/s vs our 3.75) in six cycles. Lekapenos (4.2, on go-juice) kept up.
  - In rand_067 the boar and Kelerk caught the pack.
  - Tail is "targeting yayo"; in rand_128 the two raiders on go-juice were the fast ones.
- **Route ESE:**
  - Small ruin (144–153, 108–116): 26 cells from (125, 124), 25 past the start, ~9 cells off the raid's line, 196 from the corner.
  - Bound 1 to x 160–164 (Claude, ~15 cells), then bound 2 to x 181–185.
  - Bound 3 to the rock hill's east side, low (187–191, 95–97): 70 cells from the start, ~27 off the line. It is bare ground here and hides nothing.
  - The nook's mouth is 25 cells further.
- **Timings there:** at the ruin t2018–2702; the first knife ran in at t3048 and died; bounds at t3118, ~t3812, ~t5610.
- **Went wrong (Claude):**
  - Powo, at the west end of the line nearest the followers, was downed between bounds 1 and 2.
  - At bound 2 the squad held in view of Pratt (incendiary, 24 cells): Dennis was downed and Elsie set on fire.
  - Elsie was later downed outside the group at (183, 107); the carry failed, and chasing three kidnappers exposed the group: 5 downed, 7 permanent.
  - The human, same route, kept the group together and carried Elsie to the east edge; the kidnapping failed.
  - In rand_128, Poikup was in melee when a bound started; he was left behind and died. Squiggle (49%, the slowest) fell behind in the kite and went down.

## Other sites (sites.md)
- **West rock pocket / notch** (~97 W): ~108 cells from the NW corner, closer to the raid than to us. The pocket is open to the north, which this raid would see into.
- **NE walled hall:** a one-cell mouth at (213, 167), ~98 cells from the start and ~221 from the corner. Untested: its granite wall survived rand_023's breach attempt, made at the 45-tick cadence.
- **Big-ruin rooms R1/R2** (~87 SSW, ~228 from the corner): ~8 cells each, slate doors. rand_015 attempt 3 lost there to gunners shooting through the doors; this raid's gunners shoot 0 and 3.
