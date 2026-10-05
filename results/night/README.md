# Router night run, 2026-10-05 00:36–04:20 (roadmap 3: failure mining)

129 random problems, 500 pt vs 500 pt on Strive to Survive (PROCEDURES §15): our squad = a
recruited raid of a random human faction (no mechanoids: they need a mechanitor), the enemy = a
raid of a random faction incl. mechanoids, on arena_forest_night / arena_open_night. Claude was
the router (one doctrine + options per problem, reason in `router.why`); the Python agents
fought. `worst.md` = the 100 worst by badness, each replayable with
`python3 tools/run_human.py --manifest scenarios_rand/scenario_<id>.json` (saves
`scenario_rand_NNN` are local, not in the repo). Problem 130 was built but not played.

Grades: decisive 29, repelled 43, pyrrhic 15, defeat 41, unresolved 1; 13 raids left with
captives. Router choices: kite 42 (29 wins), close 45 (28), doctrine 19 (7), turtle 11 (5),
amove 11 (3), spread 1 (0). n = 1 per problem: every line below is a hypothesis for the gate.

Router rules that held (draft for the rule-based router, roadmap 6):

| Situation | Choice | Record |
|---|---|---|
| Ranged mechs that hold back (lancer, pikeman, legionary) | close | 9 / 9 won (decisive mostly) |
| Short-range mechs that must come (militors) | turtle | 1 / 1 decisive |
| Melee rush (≥ 0.4 melee) vs a gun squad | kite | ~20 wins; losses only with bow or all-thrower squads |
| Melee-heavy squad (≥ half melee) vs anything | close | best tool for melee squads; amove and doctrine 0 / 5 vs gunners |
| Melee squad vs Empire raids | close | 4 / 4 won |
| Even gun duel, few throwers | doctrine (focus fire) | 4 / 4; outnumbered duels lost |
| Pure thrower raid | doctrine | 2 / 2 decisive |
| Forest + grenadiers | close | mostly won (v2 and tonight) |
| Throwers + guns on open ground | – | volatile: every doctrine lost at least once (mass kidnapping) |

Losing types (no doctrine won; candidates for human demonstrations):
- tribal bow squads vs gun raids: 0 / 6 (turtle, doctrine, kite, close);
- all-thrower squads: 1 / 6, even when outnumbering a melee rush;
- gun squads vs Empire raids: 0 / 4 (kite, doctrine, close, turtle) — while melee squads beat them 4 / 4;
- savage-tribe squads (poor short bows, poor melee): 9 defeats in 12.

Mechanisms seen:
- **Kidnapping is the main loss on Strive**: long fights (> ~10 000 ticks) wear pawns down one by
  one and the raid leaves with them (rand_030: all 9, rand_067: all 9, rand_107: 9). Staying packed
  kept downed pawns from being carried off (rand_106: 5 downed, 0 lost).
- Low-point mechs loiter: kite never advances while melee mechs are near → stalemate (rand_004).
- Melee brawls are decided by numbers (wins at 9 v 9, 10 v 6, 11 v 6; losses at 5 v 6, 5 v 8) and
  cost many permanent injuries (rand_018: 23).

# Second mining run, 2026-10-05 13:50–~16:30 (rand_130–230)

101 problems, built and played the same way (Claude routing by the table above, the frozen
Python agents fighting, `tools/night.py`). Asked for by the user once the worst list reached
problems the agent had won. Rows run until the raid is gone (`end_rule: raid_gone`), so
kidnapped pawns count and badness is higher than in the first run for the same losses; the
second run's ranking is `worst_2.md`.

Grades: repelled 37, decisive 21, pyrrhic 6, defeat 35, unresolved 2 (timeouts).
Router choices, won / lost (defeat or unresolved): close 37 / 12, kite 17 / 4, doctrine 6 / 16,
turtle 3 / 2, amove 1 / 3. n = 1 per problem.

What the second run showed (observations against the table above):
- **Doctrine in gun duels lost 16 of 22**: civil / outlander / pirate mirrors and duels with
  throwers (rand_130, 150, 168, 186, 221, 226, 227) mostly ended with the raid leaving with
  captives. The first run's "even gun duel → doctrine 4 / 4" did not hold.
- **Gun squads vs Empire raids: 2 wins in 10** (both `turtle` against melee-champion raids,
  rand_175 and rand_202; turtle also lost twice, rand_192 and rand_215; doctrine, kite and close
  lost).
- **Bow and savage squads vs guns** lost again with every router choice tried, amove included
  (rand_138, 169, 178, 190, 218).
- `close` with melee squads, `close` vs ranged mechs (rand_132, 195, 212, 216, 223) and `kite`
  vs melee rushes kept their records; losses there came against Neanderthals or Empire
  champions (rand_158, 164, 165, 170, 229).
