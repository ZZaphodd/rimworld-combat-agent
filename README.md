# rimworld-combat-agent

Research on combat agents for RimWorld, driven through the [RimMolt](https://steamcommunity.com/sharedfiles/filedetails/?id=3796006886)
mod's MCP server. The agents fight RimWorld's built-in raid AI (not other players) and are
evaluated on generated test scenarios.

Status: **pre-baseline** — the docs are the source of truth; the Python code is being
rebuilt on a three-layer architecture (micro / tactical / strategic). See [DOCS.md](DOCS.md)
for the document index, [TODO.md](TODO.md) for the roadmap and [WORKFLOW.md](WORKFLOW.md) for
how changes are tested.

## Requirements
- RimWorld with the RimMolt mod (MCP server at `http://localhost:8787/mcp`); dev mode allowed for
  the AI in RimMolt's settings for scenario building.
- Python 3 (standard library only).
- `./restore_saves.sh` unpacks the versioned arena/scenario saves into RimWorld's Saves folder.

Not affiliated with Ludeon Studios or the RimMolt author. No game files are included.

## License
[0BSD](LICENSE) — use it however you like; provided as is, without warranty or liability.
