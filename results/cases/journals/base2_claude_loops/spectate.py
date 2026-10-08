"""Read-only spectator for an agent's battle: an event log plus frames at key moments (scratch)."""
import sys, math, time, json
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4] / "tools"))   # repo tools/
from hands import rm, pawns, shot, projectiles
from rca.eval.tracker import short_name
OUT = sys.argv[1]
T0 = None
log = open(OUT, "a", buffering=1)
def say(s):
    log.write(s + "\n")
prev_ours, prev_them, prev_msgs, contact, last_frame = {}, None, set(), False, 0
weap = {}
end = time.time() + 3 * 3600
while time.time() < end:
    try:
        st = rm.call("get_status")
        t = st["ticksGame"]
        if T0 is None:
            T0 = t
        ours = {short_name(p["label"]): p for p in pawns("player")}
        cols = {c["id"]: c for c in rm.call("list_colonists")["colonists"]}
        them = [h for h in pawns("hostile")]
        up = [h for h in them if not h.get("downed")]
        if not ours:
            time.sleep(1); continue
        cx = sum(p["x"] for p in ours.values()) / len(ours); cz = sum(p["z"] for p in ours.values()) / len(ours)
        for n, p in ours.items():
            c = cols.get(p["id"], {})
            s = (bool(p.get("downed")), (c.get("health") or 0) // 10)
            if n in prev_ours and prev_ours[n] != s:
                say(f"t{t - T0} OURS {n} hp {c.get('health')}%{' DOWN' if p.get('downed') else ''} @{p['x']},{p['z']} job {(c.get('job') or '')[:30]}")
            prev_ours[n] = s
        gone = [n for n in prev_ours if n not in ours]
        for n in gone:
            say(f"t{t - T0} OURS {n} GONE (dead or carried off)"); prev_ours.pop(n)
        names = {short_name(h["label"]) for h in up}
        if prev_them is not None and prev_them - names:
            say(f"t{t - T0} RAID out: {sorted(prev_them - names)} -> {len(names)} standing")
        prev_them = names
        near = sorted(up, key=lambda h: math.dist((h["x"], h["z"]), (cx, cz)))
        if near and math.dist((near[0]["x"], near[0]["z"]), (cx, cz)) <= 30 and not contact:
            contact = True; say(f"t{t - T0} CONTACT: {short_name(near[0]['label'])} @{near[0]['x']},{near[0]['z']}")
        for m in rm.call("get_alerts").get("recentMessages") or []:
            k = (m.get("tick"), m.get("text"))
            if k not in prev_msgs and (m.get("tick") or 0) >= T0 and "Auto-attack" not in (m.get("text") or ""):
                prev_msgs.add(k); say(f"t{(m.get('tick') or 0) - T0} MSG {m.get('text', '')[:90]}")
        pr = projectiles()
        if pr:
            say(f"t{t - T0} PROJ {pr}")
        if t - last_frame >= 1500 or (contact and t - last_frame >= 600 and near and math.dist((near[0]['x'], near[0]['z']), (cx, cz)) <= 20):
            last_frame = t
            line = f"t{t - T0} LOOK ours: " + ", ".join(f"{n}@{p['x']},{p['z']} {cols.get(p['id'], {}).get('health')}%{'D' if p.get('downed') else ''}" for n, p in ours.items())
            for h in near[:6]:
                hn = short_name(h["label"])
                if hn not in weap:
                    weap[hn] = (rm.call("get_pawn", id=h["id"]).get("weapon") or "-").split(" (")[0][:14]
                line += f" | {hn}@{h['x']},{h['z']} d{math.dist((h['x'], h['z']), (cx, cz)):.0f} {weap[hn]} {(h.get('targeting') or '')[:24]}"
            say(line)
            try:
                x0, z0 = int(min(cx, near[0]["x"] if near else cx) - 8), int(min(cz, near[0]["z"] if near else cz) - 8)
                w = int(max(40, abs((near[0]['x'] if near else cx) - cx) + 18)); h_ = int(max(30, abs((near[0]['z'] if near else cz) - cz) + 18))
                import io, contextlib
                with contextlib.redirect_stdout(io.StringIO()):
                    shot(x0, z0, min(w, 70), min(h_, 60), out=f"spec_{t - T0}.jpg", caption=f"turtle_at t{t - T0}")
                say(f"   frame results/human/hands_spec_{t - T0}.jpg")
            except Exception as e:
                say(f"   frame error {e}")
    except Exception as e:
        say(f"err {e!r}")
    time.sleep(1.0)
