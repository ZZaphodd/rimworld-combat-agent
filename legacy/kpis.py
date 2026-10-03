"""Behaviour KPIs: does a doctrine do what it claims, whatever the outcome?

Agents keep a Tally and feed it from data they already read each step (no
extra game calls); eval stores agent.kpis() in the result row. Most KPIs only
count CONTACT steps (some raider within CONTACT cells of some fighter): how a
squad stands while the raid is still 100 cells out says nothing.
"""
import math

CONTACT = 30


def in_contact(fighters, hostiles):
    return any(math.dist(c["pos"], (h["x"], h["z"])) <= CONTACT
               for c in fighters for h in hostiles)


class Tally:
    """Running means (add) and one-off values (once/put); summary() -> small dict."""

    def __init__(self):
        self.sum, self.n, self.vals = {}, {}, {}

    def add(self, key, x):
        self.sum[key] = self.sum.get(key, 0.0) + x
        self.n[key] = self.n.get(key, 0) + 1

    def once(self, key, value):
        """Keep the first value only (e.g. 'first shot at tick ...')."""
        self.vals.setdefault(key, value)

    def put(self, key, value):
        self.vals[key] = value

    def summary(self):
        out = {k: round(self.sum[k] / self.n[k], 3) for k in self.sum}
        out.update(self.vals)
        return out


def nearest_ally(c, fighters):
    return min((math.dist(c["pos"], o["pos"]) for o in fighters if o["id"] != c["id"]),
               default=math.inf)


def add_spacing(tally, fighters, gap=5):
    """Shared by every doctrine: one blast hits everyone within a few cells."""
    for c in fighters:
        tally.add("gap5_share", nearest_ally(c, fighters) >= gap)
