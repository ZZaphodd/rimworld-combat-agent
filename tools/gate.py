"""Merge gate: no regression of a branch against the tagged baseline
(WORKFLOW.md "Merge gate"; the rule below is the one documented there).

    python3 tools/gate.py results/gate/<branch>.jsonl \
        [--baseline results/baseline/core.jsonl] [--agents amove,turtle] \
        [--base-version doctrine=5] [--branch-version doctrine=6]
    python3 tools/gate.py --simulate        # false-alarm rate and power on the baseline

Cells are agent x scenario. Each side uses one agent version: the highest in its
file unless given (baseline-v1 holds doctrine v4 and v5; v5 is the baseline),
only rows with the agent's natural options, and the branch's config (cycle,
reflex) on both sides.

Per battle:
  lost   colonists lost (dead + kidnapped); lower is better;
  trade  trade share = E / (E + O), E = enemy points lost, O = our points lost
         (lost x colonist value, EVAL_SPEC §6): 1 = clean, 0.5 = even, nothing
         lost on either side = 0.5. A bounded twin of the trade ratio
         (LER = trade / (1 - trade)), so a mean exists when LER = inf.
Worsening d per cell and metric: d_lost = mean(branch) - mean(baseline),
d_trade = mean(baseline) - mean(branch); d > 0 = the branch is worse.
Its uncertainty: percentile bootstrap, each side resampled on its own
(N_BOOT draws, fixed seed).

REGRESSION (either metric):
  cell   the 98% interval of d lies wholly above the margin
         (MARGIN: 0.5 colonists per battle, 0.10 trade share);
  agent  pooled over the agent's scenarios (d = mean of its cell d's;
         bootstrap draw = mean of the cells' draws, i.e. stratified), the 95%
         interval lies wholly above a quarter of the margin (0.125 colonists
         per battle, 0.025 trade share).
PASS = no cell regression, no agent regression and no incomplete cell (fewer
than MIN_N battles on a side). `watch` (shown, not a failure) = the cell's 90%
interval is above 0 and d > margin: a dip worth a look; ~2.6 of 42 cells by
chance on the baseline.
Why two levels and these widths (--simulate, A/A resampling of baseline-v1,
both samples of 10 drawn from the same cell): with 42 cells x 2 metrics a
looser per-cell rule fails an unchanged branch almost surely (90% interval
above 0 and d > margin: P(any cell) ~0.93). The cell rule (~0.05 for the suite)
catches a +1 colonist/battle regression in one cell ~70% of the time; the agent
rule (~0.10 for 6 agents) catches +0.5 colonists/battle across an agent's cells
~97%.
"""
import argparse
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import _path  # noqa: F401
from rca.eval import scoring
from rca.eval.results import config_label, read_rows, row_config, row_difficulty, row_options
from rca.tactical import options_of

ROOT = Path(__file__).resolve().parent.parent
METRICS = ("lost", "trade")
MARGIN = {"lost": 0.5, "trade": 0.10}
WORSE_SIGN = {"lost": 1, "trade": -1}
CELL_CONF, AGENT_CONF, WATCH_CONF = 0.98, 0.95, 0.90
AGENT_MARGIN_SHARE = 0.25
N_BOOT = 4000
MIN_N = 5
SEED = 20261004


def run_metrics(r):
    t = scoring.trade(r)
    e, o = t["enemy_lost_points"], t["our_lost_points"]
    return {"lost": r["deaths"], "trade": e / (e + o) if e + o else 0.5}


def boot_draws(base, branch, sign, n_boot=N_BOOT, rng=None):
    """n_boot bootstrap draws of d = sign x (mean(branch) - mean(base))."""
    rng = rng or random.Random(SEED)
    nb, nx = len(base), len(branch)
    return [sign * (sum(rng.choice(branch) for _ in range(nx)) / nx
                    - sum(rng.choice(base) for _ in range(nb)) / nb) for _ in range(n_boot)]


def lower(draws, conf):
    """Lower end of the central `conf` percentile interval."""
    s = sorted(draws)
    return s[int((1 - conf) / 2 * len(s))]


def upper(draws, conf):
    s = sorted(draws)
    return s[min(len(s) - 1, int((1 + conf) / 2 * len(s)))]


def judge_cell(base, branch, metric, rng=None, n_boot=N_BOOT):
    """-> {d, lo, hi, watch, regress, draws, base, branch} for one cell and
    metric (lists of per-battle values)."""
    s, m = WORSE_SIGN[metric], MARGIN[metric]
    d = s * (statistics.mean(branch) - statistics.mean(base))
    draws = boot_draws(base, branch, s, n_boot, rng)
    lo, hi = lower(draws, CELL_CONF), upper(draws, CELL_CONF)
    return {"d": d, "lo": lo, "hi": hi, "regress": lo > m,
            "watch": lower(draws, WATCH_CONF) > 0 and d > m, "draws": draws,
            "base": statistics.mean(base), "branch": statistics.mean(branch)}


def judge_agent(cell_results, metric):
    """Stratified pooling of one agent's cells for one metric."""
    d = statistics.mean(c["d"] for c in cell_results)
    n = min(len(c["draws"]) for c in cell_results)
    draws = [statistics.mean(c["draws"][i] for c in cell_results) for i in range(n)]
    lo, hi = lower(draws, AGENT_CONF), upper(draws, AGENT_CONF)
    return {"d": d, "lo": lo, "hi": hi, "regress": lo > AGENT_MARGIN_SHARE * MARGIN[metric]}


def select(rows, version=None, config=None):
    """{agent: rows}: one version per agent (highest unless given), the agent's
    natural options and, if given, one config."""
    by = defaultdict(list)
    for r in rows:
        if config is not None and row_config(r) != config:
            continue
        if row_options(r, options_of) != options_of(r["agent"]):
            continue
        by[r["agent"]].append(r)
    out = {}
    for a, rs in by.items():
        v = (version or {}).get(a) or max(r["agent_version"] for r in rs)
        out[a] = [r for r in rs if r["agent_version"] == v]
    return out


def compare(base_cells, branch_cells, rng=None, n_boot=N_BOOT):
    """base_cells / branch_cells: {(agent, scenario): [run_metrics dicts]}.
    -> (cells, agents, passed)."""
    rng = rng or random.Random(SEED)
    cells, per_agent, passed = [], defaultdict(list), True
    for key in sorted(set(base_cells) | set(branch_cells)):
        xb, xx = base_cells.get(key, []), branch_cells.get(key, [])
        c = {"agent": key[0], "scenario": key[1], "n_base": len(xb), "n_branch": len(xx)}
        if min(len(xb), len(xx)) < MIN_N:
            c["verdict"] = "INCOMPLETE"
            passed = False
        else:
            for m in METRICS:
                c[m] = judge_cell([x[m] for x in xb], [x[m] for x in xx], m, rng, n_boot)
            bad = [m for m in METRICS if c[m]["regress"]]
            watch = [m for m in METRICS if c[m]["watch"] and not c[m]["regress"]]
            c["verdict"] = ("REGRESS " + "+".join(bad) if bad
                            else "watch " + "+".join(watch) if watch else "ok")
            passed &= not bad
            per_agent[key[0]].append(c)
        cells.append(c)
    agents = {}
    for a, cs in sorted(per_agent.items()):
        agents[a] = {m: judge_agent([c[m] for c in cs], m) for m in METRICS}
        agents[a]["n_cells"] = len(cs)
        bad = [m for m in METRICS if agents[a][m]["regress"]]
        agents[a]["verdict"] = "REGRESS " + "+".join(bad) if bad else "ok"
        passed &= not bad
    return cells, agents, passed


def cells_of(selected):
    out = defaultdict(list)
    for a, rs in selected.items():
        for r in rs:
            out[(a, r["scenario"])].append(run_metrics(r))
    return out


def gate(base_rows, branch_rows, agents=None, base_version=None, branch_version=None):
    configs = {row_config(r) for r in branch_rows}
    if len(configs) != 1:
        raise SystemExit(f"branch rows mix configs: {configs}")
    config = configs.pop()
    diffs = {row_difficulty(r) for r in branch_rows}
    if len(diffs) != 1:
        raise SystemExit(f"branch rows mix difficulties: {diffs}")
    base_rows = [r for r in base_rows if row_difficulty(r) in diffs]   # none -> INCOMPLETE
    br = select(branch_rows, branch_version, config)
    ba = select(base_rows, base_version, config)
    keep = set(agents or br)
    versions = {a: (ba[a][0]["agent_version"] if ba.get(a) else None,
                    br[a][0]["agent_version"] if br.get(a) else None) for a in keep}
    bc = {k: v for k, v in cells_of(ba).items() if k[0] in keep}
    xc = {k: v for k, v in cells_of(br).items() if k[0] in keep}
    cells, agent_res, passed = compare(bc, xc)
    return cells, agent_res, passed, config, versions


def fmt(x):
    return (f"{x['base']:.2f} → {x['branch']:.2f} ({x['d']:+.2f}; "
            f"{x['lo']:+.2f}..{x['hi']:+.2f})")


def report(cells, agents, passed, versions):
    out = ["| agent | scenario | n base/branch | lost/battle base → branch (d; 98% CI) "
           "| trade share base → branch (d; 98% CI) | verdict |", "|---|---|---|---|---|---|"]
    for c in cells:
        vb, vx = versions.get(c["agent"], (None, None))
        head = f"| {c['agent']} v{vb}→v{vx} | {c['scenario']} | {c['n_base']}/{c['n_branch']} |"
        if "lost" not in c:
            out.append(f"{head} - | - | {c['verdict']} |")
        else:
            out.append(f"{head} {fmt(c['lost'])} | {fmt(c['trade'])} | {c['verdict']} |")
    out += ["", "| agent (pooled) | cells | d lost (95% CI) | d trade share (95% CI) | verdict |",
            "|---|---|---|---|---|"]
    for a, r in agents.items():
        cols = [f"{r[m]['d']:+.3f} ({r[m]['lo']:+.3f}..{r[m]['hi']:+.3f})" for m in METRICS]
        out.append(f"| {a} | {r['n_cells']} | {cols[0]} | {cols[1]} | {r['verdict']} |")
    v = Counter(c["verdict"].split()[0] for c in cells)
    reg_a = sum(r["verdict"] != "ok" for r in agents.values())
    out += ["", f"{len(cells)} cells: {v['ok']} ok, {v['watch']} watch, {v['REGRESS']} regress, "
            f"{v['INCOMPLETE']} incomplete; {len(agents)} agents: {reg_a} regress -> "
            f"**{'PASS' if passed else 'FAIL'}**"]
    return "\n".join(out)


def simulate(base_rows, trials=60, n_boot=1000, seed=1):
    """A/A false-alarm rate and power, by resampling the baseline cells: both
    samples of a cell are drawn (with replacement, n as in the cell) from its
    baseline battles; a regression adds +shift colonists lost to branch runs."""
    base = cells_of(select(base_rows))
    rng = random.Random(seed)
    # the one-cell regression goes to the cell with the median spread of losses
    one = sorted(base, key=lambda k: (statistics.pstdev(m["lost"] for m in base[k]), k))[
        len(base) // 2]
    scen = [("A/A (no change)", 0, None), ("+0.5 lost/battle, every cell", 0.5, None),
            (f"+1 lost/battle, one cell ({one[0]} {one[1]})", 1.0, one)]
    print("| scenario | P(cell rule fails) | P(agent rule fails) | P(FAIL) | mean watch cells |")
    print("|---|---|---|---|---|")
    for name, shift, only in scen:
        cf = af = ff = 0
        watch = 0
        for _ in range(trials):
            b, x = {}, {}
            for k, xs in base.items():
                b[k] = [rng.choice(xs) for _ in xs]
                hit = only is None or k == only
                x[k] = []
                for _ in xs:
                    m = dict(rng.choice(xs))
                    if hit and rng.random() < shift:
                        m["lost"] += 1
                    x[k].append(m)
            cells, agents, passed = compare(b, x, rng, n_boot)
            c = any(cc["verdict"].startswith("REGRESS") for cc in cells)
            a = any(r["verdict"] != "ok" for r in agents.values())
            cf, af, ff = cf + c, af + a, ff + (not passed)
            watch += sum(cc["verdict"].startswith("watch") for cc in cells)
        print(f"| {name} | {cf / trials:.2f} | {af / trials:.2f} | {ff / trials:.2f} | "
              f"{watch / trials:.1f} |")


def parse_versions(s):
    return {k: int(v) for k, v in (kv.split("=") for kv in (s or "").split(",") if kv)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("branch", nargs="?")
    ap.add_argument("--baseline", default=str(ROOT / "results/baseline_v2/core.jsonl"))
    ap.add_argument("--agents")
    ap.add_argument("--base-version", help="agent=version,... (default: highest)")
    ap.add_argument("--branch-version", help="agent=version,... (default: highest)")
    ap.add_argument("--simulate", action="store_true")
    a = ap.parse_args(argv)
    base_rows = read_rows(Path(a.baseline))
    if a.simulate:
        simulate(base_rows)
        return 0
    if not a.branch:
        ap.error("branch results file required")
    cells, agents, passed, config, versions = gate(
        base_rows, read_rows(Path(a.branch)), a.agents.split(",") if a.agents else None,
        parse_versions(a.base_version), parse_versions(a.branch_version))
    print(f"# Gate: {a.branch} vs {a.baseline} [{config_label(config)}]\n")
    print(f"Rule (WORKFLOW.md): a cell regresses if the {CELL_CONF:.0%} bootstrap interval of "
          f"its worsening lies above the margin (lost {MARGIN['lost']}/battle, trade share "
          f"{MARGIN['trade']}); an agent regresses if the {AGENT_CONF:.0%} interval of its "
          f"pooled worsening lies above {AGENT_MARGIN_SHARE} x margin. PASS = no regression, "
          f"no incomplete cell.\n")
    print(report(cells, agents, passed, versions))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
