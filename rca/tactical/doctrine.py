"""Doctrine interface (EVAL_SPEC §2, GLOSSARY "doctrine", WORKFLOW layer
contracts): a posture with a win condition, preconditions and its own phases
(setup -> hold -> commit -> reset). Judged per battle with micro pinned.

The harness sets reflex, rx_version, terrain (one per episode), options,
step_ticks and now before calling reset()/step(). All durations are ticks.

Tactical owns stalemate detection: a doctrine raises "win condition
unattainable" (self.signals) after NO_PROGRESS_TICKS of *contested* time
without enemy points lost (rule 2, EVAL_SPEC §2: only steps in which we paid a
cost or were under threat count; a quiet pause is not a stalemate) or when a
precondition breaks. It never switches to another doctrine; the strategic
layer reads the signal (later). Preconditions are data on the class
(`preconditions`, checked by rca.tactical.preconditions.check) so the router
can test them without running the doctrine.

A second signal, losing_trade (report-only: no doctrine acts on it), covers
the fast defeats no_progress misses (results/baseline/calibration.md): from
first contact, on a contested step (cost or threat), once at least
LOSING_TRADE_MIN_LOST squad pawns are gone (dead or carried off; no longer in
list_colonists) and the running trade ratio
    enemy points lost / (pawns gone x colonist value)
is below LOSING_TRADE_LER. Colonist value = COLONIST_ENEMIES (4) x the mean
combat points of the raiders seen so far (the trade-ratio parameter, EVAL_SPEC
§6); enemy points lost = the doctrine-side progress meter. Window: cumulative
since first contact. Fires once per battle. Thresholds fitted offline on
baseline-v1 (results/baseline/calibration.md, tools/fit_signals.py). The
running trade is kept as kpis.trade_curve so the fit can be redone exactly.
"""
from ..eval.progress import ProgressMeter, lost_points, pressure
from ..eval.scoring import COLONIST_ENEMIES
from ..eval.tracker import EDGE, near_edge, short_name
from ..game.defs import combat_power
from ..game.weapons import THROWER_WORDS, weapon_range
from ..micro import MICRO_VERSION, VISCOSITY, MicroLayer
from ..rimmolt import player_pawns

NO_PROGRESS_TICKS = 3000      # contested ticks without enemy points lost (UNVERIFIED value)
NO_PROGRESS_RULE = 2          # 1 = raw pause (rows before 2026-10-03 pm), 2 = contested time
MAX_SIGNALS = 10
LOSING_TRADE_MIN_LOST = 2     # squad pawns gone before the trade is judged (fitted, baseline-v1)
LOSING_TRADE_LER = 1.0        # running trade ratio below this fires (fitted, baseline-v1)
MAX_TRADE_CURVE = 60


class Doctrine:
    name = "?"
    version = 1
    win_condition = ""          # prose
    preconditions = {}          # name -> params (rca.tactical.preconditions)
    phases_spec = {}            # phase -> what happens / when it ends (prose, for reports)
    option_choices = {}         # option -> allowed values; first = the doctrine's natural one
    no_progress_ticks = NO_PROGRESS_TICKS
    reflex = True               # micro may act (False: observe and count only)
    rx_version = MICRO_VERSION
    terrain = None
    options = {}
    step_ticks, now = 120, 0

    @property
    def viscosity(self):
        return VISCOSITY.get(self.name, 0.3)

    def effective_options(self):
        """Options this doctrine offers, with overrides applied; stored in rows
        and part of the resume key. Unknown keys/values are ignored."""
        out = {}
        for k, choices in self.option_choices.items():
            v = self.options.get(k)
            out[k] = v if v in choices else choices[0]
        return out

    def reset(self, rm, manifest):
        """Episode start (not the MOBA 'reset'; see the phases)."""
        self.rm = rm
        self.micro = MicroLayer(rm, self.terrain, self.viscosity, self.reflex)
        squad = {p["id"] for p in manifest["squad"]}
        self.micro.start({t["id"]: short_name(t.get("label")) for t in player_pawns(rm)
                          if t["id"] in squad})
        self.opt = self.effective_options()
        self.init_tactical()

    def init_tactical(self):
        """Phase log, signal history and the doctrine-side progress meter."""
        self.signals, self._seen_pts, self.meter = [], {}, ProgressMeter()
        self._np_armed, self._last_xz = True, {}
        self._sq_prev, self._reach = None, {}
        self._sq_seen, self._raw_pts, self.trade_curve = set(), {}, []
        self.phase, self.phase_log = None, []

    def step(self, rm):
        raise NotImplementedError

    # ------------------------------------------------------------ phases and signal
    def set_phase(self, phase):
        if phase != self.phase:
            self.phase = phase
            if len(self.phase_log) < 30:
                self.phase_log.append([self.now, phase])

    def raise_signal(self, reason, **extra):
        """'Win condition unattainable' for the strategic layer (a history:
        each reason once, except no_progress, which re-arms after progress).
        extra: fields stored with the entry (losing_trade: lost, our_pts,
        enemy_pts, ler)."""
        if len(self.signals) >= MAX_SIGNALS:
            return
        if reason == "no_progress":
            if not self._np_armed:
                return
            self._np_armed = False
        elif any(s["reason"] == reason for s in self.signals):
            return
        sig = {"tick": self.now, "reason": reason, "phase": self.phase}
        if reason == "no_progress":
            sig |= {"pause": self.meter.stretch(), "contested": self.meter.contested}
        self.signals.append(sig | extra)

    def enemy_reach(self, h):
        """(weapon range, thrower) of a raider for the threat test: one
        get_pawn per raider per episode. SquadDoctrine reuses enemy_info."""
        r = self._reach.get(h["id"])
        if r is None:
            label = ""
            if getattr(self, "rm", None) is not None:
                label = self.rm.call("get_pawn", id=h["id"]).get("weapon") or ""
            kind = h.get("kind") or h.get("def", "")
            r = self._reach[h["id"]] = (weapon_range(label, kind),
                                        any(w in label.lower() for w in THROWER_WORDS))
        return r

    def note_progress(self, hostiles, contact, squad=None):
        """Doctrine-side progress: points of raiders once seen live that are no
        longer live, except those last seen near the map edge (walked off: not
        progress). squad: {id: {pos, health, downed}} of our squad pawns now
        (None: pressure not measured, so no contested time and no signal).
        Raises no_progress after `no_progress_ticks` of contested time."""
        live = {h["id"] for h in hostiles}
        for h in hostiles:
            if h["id"] not in self._seen_pts:
                self._seen_pts[h["id"]] = combat_power(h.get("kind") or "", 0) or 0
                self._raw_pts[h["id"]] = self._seen_pts[h["id"]]
            self._last_xz[h["id"]] = (h["x"], h["z"])
        for i, p in self._last_xz.items():
            if i not in live and near_edge(*p, EDGE):
                self._seen_pts[i] = 0
        pressed = None
        if squad is not None:
            enemies = []
            for h in hostiles:
                rng, thrower = self.enemy_reach(h)
                enemies.append({"pos": (h["x"], h["z"]), "range": rng, "thrower": thrower})
            pressed = pressure(squad, self._sq_prev, enemies)
            self._sq_prev = squad
        before = self.meter.points
        self.meter.update(self.now, lost_points(self._seen_pts, live), contact, pressed)
        if self.meter.points > before:
            self._np_armed = True
        if self.meter.contested >= self.no_progress_ticks:
            self.raise_signal("no_progress")
        if squad is not None:
            self.note_trade(squad, pressed)

    def colonist_value(self):
        """COLONIST_ENEMIES x mean combat points of the raiders seen so far
        (raiders of unknown kind are left out of the mean)."""
        pts = [p for p in self._raw_pts.values() if p]
        return COLONIST_ENEMIES * sum(pts) / len(pts) if pts else None

    def note_trade(self, squad, pressed):
        """losing_trade (report-only; module docstring). squad: {id: ...} of
        the squad pawns listed now; a pawn listed before and missing now is
        gone (dead or carried off)."""
        self._sq_seen |= set(squad)
        if self.meter.first_contact is None:
            return
        lost = len(self._sq_seen - set(squad))
        enemy = round(self.meter.points, 1)
        if len(self.trade_curve) < MAX_TRADE_CURVE and (
                not self.trade_curve or self.trade_curve[-1][1:] != [lost, enemy]):
            self.trade_curve.append([self.now, lost, enemy])
        cv = self.colonist_value()
        if not cv or lost < LOSING_TRADE_MIN_LOST or not (pressed and any(pressed)):
            return
        ours = lost * cv
        if enemy < LOSING_TRADE_LER * ours:
            self.raise_signal("losing_trade", lost=lost, our_pts=round(ours, 1),
                              enemy_pts=enemy, ler=round(enemy / ours, 3))

    def kpis(self):
        k = self.micro.kpis() if getattr(self, "micro", None) else {}
        k = k | (self.terrain.summary() if self.terrain else {})
        if getattr(self, "phase_log", None) is not None:
            k["phase_log"] = self.phase_log
        if getattr(self, "meter", None) is not None:
            k |= self.meter.contested_summary() | {"no_progress_rule": NO_PROGRESS_RULE}
            k |= {"trade_curve": self.trade_curve,
                  "losing_trade_rule": {"min_lost": LOSING_TRADE_MIN_LOST,
                                        "ler": LOSING_TRADE_LER, "window": "since_contact"}}
        return k


class Idle(Doctrine):
    """b0: does nothing; colonists follow their hostility response (flee)."""
    name = "b0"

    def reset(self, rm, manifest):
        self.micro = None
        self.signals, self.phase_log = [], None

    def step(self, rm):
        pass
