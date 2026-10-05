# rand_023 replay start sheet: Claude plays the user's way (2026-10-05 evening)

The plan is the user's winning play (`cards/rand_023.md`, report `results/human/reports/rand_023.md`,
25.6), not a retrieval: the point is to see whether Claude reproduces it.

## The user's play, as told and as traced
- **Loadout:** Whale (melee 11) ↔ Ram: Whale gets the steel spear.
- **`concealed-wait`:** all ten packed in the small ruin (145–150, 108–111), drafted, until the
  raid's front is ~4 cells away. The raid strings out on the way: Toni (knife) first, Lissa (revolver,
  shooting 19) ~50 cells behind.
- **`mark-shooters`:** at contact, one of ours on each shooter, in order of danger.
- **`dealer-shields`:** two groups, each with a dealer: Whale's (Whale, Ram, Salamander, Gorilla)
  round the south of the ruin, Hornet's (Hornet, Emsea, Colmea, Tiger, Bustba, Emñobi) the rest.
- **Toni:** passive; he runs in and is ganged where he lands.
- **Lissa:** Gorilla (melee 0, low value) locks her when she holds at range; once the rest are
  dead, everyone chases her.

## Controller (scratchpad `mark23.py`)
- Hold until a raider is within 5 cells of ours.
- Shields (non-dealers): the more dangerous / nearer of the two most dangerous unmarked raiders
  within 20 (DANGER: Furr, Van, Jenn, Werner, Cholaky, Nytro, Toni).
- Dealers (Whale, Hornet): the most dangerous raider already locked, nearest first; spare
  pawns join their group's dealer.
- Gorilla to Lissa once contact has started and she is within 40.
