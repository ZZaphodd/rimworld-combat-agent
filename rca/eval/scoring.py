"""Grade and trade ratio from raw metrics (EVAL_SPEC §5-§6). Stored verdicts go
stale whenever this file changes, so reports always recompute.

Primary development metric: the trade ratio (LER, loss-exchange ratio)
    LER = enemy strength lost / our strength lost
  * enemy strength lost = combat points (PawnKindDef combatPower, read from the
    game XML, rca/game/defs.py) of raiders killed, killed_inferred or downed at
    the end. Escaped raiders are not lost.
  * our strength lost = colonists lost (dead + kidnapped) x colonist value;
    colonist value = COLONIST_ENEMIES x the mean points of a raider in that
    battle (default 4: "1 colonist = 4 enemies by points").
  * Rows from before per-raider points (everything before rca) have only counts:
    their enemy points are count x the scenario's mean points per raider, which
    makes their LER count-based (enemy lost / 4 x colonists lost).
  * No colonist lost: LER = inf (a "clean" trade); nothing lost on either side:
    LER undefined, ranked as an even trade (1.0).
Colonist losses and the grade are reported next to it, never folded in.
"""
import math

COLONIST_ENEMIES = 4.0
BROKE, INTACT, CLEAN_ESCAPE = 0.5, 0.5, 0.1
GRADE_BONUS = {"decisive": 50, "repelled": 30, "pyrrhic": 0, "unresolved": 0, "defeat": -50}
WEIGHTS = {"enemy_neutralized_frac": 150, "death": -100, "downed_at_end": -5,
           "hp_lost_pct_per_pawn": -1, "new_permanent_per_pawn": -50}


def standing(m):
    n = max(1, m["squad_size"])
    return (n - m["deaths"] - m["downed_at_end"]) / n


def broken(m):
    return (m["enemies_killed"] + m["enemies_killed_inferred"] + m["enemies_downed_end"]) / max(
        1, m["enemies_seen"])


def grade(m):
    """decisive / repelled / pyrrhic / unresolved / defeat. v2 (rca): a clean
    sweep at the cost of half the squad or more is pyrrhic, not decisive."""
    if "enemies_escaped" not in m:                          # pre-tracker rows
        return "decisive" if m.get("win") else "defeat"
    n = max(1, m["squad_size"])
    if m["squad_kidnapped"] or m["deaths"] + m["downed_at_end"] >= n:
        return "defeat"
    if m.get("raid_satisfied_tick") is not None:            # they left because they won
        return "defeat"
    if m["enemies_active_end"] > 0:
        return "unresolved"
    if m["enemies_escaped"] <= CLEAN_ESCAPE * max(1, m["enemies_seen"]):
        return "decisive" if standing(m) >= INTACT else "pyrrhic"
    if m.get("raid_fled_tick") is None and broken(m) < BROKE:   # no message: fallback
        return "defeat"
    return "repelled" if standing(m) >= INTACT else "pyrrhic"


def grade_v1(m):
    """The legacy grade (decisive ignored our losses), kept to compare rankings."""
    if "enemies_escaped" not in m:
        return "decisive" if m.get("win") else "defeat"
    n = max(1, m["squad_size"])
    if m["squad_kidnapped"] or m["deaths"] + m["downed_at_end"] >= n:
        return "defeat"
    if m.get("raid_satisfied_tick") is not None:
        return "defeat"
    if m["enemies_active_end"] > 0:
        return "unresolved"
    if m["enemies_escaped"] <= CLEAN_ESCAPE * max(1, m["enemies_seen"]):
        return "decisive"
    if m.get("raid_fled_tick") is None and broken(m) < BROKE:
        return "defeat"
    return "repelled" if standing(m) >= INTACT else "pyrrhic"


def is_win(g):
    return g in ("decisive", "repelled")


def score_v1(m, grade_fn=grade_v1):
    """Legacy weighted score (1 death = -100 vs 150 for the whole raid)."""
    n = max(1, m["squad_size"])
    return round(GRADE_BONUS[grade_fn(m)]
                 + WEIGHTS["enemy_neutralized_frac"] * m["enemy_neutralized_frac"]
                 + WEIGHTS["death"] * m["deaths"]
                 + WEIGHTS["downed_at_end"] * m.get("downed_at_end", 0)
                 + WEIGHTS["hp_lost_pct_per_pawn"] * m.get("hp_lost_pct", 0) / n
                 + WEIGHTS["new_permanent_per_pawn"] * m.get("new_permanent_injuries", 0) / n, 2)


def manifest_mean_points(manifest):
    """Mean combat points per raider of a scenario: from the kinds in the
    manifest if all are known, else the spec's raid points / raiders."""
    from ..game.defs import combat_power
    enemy = manifest.get("enemy") or []
    pts = [combat_power(e.get("def")) for e in enemy]
    if enemy and all(p is not None for p in pts):
        return sum(pts) / len(pts)
    spec_points = (manifest.get("spec", {}).get("enemy") or {}).get("points")
    return spec_points / len(enemy) if enemy and spec_points else None


def enemy_lost_count(m):
    if "enemies_killed" in m:
        return m["enemies_killed"] + m["enemies_killed_inferred"] + m["enemies_downed_end"]
    return round(m.get("enemy_neutralized_frac", 0) * m.get("enemies_seen", 0))


def trade(m, mean_points=None, colonist_enemies=COLONIST_ENEMIES):
    """{enemy_lost_points, our_lost_points, ler, ler_basis}. mean_points: mean
    combat points per raider of the scenario, for rows without per-raider points."""
    if m.get("enemy_lost_points") is not None and m.get("enemy_seen_points"):
        lost = m["enemy_lost_points"]
        mean = m["enemy_seen_points"] / max(1, m["enemies_seen"])
        basis = "points"
    else:
        mean = mean_points or 1.0
        lost = enemy_lost_count(m) * mean
        basis = "count" if not mean_points else "count_x_mean"
    ours = m["deaths"] * colonist_enemies * mean
    if ours:
        ler = lost / ours
    else:
        ler = math.inf if lost else None
    return {"enemy_lost_points": round(lost, 1), "our_lost_points": round(ours, 1),
            "ler": ler, "ler_basis": basis}


def ler_key(t):
    """Ordering for superiority: LER first (undefined = even), then points taken."""
    return (1.0 if t["ler"] is None else t["ler"], t["enemy_lost_points"])


def pooled_ler(trades):
    """Cell summary: total enemy points lost / total ours (inf if we lost none)."""
    e = sum(t["enemy_lost_points"] for t in trades)
    o = sum(t["our_lost_points"] for t in trades)
    return e / o if o else (math.inf if e else None)


def fmt_ler(x):
    return "-" if x is None else "inf" if x == math.inf else f"{x:.2f}"


def json_ler(x):
    """JSON has no inf: store clean trades as the string 'inf'."""
    return "inf" if x == math.inf else (None if x is None else round(x, 3))
