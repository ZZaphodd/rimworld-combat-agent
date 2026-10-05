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


PROJ_DEFS = ("Proj_GrenadeFrag", "Proj_GrenadeMolotov", "Proj_GrenadeEMP")


def projectiles():
    """Grenades on the map (in flight or lying on their fuse): [(id, def, x, z)]."""
    out = []
    for d in PROJ_DEFS:
        for t in rm.call("list_things", category="all", defName=d, verbose=True, confirm=True).get("things", []):
            out.append((t["id"], d.replace("Proj_Grenade", ""), t["x"], t["z"]))
    return out


def aims():
    """Who each standing raider is aiming at (list_things 'targeting', mod setting on) and how far."""
    ours = {short_name(p["label"]): p for p in pawns("player")}
    for h in pawns("hostile"):
        if h.get("downed"):
            continue
        tg = h.get("targeting")
        name = tg if isinstance(tg, str) else (tg or {}).get("label") or (tg or {}).get("name") if tg else None
        tgt = next((o for n, o in ours.items() if name and n in str(name)), None)
        d = math.dist((h["x"], h["z"]), (tgt["x"], tgt["z"])) if tgt else None
        print(f"  {short_name(h['label'])[:9]:9} @{h['x']},{h['z']} -> {name or '-'}"
              f"{f' ({d:.0f})' if d else ''}")


def frags(dt=3):
    """Grenades now and dt ticks later: direction, landed or not, and our pawns within 4 cells of
    where each one is or is heading (the target if in flight). Advances the game by dt."""
    a = {i: (k, x, z) for i, k, x, z in projectiles()}
    if not a:
        return []
    wait(dt)
    b = {i: (k, x, z) for i, k, x, z in projectiles()}
    ours = pawns("player")
    out = []
    for i, (k, x2, z2) in b.items():
        x1, z1 = a.get(i, (k, x2, z2))[1:]
        vx, vz = x2 - x1, z2 - z1
        landed = (vx, vz) == (0, 0) and i in a
        if i not in a or (vx, vz) == (0, 0) and not landed:     # just thrown: no direction yet
            near = sorted((round(math.dist((x2, z2), (p["x"], p["z"])), 1), short_name(p["label"]))
                          for p in ours if math.dist((x2, z2), (p["x"], p["z"])) <= 4)
            out.append({"id": i, "kind": k, "at": (x2, z2), "vel": None, "landed": False,
                        "target": None, "near": near})
            print(f"  {k} @{x2},{z2} new (no direction yet) within4={near}")
            continue
        # in flight: the pawn nearest to the ray ahead is the likely target
        best = None
        for p in ours:
            if p.get("downed"):
                continue
            px, pz = p["x"] - x2, p["z"] - z2
            if landed:
                d = math.hypot(px, pz)
            else:
                n = math.hypot(vx, vz) or 1
                ahead = (px * vx + pz * vz) / n
                if ahead < -1:
                    continue
                d = abs(px * vz - pz * vx) / n
            if best is None or d < best[0]:
                best = (d, short_name(p["label"]))
        near = sorted((round(math.dist((x2, z2), (p["x"], p["z"])), 1), short_name(p["label"]))
                      for p in ours if math.dist((x2, z2), (p["x"], p["z"])) <= 4)
        out.append({"id": i, "kind": k, "at": (x2, z2), "vel": (vx, vz), "landed": landed,
                    "target": best[1] if best else None, "near": near})
        print(f"  {k} @{x2},{z2} {'LANDED' if landed else f'moving {vx:+},{vz:+}'} "
              f"target~{best[1] if best else '-'} within4={near}")
    return out


def away(name, fx, fz, dist=5, toward=None):
    """Step `name` ~dist cells away from (fx, fz); with toward=(x, z), prefer the side that keeps
    it facing that point (perpendicular sidestep rather than straight back)."""
    p = next(p for p in pawns("player") if short_name(p["label"]) == name)
    dx, dz = p["x"] - fx, p["z"] - fz
    if (dx, dz) == (0, 0):
        dx, dz = 1, 0
    n = math.hypot(dx, dz)
    cands = []
    for ang in (0, 60, -60, 90, -90):
        r = math.radians(ang)
        ux = (dx * math.cos(r) - dz * math.sin(r)) / n
        uz = (dx * math.sin(r) + dz * math.cos(r)) / n
        c = (round(fx + ux * (n + dist)), round(fz + uz * (n + dist)))
        if math.dist(c, (fx, fz)) < 4:
            continue
        score = math.dist(c, toward) if toward else 0
        cands.append((score, c))
    c = min(cands)[1]
    go(name, *c)
    return c



THROWN = ("frag", "molotov", "emp grenade")


def _aimed(h):
    """The colonist a raider's `targeting` names ("targeting colonist X" / "attacking colonist X")."""
    t = h.get("targeting") or ""
    return t.split("colonist ", 1)[1].strip() if "colonist " in t else None


def _dodge_cell(me, fx, fz, ours, foes, dist=5):
    """A cell ~dist from (fx, fz): keeps about the same distance to the raid (a sidestep, so the
    pawn can keep shooting), stays 2+ cells from other squadmates, never closer to the raid."""
    ex = sum(f["x"] for f in foes) / len(foes) if foes else me["x"]
    ez = sum(f["z"] for f in foes) / len(foes) if foes else me["z"]
    d0 = math.dist((me["x"], me["z"]), (ex, ez))
    best = None
    for ang in range(0, 360, 30):
        r = math.radians(ang)
        c = (round(fx + math.cos(r) * dist), round(fz + math.sin(r) * dist))
        if math.dist(c, (fx, fz)) < 4 or not (1 <= c[0] <= 248 and 1 <= c[1] <= 248):
            continue
        de = math.dist(c, (ex, ez))
        crowd = sum(1 for o in ours if o is not me and math.dist(c, (o["x"], o["z"])) < 2)
        score = abs(de - d0) + (8 if de < d0 - 1 else 0) + 5 * crowd + 0.2 * math.dist(c, (me["x"], me["z"]))
        if best is None or score < best[0]:
            best = (score, c)
    return best[1]


def guard(n=60, dt=3, hp_every=10, hp_drop=12, near=None, keep=(), resume=None, quiet=False):
    """Fine-grained steps (dt ticks) with a grenade reflex, the player's way: when a grenade
    appears, its target is the colonist the nearest grenadier was aiming at (`targeting`), else
    the pawn nearest its line of flight; only that pawn sidesteps ~5 cells (same distance to the
    raid, clear of squadmates); once the grenade is gone the pawn's errand is re-issued from
    `resume` {name: callable}. Pawns in `keep` never dodge. Returns early on an event: one of
    ours down or -hp_drop % (checked every hp_every steps), a raider down or gone, or
    near=(name, d) a raider within d of that pawn. Cheap per step: 4 calls. NB: a wait(dt)
    advances by the mod's wait speed (~15 ticks per step at the current setting, RIMMOLT_API),
    so dt below that is not honoured."""
    resume = resume or {}
    weap = {h["id"]: (rm.call("get_pawn", id=h["id"]).get("weapon") or "").lower() for h in pawns("hostile")}
    throwers = {i for i, w in weap.items() if any(k in w for k in THROWN)}
    def hp():
        return {n_: rm.call("get_pawn", id=i).get("health") for n_, i in ids().items()}
    h0 = hp()
    ours0 = {short_name(p["label"]): bool(p.get("downed")) for p in pawns("player")}
    foes0 = {short_name(p["label"]): bool(p.get("downed")) for p in pawns("hostile")}
    seen, dodging, last_aim = {}, {}, {}
    for k in range(n):
        wait(dt)
        ours, foes = pawns("player"), pawns("hostile")
        byname = {short_name(p["label"]): p for p in ours}
        for f in foes:
            if f["id"] in throwers and _aimed(f):
                last_aim[f["id"]] = (_aimed(f), f["x"], f["z"])
        projs = {i: (kind, x, z) for i, kind, x, z in projectiles()}
        for i, (kind, x, z) in projs.items():
            if i in seen:
                continue
            seen[i] = (x, z)
            # who threw it: the thrower nearest to where it first appeared
            src = min(((math.dist((x, z), (a[1], a[2])), a[0]) for a in last_aim.values()), default=(99, None))
            who = src[1] if src[0] <= 6 else None
            if who is None:                                  # fall back: nearest standing pawn
                cand = [p for p in ours if not p.get("downed")]
                who = min(cand, key=lambda p: math.dist((x, z), (p["x"], p["z"]))) if cand else None
                who = short_name(who["label"]) if who else None
            me = byname.get(who)
            if not me or who in keep or me.get("downed"):
                continue
            c = _dodge_cell(me, me["x"], me["z"], ours, [f for f in foes if not f.get("downed")])
            go(who, *c)
            dodging[i] = who
            if not quiet:
                print(f"   t{rm.call('get_status')['ticksGame'] - 383} {kind} thrown at {who} -> sidestep {c}")
        for i in [i for i in dodging if i not in projs]:     # exploded or gone: back to the errand
            who = dodging.pop(i)
            if who in resume:
                resume[who]()
                if not quiet:
                    print(f"   {who} back to its errand")
        ev = [f"{n_} DOWN" for n_, p in byname.items() if p.get("downed") and not ours0.get(n_)]
        ev += [f"{n_} gone" for n_ in ours0 if n_ not in byname]
        fn = {short_name(p["label"]): bool(p.get("downed")) for p in foes}
        ev += [f"raider {n_} down" for n_, d in fn.items() if d and not foes0.get(n_)]
        ev += [f"raider {n_} dead/gone" for n_ in foes0 if n_ not in fn]
        if near and near[0] in byname:
            me = byname[near[0]]
            ev += [f"{short_name(f['label'])} within {near[1]} of {near[0]}" for f in foes
                   if not f.get("downed") and math.dist((f["x"], f["z"]), (me["x"], me["z"])) <= near[1]]
        if k % hp_every == hp_every - 1:
            h1 = hp()
            ev += [f"{n_} {h0[n_]}->{h1[n_]}" for n_ in h1 if h0.get(n_) and h1.get(n_) is not None
                   and h0[n_] - h1[n_] >= hp_drop]
        if ev:
            print(f"   t{rm.call('get_status')['ticksGame'] - 383}: " + "; ".join(ev))
            return ev
    print(f"   t{rm.call('get_status')['ticksGame'] - 383}: quiet")
    return []
