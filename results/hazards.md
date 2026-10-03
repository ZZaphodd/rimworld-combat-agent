# Telegraphed area attacks: what we can see and when

Measured with `measure_hazards.py` (spawned carriers ~12–20 cells from the theme squad,
2-tick sampling) plus static stats from `get_info_card`. Raw rows: `results/hazards.jsonl`.

| Weapon | Aiming (info card) | Projectile visible in flight | After landing | Observable aiming? | Reflex possible? |
|---|---|---|---|---|---|
| Frag grenade | 1.5 s (90 ticks) | 75–122 ticks (`Proj_GrenadeFrag`) | **fuse 88–91 ticks**, very stable | no | **yes, if decision cycle ≤ ~50 ticks** (landing → 90 ticks; escape 2–3 cells ≈ 30–40) |
| Molotov | 1.5 s | ~90–105 ticks (`Proj_GrenadeMolotov`) | bursts on impact; fire lingers | no | partly: extrapolate the flight heading, or leave fire cells afterwards |
| Doomsday rocket | 4.5 s (270 ticks) | **30–45 ticks** (`Bullet_DoomsdayRocket`) | bursts on impact, wide blast (several cells) | **no** (carrier job stays "watching for targets") | **no** |
| Triple rocket | 4.5 s, burst 3 | 30–60 ticks (`Bullet_Rocket`) | bursts on impact | no | no |
| Incendiary / EMP / smoke launcher | 3.5 s | not measured yet | | | |

Notes
- `list_things(category="all")` on the forest map is truncated by plants; query projectile defs by name.
- Explosions appear as short-lived `Explosion` things (several cells for doomsday).
- Rockets can only be countered before the shot: spacing, cover against the carrier, and killing rocket carriers first.
- Mech bosses: see TODO.md.
- Frag blast reach (`measure_blast.py`, squad standing still, hits read from the battle log
  right after each blast; only 4 blasts could be attributed before the squad went down, so n is small):
  hit 1/2 pawns at d=1.0, 5/5 at d=1.4, 0/2 at d=2.2, 0/10 at d=3.2, 0/20 at d>=3.6. Consistent with
  the XML radius 1.9 (the 3x3 cells around the grenade). The reflex layer keeps pawns 2.5 cells clear.
- The wait tool advances in 15-tick quanta (a 6-tick request advanced 14-16), so 30 ticks is
  two quanta; nothing finer than 15 is possible from the harness.
- Battle log: thrown grenades are logged with their target ("X flung her frag grenade at Y"), damage as
  "X's frag grenade(s) <verb> Y's <parts>" / "The blast|shockwave from X's frag grenade ...".
