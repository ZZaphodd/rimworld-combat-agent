# Model A/B battle: the briefing (identical for every player)

You play one RimWorld 1.6 combat scenario yourself, start to end, alone. You command our squad
(the player faction); a raid is coming. Nobody will answer questions: decide everything yourself
and play to the end.

**Goal:** win the battle (the raid killed, downed or driven off) and lose as little as possible.
The harness grades it, and the comparison uses its row:

- `grade`: decisive / repelled (wins), pyrrhic, defeat, unresolved.
- `badness` (lower is better) = 10 per pawn of ours lost (dead or kidnapped) + 3 per pawn of ours
  downed at the end + 2 per new permanent injury + 1 per 25 % of HP lost (summed over the squad)
  + 10 for defeat, 4 for pyrrhic, 3 for unresolved.

## The setup

- The game is RimWorld with the RimMolt mod, which answers on 127.0.0.1:8787. You reach it through
  the Python helpers in `tools/hands.py` (they wrap `rca/rimmolt.py`). Run them from the repo root
  as short scripts, e.g.
  `python3 -c "import sys; sys.path.insert(0, 'tools'); from hands import *; st()"`.
- The game is paused. **Game time moves only when you advance it** (`wait`, `guard`, `wait_safe`,
  `skip`); thinking between calls costs no game time.
- `tools/run_human.py` loads the scenario and only watches: it never orders, pauses or advances.
  It ends by itself when the raid is gone, when the squad is down (it then watches 6000 more
  ticks), or at 15000 ticks, and appends one row to `results/model_ab/play.jsonl`.

## Rules

1. Play only your scenario. Never load, save or overwrite a save yourself; never run builders,
   ladders, night runs, the overlay, `tools/cawalia.py`, git, or anything else not named here.
   Never call port 28781 (another mod).
2. Read only: this file, the scenario's manifest (`scenarios_rand/scenario_<id>.json`),
   `tools/hands.py`, `rca/` code, `RIMMOLT_API.md`, `GAME_FACTS.md`, `GLOSSARY.md`, `LESSONS.md`.
   Do **not** read anything else under `results/` (past battles, cards, journals, traces, other
   players' notes or rows), `PROCEDURES.md`, or git history. Exception: your own frames, which
   `shot()` writes to `results/human/hands_<run>_*.jpg`.
3. Write only under your run folder `results/model_ab/runs/<run>/` (notes, scratch scripts,
   images). Do not edit any other file in the repo.
4. Never advance time blind: in any loop that moves time, use `guard()` or `wait_safe()`, which
   stop when a raider comes near or one of ours goes down. A plain `wait()` loop has let raids
   arrive unseen. `skip(t)` fast-forwards and does not stop on threats: only for stretches where
   nothing can happen.
5. If the game or RimMolt breaks (errors that do not go away, the game gone), stop, kill your own
   harness, and report; never restart or reload the game.

## Procedure

1. **Check** that no other harness runs: `pgrep -fl run_human.py` must print nothing. If one runs,
   wait up to 2 minutes, then report and stop.
2. **Start the harness** in the background and wait for its "loaded and paused" line:
   ```
   mkdir -p results/model_ab/runs/<run>
   nohup python3 tools/run_human.py --manifest scenarios_rand/scenario_<id>.json --player <tag> \
     --results results/model_ab/play.jsonl --trace-dir results/model_ab/traces \
     > results/model_ab/runs/<run>/harness.log 2>&1 &
   ```
3. **Read the situation:** `brief("player")`, `brief("hostile")` (skills, traits, weapons, armour,
   items, positions), `st()`, the manifest's `briefing.features`, and frames with
   `shot(x0, z0, w, h, out="<run>_<name>.jpg")`: it prints the path it wrote
   (`results/human/hands_<run>_<name>.jpg`); look at the image with your file reader.
   `GAME_FACTS.md` has weapon ranges and game rules.
4. **Plan** where to fight, the loadout and the play. Write the plan in a few lines to
   `results/model_ab/runs/<run>/plan.md` before the first order.
5. **Loadout** (optional) before anyone is drafted: drafting cancels a pick-up job. Swapping
   weapons goes through `manage_gear` (drop, then equip by thing id; RIMMOLT_API.md).
6. **Play:** draft and order with the helpers (`draft`, `go`, `fire`/`attack`, `melee`, `hit`,
   `fire_at_will`, `stop`, ...; read `tools/hands.py` for the full list and their caveats). Look
   with `st()` and `shot()`. Advance 45-150 ticks per decision, less in contact.
7. **End:** when the harness has written its last line ("... grade=... -> results/model_ab/play.jsonl")
   and exited, compute badness:
   ```
   python3 -c "import json,sys; sys.path.insert(0,'.'); from rca.eval.ranking import badness; \
   r=[json.loads(l) for l in open('results/model_ab/play.jsonl') if l.strip()]; \
   r=[x for x in r if x['agent']=='<tag>' and x['scenario']=='<id>'][-1]; print(r['grade'], r['deaths'], r['downed_at_end'], r['ticks'], badness(r))"
   ```
   If you must stop early, kill your harness (`pkill -f "player <tag>"`) so the next player
   starts clean. Aim to finish within about 90 minutes of wall time.

## Facts about the tools worth knowing

- Enemy short names repeat (two "Villager"s); `fire`/`attack`/`melee` pick by short name. When a
  name is ambiguous, target by thing id (`hit(name, thing_id)`; ids come from `pawns("hostile")`).
- A fire order given to a walking pawn stops it where it is.
- "Go here" is not offered for a blocked cell; `go()` then prints a failure and the pawn stays.
- Never send pawns at a raider that one of our own grenades is aimed at: throw first, close in
  after the blast.

## Your report (final answer)

Return, as plain text:
- `model`: your exact model ID (from your system prompt).
- `run`, `scenario`, `tag`.
- `result`: the harness's last line, and the badness line printed by the command above.
- `plan`: 3-5 lines. `moments`: up to 8 key moments with game ticks. `tool_problems`: up to 5.
- `wall_minutes`: about how long you played.
