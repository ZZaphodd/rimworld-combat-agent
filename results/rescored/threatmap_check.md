## threatmap_check.jsonl

### config `adaptive:30/120@40+rx2`

| scenario | agent | n | grades D/R/P/U/X | lost/battle | enemy pts lost | LER pooled | LER median | P(LER)>amove | score_v1 median | P(v1)>amove | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| theme_frag_check | amove@v2 | 10 | 10/0/0/0/0 | 0.00 | 350 | inf | inf | - | 198.4 | - | count_x_mean |
| theme_frag_check | spread@v2 | 10 | 10/0/0/0/0 | 0.10 | 350 | 12.50 | inf | 0.45 | 196.6 | 0.36 | count_x_mean |
| theme_frag_check | turtle@v5 | 10 | 10/0/0/0/0 | 0.00 | 350 | inf | inf | 0.50 | 196.4 | 0.34 | count_x_mean |
| theme_pirate_grenadier | amove@v2 | 5 | 0/2/0/0/3 | 3.40 | 819 | 0.57 | 0.42 | - | -434.6 | - | count_x_mean |
| theme_pirate_grenadier | spread@v2 | 5 | 0/5/0/0/0 | 0.80 | 1071 | 3.19 | inf | 0.88 | 69.1 | 0.84 | count_x_mean |
| theme_pirate_grenadier | turtle@v5 | 5 | 1/0/0/0/4 | 2.60 | 588 | 0.54 | 0.31 | 0.36 | -452.1 | 0.44 | count_x_mean |

Headline (mean of per-scenario P vs amove; pooled LER over all rows):

| agent | scenarios | n | P(LER)>amove | P(v1)>amove | LER pooled | lost/battle | win |
|---|---|---|---|---|---|---|---|
| amove@v2 | 2 | 15 | - | - | 1.06 | 1.13 | 0.80 |
| spread@v2 | 2 | 15 | 0.67 | 0.60 | 4.52 | 0.33 | 1.00 |
| turtle@v5 | 2 | 15 | 0.43 | 0.39 | 1.18 | 0.87 | 0.73 |

Ranking per scenario (best first): new = pooled LER, old = median legacy score

| scenario | new (LER) | old (score_v1) | top changed |
|---|---|---|---|
| theme_frag_check | amove@v2 > turtle@v5 > spread@v2 | amove@v2 > spread@v2 > turtle@v5 | no |
| theme_pirate_grenadier | spread@v2 > amove@v2 > turtle@v5 | spread@v2 > amove@v2 > turtle@v5 | no |

### config `adaptive:30/120@40+rx3`

| scenario | agent | n | grades D/R/P/U/X | lost/battle | enemy pts lost | LER pooled | LER median | P(LER)>amove | score_v1 median | P(v1)>amove | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| theme_frag_check | amove@v3 | 10 | 5/5/0/0/0 | 0.00 | 315 | inf | inf | 0.45 | 175.0 | 0.45 | count_x_mean |
| theme_frag_check | amove@v4 | 10 | 6/4/0/0/0 | 0.00 | 322 | inf | inf | - | 200.0 | - | count_x_mean |
| theme_frag_check | spread@v3 | 10 | 4/6/0/0/0 | 0.00 | 308 | inf | inf | 0.40 | 150.0 | 0.35 | count_x_mean |
| theme_frag_check | spread@v4 | 10 | 1/9/0/0/0 | 0.00 | 287 | inf | inf | 0.25 | 150.0 | 0.25 | count_x_mean |
| theme_frag_check | turtle@v6 | 10 | 2/8/0/0/0 | 0.00 | 294 | inf | inf | 0.30 | 149.5 | 0.17 | count_x_mean |
| theme_frag_check | turtle@v7 | 10 | 5/5/0/0/0 | 0.00 | 315 | inf | inf | 0.45 | 173.6 | 0.38 | count_x_mean |
| theme_pirate_grenadier | amove@v3 | 5 | 0/3/0/0/2 | 3.60 | 966 | 0.64 | 0.67 | 0.60 | -331.7 | 0.64 | count_x_mean |
| theme_pirate_grenadier | amove@v4 | 5 | 1/0/0/0/4 | 3.20 | 840 | 0.62 | 0.50 | - | -389.0 | - | count_x_mean |
| theme_pirate_grenadier | spread@v3 | 5 | 1/4/0/0/0 | 2.00 | 1113 | 1.32 | 1.38 | 0.80 | -86.1 | 0.84 | count_x_mean |
| theme_pirate_grenadier | spread@v4 | 5 | 2/1/0/0/2 | 1.60 | 1092 | 1.62 | 3.00 | 0.80 | -2.0 | 0.80 | count_x_mean |
| theme_pirate_grenadier | turtle@v6 | 5 | 0/1/0/0/4 | 4.20 | 315 | 0.18 | 0.00 | 0.26 | -510.2 | 0.40 | count_x_mean |
| theme_pirate_grenadier | turtle@v7 | 5 | 1/1/0/0/3 | 3.40 | 546 | 0.38 | 0.33 | 0.36 | -427.4 | 0.40 | count_x_mean |

Headline (mean of per-scenario P vs amove; pooled LER over all rows):

| agent | scenarios | n | P(LER)>amove | P(v1)>amove | LER pooled | lost/battle | win |
|---|---|---|---|---|---|---|---|
| amove@v3 | 2 | 15 | 0.53 | 0.55 | 1.06 | 1.20 | 0.87 |
| amove@v4 | 2 | 15 | - | - | 1.10 | 1.07 | 0.73 |
| spread@v3 | 2 | 15 | 0.60 | 0.59 | 2.06 | 0.67 | 1.00 |
| spread@v4 | 2 | 15 | 0.53 | 0.53 | 2.48 | 0.53 | 0.87 |
| turtle@v6 | 2 | 15 | 0.28 | 0.29 | 0.51 | 1.40 | 0.73 |
| turtle@v7 | 2 | 15 | 0.41 | 0.39 | 0.82 | 1.13 | 0.80 |

Ranking per scenario (best first): new = pooled LER, old = median legacy score

| scenario | new (LER) | old (score_v1) | top changed |
|---|---|---|---|
| theme_frag_check | amove@v3 > turtle@v6 > spread@v3 > amove@v4 > turtle@v7 > spread@v4 | amove@v4 > amove@v3 > turtle@v7 > spread@v3 > spread@v4 > turtle@v6 | yes |
| theme_pirate_grenadier | spread@v4 > spread@v3 > amove@v3 > amove@v4 > turtle@v7 > turtle@v6 | spread@v4 > spread@v3 > amove@v3 > amove@v4 > turtle@v7 > turtle@v6 | no |
