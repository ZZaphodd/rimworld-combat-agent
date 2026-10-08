from pc2 import *

def hold3(team, maxt=900, dt=30, close=18, log=lg):
    t0 = tick()
    base = {c["name"].split()[0]: c.get("health") or 100 for c in rm.call("list_colonists")["colonists"]}
    n0 = len(up())
    while tick() - t0 < maxt:
        wait(dt)
        ours = [q for q in pawns("player") if short_name(q["label"]) in team and not q.get("downed")]
        if not ours:
            return "team down"
        c = centroid(ours); h, d = nearest(c)
        hs = up()
        if len(hs) < n0:
            log(f"mech out ({len(hs)} up) traps {traps()['count']}"); n0 = len(hs)
        if not hs:
            return "no mechs"
        hurt = [(x["name"].split()[0], x.get("health"), x.get("downed")) for x in rm.call("list_colonists")["colonists"]
                if (x.get("health") or 100) < base.get(x["name"].split()[0], 100) - 6 or x.get("downed")]
        if hurt:
            return f"hurt {hurt} near {short_name(h['label'])} {d:.0f}"
        if d < close:
            return f"close {short_name(h['label'])} {d:.0f} @{h['x']},{h['z']}"
    return "time"

def fire_id(name, eid):
    """Fire at the hostile with id eid (labels repeat among mechs)."""
    opts = rm.call("order_pawn", id=ids()[name], targetId=eid).get("options", [])
    m = next((o for o in opts if o["label"].lower().startswith("fire at") and not o["disabled"]), None)
    return bool(m) and bool(rm.call("order_pawn", id=ids()[name], targetId=eid, index=m["index"]).get("executed"))
