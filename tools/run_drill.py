"""Micro frag drill, dodge OFF vs ON, judged per event (rca/micro/drills.py).

  python3 tools/run_drill.py --sessions 3 --events 12
  python3 tools/run_drill.py --summary results/drills/frag_drill.jsonl
"""
import argparse
import json
from pathlib import Path

import _path  # noqa: F401
from rca import ROOT
from rca.game.session import Watchdog
from rca.micro import drills
from rca.rimmolt import RimMolt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", type=int, default=3, help="per mode")
    ap.add_argument("--events", type=int, default=12, help="exploded frags per session")
    ap.add_argument("--count", type=int, default=3, help="grenadiers spawned")
    ap.add_argument("--range", dest="rng", type=int, default=12)
    ap.add_argument("--max-ticks", type=int, default=6000)
    ap.add_argument("--modes", default="off,on")
    ap.add_argument("--out", type=Path, default=ROOT / "results/drills/frag_drill.jsonl")
    ap.add_argument("--summary", type=Path)
    a = ap.parse_args()
    if a.summary:
        rows = [json.loads(l) for l in a.summary.read_text().splitlines() if l.strip()]
        print(json.dumps(drills.summarize(rows), indent=1))
        return
    rm = RimMolt()
    modes = tuple(m == "on" for m in a.modes.split(","))
    out = drills.run(rm, a.sessions, a.events, a.out, modes, log=lambda s: print(s, flush=True),
                     watchdog=Watchdog(rm), count=a.count, rng=a.rng, max_ticks=a.max_ticks)
    rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    print(json.dumps(drills.summarize(rows), indent=1), flush=True)


if __name__ == "__main__":
    main()
