"""Cawalia helpers (scratch): a kiting line that keeps the raid's archers walking over trap fields."""
import sys, math
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))   # the sibling loop modules
import p
from p import *
from rca.eval.harness import trap_census

T0 = 41226471
p.T0 = T0
LOG = []


def lg(s):
    s = f"  t{tick() - T0} {s}"
    LOG.append(s); print(s)


def up():
    return [h for h in pawns("hostile") if not h.get("downed")]


def centroid(ps):
    return (sum(q["x"] for q in ps) / len(ps), sum(q["z"] for q in ps) / len(ps))


def line(cx, cz, names, dx=3, axis="x"):
    """Cells for `names` in a row through (cx, cz), dx apart (axis x: a row along x)."""
    n = len(names)
    out = {}
    for k, nm in enumerate(names):
        off = int(round((k - (n - 1) / 2) * dx))
        out[nm] = (int(cx) + off, int(cz)) if axis == "x" else (int(cx), int(cz) + off)
    return out


def place(cells):
    for nm, c in cells.items():
        go(nm, *c)


def nearest(pt):
    hs = up()
    if not hs:
        return None, 999
    h = min(hs, key=lambda h: math.dist((h["x"], h["z"]), pt))
    return h, math.dist((h["x"], h["z"]), pt)


def traps():
    return trap_census(rm)


def kite(maxt=1500, dt=30, close=26, step=6, zmin=150, low=60, axis_dir=(0, -1), log=lg):
    """Hold the line; when a standing raider comes within `close` of the line's centroid, step the
    line `step` cells along axis_dir (away from the raid) unless that passes zmin. Returns on one of
    ours below `low` or down, the line at its limit with a raider close, or time."""
    t0 = tick()
    down0 = {c["id"] for c in rm.call("list_colonists")["colonists"] if c.get("downed")}
    names0 = None
    while tick() - t0 < maxt:
        wait(dt)
        ours = [q for q in pawns("player") if not q.get("downed")]
        hs = up()
        now = {short_name(h["label"]) for h in hs}
        if names0 is not None and names0 - now:
            log(f"out: {sorted(names0 - now)} ({len(now)} up)")
        names0 = now
        if not ours or not hs:
            return "no raiders" if not hs else "squad down"
        c = centroid(ours)
        h, d = nearest(c)
        cols = rm.call("list_colonists")["colonists"]
        lowp = [x for x in cols if x["id"] not in down0 and (x.get("downed") or (x.get("health") or 100) < low)]
        if lowp:
            return f"low {[(x['name'].split()[0], x.get('health'), x.get('downed')) for x in lowp]}"
        if d < close:
            nz = c[1] + axis_dir[1] * step
            nx = c[0] + axis_dir[0] * step
            if nz < zmin:
                return f"limit: {short_name(h['label'])} at {d:.0f}"
            names = [short_name(q["label"]) for q in sorted(ours, key=lambda q: q["x"])]
            place(line(nx, nz, names))
            log(f"step back to z {nz:.0f} ({short_name(h['label'])} at {d:.0f})")
    return "time"
