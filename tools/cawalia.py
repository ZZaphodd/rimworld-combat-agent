"""Cawalia Union's raid-size staircase (the user, 2026-10-08): Claude plays every battle directly;
after a win the raid grows by 0.5x, after a loss it shrinks by 0.5x, so the run settles around the
size the base can hold with active maneuvering. The raid kind rotates (tribe, pirate, mech): the
amount matters more than the kind. Spike traps left is the second measure.

From battle 14 on (the user, after mech 7.5x was lost) one multiplier still moves by 0.5x, but the
step comes from a sliding window of the last 6 counted battles (2 per raid kind): more wins than
losses in it -> up, more losses -> down, a tie -> the same. One kind's loss no longer pulls the
others down on its own.

  python3 tools/cawalia.py next             # the next multiplier and kind
  python3 tools/cawalia.py prepare          # build that scenario if it is missing; print the manifest path
  python3 tools/cawalia.py record           # append the last Claude row on a base2_caw problem
  python3 tools/cawalia.py record --concede # the same, booked as a loss (a battle given up)
  python3 tools/cawalia.py show

Play each battle with tools/run_human.py --player claude --max-ticks 30000; 60000 for a mech battle
(the user, 2026-10-08: mech raids gather ~7,000 ticks and never flee).

State: results/base/cawalia_staircase.jsonl (one line per battle). A win is the row's `win`
(decisive or repelled, EVAL_SPEC); an unresolved or invalid row does not move the staircase.
"""
import argparse
import json
import sys
from pathlib import Path

import _path  # noqa: F401
from rca import ROOT

STATE = ROOT / "results/base/cawalia_staircase.jsonl"
PLAY = ROOT / "results/human/play.jsonl"
SPECS = ROOT / "scenarios_base2.json"
SCEN = ROOT / "scenarios_base2"
KINDS = ("tribe", "pirate", "mech")
START, STEP, FLOOR = 2.0, 0.5, 0.5
WINDOW, WINDOW_FROM = 2 * len(KINDS), 14       # the window rule decides the step after battle 14 on
RATIONS_DAYS = 2              # survival meals by the squad's start in new builds (the user, battle 24)


def rows():
    return [json.loads(l) for l in STATE.read_text().splitlines() if l.strip()] if STATE.exists() else []


def counted(r):
    return r.get("grade") not in ("unresolved", "invalid", None)


def step_after(played):
    """The step after the last counted battle: its own result before WINDOW_FROM, then the balance
    of wins and losses over the last WINDOW counted battles."""
    last = played[-1]
    if last.get("n", 0) < WINDOW_FROM:
        return STEP if last["win"] else -STEP
    w = played[-WINDOW:]
    wins = sum(1 for r in w if r["win"])
    return STEP if wins > len(w) - wins else -STEP if wins < len(w) - wins else 0.0


def next_step(history):
    """(multiplier, kind) for the next battle."""
    played = [r for r in history if counted(r)]
    if not played:
        return START, KINDS[0]
    return max(FLOOR, played[-1]["mult"] + step_after(played)), KINDS[len(played) % len(KINDS)]


def pid(kind, mult):
    tag = f"{mult:g}".replace(".", "p")
    return f"base2_caw_{kind}_{tag}x"


def prepare(kind, mult, log=print):
    """The scenario for (kind, mult): its manifest path, built (and its spec added) if missing."""
    p = pid(kind, mult)
    path = SCEN / f"scenario_{p}.json"
    if path.exists():
        return path
    specs = json.loads(SPECS.read_text())
    spec = next((s for s in specs if s["id"] == p), None)
    if spec is None:
        base = next(s for s in specs if s["id"] == f"base2_caw_{kind}_2x")
        spec = json.loads(json.dumps(base))
        spec["id"] = p
        spec["enemy"]["points"] = int(round(500 * mult))
        spec["rations_days"] = RATIONS_DAYS
        specs.append(spec)
        SPECS.write_text(json.dumps(specs, indent=1, ensure_ascii=False) + "\n")
        log(f"spec {p} added ({spec['enemy']['points']} pt)")
    from rca.game.builders import scenario
    from rca.rimmolt import RimMolt
    scenario.build_checked(RimMolt(), spec, SCEN)
    return path


def record(log=print, concede=False):
    """Append the last Claude row on a base2_caw problem to the staircase (once). concede books it
    as a loss whatever the harness graded it (grade "conceded")."""
    play = [json.loads(l) for l in PLAY.read_text().splitlines() if l.strip()]
    r = next((x for x in reversed(play) if x.get("agent") == "claude"
              and str(x.get("scenario", "")).startswith("base2_caw_")), None)
    if r is None:
        raise SystemExit("no Claude row on a base2_caw problem")
    history = rows()
    if any(h.get("time") == r.get("time") for h in history):
        raise SystemExit(f"already recorded: {r['scenario']}")
    from rca.eval.ranking import badness
    _, kind, tag = r["scenario"].split("_")[1:4]
    mult = float(tag[:-1].replace("p", "."))
    traps = r.get("traps") or {}
    t0, t1 = (traps.get("start") or {}).get("count"), (traps.get("end") or {}).get("count")
    line = {"n": len(history) + 1, "scenario": r["scenario"], "kind": kind, "mult": mult,
            "grade": "conceded" if concede else r.get("grade"),
            "win": False if concede else bool(r.get("win")), "badness": badness(r)[0],
            "deaths": r.get("deaths"), "downed": r.get("downed_at_end"),
            "enemies_seen": r.get("enemies_seen"), "raid_fled_tick": r.get("raid_fled_tick"),
            "ticks": r.get("ticks"), "traps_start": t0, "traps_end": t1,
            "traps_used": (t0 - t1) if t0 is not None and t1 is not None else None,
            "trace": r.get("trace"), "time": r.get("time")}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with STATE.open("a") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    log(json.dumps(line, ensure_ascii=False))
    return line


def show():
    for r in rows():
        print(f"{r['n']:>3} x{r['mult']:<4g} {r['kind']:6} {r['grade']:10} badness {r['badness']:>6} "
              f"lost {r['deaths']} downed {r['downed']} traps {r['traps_start']} -> {r['traps_end']}")
    m, k = next_step(rows())
    print(f"next: x{m:g} {k} ({pid(k, m)})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("next", "prepare", "record", "show"))
    ap.add_argument("--concede", action="store_true", help="record: book the battle as a loss")
    a = ap.parse_args()
    if a.cmd == "next":
        m, k = next_step(rows())
        print(f"x{m:g} {k} {pid(k, m)}")
    elif a.cmd == "prepare":
        m, k = next_step(rows())
        print(prepare(k, m))
    elif a.cmd == "record":
        record(concede=a.concede)
    else:
        show()


if __name__ == "__main__":
    sys.exit(main())
