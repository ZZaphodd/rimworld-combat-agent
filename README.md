# rimworld-combat-agent

Research on combat agents for RimWorld, driven through the [RimMolt](https://steamcommunity.com/sharedfiles/filedetails/?id=3796006886)
mod's MCP server. The agents fight RimWorld's built-in raid AI (not other players) and are
evaluated on generated test scenarios.

Status: the code is rebuilt on a three-layer architecture (micro / tactical / strategic) in `rca/`,
with six doctrines (amove, doctrine, turtle, spread, kite, close). **baseline-v1** was measured on
the Peaceful difficulty; the evaluation standard is now **Strive to Survive** (WORKFLOW.md), so
baseline-v1 is exploration data and **baseline-v2** is next. The docs are the source of truth; the
exploration code is kept in `legacy/` for reference. See [DOCS.md](DOCS.md) for the document index
and code layout, [TODO.md](TODO.md) for the roadmap and [WORKFLOW.md](WORKFLOW.md) for how changes
are tested.

## Usage

```
./restore_saves.sh                                    # scenario saves -> RimWorld's Saves folder
python3 -m unittest discover -s tests -t .            # offline tests
python3 tools/run_eval.py --agents amove --scenarios theme_pirate_mixed --runs 5 \
    --results results/my_batch.jsonl --resume          # episodes (one game instance only)
python3 tools/report.py results/my_batch.jsonl         # trade ratio, grades, P vs amove
python3 tools/run_eval.py --agents turtle --scenarios theme_frag_check --runs 1 \
    --option vs_throwers=stand_off --results results/my_batch.jsonl   # tactical option
python3 tools/run_drill.py --sessions 3 --events 12   # micro frag drill, dodge off vs on
python3 tools/rescore.py                               # rescore every results file
python3 tools/gate.py results/gate/<branch>.jsonl     # merge gate: branch vs baseline
python3 tools/rm.py status                            # probe the running game, compact output
```

## Requirements
- RimWorld with the RimMolt mod (MCP server at `http://localhost:8787/mcp`); dev mode allowed for
  the AI in RimMolt's settings for scenario building.
- Python 3 (standard library only).
- `./restore_saves.sh` unpacks the versioned arena/scenario saves into RimWorld's Saves folder.

Not affiliated with Ludeon Studios or the RimMolt author. No game files are included.

## License
[0BSD](LICENSE) — use it however you like; provided as is, without warranty or liability.
