# rand_006 start sheet (2026-10-18)

Savage tribals ×8 (6 bows, 2 ikwas; Berro 12/9 holds an ikwa, Red 0/0 a greatbow, Cane 9/11 a bow)
vs 13 Drifters (pirates), all melee (Wttytt knife 12 Brawler, Bryan 9, Eva 8, Lainey 8, Jumper 7,
the rest 0–4; most weapons at 24–59%), open arena, raid from the south edge (175–187, 0–6), 133
cells, all targeting Hare. No wild animals. Count ratio 0.62.

`cases.py similar` gives base arenas first; the close ones are the mouth holds against all-melee
raids:

**rand_094** (today, open): the nook mouth, two melee pawns on the cells touching it, four guns on
the raider in it, one rotation; none of ours down. Deconstruction by one undrafted pawn, the job
given at the start (it had to be drafted and undrafted once to take it).

**rand_118 / rand_127** (nook, open and forest, bows vs melee): bows on the raider in the mouth
shot; bows on raiders farther out sat "attacking" without shooting (use the float menu's Fire at,
check shots).

**rand_115 / rand_164** (the NE walled hall, open and forest): a one-cell breach in the south wall,
(209, 167), deconstructed; one raider at a time.

Differs: here the raid starts 86 cells from the nook (ours 96), so the nook cannot be opened in time;
the walled hall is ~95 cells for us and ~166 for the raid. Thirteen raiders, not six or seven.

## Plan
- Loadout: greatbow Red → Berro (12); ikwa Toad → Cane (11); ikwa Berro → Llolou (6, Nimble);
  recurve Cane → Toad; short bow Llolou → Red.
- Site: the walled hall. Breach the south wall's corner cell (213, 167) by deconstruction (Red,
  construction 13, undrafted; draft and undraft him once). sight.py with it open: only (212, 168)
  and (213, 168) touch it (the corner (214, 168) is wall); (213, 169), (211–212, 170–173) shoot it
  and see the queue outside (212–214, 164–166).
- Front: Cane (212, 168), Llolou (213, 168). Bows within 5 cells of the front (no interception
  by our own): Berro, Blue, Toad, Hawk, Hare, Red on (213, 169), (212, 170), (211, 171), (212, 171),
  (211, 172), (212, 172). Fire at the raider in the breach first. Rotate a front pawn below ~45%
  (Hare, melee 5, or Berro, melee 9, after a weapon swap).
