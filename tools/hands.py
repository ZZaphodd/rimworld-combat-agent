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


def shot(x0, z0, w=40, h=30, out="cp.jpg", caption="", keep=None, ppc=18):
    """A labelled frame. keep="rand_011_t2600.jpg" writes it to results/cases/img/ (versioned,
    for a journal) instead of the scratch results/human/hands_<out>."""
    from rca.eval import frames
    r = rm.call("screenshot", x=x0, z=z0, w=w, h=h, include_ui=False, pixels_per_cell=ppc)
    ps = [{"n": short_name(p["label"]), "x": p["x"], "z": p["z"], "side": "ours" if s == "player" else "them",
           "d": bool(p.get("downed"))} for s in ("player", "hostile") for p in pawns(s)]
    o = f"{ROOT}/results/cases/img/{keep}" if keep else f"{ROOT}/results/human/hands_{out}"
    frames.annotate(r["path"], (x0, x0 + w, z0, z0 + h), o, ps, caption=caption, gamma=1.3)
    print(o)


def melee(name, enemy):
    """Melee attack <enemy> from the float menu (the verb gizmo would use a gun)."""
    e = {short_name(p["label"]): p["id"] for p in pawns("hostile")}[enemy]
    opts = rm.call("order_pawn", id=ids()[name], targetId=e).get("options", [])
    m = next((o for o in opts if o["label"].lower().startswith("melee attack") and not o["disabled"]), None)
    return bool(m) and bool(rm.call("order_pawn", id=ids()[name], targetId=e, index=m["index"]).get("executed"))


KEEP_TRAITS = ("Brawler", "Tough", "Nimble", "Jogger", "Slowpoke", "Trigger-happy", "Careful shooter",
               "Wimp", "Iron-willed", "Bloodlust", "Fast walker", "Kind", "Psychopath")
PLAIN_ACTIONS = {"Show information", "Draft", "Undraft", "Command_VerbTarget", "Auto attack (AI)",
                 "Fire at will", "Pop smoke", "Melee attack", "Strip"}      # anything else on a pawn is a gene/psy ability
ARMOUR = ("flak", "recon", "marine", "cataphract", "plate", "shield", "helmet", "armor", "armour")


def brief(side="player"):
    """One line per pawn for the battle card: shooting/melee, combat traits, weapon, armour,
    carried items, abilities (gizmos other than the plain ones: Fire spew, psycasts, ...),
    position (get_pawn tab=all: bio.skills, bio.traits, gear; inspect_thing: actions)."""
    abilities = {}
    if side == "player":
        # ability gizmos show only on drafted pawns: draft the undrafted ones for a moment (call
        # this before the loadout: drafting cancels a pick-up job); raiders' abilities stay unseen
        ours = pawns("player")
        was = {p["id"]: rm.call("inspect_thing", id=p["id"]).get("drafted") for p in ours}
        off = [pid for pid, d in was.items() if not d]
        if off:
            rm.call("draft", action="draft", ids=",".join(off))
        for p in ours:
            abilities[p["id"]] = [a["label"] for a in rm.call("inspect_thing", id=p["id"]).get("actions") or []
                                  if a.get("label") not in PLAIN_ACTIONS
                                  and not a.get("label", "").startswith("Drop ")]
        if off:
            rm.call("draft", action="undraft", ids=",".join(off))
    for p in pawns(side):
        g = rm.call("get_pawn", id=p["id"], tab="all")
        bio, gear = g.get("bio") or {}, g.get("gear") or {}
        sk = {s["skill"]: ("-" if s.get("disabled") else s["level"]) for s in bio.get("skills") or []}
        tr = [t["label"] for t in bio.get("traits") or [] if t["label"] in KEEP_TRAITS]
        arm = [a["label"].split(" (")[0] for a in gear.get("apparel") or []
               if any(k in a["label"].lower() for k in ARMOUR)]
        inv = [i["label"].split(" (")[0] for i in gear.get("inventory") or []
               if "smoke" in i["label"].lower() or "pack" in i["label"].lower()]
        w = ", ".join(e["label"] for e in gear.get("equipment") or []) or "-"
        ab = abilities.get(p["id"], [])
        kind = " ".join(v for v, plain in ((p.get("def"), "Human"), (p.get("kind"), "Colonist"))
                        if v and v != plain)            # race if not human, kind if not ours
        print(f"{short_name(p['label'])[:12]:12} {kind:22} "
              f"sh {sk.get('Shooting', '?'):>2} me {sk.get('Melee', '?'):>2}  {w}"
              f"{'  [' + ', '.join(tr) + ']' if tr else ''}{'  armour: ' + ', '.join(arm) if arm else ''}"
              f"{'  carries: ' + ', '.join(inv) if inv else ''}"
              f"{'  ABILITIES: ' + ', '.join(ab) if ab else ''}  @{p['x']},{p['z']}")
