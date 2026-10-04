"""Threat montage: one raid per (type, points) cell, laid out on the map in a
2D grid of walled pens so a person can look at raid sizes in game.

Columns (west -> east) = raid types, rows (south -> north) = raid points.
Each pen has a gold or silver tile floor in a checkerboard, so neighbours
always differ. Raiders stand in rows sorted by weapon class. Before building,
every cell is also sampled N times (spawn, record, destroy) for size stats:
one raid per cell is a single random draw.

Mechs come only through the faction route, whose pods take time to land; the
settle waits let raiders already on the map walk, so mech cells are placed
first and every pen is walled. Human raids spawn instantly (EdgeWalkIn) and
are placed with no time passing; a final pass re-places anyone off its slot.
"""
from ...eval.tracker import kind_points, short_name
from ...rimmolt import RimMoltError
from .. import session, weapons
from ..debug import Debug

TYPES = [("Pirate", "pirates"), ("OutlanderRough", "outlanders"), ("TribeRough", "tribe (fierce)"),
         ("Mechanoid", "mechanoids")]
POINTS = [100, 200, 300, 500, 700, 1000, 1500]
INNER_W, INNER_H, GAP = 14, 12, 2          # pen interior, ground between walls
PITCH_X, PITCH_Z = INNER_W + 2 + GAP, INNER_H + 2 + GAP
ORIGIN = (114, 94)                         # south-west wall corner of pen (0, 0)
CLASS_ORDER = ["melee", "short", "medium", "support", "long", "bow", "thrown", "explosive", "other"]
FLOORS = ("GoldTile", "SilverTile")
TRIES = 3                                  # raid generation fails now and then


def pen(col, row):
    """Wall rectangle (x0, z0, x1, z1) of a cell; the interior is one cell in."""
    x0, z0 = ORIGIN[0] + col * PITCH_X, ORIGIN[1] + row * PITCH_Z
    return x0, z0, x0 + INNER_W + 1, z0 + INNER_H + 1


def extent():
    x0, z0, _, _ = pen(0, 0)
    _, _, x1, z1 = pen(len(TYPES) - 1, len(POINTS) - 1)
    return x0, z0, x1, z1


def slots(col, row, n):
    """Rows of 7 cells, 2 apart, from the pen's north-west corner; denser
    (1 apart) if the raid doesn't fit."""
    x0, z0, x1, z1 = pen(col, row)
    step = 2 if n <= (INNER_W // 2) * (INNER_H // 2) else 1
    off, per_row = step - 1, INNER_W // step
    return [(x0 + 1 + off + c * step, z1 - 1 - off - r * step)
            for r, c in (divmod(i, per_row) for i in range(n))]


def legend(result):
    """Markdown: the grid as it lies on the map (north = largest raids on top)."""
    types, pts = result["types"], result["points"]
    by = {(c["col"], c["row"]): c for c in result["cells"]}
    lines = ["| points \\ type | " + " | ".join(types) + " |",
             "|---|" + "---|" * len(types)]
    for row in reversed(range(len(pts))):
        cells = []
        for col, (faction, _) in enumerate(TYPES):
            c = by.get((col, row))
            draws = [s["n"] for s in result["samples"].get(f"{faction}:{pts[row]}", [])]
            if not c or not c["n"]:
                cells.append("none" + (f" (draws {draws})" if draws else ""))
                continue
            cls = ", ".join(f"{k} {v}" for k, v in sorted(c["classes"].items(),
                                                           key=lambda kv: -kv[1]))
            cells.append(f"**{c['n']}** ({cls})" + (f"; draws {draws}" if draws else ""))
        lines.append(f"| {pts[row]} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def describe(rm, raiders):
    """[{id, name, kind, weapon, class, points}] sorted by class order, then kind."""
    out = []
    for t in raiders:
        p = rm.call("get_pawn", id=t["id"])
        kind = t.get("kind") or t.get("def", "")
        w = p.get("weapon") or ""
        out.append({"id": t["id"], "name": short_name(t.get("label", "")), "kind": kind,
                    "weapon": weapons.weapon_name(w), "class": weapons.weapon_class(w, kind),
                    "points": kind_points(kind, t.get("def", ""))})
    rank = {c: i for i, c in enumerate(CLASS_ORDER)}
    return sorted(out, key=lambda r: (rank.get(r["class"], 99), r["kind"], r["weapon"]))


def summary(pawns):
    classes = {}
    for p in pawns:
        classes[p["class"]] = classes.get(p["class"], 0) + 1
    return {"n": len(pawns), "classes": classes,
            "kind_points": sum(p["points"] or 0 for p in pawns)}


def spawn(d, faction, points):
    """New raiders of one raid, or [] if every try failed."""
    for _ in range(TRIES):
        try:
            if faction == "Mechanoid":
                return d.spawn_raid_by_faction(faction, points, max_steps=60)
            return d.spawn_raid(faction, points, instant=True)
        except RimMoltError as e:
            d.log(f"  {e}")
            d.close()
    return []


def sample(rm, d, n, log=print):
    """n raids per cell: spawn, describe, destroy. Returns {f"{faction}:{points}": [summary...]}."""
    out = {}
    for faction, _ in TYPES:
        for pts in POINTS:
            key = f"{faction}:{pts}"
            out[key] = []
            for i in range(n):
                raid = spawn(d, faction, pts)
                d.close()
                s = summary(describe(rm, raid)) if raid else {"n": 0, "failed": True}
                out[key].append(s)
                log(f"sample {key} #{i + 1}: {s}")
                d.run("Destroy non-colonists")
                d.close()
    return out


def build_pens(rm, d, log=print):
    x0, z0, x1, z1 = extent()
    d.clear_area(x0 - 2, z0 - 2, x1 + 2, z1 + 2)
    d.close()
    rm.call("dev_mode", devMode=True, godMode=True)
    for col in range(len(TYPES)):
        for row in range(len(POINTS)):
            a, b, c, e = pen(col, row)
            floor = rm.call("build", **{"def": FLOORS[(col + row) % 2], "minX": a + 1, "minZ": b + 1,
                                        "maxX": c - 1, "maxZ": e - 1, "fill": "filled"})
            wall = rm.call("build", **{"def": "Wall", "stuff": "BlocksGranite", "minX": a,
                                       "minZ": b, "maxX": c, "maxZ": e, "fill": "outline"})
            for what, r in (("floor", floor), ("wall", wall)):
                if r.get("rejected") or not r.get("ok", True):
                    log(f"pen {col},{row} {what}: {r.get('error') or r.get('reasons')}")
    rm.call("dev_mode", godMode=False)


def build(rm, n_samples=3, save_name="montage_threats", log=print):
    """Sample, build the pens, place one raid per cell, save. Expects a loaded,
    paused map with dev mode on and the observer far from the montage."""
    d = Debug(rm, log)
    samples = sample(rm, d, n_samples, log) if n_samples else {}
    build_pens(rm, d, log)
    cells, placed = [], {}
    order = sorted(((c, r) for c in range(len(TYPES)) for r in range(len(POINTS))),
                   key=lambda cr: TYPES[cr[0]][0] != "Mechanoid")          # mechs first
    for col, row in order:
        faction, label = TYPES[col]
        pts = POINTS[row]
        raid = spawn(d, faction, pts)
        d.close()
        pawns = describe(rm, raid)
        for p, s in zip(pawns, slots(col, row, len(pawns))):
            p["slot"] = s
            placed[p["id"]] = s
            d.teleport(p["id"], *s, rounds=3)
        d.close()
        x0, z0, x1, z1 = pen(col, row)
        cells.append({"type": label, "faction": faction, "points": pts, "col": col, "row": row,
                      "pen": [x0, z0, x1, z1], "floor": FLOORS[(col + row) % 2],
                      **summary(pawns), "pawns": pawns})
        log(f"cell {faction}:{pts} -> {len(pawns)} raiders in pen {x0},{z0}")
    off = [pid for pid, s in placed.items() if d.pos(pid) not in (tuple(s), None)]
    if off:
        log(f"re-placing {len(off)} raiders that moved")
        d.place({pid: placed[pid] for pid in off})
        d.close()
    rm.call("set_speed", action="pause")
    session.save(rm, save_name)
    log(f"saved {save_name}")
    return {"save": save_name, "types": [t[1] for t in TYPES], "points": POINTS,
            "origin": ORIGIN, "pitch": [PITCH_X, PITCH_Z], "inner": [INNER_W, INNER_H],
            "samples": samples, "cells": cells}
