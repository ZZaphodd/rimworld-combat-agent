from pc5 import *
RIFLES=["Fitz","Blake","Wayne","Howe","Mad"]
STEP=8
def focus_loop(order, maxt=1500, dt=30, keep=28, log=lg):
    """order: list of hostile ids to kill in turn. Each rifle fires at the first one in its range;
    a pawn within `keep` of any mech steps back (away from the nearest one)."""
    t0=tick(); n0=len(up()); N0=len(rm.call("list_colonists")["colonists"])
    while tick()-t0<maxt:
        hs={h["id"]:h for h in up()}
        if len(hs)<n0: log(f"out ({len(hs)} up) traps {traps()['count']}"); n0=len(hs)
        if not hs: return "none"
        me={short_name(q["label"]):q for q in pawns("player") if short_name(q["label"]) in RIFLES}
        for n,q in me.items():
            near=min(hs.values(), key=lambda h: math.dist((q["x"],q["z"]),(h["x"],h["z"])))
            d=math.dist((q["x"],q["z"]),(near["x"],near["z"]))
            if d<keep:
                vx,vz=q["x"]-near["x"],q["z"]-near["z"]; L=math.hypot(vx,vz) or 1
                go(n,int(q["x"]+vx/L*STEP),int(q["z"]+vz/L*STEP)); continue
            if n not in RIFLES: continue
            tgt=next((hs[i] for i in order if i in hs and math.dist((q["x"],q["z"]),(hs[i]["x"],hs[i]["z"]))<=36), None)
            j=rm.call("get_pawn", id=ids()[n]).get("job") or ""
            if tgt and ("attacking" not in j or q.get("_t")!=tgt["id"]):
                if fire_id(n,tgt["id"]): pass
        cols=rm.call("list_colonists")["colonists"]
        lowp=[(c["name"],c.get("health")) for c in cols if c.get("downed") or (c.get("health") or 100)<50]
        if lowp or len(cols)<N0: return f"low {lowp} n {len(cols)}"
        wait(dt)
    return "time"
