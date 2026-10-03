"""PawnKindDef combat power read from the game's XML.

RimMolt does not expose combatPower (not on the info card, and get_info_card
only takes ThingDefs), but list_things(verbose) gives each pawn's `kind`
(PawnKindDef) and the XML ships with the game. The table is extracted once into
data/combat_power.json and versioned, so scoring never needs the game.
"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

GAME = Path.home() / "Library/Application Support/Steam/steamapps/common/RimWorld/RimWorldMac.app"
TABLE = Path(__file__).resolve().parents[2] / "data" / "combat_power.json"


def _nodes(data_dir):
    """Every PawnKindDef node (incl. abstract parents) under Data/*/Defs."""
    for f in sorted(Path(data_dir).glob("*/Defs/**/*.xml")):
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError:
            continue
        for n in root:
            if n.tag == "PawnKindDef" or n.tag.endswith("KindDef"):
                yield n


def extract(game=GAME):
    """{kindDefName: combatPower}, resolving ParentName inheritance."""
    named, concrete = {}, []
    for n in _nodes(Path(game) / "Data"):
        if n.get("Name"):
            named[n.get("Name")] = n
        if n.findtext("defName"):
            concrete.append(n)

    def power(n, seen=()):
        v = n.findtext("combatPower")
        if v is not None:
            return float(v)
        p = n.get("ParentName")
        if p and p in named and p not in seen:
            return power(named[p], seen + (p,))
        return None

    out = {}
    for n in concrete:
        v = power(n)
        if v is not None:
            out[n.findtext("defName")] = v
    return dict(sorted(out.items()))


_cache = None


def combat_power(kind, default=None):
    """Points of one PawnKindDef from the versioned table. Old manifests store
    the race ThingDef (Mech_Termite) instead: then a unique kind starting with
    it (Mech_Termite_Breach) is used. 'Human' is ambiguous -> default."""
    global _cache
    if _cache is None:
        _cache = json.loads(TABLE.read_text()) if TABLE.exists() else {}
    if kind in _cache:
        return _cache[kind]
    alt = [k for k in _cache if k.startswith(f"{kind}_")] if kind else []
    return _cache[alt[0]] if len(alt) == 1 else default


if __name__ == "__main__":
    t = extract()
    TABLE.parent.mkdir(exist_ok=True)
    TABLE.write_text(json.dumps(t, indent=1) + "\n")
    print(f"{len(t)} kinds -> {TABLE}")
