## pilot.jsonl

### config `fixed:120`

| scenario | agent | n | grades D/R/P/U/X | lost/battle | enemy pts lost | LER pooled | LER median | P(LER)>amove | score_v1 median | P(v1)>amove | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hard_pirates_vs_mechs_forest | amove | 2 | 0/0/0/0/2 | 6.50 | 2228 | 0.35 | 0.37 | - | -764.9 | - | count_x_mean |
| hard_pirates_vs_mechs_forest | b0 | 1 | 0/0/0/0/1 | 5.00 | 0 | 0.00 | 0.00 | 0.00 | -715.2 | 0.50 | count_x_mean |
| hard_pirates_vs_mechs_forest | doctrine | 1 | 0/0/0/0/1 | 4.00 | 1485 | 0.38 | 0.38 | 0.50 | -539.1 | 1.00 | count_x_mean |
| smoke_pirates_vs_savage_open | amove | 2 | 2/0/0/0/0 | 0.50 | 400 | 4.00 | inf | - | 115.1 | - | count_x_mean |
| smoke_pirates_vs_savage_open | b0 | 1 | 1/0/0/0/0 | 2.00 | 400 | 1.00 | 1.00 | 0.00 | -32.2 | 0.00 | count_x_mean |
| smoke_pirates_vs_savage_open | doctrine | 1 | 1/0/0/0/0 | 1.00 | 400 | 2.00 | 2.00 | 0.25 | 47.0 | 0.00 | count_x_mean |

Headline (mean of per-scenario P vs amove; pooled LER over all rows):

| agent | scenarios | n | P(LER)>amove | P(v1)>amove | LER pooled | lost/battle | win |
|---|---|---|---|---|---|---|---|
| amove | 2 | 4 | - | - | 0.40 | 3.50 | 0.50 |
| b0 | 2 | 2 | 0.00 | 0.25 | 0.07 | 3.50 | 0.50 |
| doctrine | 2 | 2 | 0.38 | 0.50 | 0.45 | 2.50 | 0.50 |

Ranking per scenario (best first): new = pooled LER, old = median legacy score

| scenario | new (LER) | old (score_v1) | top changed |
|---|---|---|---|
| hard_pirates_vs_mechs_forest | doctrine > amove > b0 | doctrine > b0 > amove | no |
| smoke_pirates_vs_savage_open | amove > doctrine > b0 | amove > doctrine > b0 | no |
