## grade_check.jsonl

### config `fixed:120`

| scenario | agent | n | grades D/R/P/U/X | lost/battle | enemy pts lost | LER pooled | LER median | P(LER)>amove | score_v1 median | P(v1)>amove | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| theme_pirate_grenadier | amove | 3 | 1/0/0/0/2 | 4.00 | 805 | 0.48 | 0.30 | - | -578.6 | - | count_x_mean |
| theme_pirate_grenadier | turtle | 3 | 0/0/0/0/3 | 2.67 | 455 | 0.41 | 0.42 | 0.44 | -416.3 | 0.67 | count_x_mean |
| theme_pirate_mixed | amove | 3 | 0/2/0/0/1 | 2.33 | 797 | 0.82 | 1.25 | - | -151.6 | - | count_x_mean |
| theme_pirate_mixed | turtle | 3 | 0/0/0/0/3 | 3.33 | 0 | 0.00 | 0.00 | 0.00 | -459.8 | 0.22 | count_x_mean |

Headline (mean of per-scenario P vs amove; pooled LER over all rows):

| agent | scenarios | n | P(LER)>amove | P(v1)>amove | LER pooled | lost/battle | win |
|---|---|---|---|---|---|---|---|
| amove | 2 | 6 | - | - | 0.60 | 3.17 | 0.50 |
| turtle | 2 | 6 | 0.22 | 0.44 | 0.18 | 3.00 | 0.00 |

Ranking per scenario (best first): new = pooled LER, old = median legacy score

| scenario | new (LER) | old (score_v1) | top changed |
|---|---|---|---|
| theme_pirate_grenadier | amove > turtle | turtle > amove | yes |
| theme_pirate_mixed | amove > turtle | amove > turtle | no |
