"""spread v6: keep spacing so one blast hits one pawn (anti-splash).

Win condition: trade at full engagement surface while splash (frags, rockets,
inferno) can't hit more than one pawn per blast.
Preconditions: a splash-heavy raid (enemy_splash_heavy >= 0.45, v6: share of
raiders with census class 'explosive'; fitted on baseline-v1, where spread beat
amove only vs grenadiers: grenadier 0.77 vs <= 0.13 elsewhere) and room to
spread around the squad (room_to_spread >= 0.7, UNVERIFIED: 1.00 on every
theme of the one baseline arena, so it is uninformative until a 2nd arena).
Phases:
  setup   draft;
  hold    any pawn with a squadmate closer than MIN_GAP steps STEP_OUT cells
          away from its close neighbours (sum of unit vectors; nearly
          cancelling = stacked -> fan out by index, angle i x 2.4 rad) and holds
          that cell HOLD_TICKS, firing at will;
  commit  otherwise each pawn Auto-attacks the raider nearest to IT (rocket
          carriers within 35 first): no shared focus target, which would pull
          everyone onto one line. Hold and commit run per pawn at once;
  reset   none (spacing is re-checked every step).
Signals: no_progress, losing_trade (report-only).
v6: report-only (losing_trade, enemy_splash_heavy recorded); behaviour
identical to v5, bumped so rows never mix. vs_throwers: accept_dodge (natural) / stand_off / close_in.
No wounded pull-back and no rescue (legacy spread had neither).
Evidence (LESSONS §2): gap5_share 0.71-0.79 vs 0.1-0.4 for the others; best vs
grenadiers (P 0.76 vs amove). Spread + threat map v3 looked worse (two owners
of spacing moves): here micro v4 only dodges frags and fire, it never spaces.
"""
import math

from .squad import SquadDoctrine, clip, unit


class Spread(SquadDoctrine):
    name = "spread"
    version = 6                  # v6 = v5 + losing_trade, enemy_splash_heavy (report-only); legacy v1-v4
    win_condition = "splash hits one pawn per blast; trade at full surface"
    preconditions = {"enemy_splash_heavy": {"min_share": 0.45},
                     "room_to_spread": {"radius": 10, "min_passable": 0.7}}
    phases_spec = {"setup": "draft", "hold": "step out of < 5-cell clumps, hold 600 ticks",
                   "commit": "Auto attack the raider nearest to each pawn", "reset": "none"}
    option_choices = {"vs_throwers": ("accept_dodge", "stand_off", "close_in")}
    MIN_GAP, STEP_OUT, HOLD_TICKS = 5, 5, 600

    def reset(self, rm, manifest):
        super().reset(rm, manifest)
        self.hold = {}
        self.k["step_outs"] = 0

    def step(self, rm):
        fighters, hs = self.observe(rm)
        if not hs or not fighters:
            return
        self.set_phase("commit" if self.contact else "hold")
        if self.contact:
            for c in self.all_fighters:
                d = min((math.dist(c["pos"], o["pos"]) for o in self.all_fighters
                         if o["id"] != c["id"]), default=15)
                self.tally.add("mean_gap", min(15, d))
        for i, c in enumerate(sorted(fighters, key=lambda c: c["id"])):
            pid, p = c["id"], c["pos"]
            close = [o["pos"] for o in self.all_fighters
                     if o["id"] != pid and math.dist(o["pos"], p) < self.MIN_GAP]
            holding = self.now < self.hold.get(pid, 0)
            if close and not holding:
                vx = sum(unit(p[0] - q[0], p[1] - q[1])[0] for q in close)
                vz = sum(unit(p[0] - q[0], p[1] - q[1])[1] for q in close)
                if math.hypot(vx, vz) < 0.3:           # stacked: fan out by index
                    vx, vz = math.cos(i * 2.4), math.sin(i * 2.4)
                ux, uz = unit(vx, vz)
                want = clip((p[0] + ux * self.STEP_OUT, p[1] + uz * self.STEP_OUT))
                if self.micro.cell_ok(pid, want):
                    self.goto(pid, want)
                    self.hold[pid] = self.now + self.HOLD_TICKS
                    self.k["step_outs"] += 1
            elif not holding:
                self.auto_attack(pid, self.target_for(c, hs))
