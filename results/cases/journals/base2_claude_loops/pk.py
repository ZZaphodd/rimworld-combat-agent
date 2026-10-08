"""Zigzag kite across the south arc (rows z 51-57): the group stands on one side; when a standing raider
comes within `trig` of the group's centroid, it crosses to the other side `dx` cells further along."""
from pc6 import *
NAMES=["Glass","Yumi","Lissa","Orthonet","Abang","Misaki","Cordova","Money"]
NORTH_Z, SOUTH_Z = 66, 42

def group_cells(cx, cz, names):
    cells=line(cx, cz, names[:5], dx=3)
    cells.update(line(cx, cz+(3 if cz>54 else -3), names[5:], dx=3))
    return cells

def ours():
    return [q for q in pawns("player") if short_name(q["label"]) in NAMES and not q.get("downed")
            and not rm.call("get_pawn", id=q["id"]).get("mentalState")]

def kite_arc(x0, side, maxt=4000, dt=20, trig=30, dx=20, xmin=80, xmax=185, log=lg, dirn=1):
    """A crossing is re-ordered only after the group has arrived (centroid within 4 of its cells' centre)
    or 400 ticks have passed."""
    t0=tick(); n0=len(up()); x=x0; goal=None; sent=0
    down0={c["id"] for c in rm.call("list_colonists")["colonists"] if c.get("downed")}
    while tick()-t0<maxt:
        wait(dt)
        hs=up()
        if len(hs)<n0: log(f"out ({len(hs)} up) traps {traps()['count']}"); n0=len(hs)
        if not hs: return "none"
        me=ours()
        if not me: return "squad down"
        c=centroid(me); h,d=nearest(c)
        cols=rm.call("list_colonists")["colonists"]
        mine={q["id"] for q in pawns("player") if short_name(q["label"]) in NAMES}
        lowp=[(cc["name"].split()[0],cc.get("health"),cc.get("downed")) for cc in cols if cc["id"] in mine and cc["id"] not in down0 and (cc.get("downed") or (cc.get("health") or 100)<55)]
        if lowp: return f"low {lowp} at x {x} side {side}"
        if goal and math.dist(c, goal)>4 and tick()-sent<400:
            continue
        goal=None
        if d<trig:
            nx=x+dirn*dx
            if nx>xmax or nx<xmin: dirn=-dirn; nx=x+dirn*dx
            side="S" if side=="N" else "N"
            cells=group_cells(nx, NORTH_Z if side=="N" else SOUTH_Z, [short_name(q["label"]) for q in me])
            place(cells); x=nx; goal=centroid([{"x":a,"z":b} for a,b in cells.values()]); sent=tick()
            log(f"cross to {side} x {nx} ({short_name(h['label'])} at {d:.0f}, {len(hs)} up)")
    return f"time x {x} side {side}"
