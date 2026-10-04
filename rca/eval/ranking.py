"""How bad a battle went, for failure mining (TODO roadmap 3).

One number per row so problems can be sorted worst first. It counts what the
grade and the trade ratio miss: downed pawns at the end, total HP lost and new
permanent injuries (a human play round showed that cost hiding behind a
'repelled' grade). Weights are a first guess; the components are stored too.
"""
WEIGHTS = {"lost": 10.0, "downed": 3.0, "permanent": 2.0, "hp_per_25pct": 1.0}
GRADE_PENALTY = {"defeat": 10.0, "pyrrhic": 4.0, "unresolved": 3.0}


def lost(r):
    return (r.get("deaths") or 0) + (r.get("squad_kidnapped") or 0)


def badness(r):
    """(score, parts): higher = worse."""
    parts = {
        "lost": lost(r) * WEIGHTS["lost"],
        "downed": (r.get("downed_at_end") or 0) * WEIGHTS["downed"],
        "permanent": (r.get("new_permanent_injuries") or 0) * WEIGHTS["permanent"],
        "hp": (r.get("hp_lost_pct") or 0) / 25 * WEIGHTS["hp_per_25pct"],
        "grade": GRADE_PENALTY.get(r.get("grade"), 0.0),
    }
    return round(sum(parts.values()), 1), {k: round(v, 1) for k, v in parts.items()}


def worst(rows, top=100):
    """Rows sorted worst first (invalid rows are expected to be filtered by read_rows)."""
    return sorted(rows, key=lambda r: -badness(r)[0])[:top]
