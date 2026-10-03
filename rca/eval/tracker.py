"""Fates without trusting corpses (EVAL_SPEC §4): blasts and fire destroy them
and walkers leave none.

  * mechs never walk off the map: a mech that disappears was destroyed;
  * humanlike deaths come from battle logs harvested from every pawn during the
    fight (a dead raider's own log vanishes with him);
  * no log evidence: last seen downed -> killed_inferred; leaving job or near
    the edge -> escaped; otherwise killed_inferred;
  * our pawns that disappeared: kidnapped if a raider was seen kidnapping them
    and no death was logged, else dead.
rca adds each raider's PawnKindDef and combat points, so the trade ratio is
point-weighted (rca/eval/scoring.py).
"""
import re

from ..game.defs import combat_power
from ..rimmolt import hostiles, player_pawns

MAP_SIZE = 250
WALK, EDGE_BASE, EDGE = 0.075, 3, 12
LEAVING = ("kidnapping", "fleeing", "exiting", "stealing", "leaving")
DEATH_RE = re.compile(r"^(?P<name>.+?) (perished|expired|died|was killed|succumbed|bled out)\b")


def short_name(label):
    return re.split(r"[<,]", label or "", maxsplit=1)[0].strip()


def near_edge(x, z, edge=EDGE):
    return min(x, z, MAP_SIZE - 1 - x, MAP_SIZE - 1 - z) <= edge


def kind_points(kind, race=""):
    p = combat_power(kind)
    return combat_power(race) if p is None and race else p


def enemy_fate(e, dead_names, edge):
    """Fate of a raider at the first observation it is missing (pure)."""
    if e["mech"]:
        return "destroyed"
    if e["name"] in dead_names:
        return "killed"
    if e["downed"]:
        return "killed_inferred"
    if e["job"].startswith(LEAVING) or near_edge(e["x"], e["z"], edge):
        return "escaped"
    return "killed_inferred"


class BattleTracker:
    def __init__(self, rm, squad_ids, harvest_ticks=600):
        # Log harvest = one call per pawn: by game time, so a short cycle doesn't multiply it.
        self.rm, self.harvest_ticks = rm, harvest_ticks
        self.now, self.harvested_at, self.edge = 0, 0, EDGE
        self.enemy = {}
        self.squad = {i: {"name": None, "downed": False, "fate": None} for i in squad_ids}
        self.dead_names, self.kidnap_targets = set(), set()
        self.kills0, self.kills = {}, {}
        self._read_kills(initial=True)

    def observe(self, now=None):
        """Once per harness step with the episode tick; returns live (not downed) hostiles."""
        if now is not None and now > self.now:
            self.edge = round(EDGE_BASE + WALK * (now - self.now))
            self.now = now
        cur = {t["id"]: t for t in hostiles(self.rm, live_only=False)}
        # Squad first, so a pawn downed this step already counts for the
        # kidnapper check below (one step earlier than legacy).
        ours = {t["id"]: t for t in player_pawns(self.rm)}
        for sid, s in self.squad.items():
            if sid in ours:
                s.update(name=short_name(ours[sid].get("label")), x=ours[sid]["x"],
                         z=ours[sid]["z"], downed=bool(ours[sid].get("downed")), fate=None)
            elif s["fate"] is None:
                s["fate"] = "pending"                     # settled in finish()
        downed_us = [(s["x"], s["z"]) for s in self.squad.values()
                     if s["downed"] and not s["fate"] and s.get("x") is not None]
        for tid, t in cur.items():
            kind = t.get("kind") or ""
            e = self.enemy.setdefault(tid, {
                "name": short_name(t.get("label")), "mech": (t.get("def") or "").startswith("Mech_"),
                "kind": kind, "points": kind_points(kind, t.get("def", "")), "job": "",
                "fate": None})
            e.update(x=t["x"], z=t["z"], downed=bool(t.get("downed")), fate=None)
            # Jobs cost a call each: only where leaving/kidnapping is plausible.
            if not e["mech"] and not e["downed"] and (
                    near_edge(t["x"], t["z"], self.edge)
                    or any(abs(t["x"] - x) <= 3 and abs(t["z"] - z) <= 3 for x, z in downed_us)):
                e["job"] = (self.rm.call("get_pawn", id=tid).get("job") or "").lower()
                if e["job"].startswith("kidnapping "):
                    self.kidnap_targets.add(e["job"][len("kidnapping "):].rstrip(". "))
        for tid, e in self.enemy.items():
            if tid not in cur and e["fate"] is None:
                e["fate"] = enemy_fate(e, self.dead_names, self.edge)
        if self.now - self.harvested_at >= self.harvest_ticks:
            self.harvested_at = self.now
            self.harvest(list(cur) + [i for i in ours if i in self.squad])
            self._read_kills()
        return [t for t in cur.values() if not t.get("downed")]

    def harvest(self, pawn_ids):
        for pid in pawn_ids:
            for entry in self.rm.call("get_pawn", id=pid, tab="log").get("entries", []):
                m = DEATH_RE.match(entry.get("text", ""))
                if m:
                    self.dead_names.add(m.group("name"))

    def _read_kills(self, initial=False):
        for sid in self.squad:
            r = self.rm.call("get_pawn", id=sid, tab="records")
            if "error" in r:
                continue
            v = next((x["value"] for x in r.get("records", []) if x["record"] == "Kills"), 0)
            (self.kills0 if initial else self.kills)[sid] = v
        if initial:
            self.kills = dict(self.kills0)

    def finish(self):
        alive = [i for i, e in self.enemy.items() if e["fate"] is None]
        self.harvest(alive + [i for i, s in self.squad.items() if s["fate"] is None])
        self._read_kills()
        for e in self.enemy.values():                # late log evidence upgrades inferences
            if e["fate"] in ("killed_inferred", "escaped") and e["name"] in self.dead_names:
                e["fate"] = "killed"
        # Kidnap names are short names from job text: ambiguous if two squad
        # pawns share one (LESSONS bug 10); flagged rather than guessed.
        short = [(s["name"] or "").lower() for s in self.squad.values()]
        ambiguous = sorted({n for n in self.kidnap_targets if short.count(n) > 1})
        for s in self.squad.values():
            if s["fate"] == "pending":
                s["fate"] = ("kidnapped" if (s["name"] or "").lower() in self.kidnap_targets
                             and s["name"] not in self.dead_names else "dead")
        fates = [e["fate"] for e in self.enemy.values()]
        live = [e for e in self.enemy.values() if e["fate"] is None]
        lost = [e for e in self.enemy.values()
                if e["fate"] in ("killed", "destroyed", "killed_inferred")
                or (e["fate"] is None and e["downed"])]
        known = all(e["points"] is not None for e in self.enemy.values())

        def pts(es):
            return round(sum(e["points"] for e in es), 1) if known else None
        kinds = {}
        for e in self.enemy.values():
            k = kinds.setdefault(e["kind"] or "?", {})
            f = e["fate"] or ("downed_end" if e["downed"] else "active_end")
            k[f] = k.get(f, 0) + 1
        return {
            "enemies_seen": len(self.enemy),
            "enemies_active_end": sum(not e["downed"] for e in live),
            "enemies_downed_end": sum(e["downed"] for e in live),
            "enemies_killed": fates.count("killed") + fates.count("destroyed"),
            "enemies_killed_inferred": fates.count("killed_inferred"),
            "enemies_escaped": fates.count("escaped"),
            "enemy_seen_points": pts(self.enemy.values()),
            "enemy_lost_points": pts(lost),
            "enemy_escaped_points": pts([e for e in self.enemy.values() if e["fate"] == "escaped"]),
            "enemy_kinds": kinds,
            "squad_dead": sum(s["fate"] == "dead" for s in self.squad.values()),
            "squad_kidnapped": sum(s["fate"] == "kidnapped" for s in self.squad.values()),
            "debug_kidnap_targets": sorted(self.kidnap_targets),
            "debug_kidnap_ambiguous": ambiguous,
            "debug_dead_names": sorted(self.dead_names),
            "debug_squad": {s["name"]: s["fate"] for s in self.squad.values()},
            "debug_leaving_jobs": sorted({e["job"] for e in self.enemy.values() if e["job"]})[:15],
            "kills_record": sum(max(0, self.kills.get(i, 0) - self.kills0.get(i, 0))
                                for i in self.squad),
        }
