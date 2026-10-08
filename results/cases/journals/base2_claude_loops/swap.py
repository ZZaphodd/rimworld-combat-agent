"""Weapon swaps before a battle: drop both, equip the other's, wait until both hold the new ones
(up to 1200 ticks: pawns far apart walk), and only then let the caller draft."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4] / "tools"))   # repo tools/
from hands import *
from rca.game.weapons import weapon_def

def swap(pairs, maxt=1200):
    i = ids(); drops = {}; before = {}
    for a, b in pairs:
        for n in (a, b):
            lab = rm.call("get_pawn", id=i[n], tab="gear")["equipment"][0]["label"]
            before[n] = lab
            drops[n] = rm.call("manage_gear", id=i[n], op="drop", item=weapon_def(lab)).get("itemId")
    for a, b in pairs:
        rm.call("manage_gear", id=i[a], op="equip", item=drops[b])
        rm.call("manage_gear", id=i[b], op="equip", item=drops[a])
    want = {a: before[b] for a, b in pairs}; want.update({b: before[a] for a, b in pairs})
    t0 = rm.call("get_status")["ticksGame"]
    while rm.call("get_status")["ticksGame"] - t0 < maxt:
        wait(30)
        w = {n: (rm.call("get_pawn", id=i[n]).get("weapon") or "") for n in want}
        if all(w[n] and w[n].split(" (")[0] == want[n].split(" (")[0] and w[n] != "" for n in want):
            break
    w = {n: (rm.call("get_pawn", id=i[n]).get("weapon") or "") for n in want}
    print("swap:", w)
    return w
