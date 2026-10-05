# Tags: the situation, named as it is seen

The tags are not rules. They name what a battle or a moment looked like so that a later
battle can find the ones that looked the same (retrieval in README.md). The list grows
from play: a new tag is added when a scene needs one, marked *(new, date)* until the user has
looked at it, and renamed or merged when two turn out to be the same thing.

A card lists its **situation tags** (what the problem is) and **play tags** (what was done).
A scene lists both for that moment.

## Situation: the matchup (battle level)

| tag | meaning |
|---|---|
| `forest-arena` / `open-arena` | which night arena (sites.md: same map, open = trees cleared in the middle) |
| `raid-far` | the raid starts ≥ 120 cells away: ≥ ~2000 ticks to set up |
| `raid-melee` | ≥ 0.4 of the raid fights in melee |
| `raid-throwers` | ≥ 2 frag or molotov throwers |
| `raid-sniper` | a long rifle (range ≥ 37) in a good shooter's hands (shooting ≥ 10) |
| `raid-outranges` | most of the raid outranges our median range |
| `raid-armoured` | flak / recon armour on most of the raid (Empire) |
| `raid-strong-1v1` | each raider beats one of ours in melee (xenotype, skill, armour) |
| `raid-outnumbers` / `us-outnumber` | count ratio ≤ 0.9 / ≥ 1.3 |
| `us-low-skill` | most of ours shoot ≤ 4 |
| `us-bows` | bows are our main weapons |
| `us-short` | our median range ≤ 18 (pistols, shotguns, throwables) |
| `us-melee-pawns` | ≥ 2 of ours with melee ≥ 8 or Brawler |
| `us-skill-mismatch` | weapons start in the wrong hands (fixable by a loadout) |
| `us-outrange` *(new, 2026-10-05)* | our good shooters outrange the raid (rand_011: two 37-cell rifles vs a median of 20) |
| `raid-low-skill` *(new, 2026-10-05)* | everyone in the raid shoots ≤ 5 |

## Situation: the moment (scene level)

| tag | meaning |
|---|---|
| `approach` | the raid is walking in, out of range |
| `raid-strung-out` | the raid's runners are ≥ 15 cells ahead of its body |
| `raid-split` | the raid is in two groups ≥ 10 cells apart (e.g. round both sides of a hill) |
| `raid-holds` | the raid's gunners stop at their own range and wait |
| `thrower-close` | a thrower is within 13 cells of ours |
| `melee-contact` | raiders are in melee with ours |
| `outflank` | a raider comes round the far end or side of our position |
| `no-los` | our targets are out of sight (attack orders refused) |
| `fire` | fires burn between or among the sides |
| `our-downed` | one of ours is down |
| `our-downed-exposed` | one of ours is down outside the group |
| `kidnap` | a raider is carrying one of ours |
| `enemy-downed` | raiders lie downed near us |
| `top-threat` | one raider is clearly the most dangerous (skill, weapon) |
| `raid-breaking` | the raid flees or gives up |
| `no-enemy-melee` *(new, 2026-10-05)* | the raid has no melee pawn left standing: ours can lock its shooters and none of ours can be locked (rand_011, the player's reasoning after Pablo died) |

## Plays: what was done

| tag | meaning |
|---|---|
| `loadout` | weapons swapped at the start (`manage_gear` drop + equip): guns to shooters, blades to melee pawns, throwables to the worst shooters |
| `hide-wait` | wait out of the raid's sight until it walks into our range |
| `cover-hold` | hold behind cover (a treeline, walls) facing an open approach |
| `corner-ambush` | wait where the raid must round a corner inside our range |
| `notch-hold` | hold a spot blocked on three sides |
| `mouth-hold` | hold a narrow entrance so only the pawns at the mouth fight |
| `rotation` | a wounded front pawn steps back, a fresh one steps in |
| `breach` | break a wall or object (several pawns, one swing per order) |
| `gap-slip` | move through a gap so rock cuts the throwers' sight |
| `kite` | keep moving away in a pack; the raid strings out behind |
| `tox-room` | hold a closed room and throw tox at raiders coming through its doors, with tox-immune pawns inside |
| `stepped-withdrawal` | fall back a bound, turn, kill whoever followed, repeat |
| `skirmish-line` | a spaced line in the open |
| `smoke` | pop smoke at contact |
| `molotov-into-group` | fire into a bunched group |
| `focus-top-threat` | everyone on the most dangerous raider first |
| `melee-lock` | a melee pawn engages a raider's gunner or thrower: in melee it cannot shoot (the user's term; renamed from `melee-tieup` 2026-10-05). One-sided once the raid has no melee pawn left (`no-enemy-melee`) |
| `carry-downed` | carry our downed along / inside |
| `chase-carrier` | pursue a kidnapper, stopping to shoot or catching it in melee |
| `edge-block` | stand on a kidnapper's way to the edge |
| `finish-downed` | kill downed raiders in melee |
| `frag-dodge` *(new, 2026-10-05)* | move only the pawn a frag is aimed at, as it is thrown (the player's method, rand_011: the launch makes a whoosh; paused, step the game a frame or two to see the grenadier and the grenade and read the target or landing cell; move that pawn ~2–3 × the blast radius to a cell with no friendly-fire line that still shoots at the raid). Strangler: ~5 frags within 1–3 cells, no frag wound |
| `bait` *(new, 2026-10-05)* | a cheap pawn sent out alone to draw the raid's fire, so the shooters in the line need not move and keep shooting (rand_011: Olaf, the player's intent) |
| `ability` *(new, 2026-10-05)* | a gene or psychic ability used (rand_011: Mila's Fire spew); `hands.brief()` lists them |
| `gang-melee` *(new, 2026-10-05)* | everyone standing piles onto one raider in melee |
