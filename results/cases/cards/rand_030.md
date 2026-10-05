# rand_030 · pig outlanders ×8 (short guns + throwables) vs outlanders ×9 · forest

**Situation:** `forest-arena` `raid-far` `raid-outranges` `raid-outnumbers` `us-short` `us-low-skill` `us-skill-mismatch` `top-threat`
**Plays seen:** `loadout` `hide-wait` `corner-ambush` `smoke` `molotov-into-group` `focus-top-threat` `melee-lock`
**Numbers:** ours 8 (explosive 3, short 5), range median 17.9 · raid 9 (short 5, long, support, melee, explosive), 500 pt, outrange share 0.56 · count ratio 0.89 · raid from the south edge behind a lake, 120 cells

## Sides
- Ours (shooting/melee, start weapon): Pwuis 9/3 frags; Butters 6/11 frags; Trough 4/4
  revolver + smokepop pack; Roller 3/4 pump shotgun (poor); Booug 3/4 machine pistol; Slop 2/4
  molotovs; Bog 0/0 revolver (good); Polork 0/1 machine pistol (poor).
- Raid: **Mushinto** pump shotgun (shooting 14, melee 12), May revolver (8, helmet), Jake
  bolt-action rifle (37), Lang heavy SMG, Smarty frags, Manuel machine pistol, Hawk autopistol,
  Ryorai revolver, Grub knife.

## Plays and results
| who | play | site | result | lost | badness |
|---|---|---|---|---|---|
| agent `close` | advance to close range in forest cover | towards the raid | defeat, captives | 7 (5 dead, 2 kidnapped) | 128.0 |
| human (swap) | loadout; wait behind the rock hill; smoke + molotov at contact | rock hill E | decisive, 9 of 9 out | 1 dead | 21.1 |
| Claude | the same loadout and hill | rock hill E | repelled t3824 | 1 dead, 1 downed, 7 permanent | 38.8 |

## Scenes
- **t0–1000 (human) / t0–135 (Claude)** `raid-far` `us-skill-mismatch` → `loadout`: Pwuis and
  Butters drop frags and take the guns of Bog and Polork (shooting 0), who get the frags.
- **t981–1490** `approach` → `hide-wait`: the squad settles on the far side of the rock hill,
  out of the raid's sight; nobody advances.
- **t2055 (human)** `approach` → `corner-ambush`: the raid must come round the hill's
  north-west corner; whoever comes round first is inside 13–16 cells.
- **t2606 (human)** `melee-contact` `top-threat` → `smoke` `molotov-into-group`
  `focus-top-threat`: contact inside Trough's smoke at 1–15 cells; Mushinto dead in the first
  exchange; molotov fires on the corner and on Hawk.
- **t3631 (human)**: Lang, Hawk, Grub dead, Manuel down; Roller the only loss; Bog (frags)
  works round the south of the hill towards Jake and May. **t3765** `raid-breaking`; the
  runners are shot down.
- **t2175 (Claude)** `raid-split` `no-los`: this time the raid split round both sides of the
  hill (Ryorai + Mushinto north, May/Smarty/Lang/Hawk south); focus orders on Mushinto refused.
- **t2249–2600 (Claude)** `thrower-close` `top-threat` → `smoke` `focus-top-threat`: molotov +
  frag on Ryorai, smoke at t2294; four guns on Mushinto → downed inside the group.
- **t2519–2955 (Claude)** `raid-split` `melee-contact` → `molotov-into-group`: molotov + frag
  into the southern cluster (Lang); Grub on Bog, three on Grub; Grub and Lang dead.
- **t2955–3329 (Claude)** `thrower-close`: guns on Smarty mostly missed; Bog dead ~t3300.
- **t3329 (Claude)** → `melee-lock`: Butters (melee 11) on Smarty; Smarty, May dead; the raid
  fled t3824.

## What the play stood on (observed)
- Site: `rock hill` (sites.md), 55–69 cells east; it hides the squad from a raid coming from
  the south-west, which must round a corner to see us.
- Half our weapons reach 13–16 cells: the fight had to happen inside that.
- The raid was far (~100 cells) when the swap began; the human's swap took ~1000 ticks
  (Claude's, by `manage_gear`, 135).
- The human's raid came round one corner; Claude's split round both (Claude knew the human's
  route; the raid did not repeat it).

## Sources
report `results/human/reports/rand_030.md` · Claude's turns `results/human/raw/rand_030/claude_turns.md` ·
trace `results/human/traces/rand_030_claude_*` (the human's game has no trace: watcher records in
`results/human/raw/rand_030/`) · agent row `results/night/router.jsonl`
