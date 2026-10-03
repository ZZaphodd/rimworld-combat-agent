## reflex_check.jsonl

### config `fixed:120`

| scenario | agent | n | grades D/R/P/U/X | lost/battle | enemy pts lost | LER pooled | LER median | P(LER)>amove | score_v1 median | P(v1)>amove | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| theme_frag_check | amove@v2 | 10 | 10/0/0/0/0 | 0.00 | 350 | inf | inf | - | 195.4 | - | count_x_mean |
| theme_frag_check | spread@v2 | 10 | 9/1/0/0/0 | 0.00 | 343 | inf | inf | 0.45 | 189.7 | 0.20 | count_x_mean |
| theme_frag_check | turtle@v5 | 10 | 10/0/0/0/0 | 0.00 | 350 | inf | inf | 0.50 | 193.2 | 0.27 | count_x_mean |
| theme_pirate_grenadier | amove@v2 | 5 | 0/1/0/0/4 | 2.20 | 903 | 0.98 | 0.88 | - | -314.7 | - | count_x_mean |
| theme_pirate_grenadier | spread@v2 | 5 | 0/1/3/0/1 | 1.80 | 1050 | 1.39 | 1.25 | 0.70 | -117.9 | 0.64 | count_x_mean |
| theme_pirate_grenadier | turtle@v5 | 5 | 0/0/0/0/5 | 3.40 | 273 | 0.19 | 0.06 | 0.10 | -482.7 | 0.12 | count_x_mean |

Headline (mean of per-scenario P vs amove; pooled LER over all rows):

| agent | scenarios | n | P(LER)>amove | P(v1)>amove | LER pooled | lost/battle | win |
|---|---|---|---|---|---|---|---|
| amove@v2 | 2 | 15 | - | - | 1.73 | 0.73 | 0.73 |
| spread@v2 | 2 | 15 | 0.57 | 0.42 | 2.30 | 0.60 | 0.73 |
| turtle@v5 | 2 | 15 | 0.30 | 0.20 | 0.68 | 1.13 | 0.67 |

Ranking per scenario (best first): new = pooled LER, old = median legacy score

| scenario | new (LER) | old (score_v1) | top changed |
|---|---|---|---|
| theme_frag_check | amove@v2 > turtle@v5 > spread@v2 | amove@v2 > turtle@v5 > spread@v2 | no |
| theme_pirate_grenadier | spread@v2 > amove@v2 > turtle@v5 | spread@v2 > amove@v2 > turtle@v5 | no |

### config `adaptive:30/120@40+rx1`

| scenario | agent | n | grades D/R/P/U/X | lost/battle | enemy pts lost | LER pooled | LER median | P(LER)>amove | score_v1 median | P(v1)>amove | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| theme_frag_check | amove@v2 | 5 | 5/0/0/0/0 | 0.00 | 350 | inf | inf | - | 200.0 | - | count_x_mean |
| theme_frag_check | spread@v2 | 5 | 5/0/0/0/0 | 0.00 | 350 | inf | inf | 0.50 | 196.4 | 0.00 | count_x_mean |
| theme_frag_check | turtle@v5 | 5 | 5/0/0/0/0 | 0.00 | 350 | inf | inf | 0.50 | 194.6 | 0.12 | count_x_mean |
| theme_pirate_grenadier | amove@v2 | 5 | 0/0/0/0/5 | 3.60 | 483 | 0.32 | 0.38 | - | -359.4 | - | count_x_mean |
| theme_pirate_grenadier | spread@v2 | 5 | 0/5/0/0/0 | 1.60 | 1113 | 1.66 | 1.38 | 0.88 | -94.7 | 1.00 | count_x_mean |
| theme_pirate_grenadier | turtle@v5 | 5 | 0/0/0/0/5 | 3.60 | 231 | 0.15 | 0.17 | 0.32 | -523.5 | 0.36 | count_x_mean |

Headline (mean of per-scenario P vs amove; pooled LER over all rows):

| agent | scenarios | n | P(LER)>amove | P(v1)>amove | LER pooled | lost/battle | win |
|---|---|---|---|---|---|---|---|
| amove@v2 | 2 | 10 | - | - | 0.55 | 1.80 | 0.50 |
| spread@v2 | 2 | 10 | 0.69 | 0.50 | 2.18 | 0.80 | 1.00 |
| turtle@v5 | 2 | 10 | 0.41 | 0.24 | 0.38 | 1.80 | 0.50 |

Ranking per scenario (best first): new = pooled LER, old = median legacy score

| scenario | new (LER) | old (score_v1) | top changed |
|---|---|---|---|
| theme_frag_check | amove@v2 > turtle@v5 > spread@v2 | amove@v2 > spread@v2 > turtle@v5 | no |
| theme_pirate_grenadier | spread@v2 > amove@v2 > turtle@v5 | spread@v2 > amove@v2 > turtle@v5 | no |

### config `adaptive:30/120@40`

| scenario | agent | n | grades D/R/P/U/X | lost/battle | enemy pts lost | LER pooled | LER median | P(LER)>amove | score_v1 median | P(v1)>amove | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| theme_frag_check | amove@v2 | 10 | 10/0/0/0/0 | 0.00 | 350 | inf | inf | - | 197.2 | - | count_x_mean |
| theme_frag_check | spread@v2 | 10 | 9/1/0/0/0 | 0.00 | 343 | inf | inf | 0.45 | 197.0 | 0.48 | count_x_mean |
| theme_frag_check | turtle@v5 | 10 | 10/0/0/0/0 | 0.10 | 350 | 12.50 | inf | 0.45 | 198.6 | 0.57 | count_x_mean |
| theme_pirate_grenadier | amove@v2 | 5 | 1/2/1/0/1 | 3.20 | 1071 | 0.80 | 1.25 | - | -158.4 | - | count_x_mean |
| theme_pirate_grenadier | spread@v2 | 5 | 0/4/1/0/0 | 0.60 | 1134 | 4.50 | inf | 0.94 | 40.4 | 0.96 | count_x_mean |
| theme_pirate_grenadier | turtle@v5 | 5 | 0/0/0/0/5 | 3.20 | 378 | 0.28 | 0.19 | 0.36 | -562.7 | 0.16 | count_x_mean |

Headline (mean of per-scenario P vs amove; pooled LER over all rows):

| agent | scenarios | n | P(LER)>amove | P(v1)>amove | LER pooled | lost/battle | win |
|---|---|---|---|---|---|---|---|
| amove@v2 | 2 | 15 | - | - | 1.32 | 1.07 | 0.87 |
| spread@v2 | 2 | 15 | 0.69 | 0.72 | 7.22 | 0.20 | 0.93 |
| turtle@v5 | 2 | 15 | 0.41 | 0.36 | 0.77 | 1.13 | 0.67 |

Ranking per scenario (best first): new = pooled LER, old = median legacy score

| scenario | new (LER) | old (score_v1) | top changed |
|---|---|---|---|
| theme_frag_check | amove@v2 > spread@v2 > turtle@v5 | turtle@v5 > amove@v2 > spread@v2 | yes |
| theme_pirate_grenadier | spread@v2 > amove@v2 > turtle@v5 | spread@v2 > amove@v2 > turtle@v5 | no |

### config `adaptive:30/120@40+rx2`

| scenario | agent | n | grades D/R/P/U/X | lost/battle | enemy pts lost | LER pooled | LER median | P(LER)>amove | score_v1 median | P(v1)>amove | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| theme_frag_check | amove@v2 | 10 | 10/0/0/0/0 | 0.10 | 350 | 12.50 | inf | - | 198.0 | - | count_x_mean |
| theme_frag_check | spread@v2 | 10 | 9/1/0/0/0 | 0.00 | 343 | inf | inf | 0.51 | 198.5 | 0.49 | count_x_mean |
| theme_frag_check | turtle@v5 | 10 | 10/0/0/0/0 | 0.00 | 350 | inf | inf | 0.55 | 196.1 | 0.43 | count_x_mean |
| theme_pirate_grenadier | amove@v2 | 5 | 0/0/0/0/5 | 4.60 | 630 | 0.33 | 0.35 | - | -549.1 | - | count_x_mean |
| theme_pirate_grenadier | spread@v2 | 5 | 0/5/0/0/0 | 1.40 | 1092 | 1.86 | 2.50 | 1.00 | -47.2 | 1.00 | count_x_mean |
| theme_pirate_grenadier | turtle@v5 | 5 | 0/0/0/0/5 | 5.40 | 273 | 0.12 | 0.04 | 0.20 | -788.3 | 0.24 | count_x_mean |

Headline (mean of per-scenario P vs amove; pooled LER over all rows):

| agent | scenarios | n | P(LER)>amove | P(v1)>amove | LER pooled | lost/battle | win |
|---|---|---|---|---|---|---|---|
| amove@v2 | 2 | 15 | - | - | 0.67 | 1.60 | 0.67 |
| spread@v2 | 2 | 15 | 0.75 | 0.74 | 3.02 | 0.47 | 1.00 |
| turtle@v5 | 2 | 15 | 0.38 | 0.34 | 0.43 | 1.80 | 0.67 |

Ranking per scenario (best first): new = pooled LER, old = median legacy score

| scenario | new (LER) | old (score_v1) | top changed |
|---|---|---|---|
| theme_frag_check | turtle@v5 > spread@v2 > amove@v2 | spread@v2 > amove@v2 > turtle@v5 | yes |
| theme_pirate_grenadier | spread@v2 > amove@v2 > turtle@v5 | spread@v2 > amove@v2 > turtle@v5 | no |
