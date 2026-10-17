# d2 / rand_058 / opus55_los — plan

- Raid: 8 Outlander civils (3 pump shotguns, 2 revolvers, 2 autopistols, 1 knife), no explosives,
  walking in from the SW corner (~150 cells). Forest at night, no real cover except a small steel
  ruin at x144-150, z107-112 and rock chunks.
- Where: the ruin interior (rows z108-109). sight.py says no cell in the W/SW/S can hit those cells
  (walls on S and W, closed door at 148,107); they are visible only from a N cone and an E/SE cone.
  Raiders coming from the SW must walk round a corner and show up 3-10 cells away, piecemeal.
- Cells: Pigork (146,108) molotov, Trev (148,108) revolver behind the door, Moinork (149,108)
  molotov, Poinis (145,109) frag, Poinlaoik (146,109) shotgun, Furr (147,109), Curly (148,109),
  Paul (149,109) shotgun. Everyone drafted, fire at will on for guns.
- Play: focus fire on whoever rounds a corner first; throwers held (fire at will off) and ordered
  only at raiders >= 4.5 cells from our pawns, stop() after each throw (standing attack job).
  Use who_can_hit / targets to check windows; step 30-60 ticks in contact.
