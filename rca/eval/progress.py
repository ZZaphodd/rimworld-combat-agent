"""Progress rate and stalemate stretch (GLOSSARY "stalemate / progress rate").

Progress = enemy combat points lost (killed, killed_inferred or downed;
data/combat_power.json). The clock starts at first contact: how long the raid
needs to walk in says nothing about a doctrine. A no-progress stretch is the
time since the last increase in points lost (or since first contact), whether
or not the raid is still in contact: a raid parked out of reach is exactly the
stalemate we want to see.
"""


class ProgressMeter:
    def __init__(self):
        self.first_contact = self.last_progress = None
        self.points, self.longest, self.now = 0.0, 0, 0

    def update(self, now, lost_points, contact):
        self.now = now
        if self.first_contact is None:
            if not contact:
                return
            self.first_contact = self.last_progress = now
        # the stretch runs until the step in which progress is seen
        self.longest = max(self.longest, now - self.last_progress)
        if lost_points > self.points + 1e-9:
            self.points = lost_points
            self.last_progress = now

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


def lost_points(seen, live_ids):
    """Doctrine-side view: points of raiders once seen live and no longer live
    (downed, dead or gone). seen: {id: points}."""
    return sum(p or 0 for i, p in seen.items() if i not in live_ids)
