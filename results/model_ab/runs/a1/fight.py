"""a1 fight loop: focus fire (grenadiers first, then nearest), grenade reflex via guard()."""
import sys, math, json
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[4] / 'tools'))
from hands import *

RANGE = {"revolver": 25.9, "autopistol": 25.9, "machine pistol": 19.9, "pump shotgun": 15.9}
GREN = ("frag", "molotov")


def wrange(w):
    w = (w or "").lower()
    for k, v in RANGE.items():
        if k in w:
            return v
    return 1.5


def snapshot():
    ours = {short_name(p["label"]): p for p in pawns("player") if not p.get("downed")}
    foes = {short_name(p["label"]): p for p in pawns("hostile") if not p.get("downed")}
    info = {}
    for n, p in list(ours.items()) + list(foes.items()):
        g = rm.call("get_pawn", id=p["id"])
        info[n] = g
    return ours, foes, info


def assign(prio=None, hold=(), verbose=True):
    """prio: explicit ordered list of raider names to focus. hold: our pawns not to order."""
    ours, foes, info = snapshot()
    if not foes:
        print("no standing foes")
        return {}
    cx = sum(p["x"] for p in ours.values()) / max(1, len(ours))
    cz = sum(p["z"] for p in ours.values()) / max(1, len(ours))
    def eff(n):
        f = foes[n]
        d = math.dist((cx, cz), (f["x"], f["z"]))
        w = (info[n].get("weapon") or "").lower()
        if any(k in w for k in GREN):
            d -= 8
        return d
    order = list(prio or []) + sorted(foes, key=eff)
    order = [o for o in order if o in foes]
    out = {}
    for n, p in ours.items():
        if n in hold:
            continue
        w = info[n].get("weapon") or ""
        r = wrange(w)
        if r < 2:
            continue
        job = (info[n].get("job") or "").lower()
        if any(b in job for b in ("flee", "wander", "extinguish")):
            continue
        for t in order:
            f = foes[t]
            d = math.dist((p["x"], p["z"]), (f["x"], f["z"]))
            if d > r - 0.3:
                continue
            if f"attacking {t.lower()}" in job:
                out[n] = t
                break
            if fire(n, t):
                out[n] = t + "*"
                break
    if verbose:
        print("  fire:", out)
    return out


def dists():
    ours = [p for p in pawns("player") if not p.get("downed")]
    foes = [p for p in pawns("hostile") if not p.get("downed")]
    if not ours or not foes:
        return 999
    return min(math.dist((a["x"], a["z"]), (b["x"], b["z"])) for a in ours for b in foes)


def brief_st():
    t = rm.call("get_status")["ticksGame"] - 383
    ours = pawns("player")
    foes = pawns("hostile")
    s = f"t{t} | "
    s += " ".join(f"{short_name(p['label'])[:5]}@{p['x']},{p['z']}:{rm.call('get_pawn', id=p['id']).get('health')}{'D' if p.get('downed') else ''}" for p in ours)
    s += "\n   THEM: " + " ".join(f"{short_name(p['label'])[:5]}@{p['x']},{p['z']}:{rm.call('get_pawn', id=p['id']).get('health')}{'D' if p.get('downed') else ''}" for p in foes)
    print(s)


def tend(doctor, patient):
    i = ids()
    opts = rm.call("order_pawn", id=i[doctor], targetId=i[patient]).get("options", [])
    m = next((o for o in opts if o["label"].startswith(f"Tend {patient}") and not o["disabled"]), None)
    if not m:
        print("no tend option", doctor, patient, [o["label"] for o in opts])
        return False
    r = rm.call("order_pawn", id=i[doctor], targetId=i[patient], index=m["index"])
    print("tend", doctor, "->", patient, r.get("executed", r.get("ok")))
    return True
