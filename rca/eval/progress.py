"""Progress rate and stalemate stretch (GLOSSARY "stalemate / progress rate").

Progress = enemy combat points lost (killed, killed_inferred or downed;
data/combat_power.json). The clock starts at first contact: how long the raid
needs to walk in says nothing about a doctrine. A no-progress stretch is the
time since the last increase in points lost (or since first contact), whether
or not the raid is still in contact: a raid parked out of reach is exactly the
stalemate we want to see.

That raw stretch is a *pause*, not a stalemate: in the phase-2 smoke it passed
3000 ticks in 2 of 20 battles, both won (raiders fleeing or bleeding out while
nobody shot at us). The "win condition unattainable" signal therefore counts
only **contested** time (EVAL_SPEC §2, rule 2): the sum of step lengths since
the last progress in which we were paying a cost or under threat (pressure()).
"""
import math

THROW_R = 12.9               # frag/molotov verb range (XML)
BLAST_R = 1.9                # frag blast radius (XML; GAME_FACTS "Frag blast reach")
HEALTH_EPS = 0.5             # summary-health drop that counts as damage taken


class ProgressMeter:
    def __init__(self):
        self.first_contact = self.last_progress = None
        self.points, self.longest, self.now = 0.0, 0, 0
        # contested time: ticks under pressure since the last progress
        self.contested, self.longest_contested = 0, 0
        self.pressure_ticks = {"cost": 0, "threat": 0, "either": 0, "total": 0}

    def update(self, now, lost_points, contact, pressed=None):
        """pressed: None (not measured) or (cost, threat) for the step that
        ended at `now`; that step's length counts as contested if either holds."""
        prev, self.now = self.now, now
        if self.first_contact is None:
            if not contact:
                return
            self.first_contact = self.last_progress = prev = now
        dt = max(0, now - prev)
        if pressed is not None:
            cost, threat = pressed
            self.pressure_ticks["total"] += dt
            self.pressure_ticks["cost"] += dt * bool(cost)
            self.pressure_ticks["threat"] += dt * bool(threat)
            if cost or threat:
                self.pressure_ticks["either"] += dt
                self.contested += dt
        # the stretch runs until the step in which progress is seen
        self.longest = max(self.longest, now - self.last_progress)
        self.longest_contested = max(self.longest_contested, self.contested)
        if lost_points > self.points + 1e-9:
            self.points = lost_points
            self.last_progress = now
            self.contested = 0

    def stretch(self):
        """Current no-progress stretch in ticks (0 before contact)."""
        return 0 if self.last_progress is None else self.now - self.last_progress

    def rate(self):
        """Points lost per 1,000 ticks since first contact (None before contact)."""
        if self.first_contact is None:
            return None
        return round(self.points * 1000 / max(1, self.now - self.first_contact), 2)

    def summary(self, prefix="progress_"):
        return {f"{prefix}rate": self.rate(), f"{prefix}points": round(self.points, 1),
                "first_contact_tick": self.first_contact,
                "longest_no_progress_ticks": self.longest if self.first_contact is not None else None}

    def contested_summary(self):
        """Doctrine-side KPIs of the no_progress rule (EVAL_SPEC §2, §8)."""
        return {"longest_pause_ticks": self.longest if self.first_contact is not None else None,
                "longest_contested_ticks": self.longest_contested
                if self.first_contact is not None else None,
                "pressure_ticks": dict(self.pressure_ticks)}


def pressure(squad, prev, enemies):
    """-> (cost, threat) for one observation (pure).

    squad / prev: {id: {"pos": (x, z) or None, "health": %, "downed": bool}} for
    our squad pawns now / at the previous observation (prev None: first one).
    enemies: live, non-downed raiders [{"pos": (x, z), "range": cells,
    "thrower": bool}].
      cost   a pawn's summary health fell by more than HEALTH_EPS, a pawn was
             newly downed, or a pawn present before is gone (dead/kidnapped);
      threat a raider within its weapon range (XML verb range; melee 1.5) of
             any squad pawn on the map, standing or downed; a frag/molotov
             carrier counts within THROW_R + BLAST_R. Distance only, no LOS.
    """
    cost = False
    if prev:
        for i, p in prev.items():
            q = squad.get(i)
            if q is None or (q.get("downed") and not p.get("downed")) \
                    or (q.get("health") or 0) < (p.get("health") or 0) - HEALTH_EPS:
                cost = True
                break
    threat = any(
        q.get("pos") is not None
        and math.dist(q["pos"], e["pos"]) <= (max(e.get("range") or 0, THROW_R + BLAST_R)
                                              if e.get("thrower") else (e.get("range") or 0))
        for e in enemies for q in squad.values())
    return cost, threat


def lost_points(seen, live_ids):
    """Doctrine-side view: points of raiders once seen live and no longer live
    (downed, dead or gone). seen: {id: points}."""
    return sum(p or 0 for i, p in seen.items() if i not in live_ids)
