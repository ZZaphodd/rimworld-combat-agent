"""Labelled frames and route maps for the three human battles watched before traces existed.

Source: results/human/raw/<id>/*.output (watcher records: tick, rect, screenshot, positions)
and overview_shots.json (full-map screenshots for the route maps). Writes
results/human/reports/img/<id>_*.jpg and prints the frame table. The screenshots themselves
stay in RimWorld's RimMoltScreenshots folder (~ paths), so this reruns only on that machine.

  python3 results/human/raw/build_reports.py [rand_030 ...]
"""
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from rca.eval import frames  # noqa: E402

RAW, IMG = ROOT / "results/human/raw", ROOT / "results/human/reports/img"
T0 = 383            # ticksGame right after loading a night-run scenario save
OVERVIEW = json.load(open(Path(__file__).parent / "overview_shots.json"))


def parse(path):
    f = {"file": path.name}
    for line in path.read_text().splitlines():
        s = line.strip()
        if m := re.search(r"\| tick (\d+) \|", s):
            f["tick"] = int(m[1])
        elif s.startswith("rect "):
            f["rect"] = frames.parse_rect(s)
        elif s.endswith(".png"):
            f["png"] = s
        elif s.startswith("[('"):
            f["ours"] = [(t[0], t[1], t[2], len(t) > 3 and t[3] == "D")
                         for t in ast.literal_eval(s)]
        elif s.startswith(("enemies: [", "jobs: [")):
            them = ast.literal_eval(s.split(": ", 1)[1])
            f["them"] = [(t[0], t[1], t[2], len(t) > 4 and t[3] == "D")
                         for t in them if len(t) >= 4 and isinstance(t[1], int)]
        elif m := re.match(r"^(\S+) (\d+) (\d+)\s+(?:\[|drafted)", s):   # 'Butters 128 125  [...]'
            f.setdefault("ours_alt", []).append((m[1], int(m[2]), int(m[3]), False))
    if "ours" not in f and "ours_alt" in f:
        f["ours"] = f["ours_alt"]
    return f


def load(bid, since=""):
    fs = [parse(p) for p in sorted((RAW / bid).iterdir()) if p.name >= since]
    return {f["tick"]: f for f in fs if "tick" in f and "png" in f}


def pawns(f):
    return ([{"n": n, "x": x, "z": z, "side": "ours", "d": d} for n, x, z, d in f.get("ours", [])]
            + [{"n": n, "x": x, "z": z, "side": "them", "d": d} for n, x, z, d in f.get("them", [])])


def centre(ps):
    ps = [(x, z) for _, x, z, d in ps if not d]
    return (round(sum(x for x, _ in ps) / len(ps)), round(sum(z for _, z in ps) / len(ps))) if ps else None


def add(path, c, label):
    """Append a route point, merging it into the previous one when they nearly overlap."""
    x, z, prev = path[-1]
    if abs(c[0] - x) + abs(c[1] - z) <= 4:
        path[-1] = (x, z, f"{prev},{label}")
    else:
        path.append((*c, label))


def build(bid, picks, notes=(), since="", gamma=1.25):
    fr = load(bid, since)
    man = json.load(open(ROOT / f"scenarios_rand/scenario_{bid}.json"))
    rows = []
    ours_path = [(*centre([(p["name"], p["x"], p["z"], False) for p in man["squad"]]), "S")]
    them_path = [(*centre([("e", e["x"], e["z"], False) for e in man["enemy"]]), "S")]
    for i, (tick, caption) in enumerate(picks, 1):
        f = fr[tick]
        t = tick - T0
        out = IMG / f"{bid}_{i}_t{t}.jpg"
        frames.annotate(Path(f["png"]).expanduser(), f["rect"], out, pawns(f), caption=f"{i}. t{t}  {caption}",
                        gamma=gamma)
        rows.append((i, t, out.name, caption))
        for path, side in ((ours_path, "ours"), (them_path, "them")):
            if c := centre(f.get(side, [])):
                add(path, c, i)
    png, rect = OVERVIEW[bid[-3:]]
    png = Path(png).expanduser()
    route = IMG / f"{bid}_route.jpg"
    frames.annotate(png, frames.parse_rect(rect), route, notes=notes,
                    paths=[("them", them_path, len(them_path) < 4), ("ours", ours_path)],
                    caption="route: squad centre (blue) and raid centre (red); S = start, "
                            "numbers = frames", gamma=1.8)
    print(f"== {bid}: {route.name}")
    for r in rows:
        print(r)


if __name__ == "__main__":
    which = sys.argv[1:] or ["rand_030", "rand_067", "rand_107"]
    if "rand_030" in which:
        build("rand_030", [
            (866, "weapon swap: guns to Pwuis and Butters, Bog and Polork fetch the frags"),
            (1364, "swap done; squad heads south-east, raid walks north along the lake"),
            (1873, "squad hides on the north face of the rock hill; raid column stretched"),
            (2438, "raid leaders reach the hill's north-west corner; Bog waits on the east flank"),
            (2989, "contact inside Trough's smoke, 1-15 cells; Mushinto already dead"),
            (4014, "Lang, Hawk, Grub dead, Manuel down; Roller (ours) dead"),
            (5551, "raid broke and fled at t3765; all 9 raiders out, 1 of ours lost"),
        ], notes=[(150, 40, "lake"), (102, 47, "ruin"), (178, 97, "rock hill"),
                  (128, 62, "rock")], since="053000")
    if "rand_067" in which:
        build("rand_067", [
            (837, "squad packs up and moves south-east to meet the raid"),
            (1505, "a drifter runs 40 cells ahead of the raid: picked off"),
            (2160, "kiting east; the boar and Kelerk catch up and melee"),
            (3134, "turned south near the east edge; raid strung out over 50 cells"),
            (3903, "melee brawl: Hadyott, Ryan, the boar and Kelerk all hitting ours"),
            (4683, "Toad, Stork and Val down in one spot; Hawke fights two"),
            (6603, "raid gives up and kidnaps: Duen takes Toad east, Kin'kovysh takes Mole"),
            (8194, "Kin'kovysh shot on the way south, Mole saved; Duen escapes with Toad"),
        ])
    if "rand_107" in which:
        build("rand_107", [
            (1076, "drafted; squad leaves the cleared ground for the forest edge"),
            (2296, "holding the forest edge; first frags land short"),
            (3101, "firefight at the edge, still no losses"),
            (4630, "Angus (Diatite) down alone on the east side"),
            (6008, "melee in the open: Yolanda down away from the group"),
            (7130, "kidnapping: Mushinto takes Mayumi (Thirock), Piglet goes for Yolanda"),
            (7722, "Pete down; both captives carried off"),
        ], notes=[(60, 230, "raid route not recorded (dashed)"), (100, 175, "cleared ground")])
