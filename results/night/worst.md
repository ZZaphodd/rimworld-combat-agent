# Worst problems of the router night run (100 of 129 battles)

Badness = 10 x lost + 3 x downed at end + 2 x new permanent injuries + HP lost/25 + grade penalty (defeat 10, pyrrhic 4, unresolved 3); rca/eval/ranking.py.

Replay one: `python3 tools/run_human.py --manifest scenarios_rand/scenario_<id>.json`

| # | problem | arena | ours | enemy | router | outcome | lost | downed | perm | HP% | badness |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | rand_107 | open_night | OutlanderRough x9 | OutlanderRoughPig x8 | doctrine | defeat | 10 | 1 | 0 | 731 | 142.2 |
| 2 | rand_067 | forest_night | TribeRough x8 | PirateYttakin x7 | kite | defeat | 9 | 1 | 0 | 687 | 130.5 |
| 3 | rand_030 | forest_night | OutlanderRoughPig x8 | OutlanderRough x9 | close | defeat | 9 | 0 | 0 | 700 | 128.0 |
| 4 | rand_084 | open_night | OutlanderRoughPig x9 | Pirate x8 | doctrine | defeat | 8 | 1 | 1 | 747 | 124.9 |
| 5 | rand_127 | forest_night | TribeSavage x10 | TribeRoughNeanderthal x7 | amove | defeat | 0 | 10 | 25 | 673 | 116.9 |
| 6 | rand_065 | open_night | OutlanderCivil x9 | Empire x6 | close | defeat | 7 | 3 | 0 | 633 | 114.3 |
| 7 | rand_029 | open_night | TribeRough x9 | OutlanderRoughPig x8 | doctrine (vs_throwers=stand_off) | defeat | 7 | 0 | 0 | 751 | 110.0 |
| 8 | rand_039 | forest_night | OutlanderRough x8 | OutlanderCivil x8 | kite | defeat | 7 | 1 | 0 | 626 | 108.0 |
| 9 | rand_011 | open_night | PirateWaster x9 | OutlanderRough x9 | close | defeat | 6 | 4 | 0 | 611 | 106.4 |
| 10 | rand_104 | forest_night | TribeSavage x8 | OutlanderCivil x8 | turtle | defeat | 4 | 4 | 8 | 688 | 105.5 |
| 11 | rand_015 | open_night | TribeRoughNeanderthal x6 | PirateWaster x9 | doctrine | defeat | 7 | 0 | 1 | 581 | 105.2 |
| 12 | rand_023 | forest_night | TribeSavage x10 | OutlanderRough x8 | amove | defeat | 2 | 8 | 9 | 745 | 101.8 |
| 13 | rand_126 | open_night | PirateWaster x10 | Pirate x8 | close | defeat | 2 | 8 | 9 | 696 | 99.8 |
| 14 | rand_058 | forest_night | OutlanderRoughPig x8 | OutlanderCivil x8 | turtle | defeat | 5 | 3 | 0 | 753 | 99.1 |
| 15 | rand_128 | open_night | OutlanderRoughPig x8 | Empire x4 | turtle | defeat | 3 | 4 | 9 | 635 | 95.4 |
| 16 | rand_118 | open_night | TribeRough x9 | PirateYttakin x8 | kite | defeat | 0 | 9 | 16 | 606 | 93.2 |
| 17 | rand_115 | open_night | PirateWaster x8 | TribeRoughNeanderthal x6 | kite | defeat | 1 | 7 | 10 | 594 | 84.8 |
| 18 | rand_012 | open_night | TribeRoughNeanderthal x5 | PirateYttakin x8 | amove | defeat | 2 | 3 | 14 | 435 | 84.4 |
| 19 | rand_018 | open_night | TribeRough x11 | TribeRoughNeanderthal x6 | amove | decisive | 0 | 4 | 23 | 633 | 83.3 |
| 20 | rand_114 | forest_night | TribeSavage x9 | OutlanderRough x8 | close | defeat | 1 | 8 | 7 | 630 | 83.2 |
| 21 | rand_028 | forest_night | OutlanderRoughPig x8 | OutlanderRough x9 | kite | pyrrhic | 4 | 2 | 1 | 685 | 79.4 |
| 22 | rand_033 | forest_night | PirateYttakin x6 | Pirate x10 | kite | defeat | 4 | 3 | 1 | 446 | 78.8 |
| 23 | rand_068 | open_night | PirateWaster x9 | OutlanderRoughPig x8 | close | defeat | 2 | 7 | 0 | 687 | 78.5 |
| 24 | rand_121 | forest_night | TribeSavage x10 | Pirate x8 | close | defeat | 4 | 2 | 0 | 549 | 78.0 |
| 25 | rand_074 | forest_night | Pirate x7 | PirateWaster x9 | kite | defeat | 3 | 4 | 1 | 588 | 77.5 |
| 26 | rand_001 | forest_night | TribeSavage x10 | OutlanderRoughPig x9 | close | defeat | 1 | 9 | 0 | 710 | 75.4 |
| 27 | rand_117 | forest_night | TribeRoughNeanderthal x5 | TribeSavage x9 | close | pyrrhic | 2 | 2 | 14 | 430 | 75.2 |
| 28 | rand_069 | open_night | OutlanderCivil x8 | OutlanderRoughPig x8 | doctrine (vs_throwers=stand_off) | defeat | 5 | 0 | 0 | 345 | 73.8 |
| 29 | rand_096 | open_night | TribeRough x10 | TribeRoughNeanderthal x6 | amove | pyrrhic | 0 | 6 | 14 | 587 | 73.5 |
| 30 | rand_006 | open_night | TribeSavage x8 | Pirate x13 | kite | defeat | 0 | 8 | 9 | 536 | 73.4 |
| 31 | rand_048 | forest_night | TribeSavage x9 | TribeSavage x9 | doctrine | defeat | 1 | 8 | 2 | 626 | 73.0 |
| 32 | rand_053 | open_night | Pirate x10 | Mechanoid x3 | close | pyrrhic | 2 | 4 | 8 | 519 | 72.8 |
| 33 | rand_059 | open_night | OutlanderCivil x9 | Empire x6 | doctrine | defeat | 1 | 8 | 2 | 613 | 72.5 |
| 34 | rand_057 | forest_night | TribeRoughNeanderthal x5 | TribeRoughNeanderthal x6 | amove | defeat | 4 | 1 | 0 | 483 | 72.3 |
| 35 | rand_041 | open_night | Pirate x9 | PirateYttakin x7 | amove | defeat | 1 | 8 | 2 | 589 | 71.6 |
| 36 | rand_016 | forest_night | PirateWaster x9 | Empire x5 | kite | defeat | 1 | 8 | 1 | 605 | 70.2 |
| 37 | rand_094 | open_night | PirateYttakin x8 | TribeRoughNeanderthal x7 | kite | defeat | 0 | 8 | 8 | 481 | 69.2 |
| 38 | rand_060 | forest_night | Empire x5 | OutlanderRough x9 | close | defeat | 4 | 1 | 0 | 300 | 65.0 |
| 39 | rand_024 | open_night | PirateYttakin x4 | OutlanderRoughPig x8 | spread | defeat | 4 | 1 | 0 | 275 | 64.0 |
| 40 | rand_095 | forest_night | TribeSavage x8 | Pirate x9 | doctrine | defeat | 1 | 7 | 0 | 543 | 62.7 |
| 41 | rand_055 | open_night | Pirate x9 | OutlanderRoughPig x9 | close | pyrrhic | 1 | 5 | 7 | 458 | 61.3 |
| 42 | rand_014 | forest_night | TribeRough x7 | OutlanderCivil x9 | turtle | defeat | 1 | 6 | 1 | 507 | 60.3 |
| 43 | rand_103 | open_night | PirateWaster x10 | Empire x5 | close | pyrrhic | 1 | 6 | 2 | 601 | 60.0 |
| 44 | rand_054 | forest_night | Empire x5 | Pirate x8 | turtle | defeat | 1 | 4 | 7 | 343 | 59.7 |
| 45 | rand_070 | open_night | TribeRough x11 | Empire x4 | close | pyrrhic | 1 | 6 | 0 | 672 | 58.9 |
| 46 | rand_116 | open_night | OutlanderRough x8 | OutlanderCivil x8 | doctrine | pyrrhic | 2 | 4 | 1 | 513 | 58.5 |
| 47 | rand_066 | open_night | TribeRoughNeanderthal x6 | OutlanderRoughPig x8 | close | pyrrhic | 3 | 1 | 1 | 464 | 57.6 |
| 48 | rand_091 | forest_night | Pirate x6 | OutlanderRough x8 | close | defeat | 1 | 5 | 2 | 424 | 56.0 |
| 49 | rand_097 | forest_night | OutlanderCivil x7 | OutlanderRoughPig x8 | close | pyrrhic | 2 | 2 | 2 | 537 | 55.5 |
| 50 | rand_003 | forest_night | PirateWaster x9 | OutlanderCivil x8 | amove | pyrrhic | 1 | 6 | 1 | 533 | 55.3 |
| 51 | rand_106 | open_night | PirateYttakin x5 | PirateWaster x9 | kite | defeat | 0 | 5 | 8 | 308 | 53.3 |
| 52 | rand_089 | open_night | Pirate x10 | TribeSavage x9 | kite | pyrrhic | 0 | 7 | 4 | 458 | 51.3 |
| 53 | rand_078 | forest_night | OutlanderRoughPig x9 | PirateWaster x9 | kite | repelled | 3 | 0 | 0 | 469 | 48.8 |
| 54 | rand_026 | open_night | Pirate x9 | PirateWaster x9 | turtle | pyrrhic | 0 | 6 | 1 | 572 | 46.9 |
| 55 | rand_077 | open_night | PirateYttakin x5 | PirateYttakin x8 | doctrine | defeat | 1 | 4 | 0 | 341 | 45.6 |
| 56 | rand_100 | open_night | OutlanderRoughPig x8 | OutlanderCivil x8 | close | repelled | 2 | 1 | 0 | 500 | 43.0 |
| 57 | rand_073 | forest_night | TribeRough x9 | TribeRough x9 | amove | pyrrhic | 0 | 5 | 2 | 467 | 41.7 |
| 58 | rand_022 | forest_night | Pirate x13 | OutlanderRough x9 | amove | repelled | 0 | 5 | 2 | 545 | 40.8 |
| 59 | rand_037 | forest_night | Pirate x8 | TribeRoughNeanderthal x6 | kite | decisive | 0 | 4 | 8 | 299 | 40.0 |
| 60 | rand_087 | open_night | PirateYttakin x5 | OutlanderRoughPig x8 | doctrine | defeat | 0 | 5 | 0 | 366 | 39.6 |
| 61 | rand_080 | open_night | OutlanderRoughPig x8 | Pirate x8 | kite | repelled | 2 | 0 | 1 | 434 | 39.4 |
| 62 | rand_034 | forest_night | OutlanderRough x9 | OutlanderRoughPig x9 | turtle | repelled | 1 | 3 | 0 | 490 | 38.6 |
| 63 | rand_025 | forest_night | Pirate x8 | Pirate x9 | close | repelled | 1 | 1 | 7 | 269 | 37.8 |
| 64 | rand_099 | open_night | OutlanderRough x7 | OutlanderRough x8 | doctrine | pyrrhic | 0 | 4 | 1 | 406 | 34.2 |
| 65 | rand_056 | open_night | OutlanderCivil x9 | TribeRoughNeanderthal x6 | kite | decisive | 0 | 3 | 7 | 235 | 32.4 |
| 66 | rand_125 | open_night | TribeRough x8 | PirateYttakin x7 | close | decisive | 0 | 4 | 1 | 432 | 31.3 |
| 67 | rand_109 | forest_night | OutlanderRough x9 | TribeRoughNeanderthal x5 | kite | decisive | 0 | 4 | 1 | 418 | 30.7 |
| 68 | rand_102 | open_night | TribeSavage x10 | Empire x4 | close | repelled | 0 | 2 | 4 | 403 | 30.1 |
| 69 | rand_063 | forest_night | OutlanderRoughPig x8 | OutlanderRoughPig x9 | close | repelled | 0 | 1 | 7 | 317 | 29.7 |
| 70 | rand_112 | forest_night | TribeRoughNeanderthal x6 | TribeRoughNeanderthal x6 | close | decisive | 1 | 0 | 3 | 333 | 29.3 |
| 71 | rand_052 | forest_night | Pirate x8 | PirateWaster x8 | turtle | repelled | 0 | 4 | 1 | 370 | 28.8 |
| 72 | rand_045 | open_night | OutlanderRoughPig x8 | Mechanoid x5 | close | decisive | 0 | 1 | 6 | 317 | 27.7 |
| 73 | rand_042 | open_night | TribeSavage x8 | TribeRough x8 | doctrine | repelled | 0 | 3 | 1 | 364 | 25.6 |
| 74 | rand_082 | open_night | OutlanderRoughPig x9 | Empire x4 | kite | decisive | 0 | 1 | 7 | 214 | 25.6 |
| 75 | rand_120 | forest_night | OutlanderCivil x8 | PirateWaster x10 | kite | repelled | 1 | 1 | 0 | 264 | 23.6 |
| 76 | rand_093 | open_night | Pirate x9 | Pirate x9 | doctrine | repelled | 0 | 3 | 1 | 311 | 23.4 |
| 77 | rand_008 | forest_night | PirateWaster x9 | Mechanoid x3 | close | decisive | 1 | 0 | 2 | 227 | 23.1 |
| 78 | rand_044 | forest_night | TribeRoughNeanderthal x6 | OutlanderRough x8 | close | repelled | 1 | 0 | 0 | 315 | 22.6 |
| 79 | rand_061 | open_night | OutlanderRoughPig x8 | PirateYttakin x7 | kite | repelled | 0 | 1 | 7 | 132 | 22.3 |
| 80 | rand_110 | open_night | TribeRoughNeanderthal x6 | Pirate x8 | close | repelled | 1 | 0 | 0 | 301 | 22.0 |
| 81 | rand_002 | forest_night | OutlanderRoughPig x9 | OutlanderRough x9 | close | repelled | 1 | 0 | 1 | 233 | 21.3 |
| 82 | rand_013 | forest_night | TribeRough x8 | Mechanoid x3 | close | decisive | 0 | 0 | 7 | 161 | 20.4 |
| 83 | rand_032 | open_night | OutlanderRough x8 | TribeRough x9 | kite | repelled | 0 | 0 | 7 | 161 | 20.4 |
| 84 | rand_010 | open_night | OutlanderCivil x10 | TribeRough x9 | kite | decisive | 0 | 2 | 3 | 200 | 20.0 |
| 85 | rand_081 | forest_night | OutlanderRoughPig x9 | TribeRough x10 | kite | decisive | 1 | 0 | 0 | 197 | 17.9 |
| 86 | rand_113 | forest_night | Pirate x9 | PirateYttakin x6 | doctrine | decisive | 0 | 2 | 1 | 232 | 17.3 |
| 87 | rand_004 | open_night | Empire x4 | Mechanoid x3 | kite | unresolved | 1 | 0 | 0 | 100 | 17.0 |
| 88 | rand_075 | forest_night | PirateWaster x7 | TribeRoughNeanderthal x6 | kite | repelled | 0 | 2 | 1 | 202 | 16.1 |
| 89 | rand_046 | forest_night | OutlanderRough x9 | Mechanoid x10 | turtle | decisive | 0 | 2 | 0 | 245 | 15.8 |
| 90 | rand_105 | open_night | Empire x5 | PirateWaster x9 | kite | repelled | 0 | 2 | 0 | 239 | 15.6 |
| 91 | rand_064 | open_night | OutlanderCivil x9 | TribeRoughNeanderthal x6 | kite | repelled | 0 | 2 | 1 | 187 | 15.5 |
| 92 | rand_009 | forest_night | OutlanderRoughPig x8 | Pirate x8 | kite | repelled | 0 | 1 | 0 | 310 | 15.4 |
| 93 | rand_076 | open_night | OutlanderRoughPig x9 | TribeRoughNeanderthal x6 | kite | decisive | 0 | 1 | 2 | 192 | 14.7 |
| 94 | rand_047 | forest_night | PirateYttakin x5 | PirateYttakin x9 | kite | repelled | 1 | 0 | 0 | 100 | 14.0 |
| 95 | rand_101 | open_night | TribeRough x9 | Pirate x9 | close | repelled | 0 | 1 | 1 | 222 | 13.9 |
| 96 | rand_123 | open_night | PirateYttakin x7 | Empire x4 | close | repelled | 0 | 2 | 0 | 197 | 13.9 |
| 97 | rand_021 | open_night | PirateYttakin x6 | TribeRough x8 | kite | repelled | 0 | 2 | 0 | 191 | 13.6 |
| 98 | rand_043 | open_night | PirateWaster x7 | Mechanoid x3 | close | decisive | 0 | 2 | 1 | 135 | 13.4 |
| 99 | rand_036 | open_night | OutlanderRough x9 | PirateYttakin x7 | kite | repelled | 0 | 2 | 0 | 171 | 12.8 |
| 100 | rand_092 | forest_night | OutlanderCivil x9 | Pirate x8 | kite | decisive | 0 | 2 | 0 | 167 | 12.7 |
