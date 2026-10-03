"""amove (old b1): draft everyone able, Auto attack the nearest active enemy,
retarget when the target is gone. No positioning, no focus: the baseline every
doctrine is compared with. Micro (frag dodge, fire step-out) owns pawns while
it acts; amove re-attacks once they are released.

It raises no_progress like every doctrine (information only; behaviour is
unchanged from phase 1, so the version stays 5).
Unlike legacy b1 v2 it does not shoot rocket carriers first (that was part of
reflex v2, not of amove); targeting is plain nearest-first.
"""
import math

from ..eval.kpis import Tally, add_spacing, in_contact
from ..rimmolt import hostiles, player_pawns
from .doctrine import Doctrine


def able(c):
    return (not c.get("downed") and not c.get("mentalState")
            and "Violent" not in (c.get("incapableOf") or ""))


class Amove(Doctrine):
    name = "amove"
    version = 5                # legacy b1 rows are v1-v4
    win_condition = "trade fire at full engagement surface; no win condition beyond that"
    phases_spec = {"hold": "none: Auto attack from the first step"}

    def reset(self, rm, manifest):
        super().reset(rm, manifest)
        self.squad_ids = {p["id"] for p in manifest["squad"]}
        self.target, self.weapon, self.drafted = {}, {}, set()
        self.tally = Tally()

    def step(self, rm):
        hs = hostiles(rm)
        if not hs:
            return
        every = rm.call("list_colonists")["colonists"]
        cols = [c for c in every if able(c)]
        self.drafted -= {c["id"] for c in every if not able(c)}   # downed -> undrafted by the game
        new = [c["id"] for c in cols if c["id"] not in self.drafted]
        if new:
            rm.call("draft", action="draft", ids=",".join(new))
            self.drafted |= set(new)
        pos = {t["id"]: (t["x"], t["z"]) for t in player_pawns(rm)}
        fighters = [{"id": c["id"], "pos": pos[c["id"]]} for c in cols if c["id"] in pos]
        owned = self.micro.step(fighters, hs, self.now, self.step_ticks)
        alive = {h["id"] for h in hs}
        for c in fighters:
            pid = c["id"]
            if pid in owned:
                self.target.pop(pid, None)          # re-attack once released
                continue
            if self.target.get(pid) in alive:
                continue
            if pid not in self.weapon:
                self.weapon[pid] = rm.call("get_pawn", id=pid).get("weapon")
            if not self.weapon[pid]:
                continue
            x, z = c["pos"]
            near = min(hs, key=lambda h: math.dist((h["x"], h["z"]), (x, z)))
            r = rm.call("do_thing_action", id=pid, label="Auto attack (AI)", targetId=near["id"])
            if r.get("ok"):
                self.target[pid] = near["id"]
        contact = bool(fighters) and in_contact(fighters, hs)
        if contact:
            add_spacing(self.tally, fighters)
        squad = {c["id"]: {"pos": pos.get(c["id"]), "health": c.get("health", 100),
                           "downed": bool(c.get("downed"))}
                 for c in every if c["id"] in self.squad_ids}
        self.note_progress(hs, contact, squad)

    def kpis(self):
        return self.tally.summary() | super().kpis()
