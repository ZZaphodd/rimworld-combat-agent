"""turtle_at v1: turtle v9 holding a position the strategic layer picked (the user, 2026-10-06).

The user: even turtle needs the strategic layer to mark where to turtle; the spawn spot in the yard
is far worse than the base allows, and rules can't pick yet, so Claude picks by hand. The pick is
one entry per problem in a frozen plan file (rca.strategic.siteplan), passed as
`--option plan=<path>`; turtle v9 itself is unchanged (rca/tactical/turtle.py).

Modes (from the entry):
  anchor  turtle v9 exactly, with its anchor (planner centre, inside rule, bearing, prechecks)
          moved to the pick: the position alone.
  cells   every pawn gets a hand cell instead of the planner's line; re-plans re-issue the same
          cells. Without a `room` nothing else changes.
  room    cells inside an enclosed hold (a room behind a door). Turtle's rules that walk a squad
          out of a room are replaced, because they would undo the position outright (straight-line
          distances through walls; the 2026-10-06 design review):
            * no sally (idle 4800 / stall 1440): when turtle's rule would have fired is recorded
              (sally_would_tick, sally_would_reason; an idle one still raises turtle's
              precondition:enemy_approaches signal); raiders wrecking the base out of sight kept
              the stall clock running in 9 of turtle's 19 v2 rows;
            * no attack orders that walk: ranged pawns fire at will from their cells (the drafted
              default; "Fire at" on a raider behind a wall falls back to Auto attack, which walks
              the pawn out to find a shot), and a pawn melees only a standing raider next to its
              cell or inside the room ("Melee attack" from the float menu: a gun can't fire at an
              adjacent raider, GAME_FACTS);
            * front pawns (the door plug and its diagonals) are held on their exact cells;
            * wounded pawns (< 45%) go to the plan's rear cells and stay there through a breach, or
              keep their post when the plan has none;
            * the plan's doors are set at reset (Hold open read, then pressed only to change it),
              and pawns marked `fire: hold` get Fire at will off (throwers in a packed room).
Rows: options.plan (resume key), kpis.site (the resolved entry and its sha), door results, and the
room counters. Pinned to turtle v9: reset refuses another base version.
"""
import math

from ..micro.reflex import VISCOSITY
from ..eval.tracker import short_name
from ..rimmolt import RimMoltError
from ..strategic import siteplan
from .squad import FALLBACK_R, pos
from .turtle import IDLE_R, IDLE_SALLY_TICKS, STALL_SALLY_TICKS, Turtle

FRONT_TOL = 0.5            # a front pawn one cell off is standing in the doorway
FRONT_REISSUE = 120
MELEE_REISSUE = 240


def chebyshev(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


class TurtleAt(Turtle):
    name = "turtle_at"
    version = 1                  # v1 = turtle v9 at a picked site; room mode as in the docstring
    BASE_VERSION = 9
    win_condition = "turtle's, at the site the strategic layer picked: they come to our cells and die at them"
    phases_spec = Turtle.phases_spec | {"breach": "room mode: a raider in the room or its doorway"}

    @property
    def viscosity(self):
        return VISCOSITY["turtle"]

    def effective_options(self):
        return super().effective_options() | {"plan": self.options.get("plan")}

    def preflight(self, manifest):
        """The plan entry, checked before the episode starts (night.py): a bad plan writes no row."""
        if Turtle.version != self.BASE_VERSION:
            raise siteplan.PlanError(f"turtle_at v{self.version} is pinned to turtle v{self.BASE_VERSION}, "
                                     f"turtle is v{Turtle.version}")
        if not self.options.get("plan"):
            raise siteplan.PlanError("turtle_at needs --option plan=<plan file>")
        return siteplan.entry(self.options["plan"], manifest)

    # ------------------------------------------------------------ reset
    def reset(self, rm, manifest):
        self.site = self.preflight(manifest)
        super().reset(rm, manifest)
        self.spawn_anchor, self.anchor = self.anchor, self.site.anchor
        self.pre = self.precheck(rm)                 # measured at the site
        self.room_mode = bool(self.site.room and self.site.cells)
        self.k.update(site_cell_moves=0, melee_orders=0, rear_orders=0, front_reissues=0,
                      fire_hold_set=0, breach_ticks=0, outside_room_ticks=0)
        self.site_slots = self._live_cells()
        self.melee_order = {}
        self.fire_held, self.fire_tries = set(), {}
        self.would = None
        self.doors = self.set_doors(rm)

    def _live_cells(self):
        """The hand cells on the live terrain: a cell the game shows blocked (furniture the save
        map missed) moves to the nearest free passable cell, inside the room when there is one."""
        out, taken = {}, set()
        for pid, c in self.site.cells.items():
            cell = c
            if self.terrain is not None and not self.terrain.passable(*c):
                near = [p for p, _ in sorted(self.terrain.bfs(c, limit=3).items(), key=lambda kv: kv[1])
                        if p not in taken and p not in self.site.cells.values()
                        and (not self.site.room or self.site.in_room(p))]
                cell = near[0] if near else c
                self.k["site_cell_moves"] += cell != c
            out[pid] = cell
            taken.add(cell)
        return out

    def set_doors(self, rm):
        """Each plan door to its hold-open state: {"x,z": "set" | "already" | "error: ..."}."""
        out = {}
        for (x, z), want in self.site.doors:
            key = f"{x},{z}"
            try:
                door = next((t for t in rm.call("list_things", category="building", nearX=x, nearZ=z, radius=0.5,
                                                verbose=True, confirm=True).get("things") or []
                             if (t["x"], t["z"]) == (x, z) and "door" in (t.get("def") or "").lower()), None)
                if door is None:
                    out[key] = "error: no door"
                    continue

                def held():
                    acts = rm.call("inspect_thing", id=door["id"]).get("actions") or []
                    return next((a.get("active") for a in acts if (a.get("label") or "").lower() == "hold open"), None)
                now = held()
                if now is None:
                    out[key] = "error: no Hold open toggle"
                elif now == want:
                    out[key] = "already"
                else:
                    rm.call("do_thing_action", id=door["id"], label="Hold open")
                    out[key] = "set" if held() == want else "error: did not change"
            except (RimMoltError, KeyError, TypeError) as e:
                out[key] = f"error: {str(e)[:60]}"
        return out

    # ------------------------------------------------------------ plan
    def make_plan(self, fighters, hs):
        if not self.site.cells:
            return super().make_plan(fighters, hs)     # anchor mode: turtle's planner at the pick
        center = self._center(hs)
        self.bearing, self.planned_at = self._bearing(center), self.now
        self.slots = dict(self.site_slots)
        self.plan = {"site": self.site.site, "mode": "room" if self.room_mode else "cells", "center": center}
        self.tally.put("plan", {"site": self.site.site, "mode": self.plan["mode"], "center": center,
                                "shooters": len(self.slots), "shooters_placed": len(self.slots)})

    def to_slot(self, c, force=False):
        if not self.room_mode or self.site.roles.get(c["id"]) != "front":
            return super().to_slot(c, force)
        pid, slot = c["id"], self.slots.get(c["id"])
        if slot is None or not self.micro.cell_ok(pid, slot) or math.dist(c["pos"], slot) <= FRONT_TOL:
            return
        if force or self.now - self.slot_order.get(pid, -math.inf) >= FRONT_REISSUE:
            self.goto(pid, slot)
            self.slot_order[pid] = self.now
            self.k["front_reissues"] += not force

    # ------------------------------------------------------------ wounded
    def keep_wounded_fighting(self, c, hs):
        if not self.room_mode:
            return super().keep_wounded_fighting(c, hs)
        return not self.site.rear                  # a breach does not call the wounded back to the front

    def fallback_cell(self, hs, origin=None, dist=FALLBACK_R, taken=()):
        if not self.room_mode:
            return super().fallback_cell(hs, origin, dist, taken)
        used = {w["dest"] for w in self.wounded.values()} | set(taken)
        self.k["rear_orders"] += 1
        return next((c for c in self.site.rear if c not in used and self.micro.cell_ok(None, c)), self.site.rear[0])

    # ------------------------------------------------------------ room step
    def step(self, rm):
        if not self.room_mode:
            return super().step(rm)
        fighters, hs = self.observe(rm)
        dt, self.last_now = self.now - self.last_now, self.now
        if not hs or not self.all_fighters:
            return
        self.hold_fire(rm)
        standing = [h for h in hs if not h.get("downed")]
        self.inside = any(self.site.in_room(pos(h), margin=1) for h in standing)
        if self.plan is None:
            self.set_phase("setup")
            self.make_plan(self.all_fighters, hs)
            for c in fighters:
                self.to_slot(c, force=True)
            return
        self.measure(hs)
        self.k["breach_ticks"] += dt if self.inside else 0
        self.k["outside_room_ticks"] += dt * sum(not self.site.in_room(c["pos"], margin=1) for c in self.all_fighters)
        near30 = any(math.dist(pos(h), c["pos"]) <= IDLE_R for h in hs for c in self.all_fighters)
        self.idle = 0 if near30 else self.idle + dt
        if self.would is None and (self.idle >= IDLE_SALLY_TICKS or self.stall >= STALL_SALLY_TICKS):
            self.would = ("stall" if self.stall >= STALL_SALLY_TICKS else "idle", self.now)
            self.tally.once("sally_would_tick", self.now)
            self.tally.once("sally_would_reason", self.would[0])
            if self.would[0] == "idle":              # turtle's signal: the raid does not come to us
                self.raise_signal("precondition:enemy_approaches")
        self.set_phase("breach" if self.inside else
                       "hold" if self.phase in ("hold", "breach") or self.on_line(fighters) else "setup")
        for c in fighters:
            pid = c["id"]
            t = self.melee_target(c, standing)
            if t is not None:
                self.melee_at(pid, t)
            elif pid in self.target or pid in self.melee_order:
                self.target.pop(pid, None)
                self.melee_order.pop(pid, None)
                self.to_slot(c, force=True)
            else:
                self.to_slot(c, force=pid in self.owned_before)
        self.owned_before = set(self.owned)

    def melee_target(self, c, standing):
        """A standing raider this pawn may melee without leaving the hold: next to its own cell, or
        (melee weapon) inside the room. None: hold the cell and fire at will."""
        cell = self.slots.get(c["id"], c["pos"])
        adj = [h for h in standing if chebyshev(pos(h), c["pos"]) <= 1 and chebyshev(pos(h), cell) <= 1]
        if adj:
            return min(adj, key=lambda h: math.dist(pos(h), c["pos"]))
        if c["melee"]:
            inside = [h for h in standing if self.site.in_room(pos(h))]
            if inside:
                return min(inside, key=lambda h: math.dist(pos(h), c["pos"]))
        return None

    def melee_at(self, pid, h):
        """Melee attack <raider> from the float menu (the verb gizmo would use a gun)."""
        last = self.melee_order.get(pid)
        if last and last[0] == h["id"] and self.target.get(pid) == h["id"] and self.now - last[1] < MELEE_REISSUE:
            return True                              # micro and Go here pop target: then order again
        name = short_name(h.get("label")).lower()
        try:
            opts = self.rm.call("order_pawn", id=pid, targetId=h["id"]).get("options") or []
            m = next((o for o in opts if (o.get("label") or "").lower().startswith("melee attack")
                      and not o.get("disabled") and "to death" not in o["label"].lower()
                      and name in o["label"].lower()), None)     # the menu lists every pawn on the cell
            r = self.rm.call("order_pawn", id=pid, targetId=h["id"], index=m["index"]) if m else {"error": "no Melee attack"}
        except (RimMoltError, KeyError, TypeError) as e:
            r = {"error": repr(e)}
        if r.get("executed"):
            self.melee_order[pid] = (h["id"], self.now)
            self.target[pid] = h["id"]
            self.k["melee_orders"] += 1
            return True
        self.fail("melee_at", r)
        return False

    def hold_fire(self, rm):
        """Fire at will off for pawns the plan marks `fire: hold`, once drafted; drafting turns it
        back on (hands.stop), so a pawn re-drafted after a down is set again."""
        from ..micro.drills import fire_at_will
        for pid in (self.site.hold_fire & self.drafted) - self.fire_held:
            if self.fire_tries.get(pid, 0) >= 3:
                continue                                 # no toggle on this pawn: stop asking
            self.fire_tries[pid] = self.fire_tries.get(pid, 0) + 1
            if fire_at_will(rm, pid, False) is False:
                self.fire_held.add(pid)
                self.k["fire_hold_set"] += 1
        for pid in self.fire_held - self.drafted:      # lapsed (downed): set again once re-drafted
            self.fire_tries.pop(pid, None)
        self.fire_held &= self.drafted

    def kpis(self):
        return super().kpis() | {
            "site": {"name": self.site.site, "mode": "room" if self.room_mode else self.site.mode,
                     "plan": self.options.get("plan"), "sha": self.site.sha, "anchor": list(self.site.anchor),
                     "spawn_anchor": list(self.spawn_anchor), "doors": self.doors,
                     "cells": {k: list(v) for k, v in self.site_slots.items()}, "entry": self.site.raw}}
