import sys, math
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[4] / 'tools'))
from hands import *
import hands

def sit():
    t = rm.call("get_status")["ticksGame"] - 383
    ours = pawns("player"); foes = pawns("hostile")
    print("tick", t)
    for p in ours:
        g = rm.call("get_pawn", id=p["id"])
        n = short_name(p["label"])
        near = min(((math.dist((p["x"],p["z"]),(f["x"],f["z"])), short_name(f["label"])) for f in foes if not f.get("downed")), default=(0,"-"))
        print(f"  O {n[:8]:8}@{p['x']},{p['z']} {g.get('health')}%{' DOWN' if p.get('downed') else ''} {(g.get('job') or '')[:24]:24} nearest {near[1]} {near[0]:.0f}")
    for f in foes:
        g = rm.call("get_pawn", id=f["id"])
        tg = f.get("targeting") or ""
        dmin = min((math.dist((f["x"],f["z"]),(p["x"],p["z"])) for p in ours), default=0)
        print(f"  T {short_name(f['label'])[:8]:8}@{f['x']},{f['z']} {g.get('health')}%{' DOWN' if f.get('downed') else ''} {(g.get('weapon') or '').split(' (')[0][:12]:12} d={dmin:.0f} {tg[:36]} | {(g.get('job') or '')[:20]}")

def run(n=10, dt=30, drop=8):
    """advance up to n steps of dt; stop on an HP drop >= drop%, a pawn down, or an enemy count/down change."""
    def snap():
        o = {short_name(p["label"]): (rm.call("get_pawn", id=p["id"]).get("health"), bool(p.get("downed"))) for p in pawns("player")}
        f = {short_name(p["label"]): (rm.call("get_pawn", id=p["id"]).get("health"), bool(p.get("downed"))) for p in pawns("hostile")}
        return o, f
    o0, f0 = snap()
    for k in range(n):
        wait(dt)
        o, f = snap()
        ev = []
        for nme, (h, d) in o.items():
            if d and not o0[nme][1]: ev.append(f"{nme} DOWN")
            elif o0[nme][0] is not None and h is not None and o0[nme][0] - h >= drop: ev.append(f"{nme} {o0[nme][0]}->{h}")
        for nme in f0:
            if nme not in f: ev.append(f"enemy {nme} gone")
            elif f[nme][1] and not f0[nme][1]: ev.append(f"enemy {nme} DOWN")
        if ev:
            print("EVENT:", "; ".join(ev)); return ev
    print("quiet"); return []
