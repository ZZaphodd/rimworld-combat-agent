# Human play (observe-only demonstrations)

A person plays a scenario; the harness only watches and grades it like an agent episode
(`tools/run_human.py`, PROCEDURES §15). Roadmap 3: the user plays the problems the agents lose
(`results/night/worst.md`), and what worked is distilled into rules for the agents.

## Files

- `play.jsonl`: one graded row per battle (same schema as agent rows, `agent` = player,
  `cycle` = observed). Since 2026-10-05 a row names its trace in `trace`.
- `traces/<id>_<player>_<time>.jsonl.gz`: every poll (~1 s): each pawn's position, health,
  weapon, job and drafted flag, both sides; fires; thrown projectiles; new game messages
  (`rca/eval/trace.py`, read with `trace.read()`). This is the demonstration itself.
- `reports/<id>.md`: a battle report a person can read later: result vs the agent, a route map,
  labelled frames (`rca/eval/frames.py`), what worked and the lessons with frame references.
- `raw/<id>/`: watcher records (positions and jobs at each screenshot; the only record of the
  battles before traces) and notes; `raw/build_reports.py` draws every report's frames and route
  maps (from the trace when there is one).
- `discarded.jsonl`: rows the player chose not to count, with `discarded.why`.

## Battles

| problem | player | result | lost (actual) | raiders out | vs agent | report |
|---|---|---|---|---|---|---|
| t500_pirate_grenadier | human | pyrrhic, then repelled | 1, then 0 | 6, then 4 | agents 164–239% HP | – (summary in TODO roadmap 3) |
| rand_107 (#1) | human | defeat (captives) | 4 | 4 | doctrine: lost 6, 3 out | [rand_107](reports/rand_107.md) |
| rand_067 (#2) | human | defeat (captives) | 1 | 5 | kite: lost 6, 2 out | [rand_067](reports/rand_067.md) |
| rand_030 (#3) | human_swap | **decisive** | 1 | 9 of 9 | close: lost 7, 3 out | [rand_030](reports/rand_030.md) |
| rand_084 (#4) | human_loadout | **repelled**, nobody downed | 0 | 6 of 8 | doctrine: lost 6, 3 out | [rand_084](reports/rand_084.md) |
| rand_127 (#5) | human_loadout | **repelled** | 0 (1 downed) | 5 of 7 | amove: all 10 downed, 0 out | [rand_127](reports/rand_127.md) |
| rand_065 (#6) | human_loadout | squad down (≈ draw) | 0 + 3 being carried off | 3 of 6 | close: lost 4, 3 out | [rand_065](reports/rand_065.md) |
| rand_029 (#7) | human_loadout | **pyrrhic** | 2 (both captives taken back) | 7 of 8 | doctrine: 7 dead, 5 out | [rand_029](reports/rand_029.md) |
| rand_039 (#8) | human_loadout | **repelled** | 0 (1 downed, carried along) | 6 of 8 | kite: lost 5, 2 out | [rand_039](reports/rand_039.md) |

**Batch 1 (worst list #1–#8, 2026-10-05), in one line each:** the human beat the agent on all
eight by badness (8.0–96 vs 108–142); five wins (030, 084, 127, 029, 039 — four of them with
Claude's loadout), two defeats with far fewer losses (107, 067) and one near-draw (065). Every
win used a terrain play; every loss had isolated pawns or a downed pawn left exposed. Rows from
this batch stopped at squad down (old rule); the next batch runs with `end_rule: raid_gone`.

`human_loadout`: Claude redistributed the weapons at the start (`manage_gear` drop + equip,
~100–150 ticks, before the player drafted), the player fought. Attempts the player abandoned or
discarded keep their traces (`_try1`, `_try2`); a discarded row goes to `discarded.jsonl`.

"Lost (actual)": the rows count a kidnapped pawn twice (TODO Now 2); the reports correct it.

## What the human games say so far (hypotheses for the gate)

1. **Kidnapping decides Strive battles.** Every defeat above ended with captives. Keep the downed
   inside the group; when a raider's job becomes "kidnapping X", that carrier is the top target
   and standing pawns move onto its path to the edge (rand_067 frames 7–8, rand_107 frames 6–7).
2. **Isolated pawns go down first** (rand_107 frame 4; rand_067 frame 5).
3. **Short-range squads ambush instead of advancing:** wait behind sight-blocking terrain where
   the raid must come round a corner inside our range (rand_030 frames 3–5; rand_084: a notch
   cancelled a 37-cell sniper).
4. **Loadout is a strategic decision:** guns to the best shooters, melee weapons to the best
   melee, throwables to the worst shooters, while the raid is still far (rand_030 frame 1;
   done by Claude in rand_084 and rand_127, both won).
5. **Bows against melee closers:** kiting stretches the raid, but once the melee arrives the
   archers lose; kill the closers before contact, never charge alone (rand_067 frames 3–6).
6. **The briefing needs skills and weapon quality** (rand_107: the router chose blind).
7. **The site decides, through a play** (user: "you need a tactical repertoire before
   battlefield selection works"). Every win used a named play that needs a terrain feature:
   corner ambush (rand_030), notch hold + gap slip to break the throwers' sight (rand_084),
   narrow mouth with rotation against stronger melee (rand_127; the same squad lost in the open).
8. **Points don't price xenotypes:** 7 Neanderthals beat 10 tribals in the open at 500 v 500
   (agent and human, rand_127).
9. **Loadout follows the play, not skill alone:** rand_065 gave Jess (shooting 16, melee 14) a
   37-cell rifle for what became a 4–6-cell fight. (play, site, loadout) is one decision.
10. **Spacing yes, width no:** rand_029's line was 4–5 cells between pawns but 43 cells end to
   end; every loss was on an end. Keep each pawn within reach of two neighbours.
11. **Stepped withdrawal against a raid that holds at range:** fall back a bound, turn, kill
   whoever followed (rand_039: knives and the grenadier arrived one at a time); carry the
   downed along.
