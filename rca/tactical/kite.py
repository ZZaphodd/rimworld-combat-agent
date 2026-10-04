"""kite v5 (behaviour of kite v3): stand and fire; only the chased shooter runs,
through the squad (anti-melee).

Win condition: melee raiders cross open ground under the fire of the whole
squad; the one shooter they reach is peeled through the group, dragging its
chaser past everyone else's guns; shooting time and cohesion, not distance
(LESSONS §2: 5/5 on both melee themes; retreat_share 0.14-0.27).
Preconditions (thresholds UNVERIFIED): a melee-heavy raid (enemy_melee_heavy)
and a ranged squad (ranged_squad). Compact by design: never route it against explosives.
Phases:
  setup   draft, nobody advances (v1 doubled the closing speed);
  hold    stand, fire at will; a shooter runs only if a melee raider that is
          after IT (the raider's "attacking colonist <name>", else the nearest
          shooter) is within reach = RAIDER_SPEED x step_ticks + MARGIN; the
          runner goes through the squad's centre to REAR cells past it (at least
          `reach`), fanned sideways by ((i mod 5) - 2) x 3; melee pawns take the
          raider nearest any shooter, one each, engaging within SCREEN_ENGAGE;
  commit  sweep: Auto attack once no melee raider has been within PRESS of a
          fighter for CALM_TICKS contact ticks (or there are no melee raiders);
  reset   back to hold as soon as a melee raider presses again.
Signals: no_progress, losing_trade (report-only; v6 = v5 + losing_trade,
behaviour identical, bumped so rows never mix). No vs_throwers option (compact squad; not for grenadiers).
At a 30-tick cycle reach is ~5.4 cells; MARGIN is untuned for it (UNVERIFIED).
"""
import math
import statistics

from .squad import SquadDoctrine, pos, unit


class Kite(SquadDoctrine):
    name = "kite"
    version = 6                  # v6 = v5 + losing_trade (report-only); legacy v1-v4 (v4 = v3 rules + reflex layer)
    win_condition = "melee raiders die crossing open ground; the hunted shooter is peeled through the squad"
    preconditions = {"enemy_melee_heavy": {"min_share": 0.4}, "ranged_squad": {"min_share": 0.5}}
    phases_spec = {"setup": "draft, stand", "hold": "fire at will; hunted shooter runs through the squad",
                   "commit": "sweep: Auto attack after 360 calm contact ticks",
                   "reset": "a melee raider presses again: back to hold"}
    RAIDER_SPEED, MARGIN = 0.08, 3
    REAR, PRESS, SCREEN_ENGAGE = 5, 40, 8
    CALM_TICKS = 360

    def reset(self, rm, manifest):
        super().reset(rm, manifest)
        self.calm, self.last_now = 0, 0

    def step(self, rm):
        fighters, hs = self.observe(rm)
        dt, self.last_now = self.now - self.last_now, self.now
        if not hs or not fighters:
            return
        melee_raiders = [h for h in hs if self.enemy_info(h)["cls"] == "melee"]
        ranged = [c for c in fighters if not c["melee"]]
        screens = [c for c in fighters if c["melee"]]
        pressing = [h for h in melee_raiders
                    if any(math.dist(pos(h), c["pos"]) <= self.PRESS for c in self.all_fighters)]
        self.calm = 0 if pressing else self.calm + dt * self.contact
        sweep = not melee_raiders or self.calm >= self.CALM_TICKS
        self.set_phase("commit" if sweep else
                       "reset" if self.phase == "commit" else "hold" if self.contact else "setup")
        reach = self.RAIDER_SPEED * self.step_ticks + self.MARGIN
        line = [c["pos"] for c in self.all_fighters if not c["melee"]] or \
            [c["pos"] for c in self.all_fighters]
        cx, cz = statistics.mean(q[0] for q in line), statistics.mean(q[1] for q in line)
        hunted = self.hunted(ranged, melee_raiders, reach)
        for i, c in enumerate(ranged):
            pid, p = c["id"], c["pos"]
            threats = hunted.get(pid, [])
            self.measure(p, melee_raiders, bool(threats))
            if threats:
                self.run(pid, p, threats, (cx, cz), i, reach)
            elif sweep:
                self.auto_attack(pid, self.target_for(c, hs))
            elif pid in self.target:          # was advancing: stop and shoot
                self.goto(pid, p)
        self.screen(screens, ranged, pressing or hs)

    def hunted(self, ranged, melee_raiders, reach):
        """shooter id -> melee raiders within `reach` that are after that shooter."""
        out = {}
        for h in melee_raiders:
            near = [c for c in ranged if math.dist(pos(h), c["pos"]) <= reach]
            if not near:
                continue
            aim = (h.get("targeting") or "").lower()
            victim = next((c for c in near if c["name"] and
                           aim.endswith(" " + c["name"].lower())), None)
            victim = victim or min(near, key=lambda c: math.dist(pos(h), c["pos"]))
            out.setdefault(victim["id"], []).append(h)
        return out

    def run(self, pid, p, threats, centre, i, reach):
        tx = statistics.mean(h["x"] for h in threats)
        tz = statistics.mean(h["z"] for h in threats)
        ux, uz = unit(centre[0] - tx, centre[1] - tz)
        if (ux, uz) == (0.0, 0.0):
            ux, uz = unit(p[0] - tx, p[1] - tz) if (p[0], p[1]) != (tx, tz) else (1.0, 0.0)
        ahead = (centre[0] - p[0]) * ux + (centre[1] - p[1]) * uz
        go = max(reach, ahead + self.REAR)
        side = ((i % 5) - 2) * 3
        self.goto(pid, (p[0] + ux * go - uz * side, p[1] + uz * go + ux * side))

    def screen(self, screens, ranged, foes):
        """Each melee pawn takes the raider nearest to any shooter (one each)."""
        taken = set()
        for c in screens:
            free = [h for h in foes if h["id"] not in taken] or foes
            threat = min(free, key=lambda h: min(
                [math.dist(pos(h), s["pos"]) for s in ranged] or [math.dist(pos(h), c["pos"])]))
            taken.add(threat["id"])
            gap = min([math.dist(pos(threat), s["pos"]) for s in ranged] or [math.inf])
            if math.dist(pos(threat), c["pos"]) <= self.SCREEN_ENGAGE or gap <= self.SCREEN_ENGAGE:
                self.auto_attack(c["id"], threat)

    def measure(self, p, melee_raiders, retreating):
        d = min((math.dist(pos(h), p) for h in melee_raiders), default=math.inf)
        if d > 30:
            return
        self.tally.add("shooter_melee_dist", d)
        self.tally.add("melee_adjacent_share", d <= 1.5)
        self.tally.add("retreat_share", retreating)
