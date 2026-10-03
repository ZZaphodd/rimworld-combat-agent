"""Unbiased engagement KPI from the battle log (replaces the job-text count,
LESSONS bug 9: drafted pawns firing at will show 'watching for targets').

Definition (EVAL_SPEC §8): a pawn *fires* in a 300-tick window if some battle
log entry in that window names it as the attacker (shot, shot at, hit, missed,
threw, stabbed, beat ...). A pawn is *available* in a window if it stood (not
downed, no fate) during a contact step in it. fire_share = fired pawn-windows /
available pawn-windows, per side; surface = mean number of firing pawns per
contact window (the engagement surface).

Attacker phrasing (seen 2026-10-03, scenario_theme_pirate_mixed):
  "Osborn tried to shoot at Mausi with her assault rifle."      -> Osborn
  "Opa's machine pistol bullet shot Xevion's left leg."          -> Opa
  "Xevion's torso was damaged by Opa's shot."                    -> Opa
  "The blast of Minoru's doomsday rocket damaged Xevion's torso" -> Minoru
  "Bellerose, using her left fist aptly, beat Xevion ..."        -> Bellerose
  "Rakool missed while trying to beat Hamster."                  -> Rakool
Names shared by several pawns of one side (mechs are all "Pikeman",
"Scyther" ...) are counted per name, not per pawn: fire_share then means "any
pawn of that name fired" (biased up) and surface counts names (biased down). Mech attacker
phrasing beyond "the <kind>'s ..." is UNVERIFIED.
Log ticks are absolute (TicksAbs), not ticksGame: the offset is estimated as
the running max of (newest entry tick - episode tick at harvest), a lower bound
that is tight while the fight is on (error <= the gap since the newest entry).
"""
import re

WINDOW = 300
PASSIVE = {"was", "is", "has", "had", "fell", "made", "collapsed", "died", "perished",
           "expired", "succumbed", "bled", "drop", "dropped"}
BY_RE = re.compile(r"\bby (.+?)'s\b")
POSS_RE = re.compile(r"^(?:The \w+ (?:of|from) )?(.+?)'s ")


def _the(n):
    n = n.strip()
    return n[4:] if n.lower().startswith("the ") else n


def attacker(text, names):
    """The known name that attacks in this entry, or None. Case-insensitive,
    a leading "the " is ignored (mechs: "the termite's head")."""
    low = {n.lower(): n for n in names}
    m = BY_RE.search(text)
    if m:
        return low.get(_the(m.group(1)).lower())
    m = POSS_RE.match(text)
    if m and _the(m.group(1)).lower() in low:
        return low[_the(m.group(1)).lower()]
    t = _the(text).lower()
    for n in sorted(low, key=len, reverse=True):
        if t.startswith(n + ",") or t.startswith(n + " "):
            nxt = t[len(n):].lstrip(", ").split(" ", 1)[0]
            return None if nxt in PASSIVE else low[n]
    return None


def fired_windows(entries, offset, names, window=WINDOW):
    """{name: set(window index)} from combat entries [(abs_tick, text)]."""
    out = {}
    for tick, text in entries:
        n = attacker(text, names)
        if n is not None:
            out.setdefault(n, set()).add((tick - offset) // window)
    return out


def share(fired, avail):
    """(fire_share, surface) for one side; avail = {name: set(window)}."""
    num = sum(len(fired.get(n, set()) & w) for n, w in avail.items())
    den = sum(len(w) for w in avail.values())
    windows = set().union(*avail.values()) if avail else set()
    surf = [sum(w in fired.get(n, set()) and w in avail[n] for n in avail) for w in windows]
    return (round(num / den, 3) if den else None,
            round(sum(surf) / len(surf), 2) if surf else None)
