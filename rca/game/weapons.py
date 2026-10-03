"""One weapon classifier for everything (LESSONS bug 4: is_melee and the census
classifier disagreed on blade, scythe, pike). Melee = class 'melee'.

Classes are label substrings, first match wins (DATA.md §4). The range table is
still guesswork (GAME_FACTS §5, UNVERIFIED) and only kept for doctrines that
need a number until ranges are read from the XML (phase 2).
"""
import re

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
RANGE_GUESS = (("sniper", 44), ("charge lance", 30), ("bolt", 30), ("assault", 31),
               ("charge rifle", 27), ("rifle", 35), ("lmg", 26), ("minigun", 30),
               ("heavy smg", 23), ("smg", 23), ("machine pistol", 19), ("chain shotgun", 15),
               ("shotgun", 16), ("autopistol", 26), ("revolver", 26), ("pistol", 26),
               ("bow", 25), ("launcher", 23))
DEFAULT_RANGE = 25
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


def weapon_range(label):
    low = (label or "").lower()
    return next((r for k, r in RANGE_GUESS if k in low), DEFAULT_RANGE)
