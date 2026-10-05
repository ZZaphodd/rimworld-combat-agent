"""Case library index and lookup (results/cases/), so a new battle finds its closest past
battles without reading the whole library.

  python3 tools/cases.py index                 # results/cases/index.json from the cards + manifests
  python3 tools/cases.py similar rand_131      # closest cards to a problem (features + tags)
  python3 tools/cases.py tags                  # tag -> cards, like a blog's tag pages

`similar` scores every card against the problem's manifest: same raid / our faction and arena,
overlap of the tags computable from manifests (`auto_tags`), and distance between the weapon-class
mixes, melee / outrange / explosive shares and the count ratio. It prints the top cards with their
tags and results; read those cards (and their journals' scenes) to write the start sheet.
"""
import argparse
import json
import math
import re
import sys

import _path  # noqa: F401
from rca import ROOT

CASES = ROOT / "results/cases"
INDEX = CASES / "index.json"
SCEN = ROOT / "scenarios_rand"
CLASSES = ("melee", "bow", "thrown", "short", "medium", "long", "support", "explosive", "other")
THROWN = ("grenade", "molotov")
STRONG_1V1 = ("Neanderthal", "Empire")          # raids whose pawns won one-on-one melee in the cards


def manifest(pid):
    p = SCEN / f"scenario_{pid}.json"
    return json.loads(p.read_text()) if p.exists() else None


def shares(classes, n):
    return {c: (classes or {}).get(c, 0) / n for c in CLASSES} if n else {c: 0 for c in CLASSES}


def auto_tags(m):
    """The situation tags (tags.md) that a manifest alone decides."""
    f, sp = m["briefing"]["features"], m["spec"]
    t = {"open-arena" if "open" in sp["arena"] else "forest-arena"}
    if (f.get("distance") or 0) >= 120:
        t.add("raid-far")
    if (f.get("enemy_melee_share") or 0) >= 0.4:
        t.add("raid-melee")
    if sum(1 for e in m["enemy"] if any(k in (e.get("weapon") or "").lower() for k in THROWN)) >= 2:
        t.add("raid-throwers")
    if (f.get("enemy_outrange_share") or 0) >= 0.5:
        t.add("raid-outranges")
    if sp["enemy"]["faction"].startswith("Empire"):
        t.add("raid-armoured")
    if any(k in sp["enemy"]["faction"] for k in STRONG_1V1):
        t.add("raid-strong-1v1")
    cr = f.get("count_ratio") or 1
    if cr <= 0.9:
        t.add("raid-outnumbers")
    if cr >= 1.3:
        t.add("us-outnumber")
    sq = shares(f.get("squad_classes"), f.get("squad_n"))
    if sq["bow"] >= 0.5:
        t.add("us-bows")
    if (f.get("squad_range_median") or 99) <= 18 and sq["melee"] < 0.5:
        t.add("us-short")
    if sq["melee"] >= 0.5:
        t.add("us-melee-pawns")
    if sq["explosive"] >= 0.5:
        t.add("us-throwers")
    if f.get("mech"):
        t.add("raid-mech")
    return t


def parse_card(path):
    s = path.read_text()
    tags = lambda label: re.findall(r"`([a-z0-9-]+)`", (re.search(rf"\*\*{label}:\*\*(.*)", s) or [None, ""])[1])
    rows = []
    sec = s.split("## Plays and results", 1)[1].split("\n## ", 1)[0] if "## Plays and results" in s else ""
    for line in sec.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 6 and c[0] not in ("who", "---") and not set(c[0]) <= {"-"}:
            rows.append({"who": c[0], "play": c[1], "result": c[3], "lost": c[4], "badness": c[-1]})
    return {"title": s.splitlines()[0].lstrip("# ").strip(), "situation": tags("Situation"),
            "plays": tags("Plays seen"), "results": rows}


def site_names():
    names = re.findall(r"^\| \*\*([^*]+)\*\*", (CASES / "sites.md").read_text(), re.M)
    return [n for n in names if n]


def cmd_index(_):
    sites = site_names()
    out = []
    for p in sorted((CASES / "cards").glob("*.md")):
        pid = p.stem
        c = parse_card(p)
        m = manifest(pid)
        text = p.read_text().lower()
        c.update({"id": pid, "sites": [n for n in sites if n.lower() in text]})
        if m:
            f = m["briefing"]["features"]
            c.update({"arena": m["spec"]["arena"], "ours": m["spec"]["squad"]["faction"],
                      "raid": m["spec"]["enemy"]["faction"], "auto": sorted(auto_tags(m)),
                      "features": {k: f.get(k) for k in ("squad_n", "squad_classes", "enemy_n", "enemy_classes",
                                                         "enemy_melee_share", "enemy_outrange_share",
                                                         "enemy_explosive_share", "count_ratio", "distance",
                                                         "squad_range_median", "mech")}})
        out.append(c)
    INDEX.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"{INDEX.relative_to(ROOT)}: {len(out)} cards")


def score(q, c):
    """Higher = closer. q: a manifest; c: an index row."""
    if "features" not in c:
        return -99, {}
    qf, cf = q["briefing"]["features"], c["features"]
    parts = {
        "raid faction": 3.0 * (q["spec"]["enemy"]["faction"] == c["raid"]),
        "our faction": 2.0 * (q["spec"]["squad"]["faction"] == c["ours"]),
        "arena": 0.5 * (q["spec"]["arena"] == c["arena"]),
        "sides swapped": 2.0 * (q["spec"]["enemy"]["faction"] == c["ours"] and q["spec"]["squad"]["faction"] == c["raid"]),
    }
    qa, ca = auto_tags(q), set(c["auto"])
    parts["tags"] = 3.0 * len(qa & ca) / max(1, len(qa | ca))
    l1 = lambda a, b: sum(abs(a[k] - b[k]) for k in CLASSES)
    parts["our mix"] = -1.5 * l1(shares(qf.get("squad_classes"), qf.get("squad_n")),
                                 shares(cf.get("squad_classes"), cf.get("squad_n")))
    parts["raid mix"] = -1.5 * l1(shares(qf.get("enemy_classes"), qf.get("enemy_n")),
                                  shares(cf.get("enemy_classes"), cf.get("enemy_n")))
    parts["count"] = -1.0 * abs(math.log((qf.get("count_ratio") or 1) / (cf.get("count_ratio") or 1)))
    return round(sum(parts.values()), 2), {k: round(v, 2) for k, v in parts.items() if v}


def cmd_similar(a):
    q = manifest(a.pid)
    if not q:
        sys.exit(f"no manifest for {a.pid}")
    idx = json.loads(INDEX.read_text())
    ranked = sorted(((score(q, c), c) for c in idx if c["id"] != a.pid), key=lambda x: -x[0][0])
    f = q["briefing"]["features"]
    print(f"{a.pid}: {q['spec']['squad']['faction']} x{f.get('squad_n')} {f.get('squad_classes')} vs "
          f"{q['spec']['enemy']['faction']} x{f.get('enemy_n')} {f.get('enemy_classes')}, "
          f"{q['spec']['arena'].replace('arena_', '')}, ratio {f.get('count_ratio')}")
    print(f"auto tags: {' '.join(sorted(auto_tags(q)))}\n")
    for (s, parts), c in ranked[:a.top]:
        print(f"{s:6.2f} {c['id']}: {c['title']}")
        print(f"       tags {' '.join(c['situation'])} | plays {' '.join(c['plays'])} | sites {', '.join(c['sites']) or '-'}")
        for r in c["results"]:
            print(f"       {r['who'][:40]}: {r['result'][:50]} — {r['badness']}")
        print(f"       why: {parts}")
    shown = {c["id"] for _, c in ranked[:a.top]}
    also = [(c["id"], "same raid faction" if c.get("raid") == q["spec"]["enemy"]["faction"] else "sides swapped")
            for _, c in ranked[a.top:]
            if c.get("raid") == q["spec"]["enemy"]["faction"]
            or (c.get("ours") == q["spec"]["enemy"]["faction"] and c.get("raid") == q["spec"]["squad"]["faction"])]
    if also:
        print("also: " + ", ".join(f"{i} ({why})" for i, why in also if i not in shown))


def cmd_tags(_):
    idx = json.loads(INDEX.read_text())
    by = {}
    for c in idx:
        for t in c["situation"] + c["plays"]:
            by.setdefault(t, []).append(c["id"])
    for t in sorted(by):
        print(f"{t}: {' '.join(by[t])}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index").set_defaults(fn=cmd_index)
    s = sub.add_parser("similar")
    s.add_argument("pid")
    s.add_argument("--top", type=int, default=5)
    s.set_defaults(fn=cmd_similar)
    sub.add_parser("tags").set_defaults(fn=cmd_tags)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
