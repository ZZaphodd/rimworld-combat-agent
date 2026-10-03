"""Tables for results/threatmap_report.md: reflex v2 vs v3 per doctrine x scenario.

  python3 threatmap_analysis.py [results/threatmap_check.jsonl]
"""
import json
import sys
from collections import defaultdict

from eval import canonical, is_win

NAMES = {"b1": "aggressive", "turtle": "turtle", "spread": "spread"}
REV = {("b1", 3): "v3a", ("spread", 3): "v3a", ("turtle", 6): "v3a",
       ("b1", 4): "v3b", ("spread", 4): "v3b", ("turtle", 7): "v3b"}


def main(path="results/threatmap_check.jsonl"):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    by = defaultdict(list)
    for r in rows:
        by[(r["scenario"].replace("theme_", ""), canonical(r["agent"]), r["reflex_version"],
            r["agent_version"])].append(r)

    def s(v, k):
        return sum((r.get("kpis") or {}).get(k, 0) or 0 for r in v)

    print("| scenario | doctrine | rx (agent v) | n | wins | lost/ep | hp lost/ep | returns to danger/ep "
          "(fled + known entries) | raw high entries/ep | time in high threat | moves/ep (reflex / map / nudge) "
          "| Auto attack : map steps | frags in blast / escaped / stayed | frag hit entries | ticks/ep | wall s/ep |")
    print("|" + "---|" * 16)
    for key in sorted(by):
        sc, ag, rv, av = key
        v = by[key]
        n = len(v)
        wins = sum(is_win(r) for r in v)
        lost = sum(r["deaths"] for r in v) / n
        hp = sum(r["hp_lost_pct"] for r in v) / n
        ret = s(v, "tm_returns_to_danger") / n
        fled, known = s(v, "tm_returns_fled") / n, s(v, "tm_entries_known") / n
        raw = s(v, "tm_entries_high") / n
        high = s(v, "tm_high_pawn_ticks") / max(1, s(v, "tm_pawn_ticks"))
        mv, mm, nu = s(v, "rx_moves") / n, s(v, "rx_map_moves") / n, s(v, "rx_nudges") / n
        au, mp = s(v, "steps_auto"), s(v, "steps_map")
        ib, es, st = s(v, "rx_in_blast_at_landing"), s(v, "rx_escaped"), s(v, "rx_stayed_in_blast")
        hits = s(v, "rx_frag_hit_entries")
        ticks = sum(r["ticks"] for r in v) / n
        wall = sum(r["wall_s"] for r in v) / n
        print(f"| {sc} | {NAMES.get(ag, ag)} | {REV.get((ag, av), f"v{rv}")} ({av}) | {n} | {wins} | {lost:.1f} | "
              f"{hp:.0f} | {ret:.1f} ({fled:.1f} + {known:.1f}) | {raw:.1f} | {100 * high:.1f}% | "
              f"{mv + mm + nu:.0f} ({mv:.0f} / {mm:.0f} / {nu:.0f}) | {au}:{mp} | {ib} / {es} / {st} | "
              f"{hits} | {ticks:.0f} | {wall:.0f} |")

    print("\ncompute per step (map update + queries), per configuration:")
    for key in sorted(by):
        v = by[key]
        st = s(v, "tm_steps")
        ms = sum((r.get("kpis") or {}).get("tm_ms_per_step", 0) * (r.get("kpis") or {}).get("tm_steps", 0)
                 for r in v) / max(1, st)
        cells = sum((r.get("kpis") or {}).get("tm_cells_per_step", 0) * (r.get("kpis") or {}).get("tm_steps", 0)
                    for r in v) / max(1, st)
        mx = max((r.get("kpis") or {}).get("tm_max_ms", 0) for r in v)
        think = sum(r["agent_think_s"] for r in v) / max(1, sum(r["steps"] for r in v)) * 1000
        wall = sum(r["wall_s"] for r in v) / max(1, sum(r["steps"] for r in v)) * 1000
        print(f"  {key}: map {ms:.0f} ms/step (max {mx:.0f}), {cells:.0f} cells/step; "
              f"agent think {think:.0f} ms/step, wall {wall:.0f} ms/step, steps {st}")

    print("\nreturns to danger per 1000 pawn-ticks, and who positioned the pawn on the step before "
          "a return (sums; attribution exists only in rows written after it was added):")
    for key in sorted(by):
        v = by[key]
        rate = 1000 * s(v, "tm_returns_to_danger") / max(1, s(v, "tm_pawn_ticks"))
        att = {m: s(v, f"rx_returns_{m}") for m in ("auto", "map", "reflex", "other")}
        print(f"  {key}: {rate:.2f} /1000 pawn-ticks; by mode {att}")

    print("\nreflex v3 move kinds / fallbacks (sums):")
    for key in sorted(by):
        if key[2] != 3:
            continue
        v = by[key]
        print(f"  {key}: " + " ".join(f"{k[3:]}={s(v, k)}" for k in (
            "rx_moves_frag", "rx_moves_throw", "rx_moves_fire", "rx_moves_rocket", "rx_stays",
            "rx_too_late", "rx_trapped", "rx_fire_at", "rx_fallback_kill", "rx_fallback_back",
            "rx_fallback_none", "rx_reslots", "rx_forbidden_cells", "rx_ignored_viscous")))


if __name__ == "__main__":
    main(*sys.argv[1:])
