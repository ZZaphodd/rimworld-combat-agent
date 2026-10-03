"""RimWorld combat agent, three layers (GLOSSARY.md): micro, tactical, strategic.

rca.game owns the game (loads, debug menu, builders), rca.eval owns episodes
and scoring, rca.terrain is the one terrain model every layer reads.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
