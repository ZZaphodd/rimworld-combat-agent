"""Per-poll trace of an observed (human) episode: who stood where, holding what, doing what.

The row in results/human/play.jsonl keeps the score; the trace keeps the play, for
battle reports and human demonstrations (TODO roadmap 3). One gzip JSON line per
poll; the first line is a header, the last an end line with the outcome:

  {"header": 1, "scenario": ..., "player": ..., "squad": [{"id", "n", "w"}], ...}
  {"t": 1185, "ours": [pawn], "them": [pawn], "fires": [[x, z]], "proj": [["frag", x, z]],
   "msg": ["..."]}
  {"end": "enemies_cleared", "grade": "decisive", "t": 4747, ...}

pawn = {"id", "n" name, "x", "z", "hp" health %, "w" weapon, "j" job, "d": 1 downed,
"dr": 1 drafted}. Pawns that are gone (dead, kidnapped, left) are simply absent.
"""
import gzip
import json
import time
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


def snapshot(rm, squad_ids):
    """Our squad and every hostile pawn on the map, plus fires and thrown projectiles."""
    pawns = [p for p in rm.call("list_things", category="pawn", verbose=True,
                                confirm=True).get("things", []) if not p.get("dead")]
    rec = {"ours": [], "them": []}
    for p in pawns:
        side = "ours" if p["id"] in squad_ids else "them" if p.get("hostile") else None
        if side:
            rec[side].append(pawn_entry(p, rm.call("get_pawn", id=p["id"])))
    rec["fires"] = [[t["x"], t["z"]] for t in rm.call(
        "list_things", category="all", defName="Fire", confirm=True).get("things", [])]
    rec["proj"] = [[short, t["x"], t["z"]] for d, short in PROJECTILES.items()
                   for t in rm.call("list_things", category="all", defName=d,
                                    confirm=True).get("things", [])]
    return rec


class Trace:
    """Writes one episode's trace; a failed poll is recorded, never raised."""

    def __init__(self, path, manifest, player):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ids = {p["id"] for p in manifest["squad"]}
        self.f = gzip.open(self.path, "wt")
        self._write({"header": 1, "scenario": manifest["id"], "save": manifest.get("save"),
                     "player": player, "commit": git_commit(),
                     "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                     "squad": [{"id": p["id"], "n": short_name(p.get("name")),
                                "w": p.get("weapon")} for p in manifest["squad"]]})

    def _write(self, rec):
        self.f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.f.flush()

    def poll(self, rm, ticks, msgs=()):
        try:
            rec = {"t": ticks, **snapshot(rm, self.ids)}
        except Exception as e:                      # noqa: BLE001 - the trace never stops a battle
            rec = {"t": ticks, "err": f"{type(e).__name__}: {e}"[:200]}
        if msgs:
            rec["msg"] = list(msgs)
        self._write(rec)

    def end(self, row):
        self._write({"end": row.get("outcome"), "t": row.get("ticks"),
                     **{k: row.get(k) for k in END_KEYS}})
        self.f.close()


def read(path):
    """All lines of a trace (header, polls, end) as dicts."""
    with gzip.open(path, "rt") as f:
        return [json.loads(line) for line in f if line.strip()]
