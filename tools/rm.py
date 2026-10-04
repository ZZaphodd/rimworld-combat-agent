"""Probe the running game by hand with compact output (rca/probe.py).

  python3 tools/rm.py status
  python3 tools/rm.py pawns [player|hostile|all] [--near ID|X,Z] [--radius R]
  python3 tools/rm.py pawn <id|name> [health|log|records|gear|...] [-n 15]
  python3 tools/rm.py area X0 Z0 X1 Z1 [--layer terrain] [--legend]
  python3 tools/rm.py wildlife
  python3 tools/rm.py wait <ticks>                  # advances game time, then pauses
  python3 tools/rm.py debug list <search> | run <path> [--tab T --value V] | pick <option>
                            | click <x,z;x,z> | close   (a label starting with "-": pick -- -Random-)
  python3 tools/rm.py tools [filter] | tool <name>  # RimMolt's own tool list / one tool's doc
  python3 tools/rm.py call <tool> key=value ...     # any tool, trimmed output

Debug chains break on any other call (RIMMOLT_API §3), so run the steps of one chain back to
back. Nothing here goes through the agent sandbox: this is the developer's view.
"""
import argparse
import sys

import _path  # noqa: F401
from rca import probe
from rca.rimmolt import RimMolt, RimMoltError


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("cmd")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--near")
    ap.add_argument("--radius", type=float)
    ap.add_argument("--layer")
    ap.add_argument("--legend", action="store_true")
    ap.add_argument("--tab")
    ap.add_argument("--value")
    ap.add_argument("-n", type=int, default=15)
    ap.add_argument("--max-list", type=int, default=20)
    a = ap.parse_args(argv)
    rm = RimMolt()
    try:
        for line in run(rm, a):
            print(line)
    except RimMoltError as e:
        print(f"RimMolt error: {e}")
        return 1
    return 0


def run(rm, a):
    cmd, args = a.cmd, a.args
    if cmd == "status":
        return [probe.status_line(rm.call("get_status"))]
    if cmd == "pawns":
        faction = (args or ["all"])[0]
        q = {"category": "pawn", "confirm": True}
        if faction != "all":
            q["faction"] = faction
        if a.near:
            x, _, z = a.near.partition(",")
            q.update({"nearX": int(x), "nearZ": int(z)} if z else {"nearId": a.near})
        if a.radius:
            q["radius"] = a.radius
        things = rm.call("list_things", **q).get("things", [])
        return [probe.pawn_line(t) for t in things] + [f"({len(things)} pawns)"]
    if cmd == "pawn":
        ref, tab = probe.pawn_ref(args[0]), (args[1] if len(args) > 1 else None)
        r = rm.call("get_pawn", **ref, **({"tab": tab} if tab else {}))
        if r.get("error") or not tab:
            return [probe.pawn_summary(r)]
        if tab == "health":
            return probe.health_lines(r)
        if tab == "log":
            return probe.log_lines(r, a.n)
        if tab == "records":
            return [probe.records_line(r)]
        return [probe.generic(r, max_list=a.max_list)]
    if cmd == "area":
        x0, z0, x1, z1 = map(int, args[:4])
        r = rm.call("get_area", minX=x0, minZ=z0, maxX=x1, maxZ=z1, render="ascii",
                    **({"layer": a.layer} if a.layer else {}))
        out = probe.area_lines(r)
        if a.legend:
            out += [f"  {k} {v}" for k, v in (r.get("legend") or {}).items()]
        return out
    if cmd == "wildlife":
        r = rm.call("list_wildlife")
        out = [f"{r.get('count')} wild animals"]
        for t in r.get("animals", [])[:a.max_list]:
            out.append(f"  {t.get('kind')} {t.get('id')} {t.get('x')},{t.get('z')}"
                       f"{' MANHUNTER' if t.get('mentalState') else ''}")
        return out
    if cmd == "wait":
        w = rm.wait(int(args[0]))
        return probe.wait_lines(w, rm.call("get_status").get("ticksGame"))
    if cmd == "debug":
        sub, rest = args[0], " ".join(args[1:])
        if sub == "list":
            r = rm.call("debug_menu", action="list", search=rest)
        elif sub == "run":
            kw = {k: v for k, v in (("tab", a.tab), ("value", a.value)) if v is not None}
            r = rm.call("debug_menu", action="run", path=rest, **kw)
        elif sub == "pick":
            r = rm.call("debug_menu", action="pick", option=rest)
        elif sub == "click":
            r = rm.call("debug_menu", action="click", cells=rest)
        elif sub == "close":
            r = rm.call("debug_menu", action="close")
        else:
            return [f"unknown debug action {sub!r}"]
        return probe.debug_lines(r)
    if cmd == "tools":
        return probe.tool_lines(probe.list_tools(rm.url), args[0] if args else "")
    if cmd == "tool":
        tools = {t["name"]: t for t in probe.list_tools(rm.url)}
        return probe.tool_doc(tools[args[0]]) if args[0] in tools else [f"no tool {args[0]!r}"]
    if cmd == "call":
        return [probe.generic(rm.call(args[0], **probe.parse_kv(args[1:])), max_list=a.max_list)]
    return [f"unknown command {cmd!r}; see python3 tools/rm.py --help"]


if __name__ == "__main__":
    sys.exit(main())
