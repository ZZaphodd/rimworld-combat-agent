"""Battle-2 loop: watch the line; stop on a raider close, one of ours hurt, or time."""
from pc import *

def watchline(maxt=600, dt=30, center=(143,104), close=26, hurt=8, log=lg):
    t0 = tick()
    base = {c["id"]: c.get("health") or 100 for c in rm.call("list_colonists")["colonists"]}
    names0 = {short_name(h["label"]) for h in up()}
    tr0 = traps()["count"]
    while tick() - t0 < maxt:
        wait(dt)
        hs = up()
        now = {short_name(h["label"]) for h in hs}
        if names0 - now:
            log(f"out: {sorted(names0 - now)} ({len(now)} up), traps {traps()['count']}")
        names0 = now
        if not hs:
            return "no raiders"
        h, d = nearest(center)
        cols = rm.call("list_colonists")["colonists"]
        hp = [(c["name"].split()[0], c.get("health"), c.get("downed")) for c in cols
              if c.get("downed") or (c.get("health") or 100) < base.get(c["id"], 100) - hurt]
        if hp:
            return f"hurt {hp}"
        if d < close:
            return f"close {short_name(h['label'])} at {d:.0f} ({h['x']},{h['z']})"
    return "time"
