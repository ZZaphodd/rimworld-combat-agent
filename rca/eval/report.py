"""Summaries from result rows (EVAL_SPEC §7). Never pools configs (cycle, reflex
and its version) or agent versions in one cell; every agent is compared with
amove under the same config. Everything is recomputed from raw metrics.

Per cell: grade counts, colonists lost per battle, pooled and median LER,
P(LER > amove), and the legacy score for comparison.
"""
import json
import math
import statistics
from collections import Counter, defaultdict

from . import scoring
from .results import config_label, row_config

GRADES = ("decisive", "repelled", "pyrrhic", "unresolved", "defeat")


def superiority(xs, ys):
    """P(a random run from xs beats one from ys); ties count half."""
    if not xs or not ys:
        return None
    return sum((x > y) + 0.5 * (x == y) for x in xs for y in ys) / (len(xs) * len(ys))


def enrich(r, mean_points, colonist_enemies=scoring.COLONIST_ENEMIES):
    """Recompute every verdict of a row (stored ones go stale)."""
    t = scoring.trade(r, mean_points, colonist_enemies)
    return {"grade": scoring.grade(r), "grade_v1": scoring.grade_v1(r),
            "score_v1": scoring.score_v1(r, scoring.grade_v1), "trade": t,
            "key": scoring.ler_key(t)}


def cells(rows, mean_points, colonist_enemies=scoring.COLONIST_ENEMIES):
    """{config label: {(scenario, agent label): [enriched rows]}}."""
    out = defaultdict(lambda: defaultdict(list))
    for r in rows:
        v = r.get("agent_version")
        label = r["agent"] + (f"@v{v}" if v is not None else "")
        e = enrich(r, mean_points.get(r["scenario"]), colonist_enemies)
        out[config_label(row_config(r))][(r["scenario"], label)].append({**r, **e})
    return out


def _ref(cell_map, scenario, ref):
    cand = [(len(v), k) for k, v in cell_map.items() if k[0] == scenario
            and k[1].split("@")[0] == ref]
    return cell_map[max(cand)[1]] if cand else None


def cell_stats(v, refs):
    trades = [x["trade"] for x in v]
    lers = [t["ler"] for t in trades if t["ler"] is not None]
    g = Counter(x["grade"] for x in v)
    return {
        "n": len(v), "grades": {k: g[k] for k in GRADES if g[k]},
        "win": sum(scoring.is_win(x["grade"]) for x in v) / len(v),
        "lost": statistics.mean(x["deaths"] for x in v),
        "enemy_pts": statistics.mean(t["enemy_lost_points"] for t in trades),
        "ler_pooled": scoring.pooled_ler(trades),
        "ler_median": statistics.median(lers) if lers else None,
        "p_ler": superiority([x["key"] for x in v], [x["key"] for x in refs]) if refs else None,
        "score_v1_median": statistics.median(x["score_v1"] for x in v),
        "p_score_v1": superiority([x["score_v1"] for x in v], [x["score_v1"] for x in refs])
        if refs else None,
        "basis": Counter(t["ler_basis"] for t in trades).most_common(1)[0][0],
    }


def summarize(rows, mean_points, ref="amove", colonist_enemies=scoring.COLONIST_ENEMIES):
    """-> {config: {"cells": {(scenario, agent): stats}, "headline": {agent: ...},
    "ranking": {scenario: {"new": [...], "old": [...]}}}}"""
    out = {}
    for cfg, cm in cells(rows, mean_points, colonist_enemies).items():
        st = {}
        for (sc, ag), v in cm.items():
            refs = _ref(cm, sc, ref)
            st[(sc, ag)] = cell_stats(v, refs if refs is not v else None)
        head = {}
        for ag in sorted({a for _, a in cm}):
            mine = [(sc, s) for (sc, a), s in st.items() if a == ag]
            allv = [x for (sc, a), v in cm.items() if a == ag for x in v]
            ps = [s["p_ler"] for _, s in mine if s["p_ler"] is not None]
            p1 = [s["p_score_v1"] for _, s in mine if s["p_score_v1"] is not None]
            head[ag] = {"scenarios": len(mine), "n": len(allv),
                        "p_ler": statistics.mean(ps) if ps else None,
                        "p_score_v1": statistics.mean(p1) if p1 else None,
                        "ler_pooled": scoring.pooled_ler([x["trade"] for x in allv]),
                        "lost": statistics.mean(x["deaths"] for x in allv),
                        "win": sum(scoring.is_win(x["grade"]) for x in allv) / len(allv)}
        rank = {}
        for sc in sorted({s for s, _ in cm}):
            here = {a: s for (s2, a), s in st.items() if s2 == sc}
            rank[sc] = {
                "new": sorted(here, key=lambda a: (_num(here[a]["ler_pooled"]),
                                                   _num(here[a]["ler_median"])), reverse=True),
                "old": sorted(here, key=lambda a: here[a]["score_v1_median"], reverse=True)}
        out[cfg] = {"cells": st, "headline": head, "ranking": rank}
    return out


def _num(x):
    return -1.0 if x is None else x


def _p(x):
    return "-" if x is None else f"{x:.2f}"


def render(summary, title="", ref="amove"):
    """Markdown tables, one block per config."""
    L = [f"## {title}"] if title else []
    for cfg, s in summary.items():
        L += [f"\n### config `{cfg}`\n",
              f"| scenario | agent | n | grades D/R/P/U/X | lost/battle | enemy pts lost | "
              f"LER pooled | LER median | P(LER)>{ref} | score_v1 median | P(v1)>{ref} | basis |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for (sc, ag), c in sorted(s["cells"].items()):
            gr = "/".join(str(c["grades"].get(g, 0)) for g in GRADES)
            L.append(f"| {sc} | {ag} | {c['n']} | {gr} | {c['lost']:.2f} | {c['enemy_pts']:.0f} | "
                     f"{scoring.fmt_ler(c['ler_pooled'])} | {scoring.fmt_ler(c['ler_median'])} | "
                     f"{_p(c['p_ler'])} | {c['score_v1_median']:.1f} | {_p(c['p_score_v1'])} | "
                     f"{c['basis']} |")
        L += ["", f"Headline (mean of per-scenario P vs {ref}; pooled LER over all rows):", "",
              f"| agent | scenarios | n | P(LER)>{ref} | P(v1)>{ref} | LER pooled | lost/battle | win |",
              "|---|---|---|---|---|---|---|---|"]
        for ag, h in s["headline"].items():
            L.append(f"| {ag} | {h['scenarios']} | {h['n']} | {_p(h['p_ler'])} | "
                     f"{_p(h['p_score_v1'])} | {scoring.fmt_ler(h['ler_pooled'])} | "
                     f"{h['lost']:.2f} | {h['win']:.2f} |")
        if any(len(r["new"]) > 1 for r in s["ranking"].values()):
            L += ["", "Ranking per scenario (best first): new = pooled LER, old = median legacy "
                  "score", "", "| scenario | new (LER) | old (score_v1) | top changed |",
                  "|---|---|---|---|"]
            for sc, r in s["ranking"].items():
                if len(r["new"]) > 1:
                    L.append(f"| {sc} | {' > '.join(r['new'])} | {' > '.join(r['old'])} | "
                             f"{'yes' if r['new'][0] != r['old'][0] else 'no'} |")
    return "\n".join(L)


def to_json(summary):
    """JSON-able copy (tuple keys -> 'scenario|agent', inf -> 'inf')."""
    def fix(x):
        if isinstance(x, float) and math.isinf(x):
            return "inf"
        if isinstance(x, dict):
            return {("|".join(k) if isinstance(k, tuple) else k): fix(v) for k, v in x.items()}
        if isinstance(x, list):
            return [fix(v) for v in x]
        return x
    return json.loads(json.dumps(fix(summary)))
