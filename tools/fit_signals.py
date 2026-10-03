"""Offline fit of the losing_trade signal and the spread splash precondition on
result rows (analysis only; results/baseline/calibration.md).

    python3 tools/fit_signals.py [results/baseline/core.jsonl]

losing_trade (rca/tactical/doctrine.py): fires at the first moment, after first
contact, when >= MIN_LOST squad pawns are gone and enemy points lost < R x
(pawns gone x colonist value). Rows from before the signal (baseline-v1) have
no trade curve, so it is reconstructed:
  * our losses: exact ticks, from the "Funeral opportunity for <name>" (dead)
    and "(*Name)<name>(/Name) kidnapped" messages (they match squad_dead and
    squad_kidnapped on all 420 baseline-v1 rows);
  * enemy points lost: unknown over time; two proxies bracket it:
      linear  final points spread evenly from first contact to the raid's end
              (fled / satisfied message, else the episode end);
      final   the final points from first contact on (enemy losses as early as
              possible: the fewest fires).
Rows that carry kpis.trade_curve (from the signal's introduction on) are
replayed exactly ("exact").
"bad" = grade defeat or pyrrhic (as in calibration.md). Lead = episode end -
fire tick, over bad battles.
"""
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import _path  # noqa: F401
from rca.eval.results import read_rows
from rca.eval.scoring import COLONIST_ENEMIES, grade
from rca.game.weapons import weapon_class

ROOT = Path(__file__).resolve().parent.parent
THEMES = ["mechs", "pirate_grenadier", "pirate_melee", "pirate_mixed", "pirate_sniper",
          "tribal_archers", "tribal_melee"]


def loss_ticks(r):
    return sorted(m["tick"] for m in r.get("game_messages") or []
                  if m["text"].startswith("Funeral opportunity for")
                  or (m["text"].startswith("(*Name)") and "kidnapped" in m["text"]))


def enemy_at(r, t, mode):
    fc, e = r.get("first_contact_tick"), r.get("enemy_lost_points") or 0
    if fc is None or t < fc:
        return 0
    if mode == "final":
        return e
    end = min([r["ticks"]] + [r[k] for k in ("raid_fled_tick", "raid_satisfied_tick") if r.get(k)])
    return e if end <= fc else e * min(1.0, (t - fc) / (end - fc))


def fire_tick(r, mode, min_lost, ratio):
    if mode == "exact":
        cv = None
        rule = r["kpis"].get("losing_trade_rule")
        sig = [s for s in r.get("signals") or [] if s["reason"] == "losing_trade"]
        if rule and rule["min_lost"] == min_lost and rule["ler"] == ratio:
            return sig[0]["tick"] if sig else None
        cv = COLONIST_ENEMIES * r["enemy_seen_points"] / max(1, r["enemies_seen"])
        for t, lost, e in r["kpis"]["trade_curve"]:
            if lost >= min_lost and e < ratio * lost * cv:
                return t
        return None
    cv = COLONIST_ENEMIES * (r.get("enemy_seen_points") or 0) / max(1, r["enemies_seen"])
    for i, t in enumerate(loss_ticks(r)):
        if i + 1 >= min_lost and enemy_at(r, t, mode) < ratio * (i + 1) * cv:
            return t
    return None


def fit_losing_trade(rows, modes):
    print("## losing_trade grid (bad = defeat or pyrrhic)\n")
    nbad = sum(grade(r) in ("defeat", "pyrrhic") for r in rows)
    print(f"{len(rows)} battles, {nbad} bad\n")
    print("| proxy | min_lost | LER < | fires | share bad among fires | share of bad caught "
          "| fires in good | median lead (ticks) |")
    print("|---|---|---|---|---|---|---|---|")
    for mode in modes:
        for ml in (1, 2, 3):
            for ratio in (0.5, 0.75, 1.0, 1.5):
                f = bf = gf = 0
                leads = []
                for r in rows:
                    t = fire_tick(r, mode, ml, ratio)
                    if t is None:
                        continue
                    bad = grade(r) in ("defeat", "pyrrhic")
                    f, bf, gf = f + 1, bf + bad, gf + (not bad)
                    if bad:
                        leads.append(r["ticks"] - t)
                lead = round(statistics.median(leads)) if leads else "-"
                print(f"| {mode} | {ml} | {ratio} | {f} | {bf / max(1, f):.2f} | "
                      f"{bf / max(1, nbad):.2f} | {gf} | {lead} |")
    print()


def overlap(rows, mode, min_lost=2, ratio=1.0):
    bad = [r for r in rows if grade(r) in ("defeat", "pyrrhic")]
    lt = {id(r) for r in bad if fire_tick(r, mode, min_lost, ratio) is not None}
    npg = {id(r) for r in bad if any(s["reason"] == "no_progress" for s in r.get("signals") or [])}
    print(f"bad battles caught ({mode}, min_lost {min_lost}, LER < {ratio}): losing_trade "
          f"{len(lt)}, no_progress {len(npg)}, both {len(lt & npg)}, either {len(lt | npg)} "
          f"of {len(bad)}\n")
    by = defaultdict(lambda: [0, 0, 0])
    for r in rows:
        t = fire_tick(r, mode, min_lost, ratio)
        b = by[r["agent"]]
        b[0] += t is not None
        b[1] += t is not None and grade(r) in ("defeat", "pyrrhic")
        b[2] += 1
    print("| agent | fires | of which bad | battles |\n|---|---|---|---|")
    for a, (f, bf, n) in sorted(by.items()):
        print(f"| {a} | {f} | {bf} | {n} |")
    print()


def splash_shares():
    import json
    print("## enemy_splash_heavy: share of raiders with census class 'explosive'\n")
    print("| theme | raiders | explosive | share |\n|---|---|---|---|")
    for t in THEMES:
        m = json.loads((ROOT / f"scenarios_out/scenario_theme_{t}.json").read_text())
        cls = [weapon_class(e.get("weapon") or "", e.get("def")) for e in m["enemy"]]
        n = sum(c == "explosive" for c in cls)
        print(f"| {t} | {len(cls)} | {n} | {n / len(cls):.3f} |")
    print()


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results/baseline/core.jsonl"
    rows = read_rows(path)
    # newest version per agent only (baseline-v1: doctrine v5, not v4)
    newest = {}
    for r in rows:
        newest[r["agent"]] = max(newest.get(r["agent"], 0), r["agent_version"])
    rows = [r for r in rows if r["agent_version"] == newest[r["agent"]]]
    exact = all("trade_curve" in (r.get("kpis") or {}) for r in rows)
    modes = ["exact"] if exact else ["linear", "final"]
    fit_losing_trade(rows, modes)
    for mode in modes:
        overlap(rows, mode)
    splash_shares()


if __name__ == "__main__":
    main()
