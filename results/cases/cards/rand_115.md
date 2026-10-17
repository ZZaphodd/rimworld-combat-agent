# rand_115 · Waster tox throwers ×8 (no guns) vs Neanderthal melee ×6 · open — won by the human

**Situation:** `open-arena` `raid-far` `raid-melee` `raid-strong-1v1` `us-outnumber` `us-low-skill`
**Plays seen:** `tox-room` (new) `mouth-hold`-like door hold `kite` (naive agent; Claude attempt 3) `breach` (by deconstruction) `area-tox` `molotov-at-mouth` (new, the human)
**Numbers:** ours 8 (explosive 8: 7 tox, 1 molotov), range 12.9 · raid 6 (melee 6), 285 pt, closer share 1.0 · count ratio 1.33 · raid from the NNW edge (37–49, 242–247), ~145 cells

## Sides
- Ours (shooting/melee): Hizak 8/8 molotovs; Fizzman 9/5 tox (moving 82%); Levy 3/6 tox (the
  raid's target); Ambush 2/4 tox, drill arm; Faz 1/2; Blurkap 0/1; Skalder 0/0, elbow blade;
  Albert 0/2, elbow blade. **All but Albert showed no tox hediff in the gas** (Wasters); Albert
  took toxic buildup like the raiders.
- Raid (TribeRoughNeanderthal): Antelope ikwa (melee 8), Crocodile knife (6, Jogger), Alobi
  ikwa (5), Jackal granite club (5), Stinkbug marble club (2), Nebar spear (1, berserker).

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| naive agent `kite` | pack kite | open ground | squad down t7796, 0 kills | 1 dead, 7 downed | 84.8 |
| Claude attempt 1 | hold ruin room R2 (three 1-cell doors), tox at the raider in each door | big ruin R2 | defeat (1 captive); 5 of 6 raiders dead/down | 1 dead + 1 kidnapped, 3 downed | 80.8 (70.8) |
| Claude attempt 2 | same room; non-immune Albert kept outside; throws from the north door before contact | big ruin R2 | defeat (2 captives); 4 raiders dead | 2 kidnapped, 3 downed | 88.8 (68.8) |
| Claude attempt 3 | gas kite on open ground | open | defeat (3 captives); no raider lost | 3 dead + 3 kidnapped | 146.9 (116.9) |
| **human** (2026-10-18) | Ambush, undrafted, carried a job to deconstruct one cell of the walled hall's south wall, (209, 167), from the start, walked there with the squad and took it down on arrival (~570 ticks, the others waiting); seven packed just inside it, Albert further in; attack-area orders from ~600 ticks before the first raider reached the breach, Hizak's molotovs on the breach | NE ridge + walled hall, breach (209, 167) | **repelled**, t7041: 3 dead, 2 downed, 1 fled; raid fled t5907 | 0 lost, 4 downed, 7 permanent | **39.5** |

Brackets: Claude's rows with today's badness (`rca.eval.ranking`, a kidnapped pawn counted once since
2026-10-07); the numbers before them were written with the double count.

## Scenes
- **Attempts 1–2, t3600–7300**: tox thrown at the raider in a doorway filled the closed room.
  Every raider got "Tox gas (severe)" with buildup ~+0.05 per 150 ticks, reaching 0.73–0.80 and
  consciousness 63–77%. Raiders died in the doors or of the buildup. Our Wasters were
  unaffected.
- **Attempts 1–2**: Antelope (melee 8) downed two of ours at the west door each time. Downed
  pawns at or near a door were carried off **while the fight went on** (Stinkbug took Hizak at
  t~4000 in attempt 2). Three fist-fighters needed 1000–2000 ticks to kill a carrier.
- **Attempt 3**: in the open the gas thinned (buildup ≤ 0.07). Ungassed Neanderthals kept up
  with the group and picked off one pawn at a time.
- **Human, intents (told after the battle):**
  - Before any tick passed the player checked the squad's construction skills and judged, roughly,
    that they were enough to open a wall by deconstruction, so the wall was deconstructed. Had they
    not been, the plan was Albert as a bait led round and about, and the three strongest in melee
    breaking the weakest wall and going in.
  - The molotovs were deliberate. A raider set alight on impact moves about trying to put the fire
    out, breathing the gas, instead of attacking ours in melee, so the damage goes up. Burning
    ground takes the raid's way in away for a while, or makes it longer: again less potential
    damage to ours and more gas damage to them.
  - Albert, the only one who is not a Waster, looked unable to survive inside the room, and more
    tox from him would not have helped the repel. He hit the wall so that, if it broke, he could get
    out and live, to cut the badness at least: by then the fight had tilted well our way, so getting
    out was enough to survive and keep the badness down.
- **Human, t0–2404** `raid-far` → `breach`:
  - From t28 (the second poll) Ambush (drill arm), undrafted, carried a job to deconstruct the
    hall's south wall cell (209, 167) and walked there with the seven, who went drafted (~95 cells).
  - Ambush was at the wall by t1649. The job ended at t2221 (~570 ticks of work); the seven waited
    on (208–210, 161–163).
  - All eight went in by t2404. Seven packed on (208–210, 169–172), right inside the breach;
    Albert, the one pawn without tox immunity, stood further in, at (209, 174), then (210, 178–180).
- **Human, t2644–3241** `approach` → `area-tox` `molotov-at-mouth` `mouth-hold`:
  - At t2644, with the raid's front 33 cells west, everyone but Hizak went on attack-area orders
    ("attacking area"; the target cells and the tox grenades in flight are not in the trace), and
    Hizak joined by t2775. The first raider reached the breach at t3168–3241, ~520–600 ticks later.
  - Hizak threw molotovs from ~t2860. By t2946 the breach cells burned ((208, 166), (208, 168),
    (209, 167)); from t3168 to the end 7–17 cells burned, most of them within 4 cells of the breach.
  - Crocodile came first, then Stinkbug; Antelope, Jackal and Nebar queued outside.
- **Human, t3168–5907** `melee-contact` `fire` `our-downed` → `area-tox` (kept):
  - Five raiders had jobs "extinguishing fire on <self>" at some point (all but Stinkbug). Their
    "wandering" polls mostly had a fire on their own cell (Antelope 25 of 38, Jackal 17 of 20);
    away from the breach that fire moved with them, so they were burning.
  - Stinkbug stood inside the block at (211, 171) from ~t3600, then (210, 171) from t4909,
    melee-attacking at 100% health in every poll up to t5175; by t5252 he was dead there (his
    corpse lay on (210, 171)). The trace has no hediffs, so it does not show what killed him.
  - Ours stayed on the area orders with raiders adjacent; Hizak went to melee from ~t4275.
  - Fizzman went down at ~t3779, Blurkap at ~t4590, Skalder at ~t4730. Each had "Crawling to
    safety" and moved 5–6 cells north into the hall ((207, 175), (210, 177), (205, 176)).
    No raider carried anyone.
  - Nebar went deep into the hall, met Albert at (204–205, 181–182) from ~t4733, and was downed
    there by t5252. Crocodile was downed unconscious at 80% by t4822 and died by t6515.
  - Levy stood on a burning cell, (209, 170), in every poll from t4909 while throwing, with Alobi
    attacking him from the next cell (t4822–5655). He was at 76% by t5512. From t5596 he was
    "wandering" with a fire moving with him, out through the breach (~t6037) and round the hall to
    the north, down to 51% at the end.
- **Human, t5907–7041** `raid-breaking`:
  - The raid fled at t5907; Jackal, last seen at (205, 162) at t5823, had died just before (the
    watcher's corpse list: (206, 163)). Antelope, burning, left east. Alobi fought on just inside
    the breach: Hizak, Faz and Ambush were on him in melee t5655–5914, and he was on Faz until
    ~t6203. He then moved about the breach and was downed at (209, 168) at ~t6857.
  - Albert came to (210, 172), by the breach, after the flight and was down unconscious at 100%
    health by t6515. At the end Faz had the job "carrying Albert" and Ambush was tending Fizzman.

## What the play stood on (observed)
- A closed room keeps tox gas thick; open air does not.
- No guns and no melee weapons. Claude's card had the breach sites (the nook, the NE hall) closed
  to this squad: in its game the throw gizmo was the only attack offered with grenades held,
  nothing with them dropped, and deconstruction was not tried (journal). In the human's game
  Ambush deconstructed a granite wall cell (~570 ticks), and Albert, holding tox grenades,
  melee-attacked another from t5257 (96% at t5427 → 81% at t5907).
- Kidnapping, not the fight, decided Claude's two R2 attempts; in the open (attempt 3) the raid
  lost no one. In the human's game nobody was carried: the three downed at the breach crawled 5–6
  cells into the hall, while the raiders inside had jobs of melee attacking, burning ("wandering")
  or putting themselves out. The trace does not show why none picked anyone up.

## Sources
journal `journals/rand_115_claude_20261005.md` · traces `results/human/traces/rand_115_claude_20261005-{124516,130226,131140}.jsonl.gz` ·
sheet `sheets/rand_115_start.md` · naive agent row `results/night/router.jsonl` ·
human: report `results/human/reports/rand_115.md`, trace `results/human/traces/rand_115_human_20261018-043556.jsonl.gz`
