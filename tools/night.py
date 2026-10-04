"""Router night run (TODO roadmap 3): random problems, a router picks the doctrine,
the Python agents fight, the worst problems are listed for a person to replay.

  python3 tools/night.py new                       # build the next problem, print the briefing
  python3 tools/night.py run rand_007 --agent turtle --option vs_throwers=stand_off \\
      --why "melee-heavy tribe comes to us; open ground"
  python3 tools/night.py rank --top 100            # results/night/worst.md

Rows: results/night/router.jsonl (harness rows + router {agent, options, why} + badness).
The game is restarted after RESTART_LOADS loads (state in results/night/state.json).
"""
import argparse
import json
import random
import sys
import time

import _path  # noqa: F401
from rca import ROOT
from rca.eval.harness import Cycle, run_episode
from rca.eval.ranking import badness, worst
from rca.eval.results import append_row, canonical, read_rows
from rca.game.builders import problem
from rca.game.session import Watchdog
from rca.rimmolt import RimMolt
from rca.strategic import briefing
from rca.tactical import make

OUT = ROOT / "results/night"
ROWS, STATE = OUT / "router.jsonl", OUT / "state.json"
RESTART_LOADS = 80


def log(s):
    print(s, flush=True)


def state():
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {"loads": 0, "factions": None}


def save_state(s):
    OUT.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s))


def ready(rm, loads):
    """Relaunch a dead game; restart a tired one (NullReferenceExceptions grow with loads)."""
    s = state()
    wd = Watchdog(rm, log=log)
    if s["loads"] + loads > RESTART_LOADS and rm.alive():
        wd.planned_restart()
        s["loads"] = 0
    wd.ensure()
    s["loads"] += loads
    save_state(s)
    return s


def manifest(pid):
    return json.loads((problem.OUT / f"scenario_{pid}.json").read_text())


def cmd_new(a):
    rm = RimMolt()
    s = ready(rm, 1)
    from rca.game import session
    from rca.game.debug import Debug
    if not s.get("factions"):
        session.load(rm, problem.ARENAS[0])
        s = state()
        s["factions"] = problem.raid_factions(Debug(rm, log))
        save_state(s)
        log(f"raid factions: {s['factions']}")
    rng = random.Random(a.seed if a.seed is not None else time.time_ns())
    m = None
    for _ in range(3):
        try:
            m = problem.make(rm, problem.next_index(), rng, s["factions"], a.points, log)
        except Exception as e:                  # a failed build costs a retry, not the night
            log(f"   build failed: {e!r}")
            m = None
        if m:
            break
    if not m:
        sys.exit("no problem could be built")
    feats = briefing.features(m)
    pre = briefing.preconditions(rm, m)
    m["briefing"] = {"features": feats, "preconditions": pre}
    (problem.OUT / f"{m['save']}.json").write_text(json.dumps(m, indent=2, ensure_ascii=False))
    print(briefing.text(m, feats, pre))


def cmd_run(a):
    rm = RimMolt()
    ready(rm, 1)
    m = manifest(a.pid)
    options = dict(o.split("=", 1) for o in a.option)
    agent = make(a.agent)
    row = run_episode(rm, m, agent, a.max_ticks, Cycle(), True, log, options)
    sp = m["spec"]
    row["problem"] = {"arena": sp["arena"], "squad": sp["squad"]["faction"],
                      "squad_n": len(m["squad"]), "enemy": sp["enemy"]["faction"],
                      "enemy_n": len(m["enemy"])}
    row["router"] = {"agent": canonical(a.agent), "options": options, "why": a.why}
    score, parts = badness(row)
    row["badness"], row["badness_parts"] = score, parts
    append_row(ROWS, row)
    log(f"{a.pid} {canonical(a.agent)} -> {row['outcome']} grade={row['grade']} lost="
        f"{row['deaths'] + row.get('squad_kidnapped', 0)} downed={row['downed_at_end']} "
        f"perm={row['new_permanent_injuries']} hp={row['hp_lost_pct']}% killed="
        f"{row['enemies_killed']}+{row['enemies_killed_inferred']}/{row['enemies_seen']} "
        f"escaped={row['enemies_escaped']} ticks={row['ticks']} wall={row['wall_s']}s "
        f"badness={score} {parts}")


def cmd_rank(a):
    rows = [r for r in read_rows(ROWS)] if ROWS.exists() else []
    top = worst(rows, a.top)
    lines = [f"# Worst problems of the router night run ({len(top)} of {len(rows)} battles)\n",
             "Badness = 10 x lost + 3 x downed at end + 2 x new permanent injuries + HP lost/25"
             " + grade penalty (defeat 10, pyrrhic 4, unresolved 3); rca/eval/ranking.py.\n",
             "Replay one: `python3 tools/run_human.py --manifest scenarios_rand/scenario_<id>.json`\n",
             "| # | problem | arena | ours | enemy | router | outcome | lost | downed | perm | HP% | badness |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(top, 1):
        p, ro = r.get("problem", {}), r.get("router", {})
        opts = ",".join(f"{k}={v}" for k, v in (ro.get("options") or {}).items())
        lines.append(f"| {i} | {r['scenario']} | {p.get('arena', '').replace('arena_', '')} | "
                     f"{p.get('squad')} x{p.get('squad_n')} | {p.get('enemy')} x{p.get('enemy_n')} | "
                     f"{ro.get('agent')}{f' ({opts})' if opts else ''} | {r['grade']} | "
                     f"{r['deaths'] + (r.get('squad_kidnapped') or 0)} | {r['downed_at_end']} | "
                     f"{r['new_permanent_injuries']} | {r['hp_lost_pct']} | {badness(r)[0]} |")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "worst.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:min(len(lines), 25)]))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("--points", type=int, default=500)
    n.add_argument("--seed", type=int)
    r = sub.add_parser("run")
    r.add_argument("pid")
    r.add_argument("--agent", required=True)
    r.add_argument("--option", action="append", default=[])
    r.add_argument("--why", default="")
    r.add_argument("--max-ticks", type=int, default=15000)
    k = sub.add_parser("rank")
    k.add_argument("--top", type=int, default=100)
    a = ap.parse_args()
    {"new": cmd_new, "run": cmd_run, "rank": cmd_rank}[a.cmd](a)


if __name__ == "__main__":
    main()
