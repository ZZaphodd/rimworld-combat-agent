"""Ithfunda tribe 6x helpers (scratch): east-room hold with a frag thrower on the corridor axis."""
import sys, math
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))   # the sibling loop modules
import p
from p import *
p.T0 = 21129266
p.DOOR = (133, 187)
T0, DOOR = p.T0, p.DOOR
CELLS = {"Jeyce": (133, 188), "Felix": (134, 188), "Elsie": (132, 188), "Smith": (133, 189),
         "Kuma": (132, 189), "Paulo": (134, 189), "Kate": (133, 190), "Hono": (134, 190)}
ROCK = "Marble1970416"          # (133, 177), the rock at the end of the straight corridor
BARRAGE = {"on": False, "at": 0}
GROUND = (133, 178)             # the cell at the corridor's end (the rock there broke at ~t5300)
THROWER = ["Elsie"]
FRAG = {"target": None, "at": 0}
GOING = {}
RESTING = set()
CARRY = {}   # carrier -> (downed, dest)


def move(n, cell):
    """Send n to cell (its new CELLS slot); no melee orders for n until it is there."""
    CELLS[n] = cell; GOING[n] = (cell, tick()); MEL.pop(n, None); go(n, *cell)
LOG = []


def lg(s):
    s = f"  t{tick() - T0} {s}"
    LOG.append(s); print(s)


def corridor(up):
    return [h for h in up if h["x"] == 133 and 176 <= h["z"] <= 186]


def safe(h, ours, d=4.5):
    return all(math.dist((h["x"], h["z"]), (o["x"], o["z"])) >= d for o in ours)


def tstop(th):
    """Cancel the thrower's order; stop() turns Fire at will back on, so turn it off again."""
    stop(th); fire_at_will(th, False)


def frag_target2(up, ours, me):
    """Any standing raider 4.5+ cells from every one of ours (downed too) and within 12 of the
    thrower, while the doorway or the cell below it holds a raider; most raiders within 2."""
    c = corridor(up)
    stalled = any(h["z"] >= 185 for h in c) or any((h["x"], h["z"]) == (133, 187) for h in up)
    allies = list(ours.values())
    cand = [h for h in up if safe(h, allies) and math.dist((h["x"], h["z"]), (me["x"], me["z"])) <= 12]
    if not stalled or not cand:
        return None
    return max(cand, key=lambda h: (sum(math.dist((h["x"], h["z"]), (o["x"], o["z"])) <= 2 for o in up), -h["z"]))


def frag_target(up):
    """A raider on the corridor axis at z <= 183 (5+ below the plug), only while the doorway or the
    cell below it holds a raider (the queue is stalled); the one with most raiders within 2."""
    c = corridor(up)
    stalled = any(h["z"] >= 185 for h in c) or any((h["x"], h["z"]) == (133, 187) for h in up)
    cand = [h for h in c if h["z"] <= 183]
    if not stalled or not cand:
        return None
    return max(cand, key=lambda h: (sum(math.dist((h["x"], h["z"]), (o["x"], o["z"])) <= 2 for o in up), -abs(h["z"] - 182)))


def room(maxt=1500, dt=20, low=50, log=lg):
    """Hold the east room: melee for any pawn next to a standing raider (back to its cell after),
    frags from Elsie at the stalled corridor queue. Returns on one of ours below `low`/down, a raider
    inside the room past the doorway, or time."""
    t0 = tick()
    down0 = {c["id"] for c in rm.call("list_colonists")["colonists"] if c.get("downed")}
    names0 = None
    while tick() - t0 < maxt:
        wait(dt)
        ours = {short_name(x["label"]): x for x in pawns("player")}
        up = [h for h in pawns("hostile") if not h.get("downed")]
        now = {short_name(h["label"]) for h in up}
        if names0 is not None and names0 - now:
            log(f"out: {sorted(names0 - now)} ({len(now)} up)")
        names0 = now
        for c, (d, dest) in list(CARRY.items()):
            oc = ours.get(c)
            if oc and math.dist((oc["x"], oc["z"]), dest) <= 1:
                rm.call("do_thing_action", id=ids()[c], label=f"Drop {d}"); CARRY.pop(c)
                log(f"{c} dropped {d}"); GOING[c] = (CELLS[c], tick()); go(c, *CELLS[c])
        for n, o in ours.items():
            if o.get("downed") or n in THROWER or n in CARRY:
                continue
            if n in GOING:
                cell, t1 = GOING[n]
                if (o["x"], o["z"]) == cell or tick() - t1 > 300:
                    GOING.pop(n)
                else:
                    if tick() - t1 > 90 and (tick() - t1) % 90 < dt:
                        go(n, *cell)
                    continue
            adj = [h for h in up if max(abs(h["x"] - o["x"]), abs(h["z"] - o["z"])) <= 1]
            if adj:
                hn = short_name(sorted(adj, key=lambda h: (h["x"], h["z"]) != (133, 187))[0]["label"])
                if MEL.get(n) != hn:
                    melee(n, hn); MEL[n] = hn; log(f"{n} melee {hn}")
            elif n in MEL:
                MEL.pop(n); stop(n)
                if n in CELLS and (o["x"], o["z"]) != CELLS[n]:
                    go(n, *CELLS[n])
        # frags: a standing order on the rock at the corridor's end (the user's way), re-given if lost
        for th in THROWER:
            e = ours.get(th)
            if not e or e.get("downed") or (e["x"], e["z"]) != CELLS.get(th):
                continue
            if any(max(abs(h["x"] - e["x"]), abs(h["z"] - e["z"])) <= 1 for h in up):
                continue
            if not BARRAGE["on"]:
                continue
            job = next((c.get("job") or "" for c in rm.call("list_colonists")["colonists"] if th in c["name"]), "")
            if "attacking" not in job.lower() and tick() - BARRAGE["at"] >= 120:
                r = rm.call("do_thing_action", id=ids()[th], label="Command_VerbTarget", targetX=GROUND[0], targetZ=GROUND[1])
                BARRAGE["at"] = tick(); log(f"{th} barrage at the ground: {r.get('executed')} (job was {job[:30]})")
        if BARRAGE["on"] and tick() - BARRAGE.get("ff_at", 0) >= 80:
            BARRAGE["ff_at"] = tick()
            for th in THROWER:
                try:
                    L = rm.call("get_pawn", id=ids()[th], tab="log").get("entries") or []
                except Exception:
                    L = []
                ours_n = [n for n in CELLS if n != th] + ["Connor", "Janik", "Ursula", "Honorio", "Paul-Olivier", "Kate"]
                bad = [e for e in L[:6] if e.get("type") == "combat" and e["tick"] > BARRAGE.get("seen", 0) and th in e["text"] and any(n in e["text"].split(th, 1)[1] for n in ours_n)]
                if L:
                    BARRAGE["seen"] = max(BARRAGE.get("seen", 0), L[0]["tick"])
                if bad:
                    BARRAGE["on"] = False
                    return f"friendly frag: {[e['text'][:90] for e in bad]}"
        cols = rm.call("list_colonists")["colonists"]
        lowp = [c for c in cols if c["id"] not in down0 and not any(r in c["name"] for r in RESTING) and (c.get("downed") or (c.get("health") or 100) < low)]
        inside = [h for h in up if 188 <= h["z"] <= 196 and 129 <= h["x"] <= 137]
        if lowp or inside:
            return f"low {[(c['name'].split()[0], c.get('health'), c.get('downed')) for c in lowp]} inside {[(short_name(h['label']), h['x'], h['z']) for h in inside]}"
    return "time"


def hide(maxt=1500, dt=40, zmin=197, names=("Elsie", "Hono")):
    """Wait in the back rooms: return when a standing raider is at z >= zmin, one of `names`
    loses health or goes down, a raider picks up one of ours, or time."""
    t0 = tick()
    hp0 = {c["name"].split()[0]: c.get("health") for c in rm.call("list_colonists")["colonists"]}
    n0 = len([h for h in pawns("hostile") if not h.get("downed")])
    while tick() - t0 < maxt:
        wait(dt)
        up = [h for h in pawns("hostile") if not h.get("downed")]
        cols = rm.call("list_colonists")["colonists"]
        hp = {c["name"].split()[0]: c for c in cols}
        near = [(short_name(h["label"]), h["x"], h["z"]) for h in up if h["z"] >= zmin]
        hurt = [n for n in ("Elsie", "Honorio") if n in hp and ((hp[n].get("health") or 0) < (hp0.get(n) or 100) - 1 or hp[n].get("downed"))]
        carried = [c["name"] for c in cols if "carried" in (c.get("job") or "")]
        gone = [n for n in hp0 if n not in hp]
        if near or hurt or carried or gone or len(up) != n0:
            return f"near {near} hurt {hurt} carried {carried} gone {gone} up {len(up)}"
    return "time"
