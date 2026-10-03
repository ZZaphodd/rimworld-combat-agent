"""Tactical layer: doctrine execution (EVAL_SPEC §2 registry).

Canonical code names follow GLOSSARY.md; old names are aliases
(rca/eval/results.ALIASES). Each doctrine's spec (win condition,
preconditions, phases, commit/reset criteria) is its module docstring.
"""
from ..eval.results import canonical
from .amove import Amove
from .close import Close
from .doctrine import Doctrine, Idle
from .focus import Focus
from .kite import Kite
from .spread import Spread
from .turtle import Turtle

AGENTS = {a.name: a for a in (Idle, Amove, Focus, Turtle, Spread, Kite, Close)}


def make(name):
    return AGENTS[canonical(name)]()


def version_of(name):
    cls = AGENTS.get(canonical(name))
    return cls.version if cls else None


def options_of(name, overrides=None):
    """Effective tactical options of an agent under CLI overrides (resume key)."""
    cls = AGENTS.get(canonical(name))
    if cls is None:
        return {}
    a = cls()
    a.options = dict(overrides or {})
    return a.effective_options()
