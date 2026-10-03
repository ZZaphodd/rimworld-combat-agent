## exec_v2.jsonl

### config `fixed:120`

| scenario | agent | n | grades D/R/P/U/X | lost/battle | enemy pts lost | LER pooled | LER median | P(LER)>amove | score_v1 median | P(v1)>amove | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| theme_mechs | doctrine@v2 | 5 | 4/0/1/0/0 | 0.20 | 1000 | 10.00 | inf | - | 103.1 | - | count_x_mean |
| theme_mechs | turtle@v4 | 4 | 4/0/0/0/0 | 0.25 | 1000 | 8.00 | inf | - | 125.0 | - | count_x_mean |
| theme_pirate_grenadier | doctrine@v2 | 3 | 0/0/0/0/3 | 5.00 | 1015 | 0.48 | 0.50 | - | -542.1 | - | count_x_mean |
| theme_pirate_melee | kite@v3 | 5 | 5/0/0/0/0 | 0.20 | 1146 | 12.50 | inf | - | 134.7 | - | count_x_mean |
| theme_pirate_melee | turtle@v4 | 2 | 2/0/0/0/0 | 0.00 | 1146 | inf | inf | - | 159.5 | - | count_x_mean |
| theme_pirate_mixed | doctrine@v2 | 5 | 0/3/0/0/2 | 1.40 | 998 | 1.71 | 2.50 | - | -22.8 | - | count_x_mean |
| theme_tribal_melee | kite@v3 | 5 | 5/0/0/0/0 | 0.40 | 1422 | 16.37 | inf | - | 133.8 | - | count_x_mean |
| theme_tribal_melee | turtle@v4 | 2 | 1/1/0/0/0 | 0.50 | 1384 | 12.75 | inf | - | 74.3 | - | count_x_mean |

Headline (mean of per-scenario P vs amove; pooled LER over all rows):

| agent | scenarios | n | P(LER)>amove | P(v1)>amove | LER pooled | lost/battle | win |
|---|---|---|---|---|---|---|---|
| doctrine@v2 | 3 | 13 | - | - | 1.34 | 1.77 | 0.54 |
| kite@v3 | 2 | 10 | - | - | 14.38 | 0.30 | 1.00 |
| turtle@v4 | 3 | 8 | - | - | 12.63 | 0.25 | 1.00 |

Ranking per scenario (best first): new = pooled LER, old = median legacy score

| scenario | new (LER) | old (score_v1) | top changed |
|---|---|---|---|
| theme_mechs | doctrine@v2 > turtle@v4 | turtle@v4 > doctrine@v2 | yes |
| theme_pirate_melee | turtle@v4 > kite@v3 | turtle@v4 > kite@v3 | no |
| theme_tribal_melee | kite@v3 > turtle@v4 | kite@v3 > turtle@v4 | no |
