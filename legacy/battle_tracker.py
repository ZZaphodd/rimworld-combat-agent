"""Who died, who fled, who got kidnapped — without trusting corpses.

Corpses are unreliable evidence: grenades, fire and inferno cannons destroy
them, and a raider walking off the map leaves none either. So:

  * mechanoids never walk off the map -> a mech that disappears was destroyed;
  * humanlike deaths are read from the battle log ("Breigo perished."), harvested
    from every pawn on the map during the fight, because per-pawn logs are short
    and a dead raider's own log disappears with him;
  * no log evidence -> last observed state decides: downed -> died, leaving job
    (kidnapping/fleeing/stealing/exiting) or last seen near the edge -> escaped,
    otherwise died but flagged 'inferred';
  * our pawns: disappeared after a raider was seen kidnapping them -> kidnapped.
The squad's own 'Kills' records are kept as a cross-check.
"""
import re

MAP_SIZE = 250
# "Last seen near the edge" margin = what a walker (~0.075 cells/tick) covers
# between two samples, plus 3: 12 at a 120-tick step (the old constant), 5 at 30.
WALK, EDGE_BASE = 0.075, 3
EDGE = 12
LEAVING = ("kidnapping", "fleeing", "exiting", "stealing", "leaving")
DEATH_RE = re.compile(r"^(?P<name>.+?) (perished|expired|died|was killed|succumbed|bled out)\b")


def short_name(label):
    return re.split(r"[<,]", label or "", maxsplit=1)[0].strip()


def near_edge(x, z, edge=EDGE):
    return min(x, z, MAP_SIZE - 1 - x, MAP_SIZE - 1 - z) <= edge


class BattleTracker:
    def __init__(self, rm, squad_ids, harvest_ticks=600):
        # Log harvesting is the expensive part (one call per pawn): by game time,
        # not per sample, so a shorter cycle doesn't multiply it.
        self.rm, self.harvest_ticks = rm, harvest_ticks
        self.now, self.harvested_at, self.edge = 0, 0, EDGE
        self.enemy = {}        # id -> {name, mech, x, z, downed, job, fate}
        self.squad = {i: {"name": None, "downed": False, "fate": None} for i in squad_ids}
        self.dead_names = set()
        self.kidnap_targets = set()      # lowercased short names raiders were seen kidnapping
        self.kills0, self.kills = {}, {}
        self.step = 0
        self._read_kills(initial=True)

    # ------------------------------------------------------------ observe
    def observe(self, now=None):
        """Call once per harness step with the episode tick. Returns live (not
        downed) hostile records."""
        self.step += 1
        if now is not None and now > self.now:
            self.edge = round(EDGE_BASE + WALK * (now - self.now))
            self.now = now
        things = self.rm.call("list_things", category="pawn", confirm=True, faction="hostile",
                              verbose=True)["things"]
        now = {t["id"]: t for t in things if not t.get("dead")}
        downed_us = [(s["x"], s["z"]) for s in self.squad.values()
                     if s["downed"] and s.get("x") is not None]
        for tid, t in now.items():
            e = self.enemy.setdefault(tid, {"name": short_name(t.get("label")),
                                            "mech": t.get("def", "").startswith("Mech_"),
                                            "job": "", "fate": None})
            e.update(x=t["x"], z=t["z"], downed=bool(t.get("downed")), fate=None)
            # Jobs cost a call each; only fetch where leaving/kidnapping is plausible:
            # near the map edge, or standing over one of our downed pawns.
            if not e["mech"] and not e["downed"] and (
                    near_edge(t["x"], t["z"], self.edge)
                    or any(abs(t["x"] - x) <= 3 and abs(t["z"] - z) <= 3 for x, z in downed_us)):
                e["job"] = (self.rm.call("get_pawn", id=tid).get("job") or "").lower()
                if e["job"].startswith("kidnapping "):
                    self.kidnap_targets.add(e["job"][len("kidnapping "):].rstrip(". "))
        for tid, e in self.enemy.items():
            if tid not in now and e["fate"] is None:
                e["fate"] = self._enemy_fate(e)

        ours = {t["id"]: t for t in self.rm.call("list_things", category="pawn", confirm=True,
                                                  faction="player", verbose=True)["things"]}
        for sid, s in self.squad.items():
            if sid in ours:
                s.update(name=short_name(ours[sid].get("label")), x=ours[sid]["x"],
                         z=ours[sid]["z"], downed=bool(ours[sid].get("downed")), fate=None)
            elif s["fate"] is None:
                s["fate"] = "pending"            # settled in finish(), once logs are in

        if self.now - self.harvested_at >= self.harvest_ticks:
            self.harvested_at = self.now
            self.harvest(list(now) + [i for i in ours if i in self.squad])
            self._read_kills()
        return [t for t in now.values() if not t.get("downed")]

    def _enemy_fate(self, e):
        if e["mech"]:
            return "destroyed"
        if e["name"] in self.dead_names:
            return "killed"
        if e["downed"]:
            return "killed_inferred"             # a downed pawn can't walk away
        if e["job"].startswith(LEAVING) or near_edge(e["x"], e["z"], self.edge):
            return "escaped"
        return "killed_inferred"

    # ------------------------------------------------------------ evidence
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

    # ------------------------------------------------------------ result
    def finish(self):
        alive = [i for i, e in self.enemy.items() if e["fate"] is None]
        self.harvest(alive + [i for i, s in self.squad.items() if s["fate"] is None])
        self._read_kills()
        for e in self.enemy.values():           # late log evidence upgrades inferences
            if e["fate"] in ("killed_inferred", "escaped") and e["name"] in self.dead_names:
                e["fate"] = "killed"
        for s in self.squad.values():
            if s["fate"] == "pending":
                s["fate"] = ("kidnapped" if (s["name"] or "").lower() in self.kidnap_targets
                             and s["name"] not in self.dead_names else "dead")
        fates = [e["fate"] for e in self.enemy.values()]
        live = [e for e in self.enemy.values() if e["fate"] is None]
        return {
            "enemies_seen": len(self.enemy),
            "enemies_active_end": sum(not e["downed"] for e in live),
            "enemies_downed_end": sum(e["downed"] for e in live),
            "enemies_killed": fates.count("killed") + fates.count("destroyed"),
            "enemies_killed_inferred": fates.count("killed_inferred"),
            "enemies_escaped": fates.count("escaped"),
            "squad_dead": sum(s["fate"] == "dead" for s in self.squad.values()),
            "squad_kidnapped": sum(s["fate"] == "kidnapped" for s in self.squad.values()),
            "debug_kidnap_targets": sorted(self.kidnap_targets),
            "debug_dead_names": sorted(self.dead_names),
            "debug_squad": {s["name"]: s["fate"] for s in self.squad.values()},
            "debug_leaving_jobs": sorted({e["job"] for e in self.enemy.values() if e["job"]})[:15],
            "kills_record": sum(max(0, self.kills.get(i, 0) - self.kills0.get(i, 0))
                                for i in self.squad),
        }
