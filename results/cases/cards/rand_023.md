# rand_023 · savage tribe ×10 (all melee) vs outlanders ×8 with a shooting-19 revolver · forest — won by the human

**Situation:** `forest-arena` `raid-far` `raid-outranges` `us-outnumber` `us-melee-pawns` `top-threat`
**Plays seen:** `concealed-wait` `cover-path-start` `mark-shooters` `dealer-shields` `loadout` `breach` (failed) `carry-downed` `melee-lock`
**Numbers:** ours 10 (all melee), range median 1.5 · raid 8 (short 7, melee 1), 415 pt, outrange share 0.88, no explosives · count ratio 1.25 · raid from the south-west corner (32–44, 0–6), ~151 cells

## Sides
- Ours (shooting/melee, weapon): Whale 2/11 wooden club → steel spear (Ram's); Colmea 4/6 knife
  (poor); Ram 2/5 steel spear → club; Hornet 2/5 steel spear; Bustba 2/3 knife, Tough; Emsea 0/3
  ikwa (poor); Tiger 7/3 knife (awful); Salamander 1/2 ikwa (awful); Emñobi 5/0 club; Gorilla 0/0
  ikwa (awful). No armour, no abilities.
- Raid: **Lissa** revolver (19/8, flak vest + jacket); Furr autopistol (11/4); Cholaky autopistol
  (6/1); Van pump shotgun (4/4); Jenn pump shotgun (3/0); Nytro machine pistol (0/0, Slowpoke);
  Werner revolver (good; 0/6); Toni steel knife (2/13).

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| agent `amove` | mass charge | near the start | squad down at t3051 | 2 dead, 8 downed, 9 permanent | 101.8 |
| **human** (Claude's loadout) | waited hidden and packed in the small ruin so the raid strung out (worst threat last); at contact one of ours on each shooter, two groups each led by a dealer (Whale, Hornet) with meat shields; Gorilla (low damage) locked the revolver ace; then all chased her | small ruin | **decisive**, all 8 dead | 1 dead, 0 downed | **25.6** |
| Claude (replay of the user's play) | same loadout and ruin cells; marks went out when a raider was within 5 (the rest 9–18 away); dealers on locked raiders; Gorilla on Lissa | small ruin | enemies cleared, pyrrhic | 2 dead, 4 downed | 60.4 |
| Claude (alone) | breach the NE walled hall to hide in its blind cells (breach failed); fought outside | NE walled hall, south-east corner | squad down | 4 dead, 6 downed | 100.2 |

## Scenes
- **Human, intents (told after the battle):** the small ruin was chosen both to hide and to let the
  raid string out; the worst threat (Lissa) arrived late as a result. Two teams on purpose: Whale
  and Hornet the dealers, the rest meat shields. Gorilla, low damage, was a good pawn to send to lock
  Lissa. Toni was handled passively: he came in before we left the hidden spot and died for free;
  with our numbers he was not counted a big threat.
- **Human, when to leave the ruin (told after Claude's replay):** cells hidden from a raider's gun
  by cover are not shot at, so the player traced the raiders' sight and set off when the walk to
  the marked shooters, counting the exposed cells only, became the shortest. Both groups had to
  set off together: if the raid hugs the north side, the group going round the south has a long
  way. Measured on the traces (`rca.terrain` LOS, snapshot, guns' ranges): at the player's start
  (t2459) the seven movers had 43 exposed steps in all (most 10), the low of the last 150 ticks
  (72 → 50 → 44 → 58 → 43); at Claude's replay start (t2315) ten movers had 95 (most 19).
- **Human, t1325–2578** `raid-strung-out` → `concealed-wait`: ten packed in the small ruin
  (145–150, 108–111); the raid's front reached them with Lissa 50 cells behind.
- **Human, t2578–3983** → `mark-shooters` `dealer-shields`: one of ours on each shooter, Whale's group
  of four round the south; Toni, Van, Furr, Jenn, Nytro, Werner, Cholaky dead; Salamander killed by a head shot from Lissa's
  revolver at ~23 cells (seen by the player in the game's UI).
- **Human, t3187–5889** `raid-holds` → `melee-lock`: Lissa held at ~23 cells; Gorilla sent to lock her,
  then everyone chased her ~80 cells south: dead t5889.
- **Claude replay, t2315–2728** `raid-strung-out` → `concealed-wait` `mark-shooters`: marks out at
  5–18 cells; Emñobi (melee 0), marked on Jenn 12 cells away, was caught by Toni on the way and
  died under his attacks without fighting back.
- **Claude replay, t3285–3973** `top-threat` → `melee-lock`: Lissa held at (128, 88) as in the user's
  run; Gorilla downed on arrival (shot 100 → 39% on the walk); Lissa free for ~570 ticks, Colmea
  shot dead; Ram and Whale then locked and killed her (t4893).
- **t1650–4729** → `breach` (failed): three pawns hit the hall's granite wall at (213, 167) with
  the order re-issued every 45 ticks (cancelling the swings): 95 → 93%; the loop did not watch
  the raid, which arrived unseen and caught the squad outside.
- **t4970–6232** → `carry-downed` `melee-lock`: carried the downed behind the hall's east face;
  locked Nytro and Van when they came round the corner; the shotgun downed the lockers.

## What the play stood on (observed)
- Site: the **NE walled hall** (sites.md): no door; inside 203–213 × 168–182 all hidden; a mouth at
  (213, 167) would keep a 32-cell block (203–211 × 168–172) hidden from every outside cell within
  35 — untested.
- All raiders targeted one colonist (Hornet) and walked at him from the south-west.

## Sources
journal `journals/rand_023_claude_20261005.md` (attempts 1–2) · traces `results/human/traces/rand_023_claude_20261005-112931.jsonl.gz`, `rand_023_claude_20261005-191247.jsonl.gz` ·
agent row `results/night/router.jsonl`
