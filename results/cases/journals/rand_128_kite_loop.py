import sys, math
sys.path.insert(0, "tools")   # run from the repo root
from hands import *
SHOOT = ("Joshua", "Chef", "Squiggle", "Piggy")
def foe(name):
    return next((h for h in pawns("hostile") if short_name(h["label"]) == name and not h.get("downed")), None)
thrown = set()
for cycle in range(8):
    T = foe("Theodore")
    if not T:
        print("Theodore down/gone"); break
    for n in SHOOT:
        if n in ids(): attack(n, "Theodore")
    while True:
        ev = guard(n=3, dt=3, keep=tuple(ids().keys()), quiet=True)
        T = foe("Theodore")
        if not T: break
        us = [p for p in pawns("player") if not p.get("downed")]
        if not us: break
        for n in ("Squap", "Dennis"):
            p = next((q for q in us if short_name(q["label"]) == n), None)
            if p and (n, cycle) not in thrown and math.dist((p["x"], p["z"]), (T["x"], T["z"])) <= 11:
                print("  ", n, "throws", attack(n, "Theodore")); thrown.add((n, cycle))
        d = min(math.dist((p["x"], p["z"]), (T["x"], T["z"])) for p in us)
        if d <= 6 or any("DOWN" in e or "gone" in e for e in ev): break
    T = foe("Theodore")
    if not T: print("Theodore down/gone"); break
    us = [p for p in pawns("player") if not p.get("downed")]
    cx = sum(p["x"] for p in us) / len(us); cz = sum(p["z"] for p in us) / len(us)
    dx, dz = cx - T["x"], cz - T["z"]; n_ = math.hypot(dx, dz) or 1
    tx, tz = cx + dx / n_ * 12, cz + dz / n_ * 12
    if not (8 < tx < 242 and 8 < tz < 242):            # near an edge: slide sideways
        tx, tz = cx - dz / n_ * 12, cz + dx / n_ * 12
    for i, p in enumerate(us):
        go(short_name(p["label"]), int(tx + (i % 3) - 1), int(tz + (i // 3) - 1))
    guard(n=10, dt=3, keep=tuple(ids().keys()), quiet=True)
    print(rm.call("get_status")["ticksGame"] - 383, "cycle", cycle, "Theodore", (T["x"], T["z"]), rm.call("get_pawn", id=T["id"]).get("health"), "squad at", (round(tx), round(tz)))
st(jobs=False); aims()
