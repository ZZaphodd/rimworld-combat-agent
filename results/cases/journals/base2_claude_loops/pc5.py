from pc4 import *
def watch5(team, maxt=900, dt=30, close=38, low=70, log=lg):
    t0=tick(); n0=len(up())
    base={c["name"]: c.get("health") or 100 for c in rm.call("list_colonists")["colonists"]}
    while tick()-t0<maxt:
        wait(dt)
        hs=up()
        if len(hs)<n0: log(f"out ({len(hs)} up) traps {traps()['count']}"); n0=len(hs)
        if not hs: return "none"
        me=[q for q in pawns("player") if short_name(q["label"]) in team and not q.get("downed")]
        dm=min((min(math.dist((h["x"],h["z"]),(q["x"],q["z"])) for q in me), short_name(h["label"]), h["x"], h["z"]) for h in hs)
        cols=rm.call("list_colonists")["colonists"]
        lp=[(c["name"].split("'")[1] if "'" in c["name"] else c["name"], c.get("health"), c.get("downed")) for c in cols if c.get("downed") or ((c.get("health") or 100)<low and (c.get("health") or 100)<base.get(c["name"],100))]
        if lp: return f"low {lp}"
        if dm[0]<close: return f"close {dm[1]} {dm[0]:.0f} @{dm[2]},{dm[3]}"
    return "time"
