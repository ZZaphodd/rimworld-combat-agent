# rand_127 — Claude playing directly (2026-10-05): turn log

Record of the orders given (episode ticks), via `tools/hands.py`; trace
`traces/rand_127_claude_20261005-082459.jsonl.gz`. Result: repelled, 0 lost, 1 downed (Crica),
1 permanent injury, badness 10.8.

| t | orders | what followed |
|---|---|---|
| 0 | loadout: drop Mabe `Pila`, Grasshopper `MeleeWeapon_Ikwa`; equip each other's item | done t122 |
| 122 | draft all; Go here: Crica (210,84), Trout (210,85), Mabe (209,84), Raraguatas (208,85), Barracuda (205,86), Laque (205,85), Ñala (206,85), Tol (206,86), Grasshopper (206,84), Owl (205,84) | Crica/Trout stopped at x 207; re-ordered at t1576, adjacent to the wall at t1666 |
| 1666–2774 | wall `Wall3166` at (211,84): `Command_VerbTarget` every 90 ticks by Crica, Trout (melee) and Laque, Ñala, Owl, Grasshopper (ranged) | 91% → 61% → 36% → 21% → down after 11 rounds |
| 2774 | all into the nook (the human's t2995 cells): Barracuda (213,83), Laque (212,82), Crica (212,83), Ñala (213,84), Tol (214,85), Mabe (213,86), Raraguatas (212,84), Trout (212,82), Grasshopper (213,85), Owl (214,86) | all in by t2985; raid leaders 13–15 cells out |
| 2985 | mouth cells: Mabe (212,83), Crica (212,84); Raraguatas back to (213,86); Trout (213,82) as reserve | Mabe ended on the breach cell (211,84); pulled back to (212,84) at t3256 |
| 3256–4600 | urn `Urn3182` (212,85): Grasshopper, Ñala, Raraguatas, Owl, Tol hit it; after round 5 only Grasshopper + Raraguatas | 82% → 2.9%, never fell; Mabe later stood on that cell (3 pawns touching the mouth) |
| 3500–6000 | rotation: a mouth pawn below 45% swaps with a reserve (Trout, Barracuda, Laque) | Mabe 48% → Trout (t4562); Crica 41% → Laque (~t5600) |
| — | raid at the mouth one at a time | Gabobrei, Iguabust, Dragonfly, Bargodue dead; Bacchus downed in the breach; raid fled t6213 |
