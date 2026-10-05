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
| rand_011 (#9) | human_loadout | **decisive** | 1 | 9 of 9 | close: lost 3 (kidnapped), 4 downed | [rand_011](reports/rand_011.md) |
| rand_104 (#10) | human_loadout | **decisive** | 2 | 8 of 8 | turtle: lost 4, 4 downed (squad down) | [rand_104](reports/rand_104.md) |

**Batch 1 (worst list #1–#8, 2026-10-05), in one line each:** the human beat the agent on all
eight by badness (8.0–96 vs 108–142); five wins (030, 084, 127, 029, 039 — four of them with
Claude's loadout), two defeats with far fewer losses (107, 067) and one near-draw (065). Every
win used a terrain play; every loss had isolated pawns or a downed pawn left exposed. Rows from
this batch stopped at squad down (old rule); the next batch runs with `end_rule: raid_gone`.

`human_loadout`: Claude redistributed the weapons at the start (`manage_gear` drop + equip,
~100–150 ticks, before the player drafted), the player fought. Attempts the player abandoned or
discarded keep their traces (`_try1`, `_try2`); a discarded row goes to `discarded.jsonl`.

"Lost (actual)": the rows count a kidnapped pawn twice (TODO Now 2); the reports correct it.

## Replays: can the plan be copied without the human? (2026-10-05)

| problem | who | how | result | lost | badness |
|---|---|---|---|---|---|
| rand_127 | `replay` v1 (Python, `tools/run_replay.py`) | the human's loadout + positions over time | squad down, 6 kidnapped | 6 | 190 |
| rand_127 | `replay` v2 | + hit the wall the human broke | same: the wall never fell | 6 | 190 |
| rand_127 | **Claude, playing directly** (`tools/hands.py`, player `claude`) | same plan, decided turn by turn: breach with 6 pawns, the two strongest at the mouth, open the urn cell (3 v 1), rotate the front below 45% | **repelled** | **0** (1 downed) | **10.8** (human 26.0) |
| rand_030 | Claude, directly | same loadout and hill; the raid split round both sides of the hill this time; smoke, Mushinto first, molotov + frags on the southern group, Butters tied up the grenadier late | repelled | 1 (7 permanent injuries) | 38.8 (human 21.1) |
| rand_084 | Claude, directly | same loadout, notch, gap slip at 11 cells, knives on Rusty, both grenadiers tied up in melee; Carlson flanked round the west end and killed Alo | repelled | 1 | 20.5 (human 1.8) |
| rand_039 | Claude, directly | same loadout, ruin, three bounds east killing the followers; carried the downed; chased three kidnappers and got all three back | pyrrhic | 0 (5 downed) | 48.4 (human 8.0) |
| rand_011 | Claude, directly | the user's plan and intentions (card); raiders' `targeting` read for their firing cells; grenadiers killed early (t2364, t2739); frag dodging by `hands.guard()`; three pawns down (bait, front shotgun, club locking a shotgunner) | repelled | 0 (3 downed) | 22.4 (human 25.8) |
| rand_104 | Claude, directly | the user's line and loadout; `hands.guard()` (3-tick steps, grenade targets from `targeting`); early melee locks on Bishop and Cholaky; throwers all dead by t3807; losses while carrying/walking under three guns | repelled | 1 (3 downed) | 35.3 (human 46.0) |
| rand_015 | **Claude alone** (no human game first) | loadout; west rock pocket, corner ambush at rock B's tip; four raiders out with no loss, then shot at the tip by gunners holding at 15–20; molotov grass fire; kidnapping | defeat (captive) | 1 dead + 1 kidnapped (1 downed) | 61.4 (agent 105.2) |
| rand_015 | Claude alone, attempts 2–3 | 2: same pocket (79.9); 3: big-ruin rooms, all six lost (no row: harness crash on the man-in-black removal, fixed) | defeat | 3 / 6 | 79.9 / – |
| rand_023 | Claude alone | breach the NE walled hall to hide in its blind cells; the breach failed (orders re-issued too fast) and a blind wait loop let the raid catch the squad outside | squad down (defeat) | 4 (6 downed) | 100.2 (agent 101.8) |
| rand_126 | Claude alone | loadout (rifle to the shooting-16 club holder); west rock pocket; tip ambush 3–4 on 1; Max's rifle, machine pistols and a Fire spew on the raiders holding north of the pocket | **repelled** | **0** (0 downed) | **13.6** (agent 99.8) |
| rand_058 | Claude alone | west rock pocket (east part, hidden from the south); frag and molotovs on the bunch at the tip and on the raiders who went north; locks; one death from our own frag | **repelled** | 2 (2 downed) | 47.3 (agent 99.1) |

Turn logs of Claude's plays (orders by tick, what followed): `raw/<id>/claude_turns.md`; the
operating facts they rely on are in RIMMOLT_API.md (verb gizmo on buildings, melee/carry
orders, manage_gear) and GAME_FACTS.md.

Claude's direct replays: better than the human where the raid moved as in the human's game
(127), worse where it did not (030: the raid split round the hill; 084: the sniper flanked
round the far end). Missing habit: track the top threat's path and keep a flank watch.

Positions alone lost; the plan won once the hands-on parts were done: breaking the wall
with many pawns (one swing per order), standing *beside* the mouth instead of in it, a
third cell touching the mouth, and rotation. Coding each intention as an agent is slow
(user, 2026-10-05), so the next replays are played directly; the Python replay rows stay in
`replay.jsonl` as the "plan only" control. Caveat: Claude knew the plan and the raid's timing.

Since 2026-10-05 Claude plays new problems directly with a case library of these battles (one card per problem, sites, tags, journals): `results/cases/`, PROCEDURES §16.

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
