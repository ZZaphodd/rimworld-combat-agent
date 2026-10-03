"""Tables read from the game's XML: PawnKindDef combat power and weapon ranges.

RimMolt does not expose combatPower (not on the info card, and get_info_card
only takes ThingDefs), but list_things(verbose) gives each pawn's `kind`
(PawnKindDef) and the XML ships with the game. Tables are extracted once into
data/*.json and versioned, so agents and scoring never need the game files.

Weapon ranges (LESSONS bug 3): the first verb with a <range> of every concrete
weapon ThingDef (parent chain reaches BaseWeapon, or it has weaponTags), with
ParentName inheritance; weaponTags lists are appended along the chain as the
game does. Mech kinds carry no weapon label, so their weapons are the ThingDefs
whose weaponTags meet the kind's weaponTags (inherited).
"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

GAME = Path.home() / "Library/Application Support/Steam/steamapps/common/RimWorld/RimWorldMac.app"
DATA = Path(__file__).resolve().parents[2] / "data"
TABLE = DATA / "combat_power.json"
RANGES = DATA / "weapon_ranges.json"


def _all_nodes(data_dir, tags=None):
    for f in sorted(Path(data_dir).glob("*/Defs/**/*.xml")):
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError:
            continue
        for n in root:
            if tags is None or tags(n.tag):
                yield n


def _nodes(data_dir):
    """Every PawnKindDef node (incl. abstract parents) under Data/*/Defs."""
    return _all_nodes(data_dir, lambda t: t == "PawnKindDef" or t.endswith("KindDef"))


class _Chain:
    """ParentName inheritance for one def family (by Name attribute)."""

    def __init__(self, nodes):
        self.nodes = list(nodes)
        self.named = {n.get("Name"): n for n in self.nodes if n.get("Name")}

    def chain(self, n):
        out, seen = [n], set()
        while (p := out[-1].get("ParentName")) and p in self.named and p not in seen:
            seen.add(p)
            out.append(self.named[p])
        return out                       # child first

    def text(self, n, path):
        return next((v for c in self.chain(n) if (v := c.findtext(path)) is not None), None)

    def first(self, n, path):
        return next((e for c in self.chain(n) if (e := c.find(path)) is not None), None)

    def tags(self, n, path="weaponTags"):
        """List inheritance: parent items first, child appended; Inherit="False" stops."""
        out = []
        for c in self.chain(n):
            e = c.find(path)
            if e is None:
                continue
            out = [li.text for li in e.findall("li") if li.text] + out
            if e.get("Inherit", "").lower() == "false":
                break
        return out


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


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def extract_weapons(game=GAME):
    """{"weapons": {defName: {label, range, min_range, warmup, burst, verb, tags}},
        "mech_kinds": {kind: {weapons: [defName], range}}} from the XML."""
    things = _Chain(_all_nodes(Path(game) / "Data", lambda t: t == "ThingDef"))
    weapons = {}
    for n in things.nodes:
        name = n.findtext("defName")
        if not name or n.get("Abstract", "").lower() == "true":
            continue
        chain = things.chain(n)
        is_weapon = any(c.get("Name") == "BaseWeapon" for c in chain) or things.tags(n)
        verbs = things.first(n, "verbs")
        verb = next((li for li in verbs.findall("li") if li.findtext("range")), None) \
            if verbs is not None else None
        if not is_weapon or verb is None or things.text(n, "category") == "Building":
            continue
        weapons[name] = {
            "label": (things.text(n, "label") or name).strip(),
            "range": _num(verb.findtext("range")),
            "min_range": _num(verb.findtext("minRange")) or 0.0,
            "warmup": _num(verb.findtext("warmupTime")),
            "burst": int(_num(verb.findtext("burstShotCount")) or 1),
            "verb": verb.findtext("verbClass"),
            "tags": things.tags(n)}
    kinds = _Chain(_nodes(Path(game) / "Data"))
    mechs = {}
    for n in kinds.nodes:
        name = n.findtext("defName")
        if not name or not name.startswith("Mech_"):
            continue
        want = set(kinds.tags(n))
        ws = sorted(w for w, v in weapons.items() if want & set(v["tags"]))
        mechs[name] = {"weapons": ws,
                       "range": max((weapons[w]["range"] for w in ws), default=None)}
    return {"weapons": dict(sorted(weapons.items())), "mech_kinds": dict(sorted(mechs.items()))}


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
    w = extract_weapons()
    RANGES.write_text(json.dumps(w, indent=1) + "\n")
    print(f"{len(w['weapons'])} weapons, {len(w['mech_kinds'])} mech kinds -> {RANGES}")
