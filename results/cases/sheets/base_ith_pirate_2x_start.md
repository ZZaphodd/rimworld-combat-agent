# base_ith_pirate_2x start sheet: 8 civil outlanders (guns + 4 throwers) vs 25 Waster melee, Ithfunda base

New battle: ours 8, shooting 0–5, no armour, start in the walled yard (113–120, 162–166). Raid: 25 Drifters, all knives and clubs (seven at melee 10–15), from the west edge, ~110 cells. Count ratio ~3.1; no card has a raid this big (rand_012 was 8 v 5).
Turtle (stood in the yard, 57.4): first contact **t1666**; squad down t5177 with 9 raiders out and 16 standing; "decided to kidnap" at t7427; raiders smashed furniture and set a wooden shelf alight.
`cases.py similar` has no base manifests; the cards below were picked from its rand_118 / rand_012 / rand_018 lists.

## 1. rand_012: ruin room R2's doors, one raider per door. Claude 55.6 (won, pyrrhic); open-ground gang 92.5
- **Close:** a melee raid that outnumbered us, strung out by speed; three one-cell doors; only pawns touching a doorway fought.
- **Differs:** ours there were 5 melee pawns; here guns fire at the doorway from point blank (shotgun, heavy SMG, revolver). Their rifle shot in through the open north door from 2 cells all fight; this raid has no gun, so that cause of loss is absent (matters). 8 raiders there, 25 here, so the queue is three times longer. R2's doors were ownerless ruin doors. Here the doors are the colony's, and no card shows how a raid treats those.
- **Borrow:** 2–3 of ours on each door; a rest cell inside, 2 cells from the door (107, 47); a swap at 29% (Irobiarbai out, Alocombar into his cell). Pace: 4 melee raiders died in the doorways in ~2350 ticks (t2539–4892). Ryshuk (melee 13) held the north doorway ~1300 ticks against 2–3 of ours. The downed lay inside, away from the doors, and no one was kidnapped.
- **Went wrong:** once corpses lay in both doorways the doors stayed open. The boars came into the room, and within ~300 ticks Bancam was dead and Alocombar down. Attempt 1 (open ground): the first arrivals died alone 5 v 1, then the body arrived together and four of ours were lost.
- rand_018 attempt 2 (R1+R2 doors, melee vs 11): the raid reached the rooms as we arrived (t1440), and one of ours was caught outside. Turtle's contact here was t1666.

## 2. rand_118: nook mouth, every bow on the raider in the mouth, rotation. Claude 28.2 (repelled); agent kite 93.2
- **Close:** low-skill ranged squad vs a near all-melee raid. Six melee raiders queued outside a one-cell mouth and died one at a time.
- **Differs:** 9 bows (range 23–30) vs 8 there, vs 25 here. The losses there came from Tail's machine pistol, fired 1–4 cells outside the mouth (both downed in attempt 2, 4 of 6 in attempt 1). Here no raider has a gun (matters). Our range is shorter except for the two rifles.
- **Borrow:** only two front cells touched the mouth from inside. Everyone else stood behind and shot the raider in the mouth. Six melee raiders died in ~2500 ticks (t3972–6486), ~420 ticks each, with 2 in front and 6 shooting.
- **Borrow, rotation:** a front pawn at 38–41% went out to a rest pocket out of the lane's sight, and a fresh one stepped in (2 rotations).
- **Borrow, fire control:** guns ordered at raiders further out sat "attacking X" for ~1000 ticks without firing. Order the raider in the mouth first. Re-pick any gun whose shot count stalls for 3 steps, using the float menu "Fire at" (`hands.fire`).
- The raid left after 5 dead and 1 down of 8. Turtle here had 9 of 25 out, and the raid had not broken.
- **Went wrong:** Babodor stepped into the mouth cell itself, was hit from several sides and went down ~180 ticks later. Attempt 1: the bows stood at the least-visible cells, not on the mouth raider; the front ran out first, and all nine went down.
- Arithmetic from cards 1–2: at ~400–600 ticks per raider, 25 raiders take ~10,000–15,000 ticks at one door. Turtle's squad was down at t5177.

## 3. rand_058: frag + molotovs on a bunch at the tip; our own frag on our lockers. Claude 47.3 (repelled); agent turtle 99.1
- **Close:** civil outlanders with a frag and two molotov throwers; the raid had no explosives and bunched at a corner within 4 cells of ours.
- **Differs:** that raid was gunners (3 shotguns). Here all are melee, so a bunch outside a door or wall is likely each time. The ground there was forest grass. Here it is the yard and rooms, with wooden furniture (floors not checked).
- **Borrow:** t2724–2814: a frag on one, molotovs on two in a bunch of five, shotguns on the nearest: 2 dead in 90 ticks. rand_179 t4571–5021: a molotov on two raiders at the tip 6 cells out killed Shark; the molotov thrower dealt the most damage (287). In both, none of ours stood among the raiders the throws hit.
- **Went wrong:** Moinork walked out to the tip to throw; a knife locked him and he went down.
- **Went wrong:** Poinis's frag was ordered at Fluona, and then three of ours were sent to melee Fluona. The frag landed among them: Poinlaoik died and Curly was hit.
- **Went wrong:** `guard()` took our own frag and molotov for the raid's and sidestepped Trev into the raid. Fixed: no dodging when the raid has no throwers (this raid has none).
- rand_015: molotov fire spread on grass and set two of ours burning after they had sidestepped the bottle; they ran about. rand_015 attempt 3: a Waster (Seizz) had Fire spew, which the card did not show. He spewed it into R2's north doorway and three of ours caught fire. The Drifters are Wasters too.
- Park's firefoam pop: no card used it.
