"""Tactical layer: doctrine execution (EVAL_SPEC §2 registry).

Canonical code names follow GLOSSARY.md; old names are aliases
(rca/eval/results.ALIASES). Phase 2 adds doctrine, turtle, spread, kite, close.
"""
from ..eval.results import canonical
from .amove import Amove
from .doctrine import Doctrine, Idle

AGENTS = {a.name: a for a in (Idle, Amove)}


def make(name):
    return AGENTS[canonical(name)]()


def version_of(name):
    cls = AGENTS.get(canonical(name))
    return cls.version if cls else None
