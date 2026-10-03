"""Behaviour KPIs from data agents already read (no extra calls). Most count
only contact steps: how a squad stands 100 cells from the raid says nothing."""
import math

CONTACT = 30


def in_contact(fighters, hostiles):
    return any(math.dist(c["pos"], (h["x"], h["z"])) <= CONTACT for c in fighters for h in hostiles)


class Tally:
    """Running means (add) and one-off values (once/put)."""

    def __init__(self):
        self.sum, self.n, self.vals = {}, {}, {}

    def add(self, key, x):
        self.sum[key] = self.sum.get(key, 0.0) + x
        self.n[key] = self.n.get(key, 0) + 1

    def once(self, key, value):
        self.vals.setdefault(key, value)

    def put(self, key, value):
        self.vals[key] = value

    def summary(self):
        return {k: round(self.sum[k] / self.n[k], 3) for k in self.sum} | self.vals


def add_spacing(tally, fighters, gap=5):
    """gap5_share: one blast hits everyone within a few cells."""
    for c in fighters:
        d = min((math.dist(c["pos"], o["pos"]) for o in fighters if o["id"] != c["id"]),
                default=math.inf)
        tally.add("gap5_share", d >= gap)
