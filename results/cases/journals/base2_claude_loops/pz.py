from pk import *
R=["Sid","Xia","Vicky","Waltz","Yury"]
SAFE={"Centipede":29.5,"Centurion":34,"Lancer":34,"Pikeman":0,"Apocriton":46,"Scyther":12,"Militor":16,"Scorcher":10,"Diabolus":21,"Tesseron":27,"Cyclops":24,"Legionary":27}
def kind(h):
    for k in SAFE:
        if k in h["label"]: return k
    return "Centipede"
def zone(maxt=3000, dt=30, prefer=("Lancer",), log=lg, zmin=14):
    t0=tick(); n0=len(up()); last={}
    while tick()-t0<maxt:
        hs=up()
        if len(hs)<n0: log(f"out ({len(hs)} up) traps {traps()['count']}"); n0=len(hs)
        if not hs: return "none"
        me={short_name(q["label"]):q for q in pawns("player") if short_name(q["label"]) in R and not q.get("downed")}
        if not me: return "team down"
        for n,q in me.items():
            threats=[(math.dist((q["x"],q["z"]),(h["x"],h["z"]))-SAFE[kind(h)], h) for h in hs]
            worst=min(threats, key=lambda t: t[0])
            if worst[0]<0:
                h=worst[1]; vx,vz=q["x"]-h["x"],q["z"]-h["z"]; L=math.hypot(vx,vz) or 1
                nx,nz=int(q["x"]+vx/L*7), max(zmin,int(q["z"]+vz/L*7))
                go(n,nx,nz); last.pop(n,None); continue
            inr=[h for h in hs if math.dist((q["x"],q["z"]),(h["x"],h["z"]))<=36.5]
            if not inr: continue
            tgt=min(inr, key=lambda h: (0 if kind(h) in prefer else 1, rm.call("get_pawn", id=h["id"]).get("health") or 100))
            j=rm.call("get_pawn", id=ids()[n]).get("job") or ""
            if last.get(n)!=tgt["id"] or "attacking" not in j:
                if fire_id(n,tgt["id"]): last[n]=tgt["id"]
        cols={cc["name"].split()[0]:cc for cc in rm.call("list_colonists")["colonists"]}
        if any((cols[k].get("health") or 100)<50 for k in ("Chad","Faina","Sandra","Aaron") if k in cols and not cols[k].get("downed")): return "low"
        if (tick()-t0)%600<dt: log(str([(kind(h)[:5],h["x"],h["z"],rm.call("get_pawn", id=h["id"]).get("health")) for h in hs if math.dist((h["x"],h["z"]),(125,40))<60]))
        wait(dt)
    return "time"
