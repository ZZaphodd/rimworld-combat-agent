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
    e = {short_name(p["label"]): p["id"] for p in pawns("hostile")}.get(enemy)
    if not e:
        return False
    opts = rm.call("order_pawn", id=ids()[name], targetId=e).get("options", [])
    # the menu lists every pawn on the target's cell (downed ones too): pick the named one
    m = next((o for o in opts if o["label"].lower().startswith("melee attack") and not o["disabled"]
              and enemy.lower() in o["label"].lower() and "to death" not in o["label"].lower()), None) \
        or next((o for o in opts if o["label"].lower().startswith("melee attack") and not o["disabled"]
                 and enemy.lower() in o["label"].lower()), None)
    return bool(m) and bool(rm.call("order_pawn", id=ids()[name], targetId=e, index=m["index"]).get("executed"))


def fire(name, enemy):
    """Fire at <enemy> from the float menu. The verb gizmo can report "executed" and leave the pawn
    watching for targets (seen with bows shooting through a 1-cell gap past downed pawns)."""
    e = {short_name(p["label"]): p["id"] for p in pawns("hostile")}.get(enemy)
    if not e:
        return False
    opts = rm.call("order_pawn", id=ids()[name], targetId=e).get("options", [])
    m = next((o for o in opts if o["label"].lower() == f"fire at {enemy}".lower() and not o["disabled"]), None)
    return bool(m) and bool(rm.call("order_pawn", id=ids()[name], targetId=e, index=m["index"]).get("executed"))


# ---- attack orders, the player's way (the user, 2026-10-06; results/audit_attack_orders.md) ----
# A player orders an attack only to change target; the pawn then keeps firing or swinging on its
# own. Our controllers switched targets every 8-24 ticks (A -> B -> A), and every switch restarts the
# aim or the swing. Repeating an order on the same target cost nothing in a test (autopistols).
_CYCLE, _DEF = {}, {}
SHOOT_VERBS = ("Verb_Shoot", "Verb_ShootOneUse")         # the verbs that move "Shots fired"


def _weapon_def(name):
    from rca.game.weapons import weapon_def
    return weapon_def(rm.call("get_pawn", id=ids()[name]).get("weapon") or "")


def _wdef(name):
    """<name>'s weapon def, looked up once per pawn (forget_weapon(name) after a loadout change)."""
    if name not in _DEF:
        _DEF[name] = _weapon_def(name)
    return _DEF[name]


def forget_weapon(name=None):
    (_DEF.clear() if name is None else _DEF.pop(name, None))


def _verb(name):
    from rca.game.weapons import RANGES
    d = _wdef(name)
    w = (json.loads(RANGES.read_text())["weapons"].get(d) or {}) if RANGES.exists() and d else {}
    return w.get("verb")


def weapon_cycle(name):
    """Ticks from one shot of <name>'s weapon to the next: aiming time + ranged cooldown from the
    weapon def's info card (`get_info_card def=`). Melee weapons and unknowns: 120. The def is
    looked up once per pawn (Keeper.forget_weapon after a loadout change)."""
    d = _wdef(name)
    if d not in _CYCLE:
        ticks = 120
        if d:
            card = rm.call("get_info_card", **{"def": d})
            st_ = {x["label"]: x["value"] for c in card.get("stats") or [] for x in c.get("stats") or []}
            sec = lambda k: float(str(st_.get(k, "0")).split()[0])
            if "Ranged cooldown" in st_:
                ticks = max(30, round((sec("Ranged cooldown") + sec("Aiming time")) * 60))
        _CYCLE[d] = ticks
    return _CYCLE[d]


def counts_shots(name):
    """Whether <name>'s weapon moves the "Shots fired" record (Verb_Shoot); thrown weapons, beams
    and flame sprayers do not (data/weapon_ranges.json `verb`)."""
    return (_verb(name) or "Verb_Shoot") in SHOOT_VERBS


def shots_fired(name):
    rec = rm.call("get_pawn", id=ids()[name], tab="records").get("records") or []
    return next((x["value"] for x in rec if x["record"] == "Shots fired"), 0)


def fire_at_will(name, on):
    """Set <name>'s Fire at will toggle (a gizmo: read its state, press it only to change it).
    False when the pawn shows no such gizmo (undrafted, unarmed)."""
    acts = rm.call("inspect_thing", id=ids()[name]).get("actions") or []
    cur = next((a.get("active") for a in acts if a.get("label") == "Fire at will"), None)
    if cur is not None and cur != on:
        rm.call("do_thing_action", id=ids()[name], label="Fire at will")
    return cur is not None


def stop(name):
    """End <name>'s order where it stands: undraft and draft again. The float menu offers no
    Go here on the pawn's own cell, and drafting turns Fire at will back on (both measured
    2026-10-06), so a pawn that had it off gets it switched off again (base2_ith_tribe_6x: a frag
    thrower held off fire was turned back on by stop() and threw at raiders next to our own)."""
    i = ids()[name]
    acts = rm.call("inspect_thing", id=i).get("actions") or []
    was = next((a.get("active") for a in acts if a.get("label") == "Fire at will"), None)
    rm.call("draft", action="undraft", ids=i)
    rm.call("draft", action="draft", ids=i)
    if was is False:
        fire_at_will(name, False)


def fireable(name, enemy):
    """Whether <name>'s float menu offers an enabled "Fire at <enemy>" (in range, in sight). Lists
    the menu only; gives no order."""
    e = {short_name(p["label"]): p["id"] for p in pawns("hostile")}.get(enemy)
    if not e:
        return False
    opts = rm.call("order_pawn", id=ids()[name], targetId=e).get("options", [])
    return any(o["label"].lower() == f"fire at {enemy}".lower() and not o["disabled"] for o in opts)


_WSTATS, _PSTATS = {}, {}
BANDS = (3, 12, 25, 40)                                  # the info card's close/short/medium/long distances


def weapon_stats(name):
    """<name>'s ranged weapon from its def's info card: damage, range, accuracy by band, aim and
    cooldown seconds, burst count. None for melee weapons."""
    d = _wdef(name)
    if d not in _WSTATS:
        w = None
        if d:
            card = rm.call("get_info_card", **{"def": d})
            st_ = {x["label"]: x["value"] for c in card.get("stats") or [] for x in c.get("stats") or []}
            num = lambda k, dflt=0.0: float(str(st_.get(k, dflt)).split()[0].rstrip("%"))
            if "Ranged cooldown" in st_:
                w = {"damage": num("Damage", 10), "range": num("Range"), "cooldown": num("Ranged cooldown"),
                     "aim": num("Aiming time"), "burst": num("Burst shot count", 1) or 1,
                     "acc": [num(f"Accuracy ({b})", 100) / 100 for b in ("close", "short", "medium", "long")]}
        _WSTATS[d] = w
    return _WSTATS[d]


def pawn_aim(name):
    """<name>'s shooting accuracy per cell and aiming-time factor, from the pawn's info card (read
    once per pawn)."""
    if name not in _PSTATS:
        card = rm.call("get_info_card", id=ids()[name])
        st_ = {x["label"]: x["value"] for c in card.get("stats") or [] for x in c.get("stats") or []}
        pct = lambda k, dflt: float(str(st_.get(k, dflt)).split()[0].rstrip("%")) / 100
        _PSTATS[name] = (pct("Shooting accuracy", "90%"), pct("Aiming time", "100%"))
    return _PSTATS[name]


def expected_dpt(name, dist):
    """Rough damage per tick of <name>'s weapon at `dist` cells: weapon accuracy for that distance
    (linear between the card's bands) x the pawn's accuracy per cell ^ distance x damage x burst
    / (aim + cooldown). Cover, armour and the target's size are left out (the user: an eyeball
    estimate is good enough; RimWorld's dice swing more)."""
    w = weapon_stats(name)
    if not w or dist > w["range"]:
        return 0.0
    acc = w["acc"]
    if dist <= BANDS[0]:
        a = acc[0]
    else:
        a = acc[-1]
        for (d0, a0), (d1, a1) in zip(zip(BANDS, acc), zip(BANDS[1:], acc[1:])):
            if dist <= d1:
                a = a0 + (a1 - a0) * (dist - d0) / (d1 - d0)
                break
    per_cell, aimf = pawn_aim(name)
    cycle = (w["aim"] * aimf + w["cooldown"]) * 60
    return a * per_cell ** dist * w["damage"] * w["burst"] / max(cycle, 1)


FF_SAFE, FF_STERILE, FF_FULL = 5.0, 5 ** 0.5, 12.0   # rimworldwiki safety radii (the user's screenshot)
SPLASH = 3.8                              # frag: forced-miss radius 1.9 + blast 1.9 (GAME_FACTS §5b)


def _intercept(d):
    """The game's intercept factor for a pawn d cells from the shooter: 0 up to FF_SAFE, rising
    in squared distance to 1 at FF_FULL (VerbUtility.InterceptChanceFactorFromDistance)."""
    return min(1.0, max(0.0, (d * d - FF_SAFE ** 2) / (FF_FULL ** 2 - FF_SAFE ** 2)))


def ff_risk(shooter, target, ours, explosive=False):
    """0..1: how much a shot at `target` risks one of `ours`. Bullets: allies within 2 cells of
    the target or within 1 cell of the shooter-to-target line, weighted by the intercept factor
    of their distance from the shooter (none inside FF_SAFE). Explosives: any ally within SPLASH
    of the target, no shooter-distance exemption."""
    sx, sz, tx, tz = shooter["x"], shooter["z"], target["x"], target["z"]
    seg = math.dist((sx, sz), (tx, tz)) or 1
    risk = 0.0
    for q in ours:
        if q is shooter:
            continue
        qx, qz = q["x"], q["z"]
        dt = math.dist((qx, qz), (tx, tz))
        if explosive:
            if dt <= SPLASH:
                return 1.0
            continue
        u = ((qx - sx) * (tx - sx) + (qz - sz) * (tz - sz)) / (seg * seg)
        near_line = 0 < u < 1 and abs((tx - sx) * (qz - sz) - (tz - sz) * (qx - sx)) / seg <= 1.0
        if dt <= 2.0 or near_line:
            risk = max(risk, _intercept(math.dist((qx, qz), (sx, sz))))
    return risk


def ff_unsafe(shooter, target, ours):
    """One of ours within 1.5 cells of the target and more than FF_SAFE from the shooter."""
    sp = (shooter["x"], shooter["z"])
    return any(math.dist((q["x"], q["z"]), (target["x"], target["z"])) <= 1.5 and math.dist((q["x"], q["z"]), sp) > FF_SAFE
               for q in ours if q is not shooter)


_TERRAIN = []


def cover(shooter, target):
    """Rough cover factor on a shot: the cell next to the target on the shooter's side holds a wall
    or rock (x0.25) or a tree (x0.75) (rca.terrain; wiki cover values ~75% / ~25%)."""
    from rca.terrain import Terrain
    if not _TERRAIN:
        _TERRAIN.append(Terrain(rm))
    T = _TERRAIN[0]
    dx, dz = shooter["x"] - target["x"], shooter["z"] - target["z"]
    L = max(abs(dx), abs(dz)) or 1
    c = T.cell(target["x"] + round(dx / L), target["z"] + round(dz / L))
    return 0.25 if c in "#%" else 0.75 if c == "*" else 1.0


BUSY = ("wandering", "extinguish", "flee", "downed", "carrying", "rescu", "tending", "crawl")


class Keeper:
    """One attack target per pawn, ordered once and kept, the player's way.

    pick(name, ranked, now, standing, job) is called every step with the pawn's current job text:
    - the pawn is busy (held by the caller, or its job is wandering, fleeing, putting out a fire,
      carrying, ...): nothing is ordered;
    - its job names the kept target ("attacking X" / "melee attacking X"): kept; for a shooter
      whose weapon moves "Shots fired", a stall is when that record has not changed for STALL
      weapon cycles while the job names the target: the target is marked bad for BAD cycles and
      the next one is ordered;
    - the job does not name it (the order ended: fire at will, idle) and it still stands: the same
      target is ordered again, which costs nothing;
    - it fell (not in `standing`, which must exclude downed raiders): the first target of `ranked`
      that takes the order, skipping targets marked bad.
    better(name, priority, now) switches to a raider of the caller's fixed priority list ranked
    above the current target, if its "Fire at" is enabled; it looks once per weapon cycle and skips
    targets marked bad. hold(name, until) / release(name) mark a pawn busy for the caller (a move,
    a dodge, a carry): nothing is ordered while it is held. `quiet` holds the shooters assign()
    told to hold fire; their Fire at will goes back on with their next fire order."""
    STALL, BAD = 3, 4

    def __init__(self):
        self.s, self.held, self.bad, self.dodges, self.quiet = {}, {}, {}, {}, {}

    def target(self, name):
        return (self.s.get(name) or {}).get("target")

    def drop(self, name):
        self.s.pop(name, None)

    def hold(self, name, until=None):
        self.held[name] = until if until is not None else 10 ** 9

    def release(self, name):
        self.held.pop(name, None)
        self.drop(name)

    def is_held(self, name, now):
        u = self.held.get(name)
        if u is None:
            return False
        if now >= u:
            self.release(name)
            return False
        return True

    def order(self, name, target, kind, now, switch=False):
        cur = self.s.get(name)
        if cur and cur["target"] == target and cur["kind"] == kind and not switch:
            return False
        ok = fire(name, target) if kind == "fire" else melee(name, target)
        if ok and kind == "fire" and self.quiet.pop(name, None) is not None:
            fire_at_will(name, True)
        if ok:
            sh = shots_fired(name) if kind == "fire" and counts_shots(name) else None
            self.s[name] = {"target": target, "kind": kind, "at": now, "shots": sh, "changed": now,
                            "checked": now}
        return ok

    def _stalled(self, name, now):
        cur = self.s[name]
        if cur["shots"] is None or now - cur["at"] < weapon_cycle(name):
            return False
        sh = shots_fired(name)
        if sh != cur["shots"]:
            cur["shots"], cur["changed"] = sh, now
            return False
        return now - cur["changed"] >= self.STALL * weapon_cycle(name)

    def _bad(self, name, t, now):
        u = self.bad.get(name, {}).get(t)
        return u is not None and now < u

    def pick(self, name, ranked, now, standing, job, kind="fire"):
        """Keep, re-order, or switch (see the class doc). Returns the target or None."""
        job = (job or "").lower()
        if self.is_held(name, now) or any(b in job for b in BUSY):
            return self.target(name)
        cur = self.s.get(name)
        if cur and cur["kind"] == kind and cur["target"] in standing:
            t = cur["target"]
            verb = "melee attacking" if kind == "melee" else "attacking"
            if f"{verb} {t.lower()}" in job:
                if kind != "fire" or not self._stalled(name, now):
                    return t
                self.bad.setdefault(name, {})[t] = now + self.BAD * weapon_cycle(name)
            elif not self._bad(name, t, now):
                return t if self.order(name, t, kind, now, switch=True) else None
        for t in ranked:
            if t in standing and not self._bad(name, t, now) and (not cur or t != cur["target"]):
                if self.order(name, t, kind, now, switch=True):
                    return t
        return self.target(name) if self.target(name) in standing else None

    SPREAD, SWITCH, REORDER_MAX = 1.0, 1.25, 2

    def assign(self, shooters, foes, ours, now, jobs, weight=None, ff=()):
        """Ranged fire for a squad, the user's micro rules (2026-10-06).

        Value of raider t for shooter n: expected_dpt at that distance x cover x the caller's
        threat weight (hard or soft focus on top threats; default 1; a (shooter, raider) key
        overrides the raider's own, for one shooter's priority) x (1 - friendly-fire risk,
        unless t is in `ff`, the raiders the tactical layer accepts the risk on) / (1 + SPREAD x
        the active shooters of ours already on t): fire spreads evenly unless focused. A shooter
        re-decides at most once per weapon cycle and switches when the best raider is worth
        SWITCH x its current one (SWITCH < 1 + SPREAD, so a pair splits to an equal free raider).
        A fallen, out-of-range, stalled or unreachable target is replaced at once. With nothing
        worth shooting the shooter holds fire: Fire at will off and its order ended (stop()), else
        the game's own targeting would pick a raider, the risky one too. Reported as None.

        shooters: names; foes: {name: pawn dict}, standing only; ours: {name: pawn dict};
        jobs: {name: job text}. Returns {shooter: target or None}."""
        weight, ff = weight or {}, set(ff or ())
        active = [n for n in shooters if n in ours and not self.is_held(n, now)
                  and not any(b in (jobs.get(n) or "").lower() for b in BUSY)]
        for n in list(self.s):
            if n in shooters and n not in ours:
                self.drop(n)                                # downed or gone
        on = {}
        for n in active:
            cur = self.s.get(n)
            if cur and cur["kind"] == "fire" and cur["target"] in foes:
                on[cur["target"]] = on.get(cur["target"], 0) + 1
        allies = list(ours.values())
        out = {n: None for n in shooters}
        for n in active:
            job = (jobs.get(n) or "").lower()
            me = ours[n]
            explosive = (_verb(n) or "Verb_Shoot") not in SHOOT_VERBS
            cur = self.s.get(n) if (self.s.get(n) or {}).get("kind") == "fire" else None
            t0 = cur["target"] if cur else None

            def value(t, mine):
                f = foes[t]
                if self._bad(n, t, now):
                    return 0.0
                dist = math.dist((me["x"], me["z"]), (f["x"], f["z"]))
                v = expected_dpt(n, dist)
                if v <= 0:
                    return 0.0
                risk = 0.0 if t in ff else ff_risk(me, f, allies, explosive)
                others = on.get(t, 0) - (1 if mine else 0)
                w = weight.get((n, t), weight.get(t, 1.0))
                return v * cover(me, f) * w * (1 - risk) / (1 + self.SPREAD * others)
            cur_v = value(t0, True) if t0 in foes else 0.0
            if cur and t0 in foes and f"attacking {t0.lower()}" in job:
                cur["reorders"] = 0
                if self._stalled(n, now):
                    self.bad.setdefault(n, {})[t0] = now + self.BAD * weapon_cycle(n)
                    cur_v = 0.0
            due = not cur or now - cur.get("assigned", -10 ** 9) >= weapon_cycle(n) or cur_v == 0.0
            if not due:
                if f"attacking {t0.lower()}" not in job:            # the order ended: same target again
                    self._reorder(n, t0, now)
                out[n] = t0 if self.target(n) == t0 and not self._bad(n, t0, now) else None
                continue
            ranked = sorted(((value(t, t == t0), t) for t in foes), reverse=True)
            chosen = t0 if cur_v > 0 else None
            for v, t in ranked:
                if v <= 0 or (cur_v > 0 and v <= self.SWITCH * cur_v):
                    break
                if t == t0:
                    continue
                if self.order(n, t, "fire", now, switch=True):
                    if t0 in on:
                        on[t0] -= 1
                    on[t] = on.get(t, 0) + 1
                    chosen = t
                    break
                self.bad.setdefault(n, {})[t] = now + weapon_cycle(n)   # no "Fire at": out of sight
            if chosen is None:                                        # nothing worth it: hold fire
                if n not in self.quiet:
                    if t0 is not None or "attacking" in job:           # our order or the game's own pick
                        stop(n)
                    fire_at_will(n, False)                             # after stop(): drafting turns it on
                    self.quiet[n] = now
                if t0 in on:
                    on[t0] -= 1
                self.drop(n)
                continue
            if chosen == t0 and f"attacking {t0.lower()}" not in job:
                self._reorder(n, t0, now)
            if self.s.get(n):
                self.s[n]["assigned"] = now
            out[n] = self.target(n) if self.target(n) == chosen else None
        return out

    def _reorder(self, name, t, now):
        """The same target again (the order ended), keeping the cycle and stall bookkeeping. After
        REORDER_MAX re-orders that the job never took up, or a failed one, the target is set aside
        for a weapon cycle."""
        cur = self.s[name]
        cur["reorders"] = cur.get("reorders", 0) + 1
        if cur["reorders"] > self.REORDER_MAX or not fire(name, t):
            self.bad.setdefault(name, {})[t] = now + weapon_cycle(name)
            cur["reorders"] = 0

    def better(self, name, priority, now):
        cur = self.s.get(name)
        if not cur or cur["kind"] != "fire" or now - cur["checked"] < weapon_cycle(name):
            return None
        cur["checked"] = now
        for t in priority:
            if t == cur["target"]:
                return None
            if not self._bad(name, t, now) and fireable(name, t) and self.order(name, t, "fire", now, switch=True):
                return t
        return None


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


def _seg_dist(p, a, b):
    """Distance from point p to the segment a-b."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dz * dz
    u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / L2))
    return math.dist(p, (a[0] + u * dx, a[1] + u * dz))


def _dodge_cell(me, fx, fz, ours, foes, dist=5, avoid=()):
    """A cell ~dist from (fx, fz): keeps about the same distance to the raid (a sidestep, so the
    pawn can keep shooting), stays 2+ cells from other squadmates, never closer to the raid, and
    clear of the grenades lying in `avoid`: the cell beyond LYING_R + 1 of each, and the straight
    walk there beyond LYING_R (2026-10-06 drill: a pawn sent from one frag walked past another
    lying one and was caught in its blast)."""
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
        score += 20 * sum(1 for a in avoid if math.dist(c, a) <= LYING_R + 1)
        start = (me["x"], me["z"])                          # a walk that comes closer than LYING_R,
        score += 20 * sum(1 for a in avoid                   # and closer than where it starts
                          if _seg_dist(a, start, c) <= LYING_R and _seg_dist(a, start, c) < math.dist(start, a) - 0.5)
        if best is None or score < best[0]:
            best = (score, c)
    return best[1]


_HANDLED = {}     # grenade id -> the pawns already sent away from it (this process; Keeper.dodges across calls)
LYING_R = 3.0     # a pawn this close to a grenade lying on its fuse steps away from it (frag blast ~1.9)
STILL = 15        # ticks on one cell before a grenade counts as lying: in flight a frag takes ~10
                  # ticks per cell (2026-10-06 drill: 10 cells in ~105 ticks), so 3-tick polls see
                  # the same cell several times while it flies
_POS = {}         # grenade id -> (cell, tick it got there)
_SEEN = {}        # grenade id -> its first cell seen (kept across guard calls)
_PENDING = set()  # grenades with no known target, waiting for a second cell to read their line


LINE_R = 3.0     # a grenade with no known target: the pawn within this of its line of flight, ahead of it
LINE_MIN = 3.0   # cells flown before its line is read: from a one-cell step the direction is too rough
                 # (rand_130 re-measure flights: a cell held 6-22 ticks, first steps straight south for
                 # a molotov that landed 2 cells east of that line)


def _on_line(ours, a, b, keep=(), most=3):
    """The standing pawns of `ours` within LINE_R of the line of flight a -> b and ahead of b,
    nearest the line first, at most `most`: read from a few cells the line is still rough
    (rand_130 re-measure: a molotov flew straight south for 3 cells and landed 2 cells east of
    that line, beside the second pawn on it), so every pawn near it steps aside."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dz)
    best = None
    for p in ours:
        nm = short_name(p["label"])
        if p.get("downed") or nm in keep:
            continue
        vx, vz = p["x"] - b[0], p["z"] - b[1]
        ahead = (vx * dx + vz * dz) / L
        off = abs(vx * dz - vz * dx) / L
        if ahead >= -1 and off <= LINE_R:
            best = (best or []) + [(off, nm)]
    return [nm for _, nm in sorted(best or [])[:most]]


def _moved(keeper, i):
    v = (keeper.dodges.get(i) if keeper is not None else None) or _HANDLED.get(i) or []
    return [v] if isinstance(v, str) else list(v)


def guard(n=60, dt=3, hp_every=10, hp_drop=12, near=None, keep=(), resume=None, quiet=False, keeper=None):
    """Fine-grained steps (dt ticks) with a grenade reflex, the player's way: when a grenade
    appears, its target is the colonist the nearest grenadier was aiming at (`targeting`), else
    the pawn nearest its line of flight at the next poll (`_on_line`; grenades are polled even
    after their thrower fell); only that pawn sidesteps ~5 cells (same distance to the
    raid, clear of squadmates); once the grenade is gone the pawn's errand is re-issued from
    `resume` {name: callable}. A grenade lying on its fuse moves every pawn within LYING_R of it
    away from it, once. A grenade is handled once: the pawns sent away from it are kept in
    _HANDLED (and in keeper.dodges across guard calls), so a later call does not send them again
    (2026-10-06: the old per-call memory re-sidestepped the same pawn every call, from its own
    cell, and Zhang walked back and forth beside a lying frag until it went off). Pawns in `keep`
    never dodge. Returns early on an event: one of
    ours down or -hp_drop % (checked every hp_every steps), a raider down or gone, or
    near=(name, d) a raider within d of that pawn. Per step: 4 calls and the 3 grenade queries
    (rand_130 re-measure: a molotov still in flight when its thrower died went unwatched under
    the old "only while a thrower stands" rule). A grenade first seen next to one of our throwers is ours (2026-10-05:
    our own frag sent Trev into the raid). NB: wait(dt) advances exactly dt ticks since the
    mod's wait setting was changed on 2026-10-05 evening (before: 15–30 ticks at least;
    RIMMOLT_API), at ~60 ticks/s of wall time. With `keeper` (a Keeper), a dodger is held (no attack
    order) until its grenade is gone, across guard calls; then it is released and the caller's next
    pick orders it again."""
    resume = resume or {}
    weap = {h["id"]: (rm.call("get_pawn", id=h["id"]).get("weapon") or "").lower() for h in pawns("hostile")}
    throwers = {i for i, w in weap.items() if any(k in w for k in THROWN)}
    def hp():
        return {n_: rm.call("get_pawn", id=i).get("health") for n_, i in ids().items()}
    h0 = hp()
    ours0 = {short_name(p["label"]): bool(p.get("downed")) for p in pawns("player")}
    foes0 = {short_name(p["label"]): bool(p.get("downed")) for p in pawns("hostile")}
    seen, dodging, last_aim, pending = _SEEN, {}, {}, _PENDING
    for k in range(n):
        wait(dt)
        ours, foes = pawns("player"), pawns("hostile")
        byname = {short_name(p["label"]): p for p in ours}
        for f in foes:
            if f["id"] in throwers and _aimed(f):
                last_aim[f["id"]] = (_aimed(f), f["x"], f["z"])
        projs = {i: (kind, x, z) for i, kind, x, z in projectiles()}   # also after the thrower fell
        tick = rm.call("get_status")["ticksGame"] if projs else 0
        lying = set()
        for i, (kind, x, z) in projs.items():
            cell, since = _POS.get(i, ((x, z), tick))
            _POS[i] = ((x, z), since if cell == (x, z) else tick)
            if tick - _POS[i][1] >= STILL:
                lying.add(i)
        for i in [i for i in _POS if i not in projs]:
            _POS.pop(i)
            _SEEN.pop(i, None)
            _PENDING.discard(i)
        avoid = [projs[i][1:] for i in lying]
        our_throwers = [p for p in ours if not p.get("downed") and any(
            k in (rm.call("get_pawn", id=p["id"]).get("weapon") or "").lower() for k in THROWN)] if projs else []
        def send(i, who, c, tag=""):
            go(who, *c)
            _HANDLED.setdefault(i, []).append(who + tag)
            if keeper is not None:
                keeper.hold(who)
                keeper.dodges[i] = list(_HANDLED[i])
            dodging.setdefault(i, []).append(who)
        live = [f for f in foes if not f.get("downed")]
        for i, (kind, x, z) in projs.items():
            done = _moved(keeper, i)
            if i in seen:
                if i in lying:                               # lying on its fuse: clear the cells around it
                    for p in ours:
                        nm = short_name(p["label"])
                        if nm in keep or p.get("downed") or nm + "@" in done or math.dist((x, z), (p["x"], p["z"])) > LYING_R:
                            continue
                        c = _dodge_cell(p, x, z, ours, live, avoid=avoid)
                        send(i, nm, c, "@")
                        if not quiet:
                            print(f"   t{rm.call('get_status')['ticksGame'] - 383} {kind} lying at {(x, z)}: {nm} -> {c}")
                elif i in pending and not done and math.dist(seen[i], (x, z)) >= LINE_MIN:   # target unknown: its line
                    for who in _on_line(ours, seen[i], (x, z), keep):
                        me = byname[who]
                        c = _dodge_cell(me, me["x"], me["z"], ours, live, avoid=avoid)
                        send(i, who, c)
                        if not quiet:
                            print(f"   t{rm.call('get_status')['ticksGame'] - 383} {kind} flying at {who} -> sidestep {c}")
                    pending.discard(i)
                if i not in pending:
                    seen[i] = (x, z)
                continue
            seen[i] = (x, z)
            if done:
                continue                                     # handled in an earlier call
            if any(math.dist((x, z), (p["x"], p["z"])) <= 2.5 for p in our_throwers):
                _HANDLED[i] = ["ours"]
                continue                                     # one of ours, just thrown
            # who threw it: the thrower nearest to where it first appeared
            src = min(((math.dist((x, z), (a[1], a[2])), a[0]) for a in last_aim.values()), default=(99, None))
            who = src[1] if src[0] <= 6 else None
            if who is None:                                  # unknown: decide on its line at the next poll
                pending.add(i)
                continue
            me = byname.get(who)
            if not me or who in keep or me.get("downed"):
                continue
            c = _dodge_cell(me, me["x"], me["z"], ours, live, avoid=avoid)   # in flight: it lands on `who`
            send(i, who, c)
            if not quiet:
                print(f"   t{rm.call('get_status')['ticksGame'] - 383} {kind} thrown at {who} -> sidestep {c}")
        if keeper is not None:                               # dodges from earlier guard calls
            for i in list(keeper.dodges):
                if i not in projs:
                    for who in {w.rstrip("@") for w in _moved(keeper, i)} - {"ours"}:
                        keeper.release(who)
                    keeper.dodges.pop(i)
        for i in [i for i in dodging if i not in projs]:     # exploded or gone: back to the errand
            for who in dodging.pop(i):
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


def wait_safe(ticks, alarm=25, chunk=60):
    """Advance up to `ticks` in chunks, returning early (with the reason) when a raider comes
    within `alarm` cells of a standing pawn of ours, or one of ours goes down. Use it instead of
    a bare wait() loop: twice on 2026-10-05 a loop without a check let the raid arrive unseen
    (rand_015 attempt 2: ~870 ticks; rand_023: ~3000 ticks)."""
    t0 = rm.call("get_status")["ticksGame"]
    down0 = {short_name(p["label"]) for p in pawns("player") if p.get("downed")}
    while rm.call("get_status")["ticksGame"] - t0 < ticks:
        wait(chunk)
        ours = pawns("player")
        down = {short_name(p["label"]) for p in ours if p.get("downed")} - down0
        if down:
            return f"down: {sorted(down)}"
        stand = [p for p in ours if not p.get("downed")]
        foes = [h for h in pawns("hostile") if not h.get("downed")]
        if stand and foes:
            d = min(math.dist((a["x"], a["z"]), (b["x"], b["z"])) for a in stand for b in foes)
            if d <= alarm:
                return f"raider within {d:.0f}"
    return None
