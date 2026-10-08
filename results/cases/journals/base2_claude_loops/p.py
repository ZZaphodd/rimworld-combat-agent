"""Compact battle view for Claude's direct play (scratch)."""
import sys, math
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4] / "tools"))   # repo tools/
from hands import *
from rca.eval.tracker import short_name
T0 = None
DOOR = (145, 84)
WEAP = {}

def tick():
    return rm.call("get_status")["ticksGame"]

def s(n=10, near=DOOR):
    t = tick()
    cols = {c["id"]: c for c in rm.call("list_colonists")["colonists"]}
    ours = pawns("player")
    print(f"t{t - (T0 or t)} ({t})")
    for p in ours:
        c = cols.get(p["id"], {})
        print(f"  {short_name(p['label'])[:8]:<8} @{p['x']},{p['z']} {c.get('health')}%{' DOWN' if p.get('downed') else ''} | {(c.get('job') or '')[:30]}")
    hs = pawns("hostile")
    up = [h for h in hs if not h.get("downed")]
    dn = [h for h in hs if h.get("downed")]
    print(f"  THEM {len(up)} up, {len(dn)} down")
    for h in sorted(up, key=lambda h: math.dist((h["x"], h["z"]), near))[:n]:
        nm = short_name(h["label"])
        if nm not in WEAP:
            WEAP[nm] = (rm.call("get_pawn", id=h["id"]).get("weapon") or "-").split(" (")[0][:16]
        print(f"   {nm[:10]:<10} @{h['x']},{h['z']} d{math.dist((h['x'], h['z']), near):.0f} {WEAP[nm]} | {(h.get('targeting') or h.get('job') or '')[:34]}")

def msgs(since=0):
    for m in rm.call("get_alerts").get("recentMessages") or []:
        if (m.get("tick") or 0) >= since and "Auto-attack" not in m.get("text", ""):
            print("  msg", m.get("tick"), m.get("text", "")[:90])

def until(maxt=2000, dt=60, r=6, hp=None):
    """Step dt ticks until a standing raider is within r of the doorway, or one of ours loses health
    or goes down. Returns the reason."""
    t0 = tick()
    base = {c["id"]: c.get("health", 100) for c in rm.call("list_colonists")["colonists"]}
    while tick() - t0 < maxt:
        wait(dt)
        up = [h for h in pawns("hostile") if not h.get("downed")]
        close = [h for h in up if math.dist((h["x"], h["z"]), DOOR) <= r]
        hurt = [c["name"] for c in rm.call("list_colonists")["colonists"] if c.get("downed") or (c.get("health", 100) < base.get(c["id"], 100) - (hp or 0.5))]
        if close or hurt:
            return f"close {[(short_name(h['label']), h['x'], h['z']) for h in close]} hurt {hurt}"
    return "time"

CELLS = {}
DANGER = ("Woddles", "Hazcaznove")
MEL = {}

def fight(maxt=1500, dt=30, low=55, crowd=3, danger_r=10, log=print):
    """Hold the room: a standing raider next to one of ours gets that pawn's melee; when it is gone
    the pawn's order ends (stop). Returns on a decision point."""
    t0 = tick()
    down0 = {c["id"] for c in rm.call("list_colonists")["colonists"] if c.get("downed")}
    while tick() - t0 < maxt:
        wait(dt)
        ours = {short_name(x["label"]): x for x in pawns("player")}
        cols = {c["name"].split(" ")[0] if c.get("name") else "": c for c in rm.call("list_colonists")["colonists"]}
        up = [h for h in pawns("hostile") if not h.get("downed")]
        for n, o in ours.items():
            if o.get("downed"):
                continue
            adj = [h for h in up if max(abs(h["x"] - o["x"]), abs(h["z"] - o["z"])) <= 1]
            if adj:
                hn = short_name(adj[0]["label"])
                if MEL.get(n) != hn:
                    melee(n, hn); MEL[n] = hn; log(f"  t{tick() - (T0 or 0)} {n} melee {hn}")
            elif n in MEL:
                MEL.pop(n); stop(n); log(f"  t{tick() - (T0 or 0)} {n} back")
        hp = {short_name(x["label"]): x for x in ours.values()}
        lowp = [c for c in rm.call("list_colonists")["colonists"] if c["id"] not in down0 and (c.get("downed") or (c.get("health") or 100) < low)]
        near = [h for h in up if math.dist((h["x"], h["z"]), DOOR) <= 4]
        dang = [h for h in up if short_name(h["label"]) in DANGER and math.dist((h["x"], h["z"]), DOOR) <= danger_r]
        if lowp or len(near) >= crowd or dang:
            return f"low {[(c['name'], c.get('health'), c.get('downed')) for c in lowp]} near {[short_name(h['label']) for h in near]} danger {[(short_name(h['label']), h['x'], h['z']) for h in dang]}"
    return "time"

def jobs():
    return {short_name(x["label"]): x for x in pawns("player")}, {c["id"]: c.get("job") or "" for c in rm.call("list_colonists")["colonists"]}

def carry_out(pairs, maxt=900):
    """pairs: [(carrier, downed, approach_cell, dest_cell)]. Approach, Carry, walk, Drop on arrival."""
    i = ids()
    state = {c: "approach" for c, *_ in pairs}
    for c, d, a, dest in pairs:
        go(c, *a)
    t0 = tick()
    while tick() - t0 < maxt and any(s != "done" for s in state.values()):
        wait(30)
        pos, job = jobs()
        for c, d, a, dest in pairs:
            s = state[c]
            pc = (pos[c]["x"], pos[c]["z"])
            if s == "approach" and math.dist(pc, a) <= 1:
                opts = rm.call("order_pawn", id=i[c], targetId=i[d]).get("options", [])
                o = next((o for o in opts if o["label"].startswith("Carry ") and not o.get("disabled")), None)
                if o:
                    rm.call("order_pawn", id=i[c], targetId=i[d], index=o["index"]); state[c] = "pickup"
            elif s == "pickup" and "being carried" in job.get(i[d], ""):
                go(c, *dest); state[c] = "walk"
            elif s == "walk" and math.dist(pc, dest) <= 1:
                rm.call("do_thing_action", id=i[c], label=f"Drop {d}"); state[c] = "done"
        print(f"  t{tick() - (T0 or 0)} {state}")
    return state

def watch(maxt=1500, dt=30, center=(120, 128), r=15, hp=2):
    """Advance until one of ours loses > hp % or goes down, a standing raider comes within r of
    center, or a grenade is in the air. Logs raider losses."""
    t0 = tick()
    base = {c["id"]: c.get("health") for c in rm.call("list_colonists")["colonists"]}
    names0 = {short_name(h["label"]) for h in pawns("hostile") if not h.get("downed")}
    while tick() - t0 < maxt:
        wait(dt)
        hs = [h for h in pawns("hostile") if not h.get("downed")]
        now = {short_name(h["label"]) for h in hs}
        if names0 - now:
            print(f"  t{tick() - (T0 or 0)} raiders out: {sorted(names0 - now)} ({len(now)} up)"); names0 = now
        oth = [h for h in hs if math.dist((h["x"], h["z"]), center) <= r]
        hurt = [c["name"] for c in rm.call("list_colonists")["colonists"] if (c.get("health") or 0) < base.get(c["id"], 100) - hp or c.get("downed")]
        pr = projectiles()
        if oth or hurt or pr:
            return f"close {[(short_name(h['label']), h['x'], h['z']) for h in oth]} hurt {hurt} proj {pr}"
    return "time"

def focus(target, names):
    can = [n for n in names if fireable(n, target)]
    return {n: fire(n, target) for n in can}

def hold(maxt=3000, dt=30, low=60, names=(), danger=(), dr=3, log=print):
    """Room hold with no melee pawns: everyone fires at will; a danger raider within dr of the door
    gets focused fire from everyone who can see it; returns when one of ours falls below low or
    goes down, or a fire starts in the room box (129-137, 188-196)."""
    t0 = tick()
    base = {c["id"] for c in rm.call("list_colonists")["colonists"] if c.get("downed")}
    focused = None
    while tick() - t0 < maxt:
        wait(dt)
        up = [h for h in pawns("hostile") if not h.get("downed")]
        hs = {short_name(h["label"]): h for h in up}
        if focused and focused not in hs:
            log(f"  t{tick() - (T0 or 0)} {focused} down/gone"); focused = None
            for n in names:
                try: stop(n)
                except Exception: pass
        d = [h for n, h in hs.items() if n in danger and math.dist((h["x"], h["z"]), DOOR) <= dr]
        if d and not focused:
            focused = short_name(d[0]["label"]); log(f"  t{tick() - (T0 or 0)} focus {focused} {focus(focused, names)}")
        lowp = [(c["name"], c.get("health")) for c in rm.call("list_colonists")["colonists"] if c["id"] not in base and (c.get("downed") or (c.get("health") or 100) < low)]
        fires = [(x["x"], x["z"]) for x in rm.call("list_things", category="all", defName="Fire", verbose=True, confirm=True).get("things", []) if 128 <= x["x"] <= 138 and 187 <= x["z"] <= 197]
        if lowp or fires:
            return f"low {lowp} fires {fires}"
    return "time"
