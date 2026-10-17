"""Per-poll trace of an observed (human) episode: who stood where, holding what, doing what.

The row in results/human/play.jsonl keeps the score; the trace keeps the play, for
battle reports and human demonstrations (TODO roadmap 3). One gzip JSON line per
poll; the first line is a header, the last an end line with the outcome:

  {"header": 1, "scenario": ..., "player": ..., "squad": [{"id", "n", "w"}], ...}
  {"t": 1185, "ours": [pawn], "them": [pawn], "fires": [[x, z]], "proj": [["frag", x, z]],
   "msg": ["..."]}
  {"t": 1190, "rec": {"Butters": [dealt, shots, kills, taken, headshots]}}   (every few polls)
  {"end": "enemies_cleared", "grade": "decisive", "t": 4747, ...}

pawn = {"id", "n" name, "x", "z", "hp" health %, "w" weapon, "j" job, "d": 1 downed,
"dr": 1 drafted}. Pawns that are gone (dead, kidnapped, left) are simply absent.
"rec" lines are our pawns' combat records since the load (rca/eval/records.py), for the pawns
read at that moment; a pawn who died or was taken keeps its last line.

Light mode (a human at the GUI): with RimMolt's mod option "Mirror AI inspection" on, every pawn
read changes the game's selection, so one call per pawn per poll makes the player's selection
flicker through every pawn (the user, 2026-10-07; with the option off it does not). A light trace reads weapons once, at load while paused
(a "weapons" line), and per poll only bulk calls: ours' health and job from list_colonists, the
raiders' job from their targeting text, no raider health ("hp": null).
"""
import gzip
import json
import time
import zlib
from pathlib import Path

from .results import git_commit
from .tracker import short_name

PROJECTILES = {"Proj_GrenadeFrag": "frag", "Proj_GrenadeMolotov": "molotov",
               "Proj_GrenadeEMP": "emp", "Proj_GrenadeSmoke": "smoke"}
END_KEYS = ("grade", "ler", "deaths", "squad_dead", "squad_kidnapped", "downed_at_end",
            "enemies_killed", "enemies_killed_inferred", "enemies_escaped", "hp_lost_pct",
            "raid_fled_tick")


def pawn_entry(listing, summary):
    """One pawn from a list_things row and its get_pawn summary."""
    e = {"id": listing["id"], "n": short_name(listing.get("label")),
         "x": listing["x"], "z": listing["z"], "hp": summary.get("health"),
         "w": summary.get("weapon"), "j": summary.get("job")}
    if listing.get("downed"):
        e["d"] = 1
    if listing.get("drafted"):
        e["dr"] = 1
    return e


def snapshot(rm, squad_ids, light=False, weapons=None):
    """Our squad and every hostile pawn on the map, plus fires and thrown projectiles. Light: no
    per-pawn call (module docstring); weapons from the load-time read."""
    pawns = [p for p in rm.call("list_things", category="pawn", verbose=True,
                                confirm=True).get("things", []) if not p.get("dead")]
    cols = {c["id"]: c for c in rm.call("list_colonists").get("colonists") or []} if light else {}
    rec = {"ours": [], "them": []}
    for p in pawns:
        side = "ours" if p["id"] in squad_ids else "them" if p.get("hostile") else None
        if not side:
            continue
        if light:
            c = cols.get(p["id"], {})
            summary = {"health": c.get("health"), "job": c.get("job") or p.get("targeting"),
                       "weapon": (weapons or {}).get(p["id"])}
        else:
            summary = rm.call("get_pawn", id=p["id"])
        rec[side].append(pawn_entry(p, summary))
    rec["fires"] = [[t["x"], t["z"]] for t in rm.call(
        "list_things", category="all", defName="Fire", confirm=True).get("things", [])]
    rec["proj"] = [[short, t["x"], t["z"]] for d, short in PROJECTILES.items()
                   for t in rm.call("list_things", category="all", defName=d,
                                    confirm=True).get("things", [])]
    return rec


class Trace:
    """Writes one episode's trace; a failed poll is recorded, never raised."""

    def __init__(self, path, manifest, player, light=False):
        self.path = Path(path)
        self.light, self.weapons = light, {}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ids = {p["id"] for p in manifest["squad"]}
        self.f = gzip.open(self.path, "wt")
        self._write({"header": 1, "scenario": manifest["id"], "save": manifest.get("save"),
                     "player": player, "commit": git_commit(), "light": light,
                     "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                     "squad": [{"id": p["id"], "n": short_name(p.get("name")),
                                "w": p.get("weapon")} for p in manifest["squad"]]})

    def _write(self, rec):
        self.f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.f.flush()

    def ready(self, rm):
        """After the load, while paused: a light trace reads every pawn's weapon once."""
        if not self.light:
            return
        try:
            for p in rm.call("list_things", category="pawn", verbose=True, confirm=True).get("things", []):
                if not p.get("dead") and (p["id"] in self.ids or p.get("hostile")):
                    self.weapons[p["id"]] = rm.call("get_pawn", id=p["id"]).get("weapon")
        except Exception as e:                      # noqa: BLE001 - the trace never stops a battle
            self._write({"weapons_err": f"{type(e).__name__}: {e}"[:200]})
        self._write({"weapons": self.weapons})

    def poll(self, rm, ticks, msgs=()):
        try:
            rec = {"t": ticks, **snapshot(rm, self.ids, self.light, self.weapons)}
        except Exception as e:                      # noqa: BLE001 - the trace never stops a battle
            rec = {"t": ticks, "err": f"{type(e).__name__}: {e}"[:200]}
        if msgs:
            rec["msg"] = list(msgs)
        self._write(rec)

    def records(self, ticks, rec):
        """Our pawns' combat records ({name: [dealt, shots, kills, taken, headshots]})."""
        self._write({"t": ticks, "rec": rec})

    def end(self, row):
        self._write({"end": row.get("outcome"), "t": row.get("ticks"),
                     **{k: row.get(k) for k in END_KEYS}})
        self.f.close()


def read(path):
    """All lines of a trace (header, polls, end) as dicts. A trace whose writer was killed
    (an abandoned attempt) has no gzip trailer and maybe half a last line: read what is there."""
    data = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(Path(path).read_bytes())
    out = []
    for line in data.decode("utf-8", "replace").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            break
    return out
