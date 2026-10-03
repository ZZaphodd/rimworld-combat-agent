"""One weapon classifier for everything (LESSONS bug 4: is_melee and the census
classifier disagreed on blade, scythe, pike). Melee = class 'melee'.

Classes are label substrings, first match wins (DATA.md §4). Ranges come from
the game XML (data/weapon_ranges.json, rca/game/defs.py; LESSONS bug 3 replaced
the guessed table): a weapon label from get_pawn is matched to a ThingDef label,
a mech (no weapon label) by its PawnKindDef.
"""
import json
import re

from .defs import RANGES

CLASSES = [
    ("explosive", ("launcher", "grenade", "molotov", "emp", "inferno", "toxbomb", "rocket",
                   "doomsday", "triple rocket", "thump cannon", "incinerator")),
    ("long", ("sniper", "greatbow", "charge lance", "bolt-action", "marksman", "needle gun")),
    ("support", ("lmg", "minigun", "heavy charge blaster", "heavy smg")),
    ("bow", ("short bow", "recurve bow", "bow")),
    ("thrown", ("pila", "javelin")),
    ("short", ("shotgun", "smg", "machine pistol", "autopistol", "revolver", "pistol",
               "chain shotgun", "spiner")),
    ("medium", ("assault rifle", "charge rifle", "rifle", "beam", "blaster", "gun", "cannon")),
    ("melee", ("sword", "knife", "club", "mace", "spear", "axe", "hammer", "ikwa", "gladius",
               "horn", "claw", "blade", "fist", "bite", "scythe", "lance", "pike")),
]
# Mechs carry built-in weapons (no label): class by kind.
MECH_CLASS = {
    "mech_lancer": "medium", "mech_pikeman": "long", "mech_scyther": "melee",
    "mech_centurion": "support", "mech_centipedeblaster": "support",
    "mech_centipedegunner": "support", "mech_centipedeburner": "explosive",
    "mech_warqueen": "support", "mech_warurchin": "short", "mech_termite": "explosive",
    "mech_termite_breach": "explosive", "mech_tesseron": "medium", "mech_legionary": "medium",
    "mech_militor": "short", "mech_scorcher": "explosive", "mech_diabolus": "explosive"}
DEFAULT_RANGE = 25          # unknown weapon (counted by range_source() == "default")
MELEE_RANGE = 1.5           # adjacent
NON_PERSONAL = {"TurretGun", "Artillery", "Artillery_BaseDestroyer"}
FRAG_WORDS = ("frag grenade",)
THROWER_WORDS = ("frag grenade", "molotov")
CARRIER_WORDS = ("doomsday", "rocket launcher")


def weapon_name(label):
    """'Biocoded heavy SMG (good 80%)' -> 'heavy SMG'; no weapon -> 'none'."""
    return re.sub(r"\s*\(.*?\)\s*", "", label or "").replace("Biocoded ", "").strip() or "none"


def weapon_class(label, kind=""):
    name = weapon_name(label)
    if name == "none":
        return MECH_CLASS.get((kind or "").lower(), "other")
    low = name.lower()
    for cls, keys in CLASSES:
        if any(k in low for k in keys):
            return cls
    return "other"


def is_melee(label, kind=""):
    return weapon_class(label, kind) == "melee"


_table = None


def _ranges():
    """(label -> range, mech kind -> range). Turret/mortar guns are left out of
    the label index: 'inferno cannon' is both a centipede gun (26.9) and a
    turret (45.9). A label shared by two personal weapons keeps the shorter."""
    global _table
    if _table is None:
        d = json.loads(RANGES.read_text()) if RANGES.exists() else {"weapons": {}, "mech_kinds": {}}
        by_label = {}
        for w in d["weapons"].values():
            if w["range"] is None or (w["tags"] and set(w["tags"]) <= NON_PERSONAL):
                continue
            k = w["label"].lower()
            by_label[k] = min(by_label.get(k, w["range"]), w["range"])
        _table = (by_label, {k: v["range"] for k, v in d["mech_kinds"].items()})
    return _table


def range_source(label, kind=""):
    """(range, source): source = label | label_sub | mech | melee | default."""
    by_label, mechs = _ranges()
    name = weapon_name(label)
    if name == "none":
        # old manifests store the race (Mech_Termite) instead of the kind (Mech_Termite_Breach)
        alt = [k for k in mechs if kind and k.startswith(kind + "_")]
        r = mechs.get(kind) or (mechs.get(alt[0]) if len(alt) == 1 else None)
        if r:
            return r, "mech"
        return (MELEE_RANGE, "melee") if weapon_class(label, kind) == "melee" else (DEFAULT_RANGE, "default")
    low = name.lower()
    if low in by_label:
        return by_label[low], "label"
    # 'Steel longsword', 'unique ...' and other prefixed labels: longest contained label
    sub = max((k for k in by_label if k in low), key=len, default=None)
    if sub:
        return by_label[sub], "label_sub"
    if weapon_class(label, kind) == "melee":
        return MELEE_RANGE, "melee"
    return DEFAULT_RANGE, "default"


def weapon_range(label, kind=""):
    """Verb range in cells from the XML (melee 1.5, unknown 25)."""
    return range_source(label, kind)[0]
