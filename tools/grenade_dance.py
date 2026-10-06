"""Anti-grenade dance (the user's idea, 2026-10-06): three hostile frag grenadiers held on an
island ringed by deep water, one colonist with full Moving 10 cells off. How often does a frag
hit it, with Claude's dodge (hands.guard, the battle code) and with a human playing?

  python3 tools/grenade_dance.py setup --pawn new --save    # dev mode; on the map that is loaded
  python3 tools/grenade_dance.py load                       # the saved drill (drill_grenade_dance)
  python3 tools/grenade_dance.py claude --ticks 3000        # Claude dodges
  python3 tools/grenade_dance.py watch --ticks 3000         # a human plays; read-only

setup writes results/drills/grenade_dance_setup.json (pawn, cells, save); the other modes read the
pawn from it unless --pawn is given. --save stores the drill as the save drill_grenade_dance
(PROCEDURES save guard: only arena_/scenario_/theme_base/drill_ names are written).

setup: three single-cell islands at (x-2|x|x+2, z), --at (default 152,100), each closed in by
deep water (two cells wide outside, one between them). A Grenadier_Destructive carrying frags
stands on each. `--pawn new` spawns a fresh Colonist (same start every run: debug healing does
not undo lost parts or scars) and prints its name for the other modes; a named pawn is healed (debug), drafted with fire at will off (so nobody kills the throwers) and
put at the home cell 10 cells north. Every other colonist is moved far away. Dev mode is turned
off at the end. The grenadiers throw on their own (no lord): a frag flies ~10 cells in ~105
ticks, lies ~100 ticks on its fuse, and each grenadier throws again ~245 ticks later.

claude: each step is hands.guard(n=1, dt=3, keeper=...) and the pawn walks home once its dodges
are released and no grenade lies within 4 cells of home. watch: polls without pausing or ordering
while the human unpauses and plays (move the pawn by hand; stay within ~12 cells of the island,
or they stop throwing).

Each exploded frag is a row in results/drills/grenade_dance.jsonl (`event`), then a `run` row:
  threatened: the pawn was within HIT_R (1.9) of the frag's final cell when it was first seen
  near_at_blast: within HIT_R of the final cell at the last poll before it went off
  hit: the pawn gained a "(frag grenades)" wound between the poll where the frag disappeared
       and 3 polls later (the health summary lags the blast; the wound list does not)
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import _path  # noqa: F401
from rca import ROOT
from rca.eval.results import git_commit
from rca.game import session
from rca.game.debug import Debug

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hands  # noqa: E402
from hands import Keeper, guard, go, ids, pawns, rm, short_name  # noqa: E402

KIND = "Grenadier_Destructive"
HIT_R = 1.9                     # frag blast reach (rca/micro/reflex.HIT_R)
OUT = ROOT / "results/drills/grenade_dance.jsonl"
SETUP = ROOT / "results/drills/grenade_dance_setup.json"
SAVE = "drill_grenade_dance"


def now():
    return rm.call("get_status")["ticksGame"]


def health(pid):
    h = rm.call("get_pawn", id=pid, tab="health")
    moving = next((c["percent"] for c in h.get("capacities") or [] if c["capacity"] == "moving"), None)
    frag = sum(1 for d in h.get("hediffs") or [] if "frag" in (d.get("label") or "").lower())
    return h.get("overallHealthPercent"), moving, frag, h.get("downed")


def island(cx, cz):
    """The three grenadier cells and the deep-water rects that close each one in."""
    inner = [(cx - 2, cz), (cx, cz), (cx + 2, cz)]
    rects = [((cx - 5, cz - 2), (cx + 5, cz - 1)), ((cx - 5, cz + 1), (cx + 5, cz + 2)),
             ((cx - 5, cz), (cx - 3, cz)), ((cx - 1, cz), (cx - 1, cz)), ((cx + 1, cz), (cx + 1, cz)),
             ((cx + 3, cz), (cx + 5, cz))]
    return inner, rects


def throwers(cx, cz):
    inner, _ = island(cx, cz)
    out = []
    for h in pawns("hostile"):
        if (h["x"], h["z"]) in inner and not h.get("downed"):
            w = (rm.call("get_pawn", id=h["id"]).get("weapon") or "").lower()
            if "frag" in w:
                out.append(h)
    return out


def setup(a):
    cx, cz = a.at
    home = (cx, cz + 10)
    rm.call("dev_mode", devMode=True)
    d = Debug(rm)
    _, rects = island(cx, cz)
    for p0, p1 in rects:
        d.run("Set terrain (rect)... > WaterDeep", cells=f"{p0[0]},{p0[1]};{p1[0]},{p1[1]}")
    d.close()
    for _ in range(4):                                   # three frag carriers on (x-2|x|x+2, z)
        have = {(h["x"], h["z"]) for h in throwers(cx, cz)}
        want = [c for c in ((cx - 2, cz), (cx, cz), (cx + 2, cz)) if c not in have]
        if not want:
            break
        for t in d.spawn_pawn(KIND, want):
            w = (rm.call("get_pawn", id=t["id"]).get("weapon") or "").lower()
            if "frag" not in w:
                d.destroy_at(t["x"], t["z"])
    th = throwers(cx, cz)
    if a.pawn == "new":
        before = {p["id"] for p in pawns("player")}
        d.run("Spawn Pawn... > Colonist", x=cx, z=cz + 40)
        d.close()
        a.pawn = next(short_name(p["label"]) for p in pawns("player") if p["id"] not in before)
    me = ids()[a.pawn]
    for p in pawns("player"):                           # nobody carries anybody
        for act in rm.call("inspect_thing", id=p["id"]).get("actions") or []:
            if (act.get("label") or "").startswith("Drop "):
                rm.call("do_thing_action", id=p["id"], label=act["label"])
    others = [p for p in pawns("player") if short_name(p["label"]) != a.pawn]
    for i, p in enumerate(others):                      # far west, out of every throw
        d.teleport(p["id"], cx - 80 + 2 * (i % 8), cz + 60 + 2 * (i // 8))
    d.teleport(me, cx, cz + 40)                         # out of range while the last frags go off
    for _ in range(20):
        if not hands.projectiles():
            break
        hands.wait(30)
    for k in range(60):                                 # heal there, then home
        hp, moving, _, _ = health(me)
        if hp == 100 and moving == 100:
            break
        d.run("T: Restore Body Part" if k % 4 == 3 else "T: Heal random injury (10)", x=cx, z=cz + 40)
    d.close()
    d.teleport(me, *home)
    rm.call("draft", action="draft", ids=me)
    hands.fire_at_will(a.pawn, False)
    rm.call("dev_mode", devMode=False)
    info = {"throwers": [(short_name(h["label"]), h["x"], h["z"]) for h in th], "pawn": a.pawn,
            "at": [cx, cz], "home": home, "health": health(me), "others_moved": len(others),
            "save": SAVE if a.save else None, "commit": git_commit()}
    if a.save:
        session.save(rm, SAVE)
    SETUP.write_text(json.dumps(info, indent=1) + "\n")
    print(json.dumps(info))


def load(a):
    session.load(rm, SAVE)
    rm.call("dev_mode", devMode=False, godMode=False)
    print(json.loads(SETUP.read_text()) if SETUP.exists() else SAVE)


class Log:
    """Per-poll bookkeeping of frags and the pawn; writes one row per exploded frag."""

    def __init__(self, a, mode):
        self.a, self.mode, self.pid = a, mode, ids()[a.pawn]
        self.g = {}                                     # id -> {first, pos, landed, threatened}
        self.rows, self.t0, self.commit = [], now(), git_commit()   # the code this process runs
        hp, moving, frag, _ = health(self.pid)
        self.start = {"hp": hp, "moving": moving, "frag_hediffs": frag}
        self.prev_hp, self.pos = hp, None
        self.frag_n, self.checks = frag, []             # wounds so far; rows awaiting the hit check

    def poll(self):
        t = now() - self.t0
        p = rm.call("get_pawn", id=self.pid)
        if "x" not in p:
            return t
        me = (p["x"], p["z"])
        hp = p.get("health")
        projs = {i: (x, z) for i, kind, x, z in hands.projectiles() if kind == "Frag"}
        for i, c in projs.items():
            g = self.g.setdefault(i, {"first": t, "first_pos": c, "pos": c, "since": t, "landed": None,
                                      "pawn_first": me})
            if g["pos"] != c:
                g["since"] = t
            elif g["landed"] is None and t - g["since"] >= hands.STILL:
                g["landed"] = g["since"]                # on this cell since then: lying on its fuse
            g["pos"], g["pawn_last"] = c, me
        for i in [i for i in self.g if i not in projs]:
            g = self.g.pop(i)
            fin = g["pos"]
            row = {"type": "event", "mode": self.mode, "pawn": self.a.pawn, "frag": i,
                   "first": g["first"], "landed": g["landed"], "gone": t, "final": fin,
                   "threatened": math.dist(g["pawn_first"], fin) <= HIT_R,
                   "near_at_blast": math.dist(g.get("pawn_last", me), fin) <= HIT_R,
                   "dist_at_blast": round(math.dist(g.get("pawn_last", me), fin), 1),
                   "hit": False, "wounds": 0, "hp_before": self.prev_hp}
            self.rows.append(row)
            self.checks.append([row, 3])
        if self.checks:
            hp_, _, n, _ = health(self.pid)
            if n > self.frag_n:                         # new frag wounds: the latest frag(s) gone
                last = max(r["gone"] for r, _ in self.checks)
                for r, _ in self.checks:
                    if r["gone"] == last:
                        r["hit"], r["wounds"] = True, n - self.frag_n
                self.frag_n = n
            for c in self.checks:
                c[1] -= 1
            for r, left in [c for c in self.checks if c[1] <= 0]:
                r["hp_after"] = hp_
                print(json.dumps(r))
            self.checks = [c for c in self.checks if c[1] > 0]
        self.prev_hp, self.pos = hp, me
        return t

    def close(self, extra):
        for r, _ in self.checks:
            print(json.dumps(r))
        hp, moving, frag, downed = health(self.pid)
        ev = self.rows
        summ = {"type": "run", "mode": self.mode, "pawn": self.a.pawn, "ticks": now() - self.t0,
                "frags": len(ev), "threatened": sum(r["threatened"] for r in ev),
                "near_at_blast": sum(r["near_at_blast"] for r in ev), "hits": sum(r["hit"] for r in ev),
                "start": self.start, "end": {"hp": hp, "moving": moving, "frag_hediffs": frag,
                                             "downed": downed},
                "commit": self.commit, **extra}
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with OUT.open("a") as f:
            for r in ev + [summ]:
                f.write(json.dumps(r) + "\n")
        print(json.dumps(summ))


def claude(a):
    cx, cz = a.at
    home = (cx, cz + 10)
    log, K = Log(a, "claude"), Keeper()
    t = 0
    while t < a.ticks:
        guard(n=1, dt=3, keep=(), quiet=False, keeper=K)
        t = log.poll()
        if K.is_held(a.pawn, t) or log.pos is None:
            continue
        lying = [g["pos"] for g in log.g.values() if g["landed"] is not None]
        if math.dist(log.pos, home) > 1 and all(math.dist(c, home) > 4 and hands._seg_dist(c, log.pos, home) > 3
                                                for c in lying):
            job = (rm.call("get_pawn", id=log.pid).get("job") or "").lower()
            if "moving" not in job:
                go(a.pawn, *home)
        if health(log.pid)[3]:
            break
    log.close({"home": home})


def watch(a):
    log = Log(a, "human")
    last, t = None, 0
    while t < a.ticks:
        n = now()
        if n == last:
            time.sleep(0.02)
            continue
        last = n
        t = log.poll()
    log.close({"home": (a.at[0], a.at[1] + 10)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("setup", "load", "claude", "watch"))
    ap.add_argument("--pawn", help="setup: a colonist's name or 'new'; others: default from the setup file")
    ap.add_argument("--at", type=lambda s: tuple(int(v) for v in s.split(",")), default=None)
    ap.add_argument("--ticks", type=int, default=3000)
    ap.add_argument("--save", action="store_true", help="setup: save the drill as " + SAVE)
    a = ap.parse_args()
    known = json.loads(SETUP.read_text()) if SETUP.exists() else {}
    if a.mode == "setup" and not a.pawn:
        ap.error("setup needs --pawn (a name or 'new')")
    a.pawn = a.pawn or known.get("pawn")
    a.at = a.at or tuple(known.get("at") or (152, 100))
    {"setup": setup, "load": load, "claude": claude, "watch": watch}[a.mode](a)


if __name__ == "__main__":
    main()
