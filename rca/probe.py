"""Compact text views of RimMolt replies for probing by hand (tools/rm.py).

Raw replies are token-heavy when read by a person or an LLM: get_status
carries the full list_colonists + get_alerts output under 'bundled' (6.3 of
7 KB with 14 colonists), labels carry <color> tags, and lists run long. These
functions keep what a probe needs, one line per thing. Nothing here is used
by agents or the harness (RIMMOLT_API.md)."""
import json
import re
import urllib.request

from .eval.tracker import short_name

NOISE = {"bundled", "statusBundle", "statusBundleHint", "_paused", "_dialogOpen", "hint",
         "tabsHint", "uiSelected", "rotationInt"}
COLOR = re.compile(r"</?color[^>]*>")
ID = re.compile(r"^[A-Za-z_]+\d+$")


def clean(s):
    return COLOR.sub("", s) if isinstance(s, str) else s


def trim(obj, max_list=20, max_str=300):
    """Drop noise keys and `loaded: true`, strip color tags, round floats to 3
    decimals, cut long lists and strings (the cut is marked)."""
    if isinstance(obj, dict):
        return {k: trim(v, max_list, max_str) for k, v in obj.items()
                if k not in NOISE and not (k == "loaded" and v is True)}
    if isinstance(obj, list):
        out = [trim(v, max_list, max_str) for v in obj[:max_list]]
        if len(obj) > max_list:
            out.append(f"...(+{len(obj) - max_list})")
        return out
    if isinstance(obj, str):
        s = clean(obj)
        return s if len(s) <= max_str else s[:max_str] + f"...(+{len(s) - max_str})"
    if isinstance(obj, float):
        return round(obj, 3)
    return obj


def generic(reply, **kw):
    """One line per top-level key, compact JSON values."""
    t = trim(reply, **kw)
    if not isinstance(t, dict):
        return json.dumps(t, ensure_ascii=False)
    return "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False, separators=(',', ':'))}"
                     for k, v in t.items())


def parse_kv(items):
    """['x=3', 'confirm=true', 'ids=a,b'] -> {'x': 3, 'confirm': True, 'ids': 'a,b'}."""
    out = {}
    for it in items:
        k, _, v = it.partition("=")
        if v.lower() in ("true", "false"):
            out[k] = v.lower() == "true"
            continue
        for conv in (int, float):
            try:
                out[k] = conv(v)
                break
            except ValueError:
                pass
        else:
            out[k] = json.loads(v) if v[:1] in "[{" else v
    return out


def pawn_ref(arg):
    """A pawn argument is an id (Human51228) or a name."""
    return {"id": arg} if ID.match(arg) else {"name": arg}


def status_line(s):
    maps = ", ".join(f"{m.get('mapIndex')}:{m.get('name')}" for m in s.get("maps", []))
    return (f"tick {s.get('ticksGame')} {'paused' if s.get('paused') else s.get('timeSpeed')}"
            f" | {s.get('difficulty')} ({s.get('storyteller')}) | colonists"
            f" {s.get('colonistCount')} | maps {maps} | bundle {s.get('statusBundle')}")


def pawn_line(t):
    flags = [f for f in ("drafted", "downed", "dead") if t.get(f)]
    who = short_name(t.get("label", "")) or t.get("def", "?")
    kind = t.get("kind") or t.get("def", "")
    line = f"{who:<14} {t.get('id', ''):<16} {kind:<22} {t.get('x')},{t.get('z')}"
    if "distance" in t:
        line += f" d={t['distance']:.1f}" if isinstance(t["distance"], (int, float)) else ""
    if flags:
        line += " " + " ".join(flags)
    if t.get("targeting"):
        line += f" -> {clean(t['targeting'])}"
    return line


def pawn_summary(p):
    if p.get("error"):
        return f"error: {p['error']}"
    flags = " ".join(f for f in ("downed", "dead") if p.get(f))
    return (f"{clean(p.get('name'))} {p.get('id')} {p.get('x')},{p.get('z')} hp {p.get('health')}%"
            f" mood {p.get('mood')} | {clean(p.get('weapon') or 'no weapon')} | {p.get('job')}"
            f" {flags}").rstrip()


def health_lines(h):
    low = [f"{c['capacity']} {c['percent']}%" for c in h.get("capacities", [])
           if c.get("percent", 100) < 100]
    out = [f"hp {h.get('overallHealthPercent')}% pain {h.get('painPercent')}% {h.get('state')}"
           + (f" | low: {', '.join(low)}" if low else "")]
    for d in h.get("hediffs", []):
        part = f" ({d['part']})" if d.get("part") else ""
        out.append(f"  {clean(d.get('label'))}{part}{' permanent' if d.get('permanent') else ''}")
    return out


def log_lines(r, n=15):
    entries = r.get("entries", [])
    return [f"{e.get('tick')} {e.get('type', '')}: {clean(e.get('text'))}" for e in entries[-n:]] \
        or ["(no entries)"]


def records_line(r):
    vals = [f"{x.get('record')}={x.get('value')}" for x in r.get("records", [])
            if x.get("value") not in (0, "0", None, "")]
    return ", ".join(vals) or "(all zero)"


def area_lines(r):
    """The ascii grid with z labels on the left and an x ruler on top."""
    b, grid = r.get("bounds", {}), r.get("grid", [])
    if not grid:
        return [generic(r)]
    x0, z1 = b.get("minX", 0), b.get("maxZ", len(grid) - 1)
    width = max(len(row) for row in grid)
    ruler = "".join(str((x0 + i) // 10 % 10) if (x0 + i) % 10 == 0 else " " for i in range(width))
    out = [f"      {ruler}   (x {x0}..{x0 + width - 1}, tens marked)"]
    out += [f"{z1 - i:>4} |{row}" for i, row in enumerate(grid)]
    return out


def wait_lines(w, tick=None):
    out = [f"cause {w.get('cause')} waited {w.get('ticksWaited')}"
           + (f" -> tick {tick}" if tick is not None else "")
           + (f" paused={w.get('pausedAfter')}" if "pausedAfter" in w else "")]
    for n in w.get("_notifications", []):
        out.append(f"  [{n.get('kind')}] {clean(n.get('text') or n.get('label'))}")
    d = w.get("_delta") or {}
    for p in d.get("pawnDamage", []):
        inj = "; ".join(clean(i) for i in p.get("newInjuries", []))
        out.append(f"  dmg {clean(p.get('name'))} {p.get('hpBefore')}->{p.get('hpAfter')} {inj}")
    for key, sign in (("newBuildings", "+"), ("removedBuildings", "-")):
        for b in d.get(key, []):
            out.append(f"  {sign}{b.get('def')} x{b.get('count')}")
    items = len(d.get("newItems", [])) + len(d.get("removedItems", []))
    if items:
        out.append(f"  item changes: {items}")
    return out


def debug_lines(r):
    out = ["ok" if r.get("ok") else f"error: {r.get('error')}"]
    opts = (r.get("optionList") or {}).get("options") or []
    out += [f"  > {o}" for o in opts[:40]] + ([f"  ...(+{len(opts) - 40})"] if len(opts) > 40 else [])
    if r.get("armedTool"):
        out.append(f"  armed: {r['armedTool']}")
    for it in r.get("items", []):
        out.append(f"  {it.get('category')}: {', '.join(it.get('entries', [])[:30])}")
    out += [f"  log: {clean(l.get('text') if isinstance(l, dict) else l)}" for l in r.get("log", [])[-8:]]
    return out


def list_tools(url):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json",
                                             "Accept": "application/json, text/event-stream"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)["result"]["tools"]


def tool_lines(tools, pattern=""):
    return [f"{t['name']}: {', '.join(t.get('inputSchema', {}).get('properties', {}))}"
            for t in sorted(tools, key=lambda t: t["name"]) if pattern in t["name"]]


def tool_doc(t, max_desc=1500):
    out = [t["name"], trim(t.get("description", ""), max_str=max_desc)]
    for k, v in t.get("inputSchema", {}).get("properties", {}).items():
        out.append(f"  {k} ({v.get('type', '?')}): {trim(v.get('description', ''), max_str=160)}")
    return out
