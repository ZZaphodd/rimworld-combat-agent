# rand_126 start sheet: Waster melee mass + one 16-shooter rifle vs pirates ×8 from the SE corner (open)

Read as: `open-arena` `raid-far` `raid-outranges` `raid-sniper` (Nadezhda 10, rifle 37) `top-threat` (Storch revolver 13; Oahnip club, melee 14) `us-melee-pawns` `us-low-skill`. Count ratio 1.25, no explosives on the raid, all eight on Sara. Agent `close`: squad down t4726, 99.8.
Picks: **rand_023** (same matchup), **rand_015** (same matchup on the open arena, corner ambush), **rand_084** (nearly the same raid, notch + brawlers on the ends).

## 1. rand_023: savage melee ×10 vs outlanders ×8, no explosives (forest; agent 101.8, Claude 100.2)
- **Close:** 10 unarmoured melee vs 8 gunners with no explosives, one top shooter (Lissa, revolver 19), ratio 1.25 in both, raid from a far corner (151 SW there, 165 SE here), every raider on one colonist (Hornet), agent squad down at t3051.
- **Differs:** forest (contact at ~11 cells) vs open: here the raid sees 25–37 cells, so every crossing costs more (matters). We have Max (16, 37 cells), Whisper (9, machine pistol), JC's tox and Dtchrath's Fire spew; rand_023 had no ranged answer at all (matters). The raid here has a melee-14 club (Oahnip) and a 37-cell rifle at shooting 10.
- **Borrow:** the NE walled hall: a mouth broken at (213, 167) keeps a 32-cell block (203–211 × 168–172) hidden from every outside cell within 35 (LOS calc, untested). 98 cells from us; the raid's corner is 166 from it (as far as from our start) and 94 cells off its line to us. rand_023 reached it ~t1650. Breach: one swing per order, rounds every ~90 ticks; rand_127 broke a marble wall with 6 pawns in ~1100 ticks (granite is harder, not measured).
- **Went wrong:** orders re-issued every 45 ticks cancelled the swings (95 → 93% in 3000 ticks); the loop did not watch the raid, which caught the squad outside in the open with gunners at 10–22 cells; carrying under fire was slow (Ram, Hornet down); one carry order picked up the raider Toni; Van's shotgun downed both lockers.

## 2. rand_015: Neanderthal melee ×6 vs Waster gunners ×9 (open; Claude 61.4 / 79.9 / ≈ agent)
- **Close:** open arena; melee squad vs a raid that outranges it; far corner (142 NE); the raid walked straight at one colonist (Crica, all three attempts) in a long column; each attempt took the first 2–4 raiders out where they came round an obstacle one or two at a time (Seizz, melee 11: 3 on 1, dead in ~150 ticks). Fire spew was in play (Seizz, a Waster gene).
- **Differs:** 6 v 9 there with a molotov and a tox thrower; 10 v 8 here and no throwers (no bottle fires, no dodging). Here Max can reach the gunners who held at 15–20 cells, the thing the melee could never reach in any attempt (matters most). The raid comes from the SE, not along z 143 from the east: whether rock B still hides the pocket from that angle is not known (LOS from ~(60, 120) and (45, 128) in `rca.terrain`). The card says the raid's Wasters were tox-immune; ours are PirateWasters, so JC's tox may land on a melee without hurting ours (check genes in `hands.brief()`).
- **Borrow:** west rock pocket (25–35 × 140–144; B's north tip (37–40, 145)): 90–97 cells from us, 243–247 from the raid's corner. In rand_015 the squad was in by ~t1900, the first raider at the tip t2880 (216 cells from the NE). Gang the runner at the tip; lock the next ones before they shoot (Horror locked before throwing).
- **Went wrong:** the fights drifted out to the tip and north of it (36–40, 145–158), in view of a free shotgun and three gunners holding at 15–20 cells; Tooth's spot (38, 158) sees the whole pocket from the north. Attempt 2: a plain `wait()` loop ran ~870 ticks while three were shot down at the tip. Attempt 3 (big-ruin rooms): gunners shot through doorways and gaps, Seizz spewed fire into a doorway. Every attempt ended in a kidnapping.

## 3. rand_084: pig outlanders ×9 vs pirates ×8 with a 37-cell sniper (open; human 1.8, Claude 20.5)
- **Close:** the raid is almost this one: pirates ×8 with a bolt-action in good hands (Carlson 16 / here Nadezhda 10), a good revolver (Rusty 11/0 / Storch 13/9), a bad-hands bolt-action (McMahon 3 / Diana 1), a wooden club at the front (Claula / Oahnip 13/14), machine pistol, revolver. Ours there: low skill with two brawlers; far raid (140 E); open arena.
- **Differs:** ours were seven guns (revolvers ~26 cells) + two knives; here one rifle, two machine pistols, seven melee (matters: the notch there was a firing position). The raid had two grenadiers and the gap slip was against them; none here. Rusty (melee 0) lost to a knife; Storch has melee 9. Raid from the east edge, not the SE corner.
- **Borrow:** west notch (29–32, 141–143), 97 cells from us, 247 from the raid's corner; there the raid came within 15 at ~t2773 after ~215 cells. The raid followed in one line, the club first; the sniper had to come within 18 cells to see into the notch; brawlers took whoever came round the ends (Choppy held Rusty). The gap (26–28, 136–140) leads to the south face, which faces a raid from the SE.
- **Went wrong (Claude):** focus on Carlson refused (rock in the way); two knives sent at him at t3634 and he backed off north, then came round the **west** end (14, 139), killed Alo and left. The raid came round both ends at t4083.

## Long gun with melee, as played
- rand_011 (open, two 13-shooter rifles in the front line): misses at 25–30 cells early; every new attack order or move restarted the bolt-action's ~1.7 s aim; left on one target, Reid dead in ~300 ticks; Schlitzer killed the last two (Dennis, Navarro).
- rand_104 (Claude): the greatbow stood on a range mark (29.8 of its 29.9 cells to rock chunks by the raid's path) and never moved; the pawns around took the molotovs; downed t3732 by Bishop (shotgun), freed when his locker Crica went down to Georgette's knife.
- rand_065: Jess 16/14 kept the 37-cell rifle in a big-ruin room; the raid, without line of sight, walked in to 4–6 cells; Jess was among the four who did the damage (armoured troopers there).
- rand_039: Powo (4/1 bolt-action) at the line's west end was downed first (t3438–3812). The user's note on long rifles is not in the card or its report.
- rand_015 attempt 3: Crica's greatbow (shooting 6) killed Seizz (neck) at a door.
- Fire spew (Dtchrath): rand_011: range 7.9, ~40 ticks to cast, it replaced Mila's melee order and caught one of two; fire left on the ground. rand_015: grass fire reached pawns who had sidestepped the bottles.
- Oahnip (melee 14): rand_011's clubs (melee 3–4) lost their exchanges with gunners; rand_127 attempt 2: strong melee raiders surrounded single fighters in the open.

## Sites from (125, 124) and the raid's line
The raid's straight line to us: (234, 2) → (125, 124), 164 cells. From the image only: a lake ~x 215–250, z 7–40 lies right north of its start and another ~x 126–170, z 25–53 to the west, so it likely goes up past the SE pocket and enters the cleared square near (190–205, 50), then ~100 cells of open ground. Leaders covered ~215 cells in ~2800 ticks in rand_015 and rand_084 (~13 ticks/cell); first contact in every past case t2000–3500. It walks at Sara, so moving her moves its line.

| site | from us | from raid's corner | off its line | note |
|---|---|---|---|---|
| small ruin (144–153, 108–116) | 26 | 140 | 9 | on the line, 24 cells before our start; low walls, hidden cells not computed; rand_039 held it (forest) |
| rock hill / rock hill E | 59 / 69 | 111 / 113 | 21 / 39 | bare ground on this arena: hides nothing |
| nook mouth (211, 84) | 95 | 85 | 38 | the raid is nearer it than we are; ~1100-tick breach: not before contact |
| SE pocket (212–216, 28–40) | 127 | 38 | 6 | on the raid's way out of its corner |
| big-ruin room (100–106, 39–41) | 87 | 135 | 72 | 7–9 hidden cells (rand_023 calc); rand_015 attempt 3 lost there |
| NE hall mouth (213, 167) | 98 | 166 | 94 | breach first; 32-cell hidden block untested |
| west rock pocket / west notch / gap | 90–97 | 243–247 | 51–59 | the raid follows Sara there: ~2.5× our walk |
| W forest edge (35–51, 118–137) | 82 | 228 | 59 | treeline is cover, not a sight blocker |
