from pc3 import *
MELEE=("club","knife","ikwa","spear")
WCACHE={}
def wpn(h):
    if h["id"] not in WCACHE:
        WCACHE[h["id"]]=(rm.call("get_pawn", id=h["id"]).get("weapon") or "-").lower()
    return WCACHE[h["id"]]
def is_melee(h):
    return any(k in wpn(h) for k in MELEE)
def watch4(team, maxt=900, dt=30, mclose=16, low=60, log=lg):
    t0=tick(); n0=len(up())
    base={c["name"]: c.get("health") or 100 for c in rm.call("list_colonists")["colonists"]}
    while tick()-t0<maxt:
        wait(dt)
        hs=up()
        if len(hs)<n0: log(f"out ({len(hs)} up) traps {traps()['count']}"); n0=len(hs)
        if not hs: return "none"
        me=[q for q in pawns("player") if short_name(q["label"]) in team and not q.get("downed")]
        mel=[h for h in hs if is_melee(h)]
        dm=min((min(math.dist((h["x"],h["z"]),(q["x"],q["z"])) for q in me), short_name(h["label"])) for h in mel) if mel else (999,"")
        cols=rm.call("list_colonists")["colonists"]
        lp=[(c["name"].split("'")[1] if "'" in c["name"] else c["name"], c.get("health"), c.get("downed")) for c in cols if c.get("downed") or ((c.get("health") or 100)<low and (c.get("health") or 100)<base.get(c["name"],100))]
        if lp: return f"low {lp}"
        if dm[0]<mclose: return f"melee close {dm[1]} {dm[0]:.0f}"
    return "time"
