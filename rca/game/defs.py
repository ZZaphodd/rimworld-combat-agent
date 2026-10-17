"""Tables read from the game's XML: PawnKindDef combat power and weapon ranges.

RimMolt does not expose combatPower (not on the info card, and get_info_card
only takes ThingDefs), but list_things(verbose) gives each pawn's `kind`
(PawnKindDef) and the XML ships with the game. Tables are extracted once into
data/*.json and versioned, so agents and scoring never need the game files.

Xenotypes (2026-10-06): a raid pays a pawn's combatPower times its xenotype's combatPowerFactor
(PawnGenOptionWithXenotype.Cost); data/xenotypes.json holds each xenotype's factor and each
faction's expected factor from its xenotypeSet chances (weights; a set summing below 1 leaves the
rest to baseliners at 1; no set: 1). RimMolt does not expose a raider's xenotype.

Buildings (2026-10-06): data/buildings.json holds each building def's passability, fill,
size and door/rock flags, so a base map can be read from a save without the game.

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
XENOS = DATA / "xenotypes.json"
BUILDINGS = DATA / "buildings.json"
COVER = DATA / "cover.json"


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


def extract_xenotypes(game=GAME):
    """{"xenotype": {defName: combatPowerFactor}, "faction": {defName: expected factor}}."""
    data = Path(game) / "Data"
    xeno = {}
    for n in _all_nodes(data, lambda t: t == "XenotypeDef"):
        if n.findtext("defName"):
            xeno[n.findtext("defName")] = float(n.findtext("combatPowerFactor") or 1.0)
    fac_nodes = list(_all_nodes(data, lambda t: t == "FactionDef"))
    ch = _Chain(fac_nodes)
    faction = {}
    for n in fac_nodes:
        name = n.findtext("defName")
        if not name:
            continue
        xs = ch.first(n, "xenotypeSet/xenotypeChances")
        chances = {c.tag: float(c.text) for c in (xs if xs is not None else []) if c.text}
        total = sum(chances.values())
        if not total:
            faction[name] = 1.0
            continue
        weight = max(total, 1.0)                 # below 1: the rest are baseliners
        faction[name] = round((sum(w * xeno.get(x, 1.0) for x, w in chances.items())
                               + (weight - total) * 1.0) / weight, 4)
    return {"xenotype": dict(sorted(xeno.items())), "faction": dict(sorted(faction.items()))}


def extract_buildings(game=GAME):
    """{defName: {kind, pass, fill, size, door, rock, packed}} for maps read from a save without
    the game (rca.game.savemap): every concrete Building ThingDef, every save-compressible one
    (natural rock, stone chunks) and every plant or item a pawn cannot stand on (trees, chunks).
    kind is the category (building, item, plant); passability is Standable, PassThroughOnly or
    Impassable; fillPercent (the game's line of sight stops at a building filled >= 0.99 and at a
    closed door); size [x, z]; door (a Building_Door class); rock (mineable natural rock or its
    smoothed wall); packed (saveCompressible: stored in the compressed thing grid by short hash)."""
    things = _Chain(_all_nodes(Path(game) / "Data", lambda t: t == "ThingDef"))
    out = {}
    for n in things.nodes:
        name = n.findtext("defName")
        if not name or n.get("Abstract", "").lower() == "true":
            continue
        cat = things.text(n, "category") or ""
        packed = (things.text(n, "saveCompressible") or "").lower() == "true"
        passing = things.text(n, "passability") or "Standable"
        if cat != "Building" and not packed and not (cat in ("Plant", "Item") and passing != "Standable"):
            continue
        size = (things.text(n, "size") or "(1,1)").strip("() ").split(",")
        cls = things.text(n, "thingClass") or ""
        out[name] = {"kind": cat.lower(), "pass": passing,
                     "fill": _num(things.text(n, "fillPercent")) or 0.0,
                     "size": [int(size[0]), int(size[1])] if len(size) == 2 else [1, 1],
                     "door": "Door" in cls,
                     "rock": cls == "Mineable" or (things.text(n, "building/isNaturalRock") or "").lower() == "true",
                     "packed": packed}
    return dict(sorted(out.items()))


def extract_cover(game=GAME):
    """{defName: {fill, building, door, size}} for every concrete ThingDef with a fill percent of at
    least 0.01 (ThingDef.Fillage above None): what rca.sight needs to answer the game's two questions
    per cell. A building filled above 0.99 is a full-fill edifice and blocks the line of sight (a door
    only while closed: GenGrid.CanBeSeenOver); anything with a fill is cover (CoverGrid), plants and
    chunks included (a bush is 0.2, a tree 0.25, an urn 0.4, a stone chunk 0.5)."""
    things = _Chain(_all_nodes(Path(game) / "Data", lambda t: t == "ThingDef"))
    out = {}
    for n in things.nodes:
        name = n.findtext("defName")
        if not name or n.get("Abstract", "").lower() == "true":
            continue
        fill = _num(things.text(n, "fillPercent")) or 0.0
        if fill < 0.01:
            continue
        size = (things.text(n, "size") or "(1,1)").strip("() ").split(",")
        out[name] = {"fill": fill, "building": (things.text(n, "category") or "") == "Building",
                     "door": "Door" in (things.text(n, "thingClass") or ""),
                     "size": [int(size[0]), int(size[1])] if len(size) == 2 else [1, 1]}
    return dict(sorted(out.items()))


def write_cover(game=GAME):
    c = extract_cover(game)
    COVER.write_text(json.dumps(c, indent=1) + "\n")
    return len(c)


_cache = None
_xenos = None
_buildings = None
_cover = None


def cover():
    """data/cover.json (rca.sight's fill table), loaded once."""
    global _cover
    if _cover is None:
        _cover = json.loads(COVER.read_text()) if COVER.exists() else {}
    return _cover


def buildings():
    """data/buildings.json (rca.game.savemap's def table), loaded once."""
    global _buildings
    if _buildings is None:
        _buildings = json.loads(BUILDINGS.read_text()) if BUILDINGS.exists() else {}
    return _buildings


def building(def_name):
    """One def's entry from data/buildings.json, or None."""
    return buildings().get(def_name)


def xenotype_factor(xenotype=None, faction=None):
    """A xenotype's combatPowerFactor, or a faction's expected one; 1.0 when unknown."""
    global _xenos
    if _xenos is None:
        _xenos = json.loads(XENOS.read_text()) if XENOS.exists() else {"xenotype": {}, "faction": {}}
    if xenotype:
        return _xenos["xenotype"].get(xenotype, 1.0)
    return _xenos["faction"].get(faction, 1.0) if faction else 1.0


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
    x = extract_xenotypes()
    XENOS.write_text(json.dumps(x, indent=1) + "\n")
    print(f"{len(x['xenotype'])} xenotypes, {len(x['faction'])} factions -> {XENOS}")
