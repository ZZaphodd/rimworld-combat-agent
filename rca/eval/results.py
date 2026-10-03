"""Result rows: schema, legacy defaults, canonical agent names, resume keys.

Every reader goes through read_rows(), which canonicalises agent names
(b1 -> amove, hold -> turtle) and fills legacy config defaults (DATA.md §5), so
a resume key, a summary cell and a rescore all agree on what a row is
(LESSONS bug 8: --resume --agents hold counted nothing because rows were keyed
by the canonical name and looked up by the alias).
"""
import json
import subprocess
from collections import Counter

from .. import ROOT

SCHEMA = 2           # 2 = rca rows (commit, enemy points, micro v4); legacy rows have none
ALIASES = {"b1": "amove", "aggressive": "amove", "hold": "turtle", "focus": "doctrine"}


def canonical(name):
    return ALIASES.get(name, name)


def row_config(r):
    """(cycle policy, reflex on, reflex version). Legacy: no cycle -> fixed:<step>,
    reflex off; reflex on without a version -> v1."""
    rx = bool(r.get("reflex"))
    return (r.get("cycle") or f"fixed:{r.get('step_ticks', 120)}", rx,
            r.get("reflex_version", 1) if rx else None)


def config_label(cfg):
    cyc, rx, rxv = cfg
    return f"{cyc}{f'+rx{rxv}' if rx else ''}"


def read_rows(path):
    rows = []
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            r["agent_raw"] = r["agent"]
            r["agent"] = canonical(r["agent"])
            rows.append(r)
    return rows


def row_options(r, natural_of=None):
    """A row's effective options. natural_of(agent) -> the doctrine's natural
    options: a key the row lacks (an option added after the row was written)
    reads as its natural value, which is what that agent version did then."""
    stored = r.get("options") or {}
    return {**natural_of(r["agent"]), **stored} if natural_of else dict(stored)


def done_counts(rows, version_of, config, options_of=None, natural_of=None):
    """Rows per (scenario, canonical agent) that count for --resume: same agent
    version (version_of(agent) for the current code), same config and, when
    options_of is given, the same tactical options (row_options; rows without
    any = {} or, with natural_of, the natural values)."""
    return Counter((r["scenario"], r["agent"]) for r in rows
                   if r.get("agent_version") == version_of(r["agent"])
                   and row_config(r) == config
                   and (options_of is None
                        or row_options(r, natural_of) == options_of(r["agent"])))


def git_commit():
    """HEAD hash, '+dirty' when rca/ has uncommitted changes (WORKFLOW traceability)."""
    try:
        h = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "rca"], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip()
        return h + ("+dirty" if dirty else "") if h else None
    except OSError:
        return None


def append_row(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
