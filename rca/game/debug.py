"""Debug-menu helpers (RIMMOLT_API.md §3). Every rule there was learned by
failure: option lists and armed tools close on ANY other call, so look things
up before `run`, and issue picks back to back."""
from ..rimmolt import RimMoltError, hostiles, things_of

PODS = ("DropPodIncoming", "ActiveDropPod")


class Debug:
    def __init__(self, rm, log=print):
        self.rm, self.log = rm, log

    def dbg(self, **args):
        r = self.rm.call("debug_menu", **args)
        if not r.get("ok"):
            raise RimMoltError(f"debug_menu {args}: {r.get('error')}")
        return r

    def run(self, path, **kw):
        return self.dbg(action="run", path=path, **kw)

    def close(self):
        self.rm.call("debug_menu", action="close")

    def hostile_ids(self):
        return {t["id"]: t for t in hostiles(self.rm, live_only=False)}

    def pos(self, pid):
        p = self.rm.call("get_pawn", id=pid)
        return (p["x"], p["z"]) if "x" in p else None

    # ------------------------------------------------------------ raids
    @staticmethod
    def _match(r, pred, what):
        opts = [o for o in r["optionList"]["options"] if not o.endswith("[NO]")]
        for o in opts:
            if pred(o):
                return o
        raise RimMoltError(f"no usable option for {what}; have {opts}")

    @staticmethod
    def _points(r, points):
        opts = [o for o in r["optionList"]["options"] if o.endswith(" points")]
        return min(opts, key=lambda o: abs(int(o.split()[0]) - points))

    def spawn_raid(self, faction, points, strategy="ImmediateAttack", arrival="EdgeWalkIn"):
        """'Execute raid with specifics': we choose strategy and arrival."""
        before = self.hostile_ids()
        r = self.run("Execute raid with specifics...")
        r = self.dbg(action="pick", option=self._match(
            r, lambda o: o.endswith(f"({faction})"), f"faction {faction}"))
        r = self.dbg(action="pick", option=self._points(r, points))
        r = self.dbg(action="pick", option=self._match(r, lambda o: o == strategy, strategy))
        r = self.dbg(action="pick", option=self._match(r, lambda o: o == arrival, arrival))
        while r.get("optionList", {}).get("options"):         # trailing extras (age, ...)
            r = self.dbg(action="pick", option=self._match(r, lambda o: o == "-Random-", "-Random-"))
        return self.settle(before, f"{faction}/{points}")

    def spawn_raid_by_faction(self, faction, points, max_steps=20):
        """'Execute raid with faction': game-chosen strategy/arrival; the only
        route for mechs. Fails silently ~25% for mechs: no letter + 'empty
        collection' in the log means nothing was generated."""
        before = self.hostile_ids()
        r = self.run("Execute raid with faction...")
        r = self.dbg(action="pick", option=self._match(
            r, lambda o: o.endswith(f"({faction})"), f"faction {faction}"))
        r = self.dbg(action="pick", option=self._points(r, points))
        while r.get("optionList", {}).get("options"):
            r = self.dbg(action="pick", option=r["optionList"]["options"][0])
        letter = any(n.get("kind") == "letter" for n in r.get("_notifications") or [])
        if not letter and any("empty collection" in (l.get("text") or "") for l in r.get("log") or []):
            raise RimMoltError(f"raid {faction}/{points} not generated")
        return self.settle(before, f"{faction}/{points}", max_steps)

    def pods_in_flight(self):
        groups = self.rm.call("list_things", category="all", summary=True,
                              confirm=True).get("groups", [])
        return sum(g.get("count", 1) for g in groups if g["def"].startswith(PODS))

    def settle(self, before, what, max_steps=20):
        """Advance 60 ticks at a time until new hostiles stop appearing and no
        pod is in flight. Spawning nobody is a failure even if the reply was ok."""
        last, new = -1, {}
        for _ in range(max_steps):
            new = {k: v for k, v in self.hostile_ids().items() if k not in before}
            if new and len(new) == last and not self.pods_in_flight():
                break
            last = len(new)
            self.rm.wait(60, max_seconds=20)
        self.rm.call("set_speed", action="pause")
        if not new:
            raise RimMoltError(f"raid {what} spawned nobody")
        return list(new.values())

    def spawn_pawn(self, kind, cells):
        """Lordless spawn ('Spawn Pawn... > Kind'): no raid lord, so the game
        never posts fleeing/satisfied for these pawns. Returns the new hostiles."""
        before = self.hostile_ids()
        self.run(f"Spawn Pawn... > {kind}")
        self.dbg(action="click", cells=";".join(f"{x},{z}" for x, z in cells))
        self.close()
        return [t for k, t in self.hostile_ids().items() if k not in before]

    # ------------------------------------------------------------ pawns
    def recruit(self, pawn):
        self.run("T: Recruit")
        self.dbg(action="click", x=pawn["x"], z=pawn["z"])

    def teleport(self, pid, x, z, rounds=5):
        """3-call teleport; the first click misses a walking or stacked pawn, so
        verify with get_pawn and retry."""
        for _ in range(rounds):
            p = self.pos(pid)                   # before arming: any call disarms the tool
            if p == (x, z):
                return True
            if p is None:
                return False
            self.run("T: Teleport")
            if self.dbg(action="click", x=p[0], z=p[1]).get("armedTool"):
                self.dbg(action="click", x=x, z=z)
        return self.pos(pid) == (x, z)

    def place(self, slots, rounds=4):
        """Re-teleport until every pawn is verified on its slot."""
        off = []
        for _ in range(rounds):
            off = [pid for pid, s in slots.items() if self.pos(pid) != tuple(s)]
            if not off:
                return
            for pid in off:
                self.teleport(pid, *slots[pid], rounds=1)
        raise RimMoltError(f"could not place {off}")

    def destroy_at(self, x, z):
        self.run("T: Destroy")
        self.dbg(action="click", x=x, z=z)

    def clear_area(self, x0, z0, x1, z1):
        self.run("Clear area (rect)")
        self.dbg(action="click", cells=f"{x0},{z0};{x1},{z1}")

    def remove_observers(self, observers, squad_ids):
        """Destroy each observer, after checking no squad pawn shares its cell;
        the colony must then equal the squad exactly."""
        for oid in observers:
            p = self.pos(oid)
            if p is None:
                continue
            if any(self.pos(s) == p for s in squad_ids):
                raise RimMoltError(f"squad pawn on observer cell {p}")
            self.destroy_at(*p)
        cols = {c["id"] for c in self.rm.call("list_colonists")["colonists"]}
        if cols != set(squad_ids):
            raise RimMoltError(f"colony after cleanup {cols} != squad {set(squad_ids)}")

    def remove_loose_weapons(self):
        """Ruins hold weapons (even persona ones) a squad would pick up."""
        groups = self.rm.call("list_things", category="item", summary=True, confirm=True)["groups"]
        for g in groups:
            if g["def"].startswith(("Gun_", "MeleeWeapon_", "Weapon_")):
                for t in things_of(self.rm, g["def"]):
                    self.destroy_at(t["x"], t["z"])
                    self.log(f"removed {g['def']} at {(t['x'], t['z'])}")


def formation(ids, place, spacing=2, width=5):
    """Rows of `width`, `spacing` apart, centred on `place`, rows going -z."""
    cx, cz = place
    out = {}
    for n, pid in enumerate(ids):
        row, col = divmod(n, width)
        out[pid] = (round(cx + (col - (min(width, len(ids)) - 1) / 2) * spacing), cz - row * spacing)
    return out
