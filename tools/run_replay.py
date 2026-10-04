"""Re-fight a human battle from its trace with the replay agent (rca/tactical/replay.py).

  python3 tools/run_replay.py --trace results/human/traces/rand_127_human_loadout_20261005-064050.jsonl.gz

Same scenario, the human's loadout and positions over time, everything else as in an agent
episode (adaptive cycle, micro on, Strive to Survive). Rows go to results/human/replay.jsonl.
"""
import argparse
import json
from pathlib import Path

import _path  # noqa: F401
from rca import ROOT
from rca.eval import trace as trace_io
from rca.eval.harness import Cycle, load_manifests, run_episode
from rca.eval.results import append_row
from rca.rimmolt import RimMolt
from rca.tactical import Replay


def manifest_for(scenario):
    rand = ROOT / f"scenarios_rand/scenario_{scenario}.json"
    return json.loads(rand.read_text()) if rand.exists() else load_manifests([scenario])[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", type=Path, required=True)
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--max-ticks", type=int, default=15000)
    ap.add_argument("--results", type=Path, default=ROOT / "results/human/replay.jsonl")
    a = ap.parse_args()
    log = lambda s: print(s, flush=True)          # noqa: E731
    head = trace_io.read(a.trace)[0]
    m = manifest_for(head["scenario"])
    path = a.trace.resolve()
    rel = str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
    rm = RimMolt()
    for run in range(a.runs):
        log(f"== replay {m['id']} of {head.get('player')} ({rel}) run {run + 1}")
        row = run_episode(rm, m, Replay(), a.max_ticks, Cycle(), reflex=True, log=log,
                          options={"trace": rel})
        row["replay_of"] = {"trace": rel, "player": head.get("player")}
        append_row(a.results, row)
        k = row.get("kpis", {}).get("replay", {})
        log(f"   {row['outcome']} grade={row['grade']} lost={row['deaths']} downed={row['downed_at_end']} "
            f"| killed {row['enemies_killed']}+{row['enemies_killed_inferred']} escaped "
            f"{row['enemies_escaped']} | ticks={row['ticks']} | loadout {k.get('loadout_swaps')} swaps "
            f"(missing {k.get('loadout_missing')}), dev {k.get('dev_before_contact')}/"
            f"{k.get('dev_after_contact')} cells")


if __name__ == "__main__":
    main()
