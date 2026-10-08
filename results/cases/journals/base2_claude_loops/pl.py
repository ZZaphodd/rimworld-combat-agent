"""Leash: lead slow mechs along waypoints; the group stands and fires while the nearest is > lo, and moves
to the next waypoint when it comes within lo."""
from pk import *
LEASH=["Fitz","Blake","Wayne","Howe","Mad"]
def gcells(c):
    return line(c[0], c[1], LEASH, dx=3)
def leash(ids_, wps, lo=29, maxt=6000, dt=30, log=lg):
    t0=tick(); k=0; goal=None; sent=0
    place(gcells(wps[0])); goal=wps[0]; sent=tick()
    while tick()-t0<maxt:
        wait(dt)
        hs={h["id"]:h for h in up() if h["id"] in ids_}
        if not hs: return "gone"
        me=[q for q in pawns("player") if short_name(q["label"]) in LEASH and not q.get("downed")]
        c=centroid(me)
        h=min(hs.values(), key=lambda h: math.dist((h["x"],h["z"]),c)); d=math.dist((h["x"],h["z"]),c)
        cols=rm.call("list_colonists")["colonists"]
        if any(cc.get("downed") or (cc.get("health") or 100)<50 for cc in cols): return "low"
        arrived=math.dist(c, goal)<=3 or tick()-sent>500
        if d<lo and arrived and k+1<len(wps):
            k+=1; goal=wps[k]; place(gcells(goal)); sent=tick(); log(f"to wp {k} {goal} (mech at {d:.0f}, hp {[rm.call('get_pawn', id=i).get('health') for i in hs]})")
        elif d>=lo and arrived:
            for n in LEASH:
                j=rm.call("get_pawn", id=ids()[n]).get("job") or ""
                if "attacking" not in j and d<=36: fire_id(n, h["id"])
        if k+1==len(wps) and arrived and d<lo-3: return f"end of leash, mech at {d:.0f}"
    return f"time wp {k}"
