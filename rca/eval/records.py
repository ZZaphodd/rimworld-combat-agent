"""Each pawn's own combat records (its Records tab), read during a battle so that a pawn who dies
or is carried off keeps its numbers.

RimMolt's get_pawn finds only living pawns on the map: a dead pawn's id gives "Pawn not found",
and a corpse's inspect and info card hold no records (checked 2026-10-18). A read at the end of a
battle therefore misses whoever died or was taken. SquadRecords reads our squad once at the start
(paused: the baseline), every `every` polls, and once more at the end; each pawn keeps its last
read, so the values are the change from the baseline up to that read (`tick`).

The game adds to "Damage dealt" in Thing.TakeDamage for any thing a pawn damages: raiders, but
also walls, doors and urns (a missed arrow that hits the cover beside its target counts too).
"Damage taken" is added by the pawn's own damage path.
"""
from .tracker import short_name

RECORDS = {"Damage dealt": "dealt", "Shots fired": "shots", "Kills": "kills",
           "Damage taken": "taken", "Headshots": "headshots"}
FIELDS = tuple(RECORDS.values())
EVERY = 5                       # polls between reads (the observed harness polls once a second)


def parse(reply):
    """{field: value} from a get_pawn(tab="records") reply; None when the pawn was not found."""
    rows = (reply or {}).get("records")
    if rows is None:
        return None
    return {RECORDS[r["record"]]: r.get("value") or 0 for r in rows if r.get("record") in RECORDS}


class SquadRecords:
    """squad: the manifest's squad entries ({"id", "name"}). every=None reads only at the start
    and the end (a light trace: with RimMolt's "Mirror AI inspection" on, each per-pawn read
    changes the player's selection)."""

    def __init__(self, rm, squad, every=EVERY):
        self.rm, self.every, self.polls = rm, every, 0
        self.names = {p["id"]: short_name(p.get("name")) for p in squad}
        self.base, self.last, self.at = {}, {}, {}

    def _read(self, ticks):
        got = {}
        for pid in self.names:
            try:
                v = parse(self.rm.call("get_pawn", id=pid, tab="records"))
            except Exception:                   # noqa: BLE001 - records never stop a battle
                v = None
            if v is None:                       # dead or off the map: keep the last read
                continue
            self.base.setdefault(pid, v)
            self.last[pid], self.at[pid] = v, ticks
            got[pid] = v
        return got

    def start(self):
        """The baseline, right after the load while the game is still paused. Names become the
        in-game short labels the trace uses ("Levy", not "Taras Levy")."""
        try:
            for p in self.rm.call("list_things", category="pawn", verbose=True,
                                  confirm=True).get("things", []):
                if p["id"] in self.names:
                    self.names[p["id"]] = short_name(p.get("label")) or self.names[p["id"]]
        except Exception:                       # noqa: BLE001 - records never stop a battle
            pass
        self._read(0)

    def poll(self, ticks, final=False):
        """Read every `every` polls (always when final). Returns {name: [dealt, shots, kills,
        taken, headshots]} for the pawns read now, or None when this poll is skipped."""
        self.polls += 1
        if not final and (not self.every or self.polls % self.every):
            return None
        return {self.names[pid]: [self.delta(pid)[f] for f in FIELDS] for pid in self._read(ticks)}

    def delta(self, pid):
        b, v = self.base.get(pid, {}), self.last.get(pid, {})
        return {f: v.get(f, 0) - b.get(f, 0) for f in FIELDS}

    def row(self):
        """Row fields: each pawn's values at its last read, and the squad's totals."""
        per = {self.names[pid]: {**self.delta(pid), "tick": self.at[pid]} for pid in self.names
               if pid in self.last}
        return {"squad_records": per,
                "damage_dealt": sum(r["dealt"] for r in per.values()),
                "damage_taken": sum(r["taken"] for r in per.values()),
                "records_every_polls": self.every}
