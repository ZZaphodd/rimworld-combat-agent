"""Hands for direct play by Claude (not an agent): state, orders, time, a labelled frame.

  python3 -c "import sys; sys.path.insert(0, 'tools'); from hands import *; st()"

Orders go straight to the game (order_pawn, do_thing_action, manage_gear); time moves only
with wait(). Used with tools/run_human.py --player claude (the harness only watches)."""
import sys, math, json
ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[1])
sys.path.insert(0, ROOT)
from rca.rimmolt import RimMolt
from rca.eval.tracker import short_name
rm = RimMolt()


def pawns(faction):
    return [p for p in rm.call("list_things", category="pawn", faction=faction, verbose=True,
                                confirm=True)["things"] if not p.get("dead")]


def ids():
    return {short_name(p["label"]): p["id"] for p in pawns("player")}


def st(jobs=True):
    t = rm.call("get_status")["ticksGame"]
    print("tick", t - 383, "(game", t, ")")
    for side in ("player", "hostile"):
        rows = []
        for p in pawns(side):
            g = rm.call("get_pawn", id=p["id"])
            w = (g.get("weapon") or "-").split(" (")[0]
            rows.append(f"{short_name(p['label'])[:9]}@{p['x']},{p['z']} {g.get('health')}%"
                        f"{' DOWN' if p.get('downed') else ''} {w} | {(g.get('job') or '')[:28] if jobs else ''}")
        print(("OURS " if side == "player" else "THEM ") + str(len(rows)))
        for r in rows:
            print("  ", r)


def go(name, x, z):
    r = rm.call("order_pawn", id=ids()[name], x=x, z=z, command="Go here")
    if not r.get("executed", r.get("ok")):
        print("go fail", name, (x, z), r.get("error") or r)


def hit(name, thing_id):
    r = rm.call("do_thing_action", id=ids()[name], label="Command_VerbTarget", targetId=thing_id)
    return bool(r.get("executed"))


def attack(name, enemy):
    e = {short_name(p["label"]): p["id"] for p in pawns("hostile")}[enemy]
    return rm.call("do_thing_action", id=ids()[name], label="Command_VerbTarget", targetId=e).get("executed")


def draft(names=None):
    i = ids()
    rm.call("draft", action="draft", ids=",".join(i[n] for n in (names or i)))


def wait(t):
    rm.wait(t)


def thing_at(x, z, d="Wall"):
    return [t for t in rm.call("list_things", category="all", nearX=x, nearZ=z, radius=0.5,
                               verbose=True, confirm=True).get("things", []) if t.get("def") == d]


def shot(x0, z0, w=40, h=30, out="cp.jpg", caption=""):
    from rca.eval import frames
    r = rm.call("screenshot", x=x0, z=z0, w=w, h=h, include_ui=False, pixels_per_cell=18)
    ps = [{"n": short_name(p["label"]), "x": p["x"], "z": p["z"], "side": "ours" if s == "player" else "them",
           "d": bool(p.get("downed"))} for s in ("player", "hostile") for p in pawns(s)]
    o = f"{ROOT}/results/human/hands_{out}"
    frames.annotate(r["path"], (x0, x0 + w, z0, z0 + h), o, ps, caption=caption, gamma=1.3)
    print(o)


def melee(name, enemy):
    """Melee attack <enemy> from the float menu (the verb gizmo would use a gun)."""
    e = {short_name(p["label"]): p["id"] for p in pawns("hostile")}[enemy]
    opts = rm.call("order_pawn", id=ids()[name], targetId=e).get("options", [])
    m = next((o for o in opts if o["label"].lower().startswith("melee attack") and not o["disabled"]), None)
    return bool(m) and bool(rm.call("order_pawn", id=ids()[name], targetId=e, index=m["index"]).get("executed"))
