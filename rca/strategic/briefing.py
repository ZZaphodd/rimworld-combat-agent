"""What the router sees before it picks a doctrine (METT-T without the time):
both sides' composition and ranges from a problem manifest, plus each
doctrine's preconditions on the live map. Text for a reader, a dict for rows.

The router (a person or an LLM for now) reads this, picks a doctrine and its
options, and writes down why: those choices are the data for a rule-based
router later (TODO roadmap 6)."""
import math
import statistics
from collections import Counter

from ..eval.tracker import kind_points
from ..game.weapons import is_melee, weapon_range

CLOSERS = {"melee", "short", "thrown"}


def _centroid(ps):
    return (sum(p["x"] for p in ps) / len(ps), sum(p["z"] for p in ps) / len(ps))


def features(manifest):
    """Composition numbers from a manifest (offline, no game)."""
    sq, en = manifest["squad"], manifest["enemy"]
    sq_r = [weapon_range(p.get("weapon") or "", p.get("kind", "")) for p in sq]
    en_r = [weapon_range(e.get("weapon") or "", e.get("def", "")) for e in en]
    en_cls = Counter(e.get("class", "other") for e in en)
    sq_cls = Counter(p.get("class", "other") for p in sq)
    en_pts = sum(kind_points(e.get("def", "")) or 0 for e in en)
    sq_med = statistics.median(sq_r) if sq_r else 0
    n = max(1, len(en))
    return {
        "squad_n": len(sq), "squad_classes": dict(sq_cls),
        "squad_range_median": round(sq_med, 1), "squad_range_max": round(max(sq_r, default=0), 1),
        "squad_melee": sum(is_melee(p.get("weapon") or "", p.get("kind", "")) for p in sq),
        "enemy_n": len(en), "enemy_classes": dict(en_cls), "enemy_points": en_pts,
        "enemy_range_median": round(statistics.median(en_r), 1) if en_r else 0,
        "enemy_closer_share": round(sum(en_cls[c] for c in CLOSERS) / n, 2),
        "enemy_melee_share": round(en_cls["melee"] / n, 2),
        "enemy_explosive_share": round(en_cls["explosive"] / n, 2),
        "enemy_outrange_share": round(sum(r >= sq_med + 5 for r in en_r) / n, 2),
        "count_ratio": round(len(sq) / n, 2),
        "distance": round(math.dist(_centroid(sq), _centroid(en)), 1) if sq and en else None,
        "mech": manifest["spec"]["enemy"]["faction"] == "Mechanoid",
    }


def preconditions(rm, manifest, names=("doctrine", "turtle", "spread", "kite", "close")):
    """Each doctrine's precondition report on the loaded map ({name: {check: {ok, value}}})."""
    from ..tactical import make
    from ..tactical.preconditions import Context, check
    from ..terrain import Terrain
    terrain = Terrain(rm)
    sq, en = manifest["squad"], manifest["enemy"]
    squad = [{"pos": (p["x"], p["z"]), "range": weapon_range(p.get("weapon") or ""),
              "melee": is_melee(p.get("weapon") or "")} for p in sq]
    enemies = [{"pos": (e["x"], e["z"]), "cls": e.get("class", "other"),
                "range": weapon_range(e.get("weapon") or "", e.get("def", ""))} for e in en]
    ctx = Context(terrain, tuple(round(v) for v in _centroid(sq)), squad, enemies)
    out = {}
    for name in names:
        try:
            out[name] = check(make(name), ctx)
        except Exception as e:                      # a check must never stop the run
            out[name] = {"error": repr(e)[:80]}
    return out


def text(manifest, feats, pre=None):
    sp, ep = manifest["spec"]["squad"], manifest["spec"]["enemy"]
    lines = [f"{manifest['id']} on {manifest['spec']['arena']}: our {sp['faction']} x{feats['squad_n']} "
             f"vs {ep['faction']} x{feats['enemy_n']} ({feats['enemy_points']:.0f} kind pts), "
             f"{feats['distance']} cells apart"]
    lines.append("  ours:  " + ", ".join(
        f"{p['name'].split(' ')[0].strip(chr(39))}: {p.get('weapon') or '-'} [{p.get('class')}]"
        for p in manifest["squad"]))
    lines.append(f"         classes {feats['squad_classes']}, range median {feats['squad_range_median']}"
                 f" max {feats['squad_range_max']}, melee pawns {feats['squad_melee']}")
    lines.append("  enemy: " + ", ".join(
        f"{c}x{n}" for c, n in Counter(f"{e['def']}/{e.get('weapon') or '-'}"
                                        for e in manifest["enemy"]).most_common()))
    lines.append(f"         classes {feats['enemy_classes']}, range median {feats['enemy_range_median']},"
                 f" closers {feats['enemy_closer_share']}, melee {feats['enemy_melee_share']},"
                 f" explosive {feats['enemy_explosive_share']}, outrange us {feats['enemy_outrange_share']},"
                 f" count ratio {feats['count_ratio']}")
    for name, rep in (pre or {}).items():
        lines.append(f"  pre {name:8} " + ", ".join(
            f"{k}={v.get('value')}{'' if v.get('ok') in (True, None) else '(X)'}"
            for k, v in rep.items() if isinstance(v, dict)))
    return "\n".join(lines)
