# Gate: results/gate/signals-preconditions.jsonl vs results/baseline/core.jsonl [adaptive:30/120@40+rx4]

Rule (WORKFLOW.md): a cell regresses if the 98% bootstrap interval of its worsening lies above the margin (lost 0.5/battle, trade share 0.1); an agent regresses if the 95% interval of its pooled worsening lies above 0.25 x margin. PASS = no regression, no incomplete cell.

| agent | scenario | n base/branch | lost/battle base → branch (d; 98% CI) | trade share base → branch (d; 98% CI) | verdict |
|---|---|---|---|---|---|
| amove v5→v6 | theme_mechs | 10/10 | 0.00 → 0.50 (+0.50; +0.10..+0.90) | 1.00 → 0.83 (+0.17; +0.03..+0.30) | watch trade |
| amove v5→v6 | theme_pirate_grenadier | 10/10 | 3.30 → 3.10 (-0.20; -2.10..+1.80) | 0.33 → 0.44 (-0.10; -0.36..+0.12) | ok |
| amove v5→v6 | theme_pirate_melee | 10/10 | 0.40 → 0.20 (-0.20; -0.80..+0.30) | 0.88 → 0.94 (-0.06; -0.23..+0.09) | ok |
| amove v5→v6 | theme_pirate_mixed | 10/10 | 2.10 → 1.60 (-0.50; -2.40..+1.10) | 0.54 → 0.66 (-0.12; -0.36..+0.13) | ok |
| amove v5→v6 | theme_pirate_sniper | 10/10 | 1.20 → 1.60 (+0.40; -0.60..+1.50) | 0.74 → 0.67 (+0.07; -0.12..+0.25) | ok |
| amove v5→v6 | theme_tribal_archers | 10/10 | 0.20 → 0.70 (+0.50; +0.00..+1.10) | 0.96 → 0.89 (+0.08; -0.02..+0.17) | ok |
| amove v5→v6 | theme_tribal_melee | 10/10 | 0.80 → 0.60 (-0.20; -0.90..+0.50) | 0.86 → 0.89 (-0.02; -0.16..+0.10) | ok |
| close v3→v4 | theme_mechs | 10/10 | 0.20 → 0.10 (-0.10; -0.70..+0.30) | 0.95 → 0.97 (-0.02; -0.15..+0.10) | ok |
| close v3→v4 | theme_pirate_grenadier | 10/10 | 3.20 → 3.30 (+0.10; -1.20..+1.40) | 0.35 → 0.27 (+0.08; -0.14..+0.33) | ok |
| close v3→v4 | theme_pirate_melee | 10/10 | 0.50 → 0.10 (-0.40; -1.00..+0.10) | 0.86 → 0.97 (-0.11; -0.25..+0.02) | ok |
| close v3→v4 | theme_pirate_mixed | 10/10 | 1.20 → 1.60 (+0.40; -0.80..+1.60) | 0.65 → 0.53 (+0.12; -0.15..+0.38) | ok |
| close v3→v4 | theme_pirate_sniper | 10/10 | 2.30 → 3.10 (+0.80; -0.80..+2.50) | 0.54 → 0.46 (+0.08; -0.14..+0.33) | ok |
| close v3→v4 | theme_tribal_archers | 10/10 | 1.00 → 0.00 (-1.00; -3.60..+0.00) | 0.91 → 1.00 (-0.09; -0.28..-0.00) | ok |
| close v3→v4 | theme_tribal_melee | 10/10 | 0.50 → 0.60 (+0.10; -0.60..+0.80) | 0.92 → 0.91 (+0.01; -0.08..+0.11) | ok |
| doctrine v5→v6 | theme_mechs | 10/10 | 0.40 → 0.50 (+0.10; -0.50..+0.70) | 0.87 → 0.85 (+0.02; -0.17..+0.20) | ok |
| doctrine v5→v6 | theme_pirate_grenadier | 10/10 | 3.20 → 3.60 (+0.40; -1.30..+2.30) | 0.43 → 0.27 (+0.16; -0.01..+0.37) | watch trade |
| doctrine v5→v6 | theme_pirate_melee | 10/10 | 0.40 → 0.40 (+0.00; -0.70..+0.70) | 0.90 → 0.90 (+0.00; -0.16..+0.17) | ok |
| doctrine v5→v6 | theme_pirate_mixed | 10/10 | 0.80 → 0.90 (+0.10; -0.90..+1.10) | 0.70 → 0.73 (-0.03; -0.31..+0.26) | ok |
| doctrine v5→v6 | theme_pirate_sniper | 10/10 | 2.10 → 1.50 (-0.60; -2.10..+0.90) | 0.61 → 0.67 (-0.06; -0.27..+0.17) | ok |
| doctrine v5→v6 | theme_tribal_archers | 10/10 | 0.80 → 0.70 (-0.10; -1.10..+1.10) | 0.87 → 0.89 (-0.02; -0.15..+0.14) | ok |
| doctrine v5→v6 | theme_tribal_melee | 10/10 | 0.70 → 0.40 (-0.30; -0.90..+0.40) | 0.82 → 0.90 (-0.08; -0.24..+0.10) | ok |
| kite v5→v6 | theme_mechs | 10/10 | 0.30 → 0.20 (-0.10; -0.50..+0.40) | 0.90 → 0.93 (-0.03; -0.20..+0.13) | ok |
| kite v5→v6 | theme_pirate_grenadier | 10/10 | 2.40 → 2.30 (-0.10; -1.90..+1.70) | 0.50 → 0.56 (-0.06; -0.36..+0.25) | ok |
| kite v5→v6 | theme_pirate_melee | 10/10 | 0.00 → 0.10 (+0.10; +0.00..+0.40) | 1.00 → 0.97 (+0.03; -0.00..+0.12) | ok |
| kite v5→v6 | theme_pirate_mixed | 10/10 | 2.10 → 1.30 (-0.80; -2.00..+0.30) | 0.35 → 0.46 (-0.11; -0.46..+0.24) | ok |
| kite v5→v6 | theme_pirate_sniper | 10/10 | 2.00 → 1.50 (-0.50; -2.10..+1.10) | 0.58 → 0.69 (-0.10; -0.36..+0.16) | ok |
| kite v5→v6 | theme_tribal_archers | 10/10 | 0.30 → 0.80 (+0.50; -0.30..+1.40) | 0.95 → 0.88 (+0.06; -0.06..+0.19) | ok |
| kite v5→v6 | theme_tribal_melee | 10/10 | 0.30 → 0.30 (+0.00; -0.50..+0.50) | 0.96 → 0.96 (-0.00; -0.07..+0.07) | ok |
| spread v5→v6 | theme_mechs | 10/10 | 0.80 → 0.50 (-0.30; -1.00..+0.50) | 0.77 → 0.85 (-0.08; -0.28..+0.13) | ok |
| spread v5→v6 | theme_pirate_grenadier | 10/10 | 1.80 → 1.10 (-0.70; -1.80..+0.40) | 0.64 → 0.73 (-0.09; -0.28..+0.12) | ok |
| spread v5→v6 | theme_pirate_melee | 10/10 | 0.80 → 1.30 (+0.50; -0.60..+1.70) | 0.76 → 0.71 (+0.05; -0.19..+0.30) | ok |
| spread v5→v6 | theme_pirate_mixed | 10/10 | 2.70 → 2.50 (-0.20; -2.10..+1.90) | 0.40 → 0.39 (+0.01; -0.22..+0.21) | ok |
| spread v5→v6 | theme_pirate_sniper | 10/10 | 3.50 → 2.40 (-1.10; -2.40..+0.20) | 0.26 → 0.43 (-0.17; -0.38..+0.02) | ok |
| spread v5→v6 | theme_tribal_archers | 10/10 | 1.70 → 1.40 (-0.30; -2.20..+1.20) | 0.77 → 0.79 (-0.01; -0.19..+0.15) | ok |
| spread v5→v6 | theme_tribal_melee | 10/10 | 1.40 → 1.10 (-0.30; -1.20..+0.50) | 0.74 → 0.73 (+0.01; -0.17..+0.19) | ok |
| turtle v8→v9 | theme_mechs | 10/10 | 0.00 → 0.00 (+0.00; +0.00..+0.00) | 1.00 → 1.00 (-0.00; -0.00..-0.00) | ok |
| turtle v8→v9 | theme_pirate_grenadier | 10/10 | 5.20 → 4.10 (-1.10; -3.70..+1.40) | 0.07 → 0.22 (-0.15; -0.48..+0.10) | ok |
| turtle v8→v9 | theme_pirate_melee | 10/10 | 0.20 → 0.20 (+0.00; -0.40..+0.40) | 0.94 → 0.94 (-0.00; -0.12..+0.12) | ok |
| turtle v8→v9 | theme_pirate_mixed | 10/10 | 1.80 → 2.20 (+0.40; -0.60..+1.40) | 0.39 → 0.35 (+0.03; -0.27..+0.36) | ok |
| turtle v8→v9 | theme_pirate_sniper | 10/10 | 2.10 → 2.70 (+0.60; -1.00..+2.30) | 0.40 → 0.35 (+0.05; -0.21..+0.29) | ok |
| turtle v8→v9 | theme_tribal_archers | 10/10 | 0.60 → 0.30 (-0.30; -0.90..+0.30) | 0.90 → 0.95 (-0.05; -0.15..+0.04) | ok |
| turtle v8→v9 | theme_tribal_melee | 10/10 | 0.10 → 0.00 (-0.10; -0.40..+0.00) | 0.99 → 1.00 (-0.01; -0.06..-0.00) | ok |

| agent (pooled) | cells | d lost (95% CI) | d trade share (95% CI) | verdict |
|---|---|---|---|---|
| amove | 7 | +0.043 (-0.343..+0.414) | -0.001 (-0.057..+0.056) | ok |
| close | 7 | -0.014 (-0.443..+0.371) | +0.011 (-0.047..+0.073) | ok |
| doctrine | 7 | -0.057 (-0.414..+0.300) | -0.003 (-0.067..+0.065) | ok |
| kite | 7 | -0.129 (-0.471..+0.214) | -0.031 (-0.099..+0.040) | ok |
| spread | 7 | -0.343 (-0.757..+0.086) | -0.039 (-0.104..+0.026) | ok |
| turtle | 7 | -0.071 (-0.486..+0.329) | -0.019 (-0.079..+0.042) | ok |

42 cells: 40 ok, 2 watch, 0 regress, 0 incomplete; 6 agents: 0 regress -> **PASS**
