"""Markdown tables for the theme x doctrine matrix (results/theme.jsonl).

  python3 theme_analysis.py [results/theme.jsonl ...]   # several files are pooled

Rows carry agent_version (missing = before versioning); pooling two versions of
one doctrine in a cell is reported, never done silently.
"""
import json
import statistics
import sys
from pathlib import Path

from eval import canonical, grade, is_win, score, superiority

DOCTRINE = {"b1": "aggressive", "doctrine": "focus", "turtle": "turtle",
            "spread": "spread", "kite": "kite", "close": "close"}
REF = "b1"


def load(*paths):
    rows = [json.loads(l) for path in paths for l in Path(path).read_text().splitlines()
            if l.strip()]
    for r in rows:
        r["score"] = score(r)
        r["grade"], r["win"] = grade(r), is_win(r)   # stored 'win' predates grading
        r["agent"] = canonical(r["agent"])             # 'hold' rows read as 'turtle'
    by = {}
    for r in rows:
        by.setdefault((r["scenario"].removeprefix("theme_"), r["agent"]), []).append(r)
    for key, v in by.items():
        vers = {r.get("agent_version") for r in v}
        if len(vers) > 1:
            print(f"WARNING: {key} pools agent versions {sorted(vers, key=str)}")
    return by


def kpi_table(by):
    """Mean of each behaviour KPI per cell (rows without kpis are skipped)."""
    out = ["| theme | doctrine | v | n | KPIs (mean over runs) |", "|---|---|---|---|---|"]
    for (th, ag), v in sorted(by.items()):
        ks = [r["kpis"] for r in v if r.get("kpis")]
        if not ks:
            continue
        keys = sorted({k for d in ks for k in d if isinstance(d[k], (int, float))})
        means = {k: statistics.mean(d[k] for d in ks if k in d) for k in keys}
        vals = ", ".join(f"{k} {x:.0f}" if abs(x) >= 100 else f"{k} {x:.2f}"
                         for k, x in means.items())
        out.append(f"| {th} | {DOCTRINE.get(ag, ag)} | {v[0].get('agent_version')} | "
                   f"{len(ks)} | {vals} |")
    return "\n".join(out)


def table(by):
    themes = sorted({t for t, _ in by})
    out, best = [], {}
    for th in themes:
        refs = [r["score"] for r in by.get((th, REF), [])]
        out += [f"\n### {th}\n",
                "| doctrine | n | win | mean lost | enemy neutralized | median score | P(>aggressive) |",
                "|---|---|---|---|---|---|---|"]
        ranked = []
        for ag, doc in DOCTRINE.items():
            v = by.get((th, ag))
            if not v:
                continue
            sc = [r["score"] for r in v]
            p = superiority(sc, refs) if refs and ag != REF else None
            ranked.append((statistics.median(sc), statistics.mean(sc), doc, ag))
            out.append(f"| {doc} | {len(v)} | {sum(r['win'] for r in v)}/{len(v)} | "
                       f"{statistics.mean(r['deaths'] for r in v):.1f} | "
                       f"{100 * statistics.mean(r['enemy_neutralized_frac'] for r in v):.0f}% | "
                       f"{statistics.median(sc):.0f} | {'-' if p is None else f'{p:.2f}'} |")
        ranked.sort(reverse=True)
        best[th] = ranked
    return "\n".join(out), best


def pairwise(by, th, a, b):
    return superiority([r["score"] for r in by[(th, a)]], [r["score"] for r in by[(th, b)]])


if __name__ == "__main__":
    by = load(*(sys.argv[1:] or ["results/theme.jsonl"]))
    text, best = table(by)
    print(text)
    print("\n### ranking by median score (tie-break mean)")
    for th, ranked in best.items():
        top, bottom = ranked[0], ranked[-1]
        p = pairwise(by, th, top[3], bottom[3])
        print(f"- {th}: best {top[2]} ({top[0]:.0f}), worst {bottom[2]} ({bottom[0]:.0f}); "
              f"P(best>worst)={p:.2f}; order: " + " > ".join(d for _, _, d, _ in ranked))
    print("\n### overall (mean P(>aggressive) over themes, mean score)")
    themes = sorted({t for t, _ in by})
    for ag, doc in DOCTRINE.items():
        ps = [pairwise(by, th, ag, REF) for th in themes if (th, ag) in by and (th, REF) in by]
        allv = [r for th in themes for r in by.get((th, ag), [])]
        if allv:
            print(f"- {doc}: P>aggr {statistics.mean(ps) if ps else float('nan'):.2f}, mean score "
                  f"{statistics.mean(r['score'] for r in allv):.0f}, "
                  f"win {sum(r['win'] for r in allv)}/{len(allv)}, "
                  f"lost/battle {statistics.mean(r['deaths'] for r in allv):.2f}, "
                  f"agent errors {sum(r['agent_errors'] for r in allv)}")
    if any(r.get("kpis") for v in by.values() for r in v):
        print("\n### behaviour KPIs\n")
        print(kpi_table(by))
