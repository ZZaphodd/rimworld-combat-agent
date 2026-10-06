# base_ith_pirate_2x — Claude, 2026-10-06 (played alone) — civil outlanders vs 25 Waster melee, Ithfunda base — repelled

Counted play: **attempt 2**, trace `results/human/traces/base_ith_pirate_2x_claude_20261006-170538.jsonl.gz` ·
row `results/human/play.jsonl` (player `claude`) · result: **repelled** (enemies_cleared t15403),
**0 lost**, 1 downed at the end (Jahames), 1 permanent (Leslie's left ear), HP 182% · raiders: 20
dead (13 at the door, in the corridor below it or in the room, 7 on the colony's spike traps),
5 left by the edges ·
**badness 12.3** (agent `turtle` 57.4, defeat: squad down, 9 of 25 out; `results/base/ladder.jsonl`).
Sheet: `sheets/base_ith_pirate_2x_start.md` (cards rand_012, rand_118, rand_058: the one-raider
doorway and the throws into a bunch were used; written before attempt 1, used again).

Ticks below are the harness's (trace `t`). Controller ticks printed in play were game ticks − 383;
harness t = controller t − 21128885 (Dani's death: controller 21132777, last seen in the trace at
t3888).

## Attempt 1 — discarded (a context compaction came during the battle)

Trace `results/human/traces/base_ith_pirate_2x_claude_20261006-164110_try1.jsonl.gz` · row
(written by hand: the harness was stopped before the end) in `results/human/discarded.jsonl`.
The compaction came at about t5450; I played on for about 1200 ticks by mistake, then stopped.
State at the stop (t6663): none of ours dead, Jahames downed, 18 of 25 raiders standing. Same
site; the guns stood 1–3 cells behind the plug and Jahames was the first plug. Two molotovs
landed early (thrown ~t3798–3822; per the console, a thrower with Fire at will on): one on and
beside the plug inside the room (fire on (133, 188)–(135, 188) at t3882, Jahames 84 → 72%), the
other in the doorway and corridor ((133, 185)–(133, 187) at t3932).

## Card at the start

- Ours: 8 OutlanderCivil, no loadout (the base had no items). Shooting/melee: Jahames 1/4 pump
  shotgun, flak vest (Bloodlust); Haney 2/0 heavy SMG; Fumiko 4/0 bolt-action rifle, flak pants
  (Tough); Leslie 2/0 bolt-action rifle, flak jacket; Park 0/1 revolver (Trigger-happy) with a
  firefoam pack; throwers Caitlin 3/3 frag, Susumu 4/2 and Christ 5/2 molotov. Start: the yard
  (113–120, 162–166).
- Raid: 25 Drifters (Wasters), knives and clubs only, no gun or throwable; melee 13–15: John 15
  (slate club), Farik 14, Dani 13, Daichi 13 (Brawlers), Kolya 11. From the west edge (2–9,
  87–102), ~123–130 cells from our start (~155 to the room door).
- Tags: `base-arena` `raid-melee` `raid-outnumbers` `us-low-skill` `raid-far`.
- Site: the **east room** (sites.md, base arenas): 9×9 (x 129–137, z 188–196), a dead end (the
  rooms behind it to z 227 open only into it), one door (133, 187) at the top of a 1-wide corridor
  x 133 (z 179–186) that starts at the nook (126–133, 175–181) off the yard.
- Plan: the door held open; one raider at a time in the doorway; all guns on him; throws only
  into the corridor queue.

![site](../img/base_ith_pirate_2x_t0.jpg)

## Scenes

### t0–916 `approach` → walk in
Drafted all eight and sent them into the room; door set to "Hold open"; the throwers' Fire at
will off. Cells: Jahames (133, 188) plug; Haney (132, 188) and Fumiko (134, 188), the doorway's
two diagonal cells; Leslie (133, 189), Park (134, 189); Caitlin (133, 190), Christ (133, 191),
Susumu (133, 193) (a torch lamp stands on (133, 192)). All inside at t916.
The raid was smashing and igniting furniture in the west (hydroponics, shelves, a bed).

### t1096–2100 `approach` `raid-wrecking`
Veli (gone by t1194), Mezzatesta (by t1971) and Eduard (by t2100) died at (52–90, 153) on the colony's spike traps (corpses there;
spike-trap frames left behind). First raider within 30 cells t2656, within 15 t2920.

### t2920–3636 `raid-wrecking`
The raid gathered in the nook and the yard (126–133, 172–179) hitting the wooden shelves. First
raider in the corridor t3636 (Dani).

### t3749–4382 `melee-contact` → `mouth-hold`
Dani (melee 13) in the doorway from t3749 (Haney, diagonal, 100 → 83%; Jahames 100 → 87% at
t3880): dead t3892. Furr next (doorway from t4033), Humberto behind him in the corridor: Jahames
(plug) 87 → 42% by t4275. A swap with Leslie ordered at t4271 did not go through: Jahames stayed
on the plug ("attacking Humberto") and Leslie on (133, 189) until Furr was gone (last seen t4365)
and Humberto went down at (133, 186) (~t4382; he crawled down the corridor to (133, 180) and lay
there). Leslie reached (133, 188) at t4426 with Jahames still on it.

### t4382–6820 `raid-wrecking` `fire`
No raider came up for ~2400 ticks: they burned devilstrand, shelves and hydroponics in the yard
(fires on the map rose from 24 at t4398 to 113 at t6527). Leslie walked on from (133, 188) into
the doorway cell (133, 187) at t4454 and stood there until t5906; Jahames never left the plug.
Per the live console the controller had given them fire orders on raiders in the nook they could
not see (a pawn ordered to fire walks to where it sees its target); the trace jobs show only
"moving" and "watching for targets". Restricted each pawn's targets to the raiders its own cell
sees; Leslie back on (133, 188) at t5924, Jahames to (130, 195) by t6058.

### t6820–7517 `melee-contact` `fire` → `molotov-into-group`
Svejgaard and Koromaru in the corridor. At ~t6994–7002 all three throwers were ordered at
Svejgaard (two in reach, 4–5 cells below the plug); the frag and two molotovs left at t7090–7102.
One molotov burst inside the room: fire on the plug cell and (134–135, 188) at t7176 (the plug
cell stood empty t7126–7289). A second round, ordered at Koromaru (jobs "attacking Koromaru" from
t7240), left at t7345–7357 and burst on and around the plug at t7427: Leslie (on the plug)
100 → 87%, Haney 83 → 72%. Park popped the firefoam ~t7472–7484 (room fires out by t7484).
Svejgaard gone t7517. Changed: one throw order per step, molotovs only 6.5+ cells from ours.

### t7941–9573 `mouth-hold` `fire`
Hairy dead t7941. **The throwers were still on their t7240 order ("attacking Koromaru" until
t8483) and threw a third round with no new order**: a frag and two molotovs at Koromaru
(133, 183–185) at t8328–8394, 3–5 cells from ours. A molotov burst on (132, 188)/(133, 188) at
t8462 (Leslie 79 → 68%, Haney 72 → 63%; both put out fire on themselves); the frag lay at
(133, 186) t8377–8474. At t8483 Koromaru (last seen at (133, 185)) was gone, Kolya 50 → 20% and
Snuff 100 → 37%. The plug cell stood empty t8470–9133 (Leslie on (134, 189), her job alternating
"attacking Kolya" and "moving").
**Kolya stood in the doorway from t8247 (76%; 57% at t8328, 50% at t8386, 20% at t8483), at 20%
until t9236 and 17–15% after** (dead t9411). In that stretch Haney (diagonal, Kolya's target) went
63 → 61% (t8569, fire still on her cell) and 61 → 54% (t8893). Snuff dead t9528. Daichi into the
doorway t9573.

### ~t9900 `melee-contact` (the turning point)
Checked why. The keeper had Haney and Fumiko on hold-fire: its friendly-fire estimate counted the
plug standing next to the doorway raider. And the float menu offered **"Fire at Paul: Too close"**
to Haney (diagonal, across the rock corner), Fumiko (diagonal) and Leslie (the plug): no one next
to the doorway raider could shoot him; only Park, 2 cells back, had been firing (17 shots).
chose: a new layout — the plug alone on (133, 188), meleeing the doorway raider; the diagonal
cells empty; guns 2+ cells back on (133, 189), (132, 189), (134, 189), (132, 190), (134, 190)
firing on the doorway raider with the friendly-fire risk accepted on him alone; gun moves hold
their fire orders until they arrive (a fire order ended the walk). Scratch script `base3.py`.
followed: guns in place t10134–10199; Park, Haney and Jahames fired on the doorway raider.
(Kolya's 20% stretch above also had an empty plug cell and Leslie, Fumiko and Park 2–3 cells
from him switching between "attacking Kolya" and "moving"; why he lost so little is not
established.)

### t10246–10600 `rotation` `our-downed` → `carry-downed`
Leslie (plug) at 44%: swapped for Fumiko at t10246. Leslie never left the cell: she went down on
the plug cell at t10368 with Fumiko standing on the same cell. Daichi's job still read "melee
attacking Leslie" while she lay there (a label he had carried since t9837); her health stayed at
36% (no further hit recorded). Park (132, 189), diagonal to her, took "Carry Leslie" and stood
~90–135 ticks with the job "carrying Leslie" without picking her up; sent toward (132, 188), next
to her orthogonally, and given the order again, by the next poll (t10509) he stood on her cell
carrying her (where he picked her up is not seen; why the first carry stalled is not known). He dropped her at (132, 192); Susumu tended her
without medicine (drafted, float menu "Tend Leslie (without medicine)").

### t10789–10984 `melee-contact` → raider in the room
Daichi dead t10789. Caitlin's frag order on John at ~t10838 (John about 5–6 cells below the plug, 7–8 from
Caitlin on (133, 190); the controller's 4.5-cell check passed); the frag left her at ~t10939 and went to John's cell then,
(133, 186), 2 cells below the plug: seen over (133, 189), (133, 188), (133, 187), then lying at
(133, 186) from t11031 to at least t11103. **At t10984 John (melee 15) stepped from the doorway
(133, 187) diagonally onto (132, 188)**, past the rock on (132, 187), while Fumiko stood on the
plug cell; his job was "melee attacking Christ". I stopped the throwers (stop + Fire at will
off), sent Fumiko off the plug (the frag beside the doorway), and turned everyone on John.

### t11122 `raid-breaking`
"Wasters from Miasma Packers are fleeing." By then 13 of 25 were dead or downed (Veli,
Mezzatesta, Eduard on the traps; Dani, Furr, Svejgaard, Hairy, Kolya, Snuff, Daichi at the door,
Koromaru in the corridor 2 cells below it; Humberto and Paul downed); Farik died inside the room at about the same time (cause not
seen).

### t10984–11860 `melee-contact` inside the room
John and Evgeny inside, both "panic fleeing" (mental state) while John still struck at us. Park,
Fumiko and Jahames next to John, with "melee attacking John", did no damage for ~150 ticks
(John stayed at 49%); after "Go here" to a neighbouring cell and a new melee order, John went
49 → 26% in ~30 ticks. Then the guns stepped to cells 2–3 from the raiders and fired. Jahames
went down at (132, 190) at ~t11560 (John beside him). John gone ~t11670 (last seen t11661),
Evgeny ~t11860. Farik had also stepped in to (134, 188) (t11103) and was gone by t11122. Paul
(downed in the doorway) had crawled in to (133, 188–189): shot dead at ~t11950. Christ tended
Jahames.

![inside](../img/base_ith_pirate_2x_t11217.jpg)

### t11635–15403 `raid-breaking`
Razor, Tony, Ryan and Kapenk, fleeing east, died on spike traps at (153–182, 118–122). Bux,
Mitsuya, Fjellsmel, Judex and Outrun left by the south, west and east edges. Humberto died where
he lay in the corridor. Leslie could walk again at t12654. Raid gone at t15403.

## What the play stood on (observed)
- One cell (133, 188) between the doorway and the room. The raid came into the corridor one raider
  at a time (13 entries, t3636–10834) over ~7500 ticks, with long gaps while it wrecked the base,
  but they queued there: 3–4 standing in the corridor at once at t8257–9411 and t10834–10980, and
  two on the doorway cell together at t9909–10421 and t10952–10980.
- At ~t9900 the float menu showed "Fire at …: Too close" for the three next to the doorway
  raider; only Park, 2 cells back, had been shooting. From t10134–10199 the guns stood 2+ back.
- Our own throws: three rounds of a frag and two molotovs (t7090–8394), the last with no new order;
  molotovs burst on the plug cell twice (t7427, t8462).
- 7 of the 20 dead died on the colony's spike traps, 3 before contact and 4 while fleeing.
- The raid fled with 13–14 of 25 out (52–56%).
- Losses (182 points net): Jahames 62 (58 on the plug t3880–4275; 6 more going down inside the
  room at t11564; 2 healed); Leslie 56 (on the plug: 13 at t7427 and 11 at t8462, the polls on which
  our molotovs vanished on or beside (133, 188) and fire appeared there; 3 at t7484, 5 at t7884;
  13, 11 and 8 at t10046–10372, down on the plug during the swap; 8 healed); Haney 46, all on the
  diagonal (132, 188) (17 at t3749; 11 and 9 at t7427 and t8462, the same molotov polls; 2 at t8569
  while on fire; 7 at t8893); Fumiko 18 (8 on the plug at t10718; 11 inside the room at
  t11271–11432; 1 healed).

## New tags / sites (for the user to look at)
- Tags: `base-arena` (situation, matchup), `raid-wrecking` (moment).
- Site: Ithfunda east room (sites.md, new section for the base arenas).
