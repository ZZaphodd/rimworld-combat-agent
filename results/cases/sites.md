# Sites on the night arenas

Sight blockers are only rock (`%`) and walls (`#`) in `rca.terrain` (trees are cover, not
blockers). Both night arenas are one map: `arena_open_night` is `arena_forest_night` with the trees cleared
inside x 50–203, z 50–203 (the dashed square). Rock, ruins and lakes are the same on both, so
a site found in one problem is a candidate in every other. Our squad always starts at
(125, 125); the raid walks in from a random edge.

![sites](img/sites.jpg)

Walking pace seen (drafted squad): 16–18 ticks per cell in the open, ~30 through forest
(rand_084: 95 cells in ~2900 ticks). First contact came at t2000–3500 in every case below.

| site | cells | what is there | from start | used in |
|---|---|---|---|---|
| **nook** | inside (212–214, 81–87); mouth (211, 84) | a pocket between an ancient ruin's wall and rock, open only to the north-west; a marble wall closes it (break it: ~1100 ticks with 6 pawns hitting; 6 rounds of 9 pawns at a 90-tick cadence in rand_118); an urn at (212, 85) beside the mouth (its cell can be stood on once broken; left standing, only (212, 83) and (212, 84) touch the mouth from inside); a column at (214, 84); only (212–214, 84) see far down the lane west (z 84–85); the south part (209–212, 78–82) is out of the lane's sight | 97 E-SE | rand_127 (human, Claude), rand_118 (Claude) |
| **rock hill** | hill ~(170–185, 89–106) | dark ground, **not rock** (no `%` cells in `rca.terrain`): on the forest arena the trees around it hid the squad; on the open arena (inside the cleared square) it hides nothing | 55 E | rand_030, rand_039 (forest) |
| rock hill E | (184–201, 95–120) | waiting spot on the far side of the hill from a south/west raid | 69 E | rand_030 (human, Claude) |
| rock hill E side, low | (187–191, 95–97) | last bound of a withdrawal east | 66 E | rand_039 (Claude) |
| **small ruin** | (144–153, 108–116) | low ruin walls, near the start | 28 E-SE | rand_039 (human, Claude) |
| **west notch** | (29–32, 141–143) | a notch in the west rock mass, blocked on three sides | 96 W | rand_084 (human, Claude) |
| gap | (26–28, 136–140) | a gap through the west rock to its south face (31–34, 135–137) | 98 W | rand_084: slip through it to cut the throwers' sight |
| **west rock pocket** (same place, cell map from `rca.terrain`) | pocket x 25–35, z 140–144 between rock A (13–24, 139–145) and rock B (27–40, 138–145); open to the north; gap to the south-west at (23–26, 139) | seen from the east, B hides the pocket: raiders coming along z 143 round B's north tip (37–40, 145) and are then 4–6 cells away; a corner ambush for melee. Raiders who go north of it (z 150–159) see into the pocket | 96 W | rand_015 (Claude, lost ×2), rand_126 (Claude, won) |
| NE ridge + walled hall | rock ridge x 196–220, z 165–222; a walled hall (walls 202–214 × 167–183, inside 203–213 × 168–182) set against it | **no door**: all 165 inner cells hidden from outside. Break one wall cell (granite) to make a one-cell mouth: at (213, 167) a 32-cell block (203–211 × 168–172) stays hidden from every outside cell within 35 (LOS calc, untested in play) | 95 NE | rand_023 (breach failed) |
| **big-ruin room** | squad waited at (100–106, 39–41); ruin ~(98–110, 38–58) | walled rooms south-west of the start | 88 SSW | rand_065 (human) |
| **big-ruin room R2** | inside (104–107, 46–47), 8 cells; doors N (105, 48), W (103, 46), inner S (106, 45) from R1 (104–107, 43–44), which has a W door (103, 44), a S door (106, 42) and a gap (105, 42) | three one-cell doors, no breach needed; every inside cell touches a door except (107, 47); closed doors block sight, so throws from inside go only through an open door; a closed room keeps tox gas thick | 82 S-SW | rand_115 (Claude ×2), rand_012 (Claude: won; a corpse in a doorway keeps the door open), rand_018 (Claude, R1+R2: lost) |
| W forest edge | (35–51, 118–137) | the treeline west of the cleared square (open arena only: on the forest arena it is just forest) | 83 W | rand_107 (human) |
| SE pocket | (212–216, 28–40) | south-east, by the lake and ruins near the edge | 130 SE | rand_067 (human, end of a kite) |

Not a site but recorded: rand_029 (open) held a north–south line at x 138–144, z 107–148, east
of the start.

Coordinates come from the traces (squad cells when the raid first came within 15) and the
watcher records; reports (`results/human/reports/`) have close-up frames of each.
