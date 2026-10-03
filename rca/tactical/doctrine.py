"""Doctrine interface (EVAL_SPEC §2, GLOSSARY "doctrine"): a posture with a win
condition plus commit and reset criteria. Judged per battle with micro pinned.

The harness sets reflex, rx_version, terrain (one per episode), step_ticks and
now before calling reset()/step(). All durations are ticks, never steps.
Phase 1: the win-condition / commit / reset hooks exist but are no-ops; the
router (strategic layer) and doctrine transitions come later.
"""
from ..micro import MICRO_VERSION, VISCOSITY, MicroLayer
from ..rimmolt import player_pawns
from ..eval.tracker import short_name


class Doctrine:
    name = "?"
    version = 1
    win_condition = ""          # prose for now
    reflex = True               # micro may act (False: observe and count only)
    rx_version = MICRO_VERSION
    terrain = None
    step_ticks, now = 120, 0

    @property
    def viscosity(self):
        return VISCOSITY.get(self.name, 0.3)

    def reset(self, rm, manifest):
        """Episode start (not the MOBA 'reset'; see wants_reset)."""
        self.micro = MicroLayer(rm, self.terrain, self.viscosity, self.reflex)
        squad = {p["id"] for p in manifest["squad"]}
        self.micro.start({t["id"]: short_name(t.get("label")) for t in player_pawns(rm)
                          if t["id"] in squad})

    def step(self, rm):
        raise NotImplementedError

    # Hooks for doctrine transitions (phase 2). obs = the step's observation.
    def win_progress(self, obs):
        return None

    def wants_commit(self, obs):
        return False

    def wants_reset(self, obs):
        return False

    def kpis(self):
        k = self.micro.kpis() if getattr(self, "micro", None) else {}
        return k | (self.terrain.summary() if self.terrain else {})


class Idle(Doctrine):
    """b0: does nothing; colonists follow their hostility response (flee)."""
    name = "b0"

    def reset(self, rm, manifest):
        self.micro = None

    def step(self, rm):
        pass
