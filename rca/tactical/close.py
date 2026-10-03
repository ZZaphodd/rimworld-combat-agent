"""close v3: close the distance fast, cover to cover (anti-poke).

Win condition: snipers and archers out-range most of the squad, so trading at
their range loses; inside CLOSE_DIST our short guns out-trade them.
Preconditions: the raid out-ranges us (enemy_outranges) and there is cover on
the way (approach_cover).
Phases:
  setup   draft;
  commit  every pawn farther than CLOSE_DIST from its nearest raider bounds
          ADVANCE cells toward it at most every ADVANCE_TICKS, ending on a free
          cell within 3 that touches cover (tree, wall, rock); bounds of
          hop = min(ADVANCE, d - CLOSE_DIST + 2);
  hold    inside CLOSE_DIST: Auto attack for good (rocket carriers first);
  reset   none (losses come during the approach; bounding overwatch is TODO).
Signal: no_progress. No vs_throwers option: closing in is its nature.
Evidence (LESSONS §2): home 4/5 sniper, 5/5 mechs; all 14 inside 14 cells by
tick ~1380; best overall win count in the theme matrix.
"""
import math
import statistics

from .squad import SquadDoctrine, clip, pos, unit

COVER = set("*#%")               # get_area ascii: tree, wall, rock (sandbags don't render)


class Close(SquadDoctrine):
    name = "close"
    version = 3                  # legacy v1-v2
    win_condition = "get inside 14 cells of the pokers, then out-trade them at short range"
    preconditions = {"enemy_outranges": {"min_share": 0.4, "margin": 5},
                     "approach_cover": {"band": 2, "min_cover": 0.05}}
    phases_spec = {"setup": "draft", "commit": "bound 10 cells cover to cover every 120 ticks",
                   "hold": "inside 14: Auto attack for good", "reset": "none"}
    CLOSE_DIST, ADVANCE, ADVANCE_TICKS = 14, 10, 120

    def reset(self, rm, manifest):
        super().reset(rm, manifest)
        self.engaged, self.closed_at, self.next_bound = set(), [], {}

    def cover_cell(self, want):
        """Free cell within 3 of `want` that has a cover cell next to it."""
        t = self.terrain
        best, best_d = clip(want), math.inf
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                c = (round(want[0]) + dx, round(want[1]) + dz)
                if not t.inside(*c) or not t.passable(*c) or t.cell(*c) in COVER:
                    continue
                if any(t.cell(c[0] + a, c[1] + b) in COVER
                       for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b):
                    d = math.hypot(dx, dz)
                    if d < best_d:
                        best, best_d = c, d
        return best

    def step(self, rm):
        fighters, hs = self.observe(rm)
        if not hs or not fighters:
            return
        for c in fighters:
            pid, p = c["id"], c["pos"]
            near = self.nearest(p, hs)
            d = math.dist(pos(near), p)
            if pid not in self.engaged and d <= self.CLOSE_DIST:
                self.closed_at.append(self.now)
                self.tally.put("close_tick_mean", round(statistics.mean(self.closed_at)))
                self.tally.put("closed_n", len(self.closed_at))
            if pid in self.engaged or d <= self.CLOSE_DIST:
                self.engaged.add(pid)
                self.auto_attack(pid, self.target_for(c, hs))
                continue
            if self.now < self.next_bound.get(pid, 0):
                continue
            self.next_bound[pid] = self.now + self.ADVANCE_TICKS
            ux, uz = unit(near["x"] - p[0], near["z"] - p[1])
            hop = min(self.ADVANCE, d - self.CLOSE_DIST + 2)
            cell = self.cover_cell((p[0] + ux * hop, p[1] + uz * hop))
            if self.micro.cell_ok(pid, cell):
                self.goto(pid, cell)
        n = len(self.all_fighters)
        self.set_phase("hold" if n and len(self.engaged) >= n / 2 else "commit")
