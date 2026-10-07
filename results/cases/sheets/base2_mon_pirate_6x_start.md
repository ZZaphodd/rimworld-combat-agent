# base2_mon_pirate_6x — start sheet (Claude, 2026-10-07)

Problem: Monler v2 (no solar flare), civil outlanders ×8 (shooting 0–8: 2 pump shotguns, HSMG, MP,
revolver, autopistol + low-shield pack, bolt-action rifle, incendiary launcher) vs 28 pirates from
the west edge (4, 124): 7 Elites in marine/recon armour (2 LMG, biocoded LMG, 3 Hellcat rifles,
chain shotgun, assault rifle), 5 sniper rifles, a Doomsday rocket launcher (Woddles, unarmoured),
a minigun, a molotov grenadier, 2 shield-belt slashers, 2 drifters, gunners. Ladder: turtle defeat
119.6 (6 lost: 1 dead, 5 kidnapped), turtle_at (R2, packed on the axis) defeat 113.3 (4 dead,
3 kidnapped; two burned by superheated air in R2).

Cards (tools/cases.py similar): base_mon_tribe_3x (same site), base_ith_pirate_2x, base_ith_tribe_2x.
- base_mon_tribe_3x (the user, repelled 1.9): R2 with the passage doors (145, 94), (145, 86) and
  R2's door held open, everyone within 3 cells of the door, frags on an area order up the passage.
  Differs: tribal bows then, guns with 33+ cell sight lines now (snipers, LMGs) — the passage axis
  x 145 is seen from ~50 outside cells up to 33 away (save-map LOS), so no one stands on x 145.
  Borrow: the site and door states. 7 raiders went down early on the west yard near the trap lane
  (x 100, z 130–146) in that play.
- base_ith_pirate_2x / base_ith_tribe_2x (Claude): plug + guns 2+ cells from the doorway; guns
  can't fire at an adjacent raider. Borrow: 2+ cells.

Plan:
- Cells (off the axis, each sees the doorway (145, 84) at 2–4 cells, hidden from the passage):
  Egan SG (144, 82), Rutana SG (146, 82), Merlicek MP (143, 81), Willy HSMG (147, 81),
  Dan revolver (142, 82), Adam BAR (148, 82), Kieri AP (144, 80), Willow IncL (146, 80) fire held.
- Kieri deploys the low shield (radius 4.9, 1800 ticks, bullets out not in) when the raid reaches
  the passage bottom: from (144, 80) the corridor z 85 is outside it, the doorway inside, so only
  a raider in the doorway can hit us.
- Targets: Woddles (Doomsday) and the molotov grenadier first, on sight.
- Downed of ours: carry to the back of R2 (z 75–77) in lulls (kidnap risk).
