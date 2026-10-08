from pk import *
def melee_fight(maxt=900, dt=15, r=6, log=lg):
    """Stand and shoot: every dt ticks, each of ours fires at the standing raider within r of our group
    that is attacking the lowest-health colonist (else the nearest to that colonist)."""
    t0=tick(); n0=len(up()); last={}
    for n in NAMES:
        try: stop(n)
        except Exception: pass
    while tick()-t0<maxt:
        hs=up()
        if len(hs)<n0: log(f"out ({len(hs)} up) traps {traps()['count']}"); n0=len(hs)
        me={short_name(q["label"]):q for q in ours()}
        if not me: return "squad down"
        c=centroid(list(me.values()))
        near=[h for h in hs if math.dist((h["x"],h["z"]),c)<=r+4]
        if not near: return "clear"
        cols={cc["name"]:cc for cc in rm.call("list_colonists")["colonists"]}
        hp={n:(next((cc.get("health") for nm,cc in cols.items() if n in nm), 100) or 100) for n in me}
        weakest=min(me, key=lambda n: hp[n])
        att=[h for h in near if weakest in (h.get("targeting") or "")]
        tgt=att[0] if att else min(near, key=lambda h: math.dist((h["x"],h["z"]),(me[weakest]["x"],me[weakest]["z"])))
        for n in me:
            if last.get(n)!=tgt["id"]:
                if fire_id(n, tgt["id"]): last[n]=tgt["id"]
        wait(dt)
    return "time"
