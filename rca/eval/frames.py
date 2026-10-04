"""Labelled battle frames for reports: a RimMolt offscreen screenshot plus who stood where.

annotate() draws our pawns (blue), enemies (red; downed ones dashed) and map notes
(yellow) over a screenshot, adds a caption bar and writes a JPEG. The screenshot covers
cells x0..x1, z0..z1 (the watcher prints 'rect x171-211 z91-127'), north up, so cell
(x, z) is at pixel ((x - x0 + .5) * ppc, (z1 - z - .5) * ppc).

Rasterising uses macOS Quick Look (qlmanage) and ffmpeg; without them the SVG is kept.
"""
import base64
import re
import shutil
import subprocess
import tempfile
from html import escape
from pathlib import Path

BAR = 58
OURS, THEM, NOTE = "#3b9cff", "#ff4d4d", "#ffd84d"


def parse_rect(text):
    """'rect x171-211 z91-127' -> (171, 211, 91, 127)."""
    m = re.search(r"x(\d+)-(\d+) z(\d+)-(\d+)", text)
    return tuple(int(v) for v in m.groups())


def image_size(path):
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
                         capture_output=True, text=True).stdout
    return int(re.search(r"pixelWidth: (\d+)", out)[1]), int(re.search(r"pixelHeight: (\d+)", out)[1])


def cell_px(x, z, rect, ppc):
    x0, _, _, z1 = rect
    return (x - x0 + 0.5) * ppc, (z1 - z - 0.5) * ppc


def _text(x, y, s, size, fill, anchor="middle"):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" text-anchor="{anchor}" '
            f'fill="{fill}" stroke="#000" stroke-width="3" paint-order="stroke">{escape(s)}</text>')


def svg(jpeg_b64, size, rect, pawns=(), notes=(), caption="", paths=()):
    """pawns: dicts {n, x, z, side: 'ours'|'them', d: downed}; notes: (x, z, text);
    paths: (side, [(x, z, label)][, dashed]) drawn as a line with labelled dots (route
    maps); dashed marks a route that was not observed in between."""
    w, h = size
    ppc = w / (rect[1] - rect[0])
    r, fs = max(5.0, ppc * 0.55), 11 if ppc >= 12 else 10
    # Quick Look scales a drawing to fill the thumbnail's width, so the canvas is never
    # narrower than it is tall; annotate() crops the padding on the right away again.
    cw = max(w, h + BAR)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{cw}" height="{h + BAR}" '
           f'viewBox="0 0 {cw} {h + BAR}" font-family="Helvetica, Arial, sans-serif" '
           f'font-weight="bold">',
           f'<rect width="{cw}" height="{h + BAR}" fill="#151515"/>',
           f'<image href="data:image/jpeg;base64,{jpeg_b64}" width="{w}" height="{h}"/>']
    for side, pts, *dashed in paths:
        color = OURS if side == "ours" else THEM
        xy = [cell_px(x, z, rect, ppc) for x, z, _ in pts]
        dash = ' stroke-dasharray="8,6"' if dashed and dashed[0] else ""
        out.append(f'<polyline points="{" ".join(f"{a:.0f},{b:.0f}" for a, b in xy)}" '
                   f'fill="none" stroke="{color}" stroke-width="3" stroke-opacity=".85"{dash}/>')
        for (px, py), (_, _, label) in zip(xy, pts):
            half = max(9, 3.3 * len(str(label)) + 3)          # a pill wide enough for "5,6,7"
            out.append(f'<rect x="{px - half:.0f}" y="{py - 9:.0f}" width="{2 * half:.0f}" '
                       f'height="18" rx="9" fill="{color}" stroke="#000" stroke-width="1.5"/>')
            if label:
                out.append(f'<text x="{px:.0f}" y="{py + 4:.0f}" font-size="11" '
                           f'text-anchor="middle" fill="#000">{escape(str(label))}</text>')
    for p in pawns:
        px, py = cell_px(p["x"], p["z"], rect, ppc)
        if not (0 <= px <= w and 0 <= py <= h):
            continue
        color = OURS if p["side"] == "ours" else THEM
        dash = ' stroke-dasharray="3,2"' if p.get("d") else ""
        out.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{r:.0f}" fill="none" '
                   f'stroke="{color}" stroke-width="2.5"{dash}/>')
        label = p["n"] + (" (down)" if p.get("d") else "")
        ly = py - r - 3 if p["side"] == "ours" else py + r + fs
        out.append(_text(px, ly, label, fs, "#fff" if p["side"] == "ours" else "#ffd6d6"))
    for x, z, s in notes:
        px, py = cell_px(x, z, rect, ppc)
        out.append(_text(px, py, s, 14, NOTE))
    out.append(_text(10, h + 23, caption, 14, "#fff", anchor="start"))
    legend = [("ours", OURS, ""), ("enemy", THEM, ""), ("downed", "#aaa", ' stroke-dasharray="3,2"')]
    lx = 16
    for name, color, dash in legend:
        out.append(f'<circle cx="{lx}" cy="{h + 43}" r="5" fill="none" stroke="{color}" '
                   f'stroke-width="2"{dash}/>')
        out.append(_text(lx + 9, h + 47, name, 11, "#bbb", anchor="start"))
        lx += 70
    out.append("</svg>")
    return "\n".join(out)


def annotate(png, rect, out, pawns=(), notes=(), caption="", paths=(), gamma=None, quality=4):
    """Writes out (.jpg) and returns its path; falls back to out with .svg.
    gamma (e.g. 1.6) brightens a night screenshot before the labels go on."""
    png, out = Path(png), Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    w, h = image_size(png)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        jpg = tmp / "frame.jpg"
        if gamma and shutil.which("ffmpeg"):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(png), "-vf",
                            f"eq=gamma={gamma}", "-q:v", "3", str(jpg)], check=True)
        else:
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "70",
                            str(png), "--out", str(jpg)], capture_output=True, check=True)
        doc = svg(base64.b64encode(jpg.read_bytes()).decode(), (w, h), rect, pawns, notes,
                  caption, paths)
        src = tmp / "frame.svg"
        src.write_text(doc)
        if not (shutil.which("qlmanage") and shutil.which("ffmpeg")):
            fallback = out.with_suffix(".svg")
            fallback.write_text(doc)
            return fallback
        side = max(w, h + BAR)                    # Quick Look renders a square, drawing top-left
        subprocess.run(["qlmanage", "-t", "-s", str(side), "-o", str(tmp), str(src)],
                       capture_output=True, check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp / "frame.svg.png"),
                        "-vf", f"crop={w}:{h + BAR}:0:0", "-q:v", str(quality), str(out)],
                       check=True)
    return out
