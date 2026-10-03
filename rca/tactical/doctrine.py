"""Doctrine interface (EVAL_SPEC §2, GLOSSARY "doctrine", WORKFLOW layer
contracts): a posture with a win condition, preconditions and its own phases
(setup -> hold -> commit -> reset). Judged per battle with micro pinned.

The harness sets reflex, rx_version, terrain (one per episode), options,
step_ticks and now before calling reset()/step(). All durations are ticks.

Tactical owns stalemate detection: a doctrine raises "win condition
unattainable" (self.signals) after a no-progress stretch or when a
precondition breaks. It never switches to another doctrine; the strategic
layer reads the signal (later). Preconditions are data on the class
(`preconditions`, checked by rca.tactical.preconditions.check) so the router
can test them without running the doctrine.
"""
from ..eval.progress import ProgressMeter, lost_points
from ..eval.tracker import EDGE, near_edge, short_name
from ..game.defs import combat_power
from ..micro import MICRO_VERSION, VISCOSITY, MicroLayer
from ..rimmolt import player_pawns

NO_PROGRESS_TICKS = 3000      # 1.2 in-game hours without enemy points lost (UNVERIFIED value)
MAX_SIGNALS = 10


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
        self.phase, self.phase_log = None, []

    def step(self, rm):
        raise NotImplementedError

    # ------------------------------------------------------------ phases and signal
    def set_phase(self, phase):
        if phase != self.phase:
            self.phase = phase
            if len(self.phase_log) < 30:
                self.phase_log.append([self.now, phase])

    def raise_signal(self, reason):
        """'Win condition unattainable' for the strategic layer (a history:
        each reason once, except no_progress, which re-arms after progress)."""
        if len(self.signals) >= MAX_SIGNALS:
            return
        if reason == "no_progress":
            if not self._np_armed:
                return
            self._np_armed = False
        elif any(s["reason"] == reason for s in self.signals):
            return
        self.signals.append({"tick": self.now, "reason": reason, "phase": self.phase})

    def note_progress(self, hostiles, contact):
        """Doctrine-side progress: points of raiders once seen live that are no
        longer live, except those last seen near the map edge (walked off: not
        progress). Raises no_progress after `no_progress_ticks`."""
        live = {h["id"] for h in hostiles}
        for h in hostiles:
            if h["id"] not in self._seen_pts:
                self._seen_pts[h["id"]] = combat_power(h.get("kind") or "", 0) or 0
            self._last_xz[h["id"]] = (h["x"], h["z"])
        for i, p in self._last_xz.items():
            if i not in live and near_edge(*p, EDGE):
                self._seen_pts[i] = 0
        before = self.meter.points
        self.meter.update(self.now, lost_points(self._seen_pts, live), contact)
        if self.meter.points > before:
            self._np_armed = True
        if self.meter.stretch() >= self.no_progress_ticks:
            self.raise_signal("no_progress")

    def kpis(self):
        k = self.micro.kpis() if getattr(self, "micro", None) else {}
        k = k | (self.terrain.summary() if self.terrain else {})
        if getattr(self, "phase_log", None) is not None:
            k["phase_log"] = self.phase_log
        return k


class Idle(Doctrine):
    """b0: does nothing; colonists follow their hostility response (flee)."""
    name = "b0"

    def reset(self, rm, manifest):
        self.micro = None
        self.signals, self.phase_log = [], None

    def step(self, rm):
        pass
