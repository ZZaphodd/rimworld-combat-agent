"""Summary tables for a results file (recomputed from raw metrics).

  python3 tools/report.py results/rca.jsonl [--ref amove] [--colonist-enemies 4]
"""
import argparse
from pathlib import Path

import _path  # noqa: F401
from rca.eval import report, scoring
from rca.eval.harness import load_manifests
from rca.eval.results import read_rows
from rca import ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results", type=Path)
    ap.add_argument("--ref", default="amove")
    ap.add_argument("--colonist-enemies", type=float, default=scoring.COLONIST_ENEMIES)
    a = ap.parse_args()
    ids = [p.stem.removeprefix("scenario_") for p in sorted((ROOT / "scenarios_out").glob("*.json"))]
    mean = {m["id"]: scoring.manifest_mean_points(m) for m in load_manifests(ids)}
    rows = [r for r in read_rows(a.results) if "scenario" in r]
    print(report.render(report.summarize(rows, mean, a.ref, a.colonist_enemies), a.results.name, a.ref))


if __name__ == "__main__":
    main()
