import sys, math
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[4] / 'tools'))
from hands import *
import hands
K = Keeper()
WEIGHT = {'Daiki': 3.0, 'Athequart': 3.0, 'Evans': 1.5}


def tick():
    return rm.call("get_status")["ticksGame"] - 383


def snapshot():
    ours = {short_name(p["label"]): p for p in pawns("player")}
    foes_all = {short_name(p["label"]): p for p in pawns("hostile")}
    jobs = {n: (rm.call("get_pawn", id=p["id"]).get("job") or "") for n, p in ours.items()}
    return ours, foes_all, jobs


def assign_once(weight=None, hold=()):
    ours, foes_all, jobs = snapshot()
    stand = {n: p for n, p in foes_all.items() if not p.get("downed")}
    shooters = [n for n, p in ours.items() if not p.get("downed") and n not in hold]
    now = tick()
    out = K.assign(shooters, stand, {n: p for n, p in ours.items() if not p.get("downed")}, now, jobs,
                   weight=weight or WEIGHT)
    return out


def run(steps=10, dt=3, hold=(), weight=None, near=None, quiet=False, verbose=True, n=10):
    """steps x (assign + guard(10 x dt ticks))."""
    for k in range(steps):
        out = assign_once(weight, hold)
        if verbose:
            print(f"t{tick()} targets:", {k_: v for k_, v in out.items() if v})
        ev = guard(n=n, dt=dt, keeper=K, near=near, quiet=quiet)
        if ev:
            return ev
    return []


def line():
    ours, foes, _ = snapshot()
    for n, p in ours.items():
        pass
    return ours, foes


def advance(dest, max_steps=30, n=5, weight=None, fire_others=True, tol=1.6):
    """Move pawns to dest {name: (x,z)}; movers are held (no fire orders) until they arrive; the rest keep
    firing via the assign loop. Returns when all arrived or an event fires."""
    for nme, (x, z) in dest.items():
        K.hold(nme)
        go(nme, x, z)
    pending = dict(dest)
    for s in range(max_steps):
        if fire_others:
            assign_once(weight, hold=tuple(pending))
        ev = guard(n=n, dt=3, keeper=K, quiet=True)
        ours = {short_name(p["label"]): p for p in pawns("player")}
        for nme in list(pending):
            p = ours.get(nme)
            if p is None or p.get("downed") or math.dist((p["x"], p["z"]), pending[nme]) <= tol:
                K.release(nme)
                pending.pop(nme)
        if not pending:
            print(f"   arrived t{tick()}")
            return ev
        if ev:
            return ev
    print("   still moving:", pending)
    return []
