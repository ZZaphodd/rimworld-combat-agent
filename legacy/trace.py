"""Step-by-step trace of one episode, for figuring out *why* an agent wins or loses.

  python3 trace.py fort_tribe_rush b0 [--every 5] [--steps 80]

Per sampled step: our pawns (standing/down, inside/outside the fort, job kinds)
and the raid (alive, inside, near the gate, what they target, what they're doing).
"""
import argparse
import json
import math
from collections import Counter

from eval import AGENTS, AgentClient
from scenario_builder import Builder
from rimmolt_client import RimMolt

FORT = (110, 110, 140, 140)
GATE = (140, 125)


def inside(t):
    x0, z0, x1, z1 = FORT
    return x0 < t["x"] < x1 and z0 < t["z"] < z1


def word(s, n=1):
    return " ".join((s or "-").replace(".", "").split()[:n])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("agent")
    ap.add_argument("--every", type=int, default=5)
    ap.add_argument("--steps", type=int, default=90)
    a = ap.parse_args()

    rm = RimMolt()
    m = json.loads(open(f"scenarios_out/scenario_{a.scenario}.json").read())
    Builder(rm).load(m["save"])
    rm.call("debug_menu", action="run", tab="settings", path="Never Force Normal Speed", value=True)
    rm.call("debug_menu", action="close")
    rm.call("dev_mode", devMode=False)

    ids = {p["id"] for p in m["squad"]}
    hr = rm.call("set_hostility_response")
    print("squad hostility response:", Counter(c["response"] for c in hr["colonists"]))
    raid = rm.call("list_things", category="pawn", confirm=True, faction="hostile")["things"]
    weapons = Counter(word(rm.call("get_pawn", id=h["id"]).get("weapon"), 2) for h in raid)
    print("raid weapons:", dict(weapons.most_common(8)))

    agent, client = AGENTS[a.agent](), AgentClient(rm)
    agent.reset(client, m)
    for i in range(a.steps):
        agent.step_ticks, agent.now = 120, i * 120     # agents keep their timers in ticks
        agent.step(client)
        rm.call("wait_for_event", _timeout=60, maxGameTicks=120, maxSeconds=20,
                pause="always", force=True)
        hs = rm.call("list_things", category="pawn", confirm=True, faction="hostile", verbose=True)["things"]
        live = [h for h in hs if not h.get("downed") and not h.get("dead")]
        us = [t for t in rm.call("list_things", category="pawn", confirm=True, faction="player",
                                 verbose=True)["things"] if t["id"] in ids]
        done = not live or all(t.get("downed") for t in us)
        if i % a.every and not done:
            continue
        cols = {c["id"]: c for c in rm.call("list_colonists")["colonists"]}
        up = [t for t in us if not t.get("downed")]
        hjobs = Counter(word(rm.call("get_pawn", id=h["id"]).get("job"), 2) for h in live[:12])
        print(f"step {i:2} | us up {len(up):2} down {len(us) - len(up):2} "
              f"in {sum(inside(t) for t in up):2} out {sum(not inside(t) for t in up):2} "
              f"drafted {sum(bool(t.get('drafted')) for t in up):2} "
              f"jobs {dict(Counter(word(cols.get(t['id'], {}).get('job'), 2) for t in up).most_common(3))}")
        print(f"        | raid live {len(live):2} downed {len(hs) - len(live):2} "
              f"in {sum(inside(h) for h in live):2} gate<8 "
              f"{sum(math.dist((h['x'], h['z']), GATE) < 8 for h in live):2} "
              f"tgt {dict(Counter(word(h.get('targeting'), 2) for h in live).most_common(3))} "
              f"jobs {dict(hjobs.most_common(3))}")
        if done:
            break


if __name__ == "__main__":
    main()
