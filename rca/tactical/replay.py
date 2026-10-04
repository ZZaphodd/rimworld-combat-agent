"""replay: re-fight a human battle from its trace (results/human/traces, TODO roadmap 3).

Win condition: the human's. The plan is copied, the play is not:
  * loadout: each pawn ends up with the weapon its human counterpart held when first drafted
    (manage_gear drop + equip at the start, before anyone is drafted; drafting cancels the
    pick-up job);
  * positions: every standing pawn walks to where the human's pawn stood LEAD ticks ahead of
    now (its last standing cell once the human's pawn was downed or gone), drafted, firing at
    will; micro (frag dodge) runs as in every doctrine;
  * breaches: a wall standing on a cell the human's pawns later stood on was broken by the
    human (rand_127: drafted melee pawns hitting it; one swing per order, so the order is
    repeated every step). Pawns whose human cell is next to such a wall hit it until it falls.
Not copied: targets, melee orders on raiders, rescues, smoke and the human's pausing. So a replay that
wins says the plan (sites and moves) won; one that loses says the human's moment-to-moment
play did. kpis: loadout result, orders, and how far the pawns stood from the human's (fidelity).
Option `trace` (path) is part of the resume key.
"""
import math

from ..eval import trace as trace_io
from ..game.weapons import weapon_def
from .squad import SquadDoctrine

LEAD = 120               # aim where the human's pawn stood this many ticks ahead
MOVE_EPS = 2.5           # a pawn this close to its cell is not re-ordered
REISSUE = 300            # re-order a pawn that drifted (micro, melee) after this many ticks
LOADOUT_MAX = 1200       # give up waiting for the pick-ups after this many ticks
BREAK_DEFS = ("Wall",)   # buildings the human may have broken (a wall on a cell a pawn stood on)


def timelines(polls):
    """pid -> [(t, x, z, downed)] from the trace polls."""
    out = {}
    for p in polls:
        for e in p.get("ours", []):
            out.setdefault(e["id"], []).append((p["t"], e["x"], e["z"], bool(e.get("d"))))
    return out


def cell_at(line, t):
    """The human's pawn's standing cell at tick t (its last standing one if it was down)."""
    best = None
    for tt, x, z, down in line:
        if tt > t:
            break
        if not down:
            best = (x, z)
    if best is None:                              # before the first poll: the first standing cell
        best = next(((x, z) for _, x, z, down in line if not down), None)
    return best


def target_weapons(polls):
    """pid -> weapon label its human counterpart held when first drafted (the loadout)."""
    out = {}
    for p in polls:
        for e in p.get("ours", []):
            if e["id"] not in out and e.get("dr") and e.get("w"):
                out[e["id"]] = e["w"]
    return out


def same_weapon(a, b):
    return (a or "").lower() == (b or "").lower()


class Replay(SquadDoctrine):
    name = "replay"
    version = 2                  # v2: breaches (walls the human broke)
    win_condition = "the human's: same loadout, same positions over time"
    phases_spec = {"loadout": "drop + equip until every pawn holds its target weapon",
                   "follow": "each pawn walks to the human's cell LEAD ticks ahead"}

    def effective_options(self):
        return {"trace": self.options.get("trace")}

    def reset(self, rm, manifest):
        super().reset(rm, manifest)
        lines = trace_io.read(self.opt["trace"])
        head = lines[0] if lines and "header" in lines[0] else {}
        if head.get("scenario") not in (None, manifest["id"]):
            raise ValueError(f"trace is for {head.get('scenario')}, not {manifest['id']}")
        polls = [p for p in lines if "ours" in p]
        self.lines = timelines(polls)
        self.want = {pid: w for pid, w in target_weapons(polls).items() if pid in self.squad_ids}
        self.ordered, self.dev = {}, {"before": [], "after": []}
        self.k.update(loadout_swaps=0, loadout_done_tick=None, loadout_missing=0, orders=0,
                      breach_walls=0, breach_hits=0, breach_done_tick=None)
        cells = {(x, z) for line in self.lines.values() for _, x, z, down in line if not down}
        self.breach = {}                              # cell -> wall id
        for d in BREAK_DEFS:
            for t in rm.call("list_things", category="all", defName=d, verbose=True,
                             confirm=True).get("things", []):
                if (t["x"], t["z"]) in cells:
                    self.breach[(t["x"], t["z"])] = t["id"]
        self.k["breach_walls"] = len(self.breach)
        self.loading = self.start_loadout(rm)
        self.set_phase("loadout" if self.loading else "follow")

    def start_loadout(self, rm):
        """Drop every weapon that must change hands, then order each pawn to pick up its own.
        Returns the pawns still to equip (empty: nothing to do)."""
        have = {pid: rm.call("get_pawn", id=pid).get("weapon") for pid in self.want}
        change = [pid for pid, w in self.want.items() if not same_weapon(have.get(pid), w)]
        dropped = []                                  # (item id, label)
        for pid in change:
            if have.get(pid) and weapon_def(have[pid]):
                r = rm.call("manage_gear", id=pid, op="drop", item=weapon_def(have[pid]))
                if r.get("itemId"):
                    dropped.append((r["itemId"], r.get("item") or ""))
        todo = set()
        for pid in change:
            item = next((i for i, label in dropped if same_weapon(label, self.want[pid])), None)
            if item is None:
                self.k["loadout_missing"] += 1
                continue
            dropped = [d for d in dropped if d[0] != item]
            r = rm.call("manage_gear", id=pid, op="equip", item=item)
            if r.get("ok"):
                todo.add(pid)
                self.k["loadout_swaps"] += 1
        return todo

    def step(self, rm):
        if self.loading:
            self.loading = {pid for pid in self.loading
                            if not same_weapon(rm.call("get_pawn", id=pid).get("weapon"),
                                               self.want[pid])}
            if self.loading and self.now < LOADOUT_MAX:
                return
            self.k["loadout_done_tick"] = self.now
            self.k["loadout_missing"] += len(self.loading)
            self.loading = set()
            self.weapons.clear()                      # re-read: they changed hands
            self.set_phase("follow")
        free, hs = self.observe(rm)
        breakers = self.breach_step(rm, free)
        free = [c for c in free if c["id"] not in breakers]
        for c in self.all_fighters:                   # fidelity, also for busy pawns
            cell = cell_at(self.lines.get(c["id"], []), self.now)
            if cell:
                self.dev["after" if self.contact else "before"].append(math.dist(c["pos"], cell))
        for c in free:
            pid = c["id"]
            cell = cell_at(self.lines.get(pid, []), self.now + LEAD)
            if cell is None or math.dist(c["pos"], cell) <= MOVE_EPS:
                continue
            last = self.ordered.get(pid)
            if last and last[0] == cell and self.now - last[1] < REISSUE:
                continue
            if self.goto(pid, cell):
                self.ordered[pid] = (cell, self.now)
                self.k["orders"] += 1

    def breach_step(self, rm, free):
        """Hit the standing breach walls with the pawns whose human cell is next to one.
        Returns the ids busy breaking."""
        busy = set()
        for cell, wid in list(self.breach.items()):
            here = [t for t in rm.call("list_things", category="all", nearX=cell[0], nearZ=cell[1],
                                       radius=0.5, verbose=True, confirm=True).get("things", [])
                    if t.get("id") == wid]
            if not here:
                del self.breach[cell]
                if not self.breach:
                    self.k["breach_done_tick"] = self.now
                continue
            for c in free:
                mine = cell_at(self.lines.get(c["id"], []), self.now + LEAD)
                if not mine or max(abs(mine[0] - cell[0]), abs(mine[1] - cell[1])) > 1:
                    continue
                busy.add(c["id"])
                if max(abs(c["pos"][0] - cell[0]), abs(c["pos"][1] - cell[1])) > 1:
                    if self.goto(c["id"], mine):
                        self.k["orders"] += 1
                    continue
                r = rm.call("do_thing_action", id=c["id"], label="Command_VerbTarget", targetId=wid)
                if r.get("executed"):
                    self.k["breach_hits"] += 1
        return busy

    def kpis(self):
        def mean(v):
            return round(sum(v) / len(v), 1) if v else None
        return super().kpis() | {"replay": dict(self.k) | {
            "dev_before_contact": mean(self.dev["before"]),
            "dev_after_contact": mean(self.dev["after"])}}
