## exec_v1.jsonl

### config `fixed:120`

| scenario | agent | n | grades D/R/P/U/X | lost/battle | enemy pts lost | LER pooled | LER median | P(LER)>amove | score_v1 median | P(v1)>amove | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| theme_mechs | doctrine@v1 | 3 | 2/0/1/0/0 | 0.67 | 1000 | 3.00 | 2.00 | - | 42.5 | - | count_x_mean |
| theme_mechs | turtle@v3 | 2 | 2/0/0/0/0 | 1.00 | 1000 | 2.00 | inf | - | 41.5 | - | count_x_mean |
| theme_pirate_grenadier | spread@v1 | 2 | 0/1/1/0/0 | 1.50 | 1102 | 1.75 | inf | - | -87.6 | - | count_x_mean |
| theme_pirate_melee | kite@v1 | 3 | 0/1/0/1/1 | 1.33 | 840 | 1.38 | 2.25 | - | -105.7 | - | count_x_mean |
| theme_pirate_mixed | doctrine@v1 | 3 | 0/2/0/0/1 | 2.67 | 1074 | 0.97 | inf | - | 81.8 | - | count_x_mean |
| theme_pirate_sniper | close@v1 | 2 | 0/1/0/0/1 | 1.00 | 880 | 2.00 | 2.00 | - | -112.7 | - | count_x_mean |
| theme_tribal_melee | kite@v1 | 3 | 0/1/0/0/2 | 2.00 | 940 | 2.17 | 2.38 | - | -153.3 | - | count_x_mean |
| theme_tribal_melee | turtle@v3 | 2 | 2/0/0/0/0 | 0.00 | 1411 | inf | inf | - | 150.8 | - | count_x_mean |

Headline (mean of per-scenario P vs amove; pooled LER over all rows):

| agent | scenarios | n | P(LER)>amove | P(v1)>amove | LER pooled | lost/battle | win |
|---|---|---|---|---|---|---|---|
| close@v1 | 1 | 2 | - | - | 2.00 | 1.00 | 0.50 |
| doctrine@v1 | 2 | 6 | - | - | 1.44 | 1.67 | 0.67 |
| kite@v1 | 2 | 6 | - | - | 1.70 | 1.67 | 0.33 |
| spread@v1 | 1 | 2 | - | - | 1.75 | 1.50 | 0.50 |
| turtle@v3 | 2 | 4 | - | - | 4.82 | 0.50 | 1.00 |

Ranking per scenario (best first): new = pooled LER, old = median legacy score

| scenario | new (LER) | old (score_v1) | top changed |
|---|---|---|---|
| theme_mechs | doctrine@v1 > turtle@v3 | doctrine@v1 > turtle@v3 | no |
| theme_tribal_melee | turtle@v3 > kite@v1 | turtle@v3 > kite@v1 | no |
