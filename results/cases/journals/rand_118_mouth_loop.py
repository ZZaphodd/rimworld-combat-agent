"""rand_118 attempt 2: nook mouth hold with real fire control.
usage: python3 mouth2.py <steps> [setup]"""
import sys, math, json, os
sys.path.insert(0, "tools")
from hands import *

MOUTH = (211, 84)
STATE = os.path.join(os.path.dirname(__file__), "mouth2_state.json")
FRONT0 = {"Crouca": (212, 83), "Babodor": (212, 85), "Carmen": (212, 84)}
ARCH0 = {"Sam": (213, 84), "Crab": (214, 84), "Wolf": (213, 83), "Verea": (213, 85), "Red": (214, 85), "Barra": (214, 86)}
REST = [(211, 81), (212, 82), (211, 82), (210, 80), (210, 81), (211, 80), (209, 79), (210, 79)]
PRIORITY = ["Tail", "Gecko"]          # the guns first
MELEE_ORDER = ["Crouca", "Babodor", "Carmen", "Barra", "Crab", "Red", "Verea", "Wolf", "Sam"]


def load():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"front": {n: list(c) for n, c in FRONT0.items()}, "arch": {n: list(c) for n, c in ARCH0.items()},
            "resting": []}


def save(s):
    json.dump(s, open(STATE, "w"))


def tick():
    return rm.call("get_status")["ticksGame"] - 383


def info(p):
    g = rm.call("get_pawn", id=p["id"])
    return g.get("health") or 0, (g.get("job") or "").lower()


def fire_opts(name, enemy_id):
    return rm.call("order_pawn", id=ids()[name], targetId=enemy_id).get("options", [])


def try_fire(name, foes, order):
    """First target in `order` that the menu lets this pawn fire at."""
    for f in order:
        n = short_name(f["label"])
        opts = fire_opts(name, f["id"])
        m = next((o for o in opts if o["label"].lower() == f"fire at {n}".lower() and not o["disabled"]), None)
        if m:
            rm.call("order_pawn", id=ids()[name], targetId=f["id"], index=m["index"])
            return n
    return None


def main(steps):
    s = load()
    for step in range(steps):
        ev = guard(n=3, dt=3, keep=tuple(ids().keys()), quiet=True)
        ours = {short_name(p["label"]): p for p in pawns("player")}
        foes = [h for h in pawns("hostile") if not h.get("downed")]
        if not foes:
            print(f"t{tick()} no raiders standing"); break
        fn = {short_name(f["label"]): f for f in foes}
        hp, job = {}, {}
        for n, p in ours.items():
            if not p.get("downed"):
                hp[n], job[n] = info(p)
        # raiders at the mouth / inside (within 1.5 of a front cell or in the mouth)
        def dmouth(f):
            return math.dist((f["x"], f["z"]), MOUTH)
        at_mouth = sorted([f for f in foes if dmouth(f) <= 1.5 or f["x"] >= 212], key=dmouth)
        # --- rotation: a front pawn under 45% goes to rest; the best melee archer takes its cell
        for n in list(s["front"]):
            if n not in hp:                          # downed: free the slot
                cell = s["front"].pop(n)
                cand = [a for a in MELEE_ORDER if a in s["arch"] and hp.get(a, 0) >= 60]
                if cand:
                    r = cand[0]; s["arch"].pop(r); s["front"][r] = cell; go(r, *cell)
                    print(f"   t{tick()} {n} down at the front; {r} steps in at {cell}")
                continue
            if hp[n] < 45:
                cand = [a for a in MELEE_ORDER if a in s["arch"] and hp.get(a, 0) >= 70]
                if cand:
                    cell = s["front"].pop(n); r = cand[0]
                    rest = next(c for c in REST if c not in [tuple(v) for v in s["front"].values()])
                    go(n, *rest); s["resting"].append(n)
                    s["arch"].pop(r); s["front"][r] = cell; go(r, *cell)
                    print(f"   t{tick()} rotate: {n} ({hp[n]}%) out to {rest}, {r} in at {cell}")
        # --- front: melee the raider in the mouth (only if not already on it)
        if at_mouth:
            tgt = at_mouth[0]; tn = short_name(tgt["label"])
            for n, cell in s["front"].items():
                if n in hp and math.dist(cell, (tgt["x"], tgt["z"])) <= 1.5 and f"melee attacking {tn.lower()}" not in job[n]:
                    melee(n, tn)
        # --- archers: the raider in the mouth first (point-blank), then the guns, then the nearest;
        # a bow whose shot count has not moved for 3 steps on the same target re-picks without it
        order = at_mouth + [fn[k] for k in PRIORITY if k in fn] + sorted(foes, key=dmouth)
        seen_ids, order_u = set(), []
        for f in order:
            if f["id"] not in seen_ids:
                seen_ids.add(f["id"]); order_u.append(f)
        shots = s.setdefault("shots", {}); stall = s.setdefault("stall", {})
        for n in s["arch"]:
            if n not in hp:
                continue
            rec = rm.call("get_pawn", id=ours[n]["id"], tab="records")["records"]
            sh = next((x["value"] for x in rec if x["record"] == "Shots fired"), 0)
            cur = next((short_name(f["label"]) for f in order_u if f"attacking {short_name(f['label']).lower()}" in job[n]), None)
            stall[n] = stall.get(n, 0) + 1 if (cur and sh == shots.get(n)) else 0
            shots[n] = sh
            skip = cur if stall[n] >= 3 else None
            for f in order_u:
                fname = short_name(f["label"])
                if fname == skip:
                    continue
                if fname == cur:
                    break
                opts = fire_opts(n, f["id"])
                m = next((o for o in opts if o["label"].lower() == f"fire at {fname}".lower() and not o["disabled"]), None)
                if m:
                    rm.call("order_pawn", id=ids()[n], targetId=f["id"], index=m["index"])
                    stall[n] = 0
                    break
        save(s)
        if ev or step % 4 == 3:
            them = " ".join(f"{short_name(f['label'])[:6]}{rm.call('get_pawn', id=f['id']).get('health')}%@{dmouth(f):.0f}" for f in sorted(foes, key=dmouth))
            us = " ".join(f"{n[:5]}{hp[n]}" for n in hp)
            print(f"t{tick()} {ev or ''} | us {us} | them {them}")
        if any("DOWN" in e and not e.startswith("raider") for e in ev or []):
            break
    save(s)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "setup":
        if os.path.exists(STATE):
            os.remove(STATE)
        for n, c in {**FRONT0, **ARCH0}.items():
            go(n, *c)
        save(load())
    else:
        main(int(sys.argv[1]))
