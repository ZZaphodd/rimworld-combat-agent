## options.jsonl

### config `adaptive:30/120@40+rx4`

| scenario | agent | n | grades D/R/P/U/X | lost/battle | enemy pts lost | LER pooled | LER median | P(LER)>amove | score_v1 median | P(v1)>amove | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| theme_mechs | doctrine@v4[rescue=off] | 5 | 5/0/0/0/0 | 0.20 | 1000 | 10.00 | inf | - | 113.9 | - | points |
| theme_mechs | turtle@v8[wounded_pullback=off] | 5 | 5/0/0/0/0 | 0.00 | 1000 | inf | inf | - | 190.9 | - | points |
| theme_pirate_grenadier | doctrine@v4[rescue=off] | 5 | 0/1/0/0/4 | 1.60 | 669 | 1.00 | 1.46 | - | -321.7 | - | points |
| theme_pirate_grenadier | turtle@v8[wounded_pullback=off] | 5 | 0/0/0/0/5 | 4.00 | 56 | 0.03 | 0.00 | - | -576.7 | - | points |
| theme_pirate_melee | doctrine@v4[rescue=off] | 5 | 2/3/0/0/0 | 0.00 | 1018 | inf | inf | - | 96.1 | - | points |
| theme_pirate_melee | turtle@v8[wounded_pullback=off] | 5 | 4/1/0/0/0 | 0.40 | 1102 | 6.01 | inf | - | 117.6 | - | points |
| theme_pirate_mixed | doctrine@v4[rescue=off] | 5 | 0/2/0/0/3 | 1.40 | 836 | 1.44 | 1.35 | - | -192.6 | - | points |
| theme_pirate_mixed | turtle@v8[wounded_pullback=off] | 5 | 0/0/0/0/5 | 2.20 | 93 | 0.10 | 0.16 | - | -288.4 | - | points |
| theme_pirate_sniper | doctrine@v4[rescue=off] | 5 | 0/3/0/0/2 | 2.60 | 1100 | 0.96 | 1.25 | - | -280.8 | - | points |
| theme_pirate_sniper | turtle@v8[wounded_pullback=off] | 5 | 0/0/1/0/4 | 3.20 | 814 | 0.58 | 0.50 | - | -465.8 | - | points |
| theme_tribal_archers | doctrine@v4[rescue=off] | 5 | 0/3/0/0/2 | 0.20 | 967 | 21.16 | inf | - | 17.4 | - | points |
| theme_tribal_archers | turtle@v8[wounded_pullback=off] | 5 | 0/5/0/0/0 | 0.00 | 980 | inf | inf | - | 104.7 | - | points |
| theme_tribal_melee | doctrine@v4[rescue=off] | 5 | 0/0/0/0/5 | 0.40 | 384 | 4.42 | inf | - | -185.9 | - | points |
| theme_tribal_melee | turtle@v8[wounded_pullback=off] | 5 | 4/1/0/0/0 | 0.20 | 1352 | 31.15 | inf | - | 147.5 | - | points |

Headline (mean of per-scenario P vs amove; pooled LER over all rows):

| agent | scenarios | n | P(LER)>amove | P(v1)>amove | LER pooled | lost/battle | win |
|---|---|---|---|---|---|---|---|
| doctrine@v4[rescue=off] | 7 | 35 | - | - | 2.27 | 0.91 | 0.54 |
| turtle@v8[wounded_pullback=off] | 7 | 35 | - | - | 1.28 | 1.43 | 0.57 |

Ranking per scenario (best first): new = pooled LER, old = median legacy score

| scenario | new (LER) | old (score_v1) | top changed |
|---|---|---|---|
| theme_mechs | turtle@v8[wounded_pullback=off] > doctrine@v4[rescue=off] | turtle@v8[wounded_pullback=off] > doctrine@v4[rescue=off] | no |
| theme_pirate_grenadier | doctrine@v4[rescue=off] > turtle@v8[wounded_pullback=off] | doctrine@v4[rescue=off] > turtle@v8[wounded_pullback=off] | no |
| theme_pirate_melee | doctrine@v4[rescue=off] > turtle@v8[wounded_pullback=off] | turtle@v8[wounded_pullback=off] > doctrine@v4[rescue=off] | yes |
| theme_pirate_mixed | doctrine@v4[rescue=off] > turtle@v8[wounded_pullback=off] | doctrine@v4[rescue=off] > turtle@v8[wounded_pullback=off] | no |
| theme_pirate_sniper | doctrine@v4[rescue=off] > turtle@v8[wounded_pullback=off] | doctrine@v4[rescue=off] > turtle@v8[wounded_pullback=off] | no |
| theme_tribal_archers | turtle@v8[wounded_pullback=off] > doctrine@v4[rescue=off] | turtle@v8[wounded_pullback=off] > doctrine@v4[rescue=off] | no |
| theme_tribal_melee | turtle@v8[wounded_pullback=off] > doctrine@v4[rescue=off] | turtle@v8[wounded_pullback=off] > doctrine@v4[rescue=off] | no |
