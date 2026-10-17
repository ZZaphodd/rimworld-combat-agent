# rand_015 · Neanderthal melee ×6 vs Waster gunners ×9 with a molotov and a tox grenadier · open — won by the human

**Situation:** `open-arena` `raid-far` `raid-throwers` `raid-outranges` `raid-outnumbers` `us-melee-pawns` `us-skill-mismatch`
**Plays seen:** `mark-shooters` `ability-bait` `loadout` `corner-ambush` `notch-hold` `gang-melee` `melee-lock` `frag-dodge` `chase-carrier` `carry-downed`
**Numbers:** ours 6 (melee 5, long 1), range median 1.5 · raid 9 (short 7, explosive 2), 490 pt, outrange share 1.0, closer share 0.78 · count ratio 0.67 · raid from the north-east corner (243–249, 191–205), ~142 cells

## Sides
- Ours (shooting/melee, weapon): Manatee 4/11 steel ikwa (poor → **normal**, Alpaca's); Crica
  6/9 steel knife (poor 50%) → **steel ikwa** (Bilegoda's); Mallard 3/7 greatbow, Psychopath;
  Curne 0/3 wooden club; Bilegoda 0/1 steel ikwa → knife, Kind; Alpaca 0/0 steel ikwa (normal →
  poor), Kind. Neanderthals: robust, reduced pain, strong melee damage.
- Raid (Wasters, tox-immune): Rubisum molotovs (6/4, Nimble, flak vest); Horror tox grenades
  (1/2); Tooth machine pistol (11/10); Davenport autopistol (awful; 9/6); Seizz machine pistol
  (0/11); Dek pump shotgun (3/2, Fast walker, Nimble, flak vest); Tasya pump shotgun (0/1); Nicole
  revolver (1/0); Tomb revolver (3/0).

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| naive agent `doctrine` (no loadout) | melee holds until an enemy is within 20, then charges | open ground | defeat, captives | 3 dead, 2 kidnapped | 105.2 |
| **human** (Claude's loadout) | out through the pocket's south-west gap to meet the raid along rock B's south face; one of ours on each shooter in order of danger; the least useful pawn (Alpaca) sent at Seizz to draw his Fire spew; Mallard (bow) used as a locker | rock pocket's south side | **decisive**, all 9 dead | 1 dead, 2 downed | **33.2** |
| Claude, attempt 4 (replaying the human's play) | same loadout and gap; out through it when Seizz neared; fixed markers on Seizz (bait), Horror, Tooth; the rest on the nearest dangerous unmarked shooter | rock pocket's south side | **repelled** | 1 dead, 1 downed | **25.5** |
| Claude (alone) | loadout; west rock pocket; ambush at rock B's north tip; locks on the throwers | west rock pocket | defeat, captives (Bilegoda) | 1 dead, 1 kidnapped, 1 downed | 61.4 |
| Claude, attempt 2 | same pocket, greatbow to Crica; a move to the south face done with a blind wait | west rock pocket | defeat, captives | 1 dead, 2 kidnapped | 79.9 |
| Claude, attempt 3 | big-ruin rooms R1/R2, melee beside the doors, Crica (the raid's target) inside | big-ruin rooms | defeat (no row: harness crash; from the trace) | 4 dead, 2 kidnapped | ≈ naive agent |

## Scenes
- **Human, intents (told after the battle):** the top threat was Seizz (Fire spew + good shooting):
  a plain melee dive would set the squad on fire and out of control under free fire. Next, the tox
  grenade, which buffs Wasters and blurs our pawns' consciousness. Alpaca, the least useful, was
  sent at Seizz on purpose to draw the Fire spew; Crica's move on Seizz later was improvised. Bows
  would add little, so Mallard locked too. Manatee was to be the main dealer; the raid's dealers
  were marked in order of danger. The molotov thrower arriving last (the raid strung out) made it
  one on one by luck.
- **Human, t2972–3982** `raid-strung-out` → `mark-shooters`: from the pocket by the south-west gap,
  out through the gap and east along the rocks' south side; six locks at once (Manatee–Tooth,
  Crica–Dek, Bilegoda–Horror, Alpaca–Tasya, Curne–Tomb, Mallard–Nicole).
- **Human, t3982–5773** `ability` → `ability-bait`: Alpaca burned from Seizz's Fire spew; Dek, Tooth,
  Tomb dead by t4655; Mallard (bow) held Rubisum (molotovs) when he arrived; Seizz dead by t5773.
- **Human, t5773–9030**: molotov fires among ours; the raid ground down one on one; Crica died in the
  last lock on Rubisum; Nicole hunted down to the west edge: all nine dead.
- **t2880–3376** `raid-strung-out` → `corner-ambush` `gang-melee`: Seizz (melee 11) 13 cells
  ahead of the raid rounded rock B's tip; three on him; dead in ~150 ticks.
- **t3376–4587** → `melee-lock`: Horror (tox) locked before he threw; Tasya, Horror, Tooth downed.
  Four out, none of ours down — but the fights drifted to the tip and north of it, in view of a
  free shotgunner (Dek) and three gunners holding at 15–20 cells.
- **t4587–5835** `raid-holds` `fire`: molotovs sidestepped, but the grass fire reached pawns;
  Curne down, Bilegoda down.
- **t6097–8236** `kidnap` → `chase-carrier` `carry-downed`: Manatee killed on his way to the
  carrier; Davenport walked off the west edge with Bilegoda; Crica carried Curne away.

- Attempts 2–3 (journal): the opening worked each time (2–4 raiders out at a corner or a door);
  then gunners holding at 10–20 cells shot into every opening our melee pawns stood in, and the
  raid ended by kidnapping. Seizz also has **Fire spew** (raiders' abilities are not in the card).

## What the play stood on (observed)
- Site: the **west rock pocket** (sites.md): rock B hides the pocket from the east; raiders
  coming along z 143 must round B's north tip, 4–6 cells from the pocket.
- The raid all targeted one pawn (Crica) and walked straight at the rock in a long column.
- Gunners who held back at 15–20 cells were out of reach for a melee squad; the pawns that left
  the pocket to fight at the tip were shot.

## Sources
journal `journals/rand_015_claude_20261005.md` · trace `results/human/traces/rand_015_claude_20261005-104313.jsonl.gz` ·
sheet `sheets/rand_015_start.md` · naive agent row `results/night/router.jsonl`
