# base2_ith_tribe_6x — start sheet (Claude, 2026-10-07)

Problem: Ithfunda v2, civil outlanders ×8 — Smith 15/9 steel knife (Jogger), Kate 5/8 revolver
(Pop firefoam), Hono 8/0 heavy SMG (flak vest), Kuma 4/0 machine pistol (Careful shooter), Jeyce 1/6
excellent revolver (flak vest), Paulo 1/3 machine pistol (Nimble), Elsie 1/2 steel knife, Felix 0/13
frag grenades — vs 34 TribeRoughNeanderthal from the EAST edge (~244, 132): 12 berserkers (spears),
12 warriors (ikwas), 7 penitents (knives, clubs; Inegato and White melee 14), the chief Abansamitran
(spear, steel plate), a heavy archer (pila), an archer (short bow). Ladder: turtle defeat 99.3 (kidnaps counted once),
turtle_at defeat 73.2 (squad down; 10 killed + 5 inferred).

Cards (tools/cases.py similar): base2_ith_tribe_3x (7.1), base_ith_tribe_2x (6.6), base_ith_pirate_2x
(3.0, 25 melee + throwers), base_mon_tribe_3x (the user's area frags).
- base2_ith_tribe_3x (Claude, repelled 50.0): east-room door hold, melee on the plug and both
  diagonals, guns 2+ back. The raid queued in the corridor; the first plug lasted ~700 ticks, the
  next died in ~200; the axis cells took arrows. Differs: 34 raiders, not 18 (twice the queue), only
  2 bows; a frag thrower now. Borrow: site, cells, plug rotation.
- base_ith_pirate_2x (Claude, repelled 12.3): the raid wrecked the base ~3600 ticks first; molotovs
  thrown into the corridor queue burst in the room (fire on the plug cell). Borrow: throws into the
  queue, but frags (no fire) and only at raiders 5+ cells below the plug.
- base_mon_tribe_3x (the user, 1.9): frags up the passage from the cell right against the wall;
  from one cell further back, off the line, they hit the wall and fell among our own. Here the
  thrower stands on the corridor axis (133, 189), so the line runs straight down the corridor.

Save-map LOS (door open): (133, 188–191) see the corridor z 177–186; (132/134, 189) see z 185–186;
(131, 189), (130, 189–190) see the doorway only.

Plan:
- Loadout: Smith ← heavy SMG (Hono), Hono ← excellent revolver (Jeyce), Jeyce ← Smith's knife,
  Felix ← Elsie's knife, Elsie ← frags (thrown accuracy does not lean on shooting the way guns do).
- Door (133, 187) held open. Felix plug (133, 188); Jeyce (132, 188), Kate (134, 188) diagonals,
  melee on the doorway raider; Elsie (133, 189) frags, fire at will OFF, explicit throws at the
  corridor queue at z ≤ 183; Smith (132, 189), Hono (134, 189), Kuma (131, 189), Paulo (133, 190).
- Rotation: plug below ~50 % → swap with Kate/Jeyce; fallback room through the door (133, 197).
