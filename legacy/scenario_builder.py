"""Build combat test scenarios as RimWorld saves via RimMolt's debug menu.

For each scenario: load an arena save -> spawn a raid and flip it to the player
(the squad) -> teleport the squad into formation -> remove the arena observer ->
spawn the enemy raid -> pause -> save as scenario_<id> + write a manifest.

  python3 scenario_builder.py scenarios.json            # build all
  python3 scenario_builder.py scenarios.json --only ID  # build one

Gotchas learned the hard way:
  * A debug option list closes if ANY other tool is called mid-chain, so raid
    picks are issued back-to-back with nothing in between.
  * Same for an armed debug tool: look things up BEFORE 'run', not between
    'run' and 'click'.
  * Debug paths are entry labels only (no category prefix).
  * Always pause first; teleport misses pawns that are walking.
  * 'Set Faction Rect' opens a vanilla float menu that vanishes when the real
    mouse is far away, so squads are converted with 'T: Recruit' instead.
"""
import argparse
import json
import math
import time
from pathlib import Path

from rimmolt_client import RimMolt, RimMoltError



class Builder:
    def __init__(self, rm: RimMolt):
        self.rm = rm

    # ---------- game lifecycle ----------
    def load(self, save):
        r = self.rm.call("load_game", name=save, confirm=True)
        if not r.get("ok", True) and "error" in r:
            raise RimMoltError(f"load_game {save}: {r['error']}")
        for _ in range(180):
            time.sleep(1)
            try:
                s = self.rm.call("game_setup_status")
            except Exception:
                continue  # server busy while the map loads
            if s.get("programState") == "Playing":
                break
        else:
            raise TimeoutError(f"{save} did not load")
        # 'Playing' flips before the map is fully up; wait until queries answer.
        for _ in range(30):
            if self.rm.call("get_status").get("loaded") and \
                    self.rm.call("list_colonists").get("colonists"):
                break
            time.sleep(1)
        time.sleep(2)
        self.rm.call("set_speed", action="pause")
        self.rm.call("dev_mode", devMode=True)

    def save(self, name):
        self.rm.call("set_speed", action="pause")
        r = self.rm.call("save_game", name=name, overwrite=True)
        if not r.get("ok"):
            raise RimMoltError(f"save_game {name}: {r}")

    # ---------- debug primitives ----------
    def dbg(self, **args):
        r = self.rm.call("debug_menu", **args)
        if not r.get("ok"):
            raise RimMoltError(f"debug_menu {args}: {r.get('error')}")
        return r

    def hostiles(self):
        return {t["id"]: t for t in self.rm.call(
            "list_things", category="pawn", confirm=True, faction="hostile")["things"]}

    def spawn_raid(self, faction_kind, points, strategy="ImmediateAttack",
                   arrival="EdgeWalkIn"):
        """Execute raid with specifics; return the new hostile pawns."""
        before = self.hostiles()
        r = self.dbg(action="run", path="Execute raid with specifics...")
        # Pick everything back-to-back: any other tool call closes the list.
        r = self.dbg(action="pick", option=self._match(
            r, lambda o: o.endswith(f"({faction_kind})"), f"faction {faction_kind}"))
        r = self.dbg(action="pick", option=self._points(r, points))
        r = self.dbg(action="pick", option=self._match(r, lambda o: o == strategy, strategy))
        r = self.dbg(action="pick", option=self._match(r, lambda o: o == arrival, arrival))
        while r.get("optionList", {}).get("options"):  # trailing extras (age, ...)
            r = self.dbg(action="pick", option=self._match(
                r, lambda o: o == "-Random-", "-Random-"))
        return self._settle(before, f"{faction_kind}/{points}")

    def spawn_raid_by_faction(self, faction_kind, points, max_steps=20):
        """'Execute raid with faction...': the only route for factions the
        specifics menu filters out (e.g. mechanoids before their earliest raid
        day). Strategy and arrival are chosen by the game."""
        before = self.hostiles()
        r = self.dbg(action="run", path="Execute raid with faction...")
        r = self.dbg(action="pick", option=self._match(
            r, lambda o: o.endswith(f"({faction_kind})"), f"faction {faction_kind}"))
        r = self.dbg(action="pick", option=self._points(r, points))
        while r.get("optionList", {}).get("options"):
            r = self.dbg(action="pick", option=r["optionList"]["options"][0])
        # No raid letter + "random element from empty collection" = the game found
        # no strategy/arrival it could use and generated nothing (~30% for mechs).
        letter = any(n.get("kind") == "letter" for n in r.get("_notifications", []))
        if not letter and any("empty collection" in (l.get("text") or "")
                              for l in r.get("log") or []):
            raise RimMoltError(f"raid {faction_kind}/{points} not generated")
        return self._settle(before, f"{faction_kind}/{points}", max_steps)

    def pods_in_flight(self):
        """Drop pods still falling or not yet opened. Their pawns are not on the
        map yet; a census that stops early counts them in the NEXT sample."""
        groups = self.rm.call("list_things", category="all", summary=True,
                              confirm=True).get("groups", [])
        return sum(g.get("count", 1) for g in groups
                   if g["def"].startswith(("DropPodIncoming", "ActiveDropPod")))

    def _settle(self, before, what, max_steps=20):
        """Advance a few ticks at a time until the new hostiles stop appearing
        and no drop pod is still in flight (pods land and open a few seconds
        after the raid fires, mech pods sometimes much later)."""
        last = -1
        for _ in range(max_steps):
            new = {k: v for k, v in self.hostiles().items() if k not in before}
            if new and len(new) == last and not self.pods_in_flight():
                break
            last = len(new)
            self.rm.call("wait_for_event", _timeout=60, maxGameTicks=60,
                         maxSeconds=20, pause="always", force=True)
        self.rm.call("set_speed", action="pause")
        if not new:
            raise RimMoltError(f"raid {what} spawned nobody")
        return list(new.values())

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

    def recruit(self, pawn):
        """Debug-recruit a pawn into the player colony (no float menu involved)."""
        self.dbg(action="run", path="T: Recruit")
        self.dbg(action="click", x=pawn["x"], z=pawn["z"])

    def _pos(self, pawn_id):
        p = self.rm.call("get_pawn", id=pawn_id)
        return (p["x"], p["z"])

    def teleport(self, pawn_id, x, z):
        px, pz = self._pos(pawn_id)  # before arming: any other call disarms the tool
        self.dbg(action="run", path="T: Teleport")
        self.dbg(action="click", x=px, z=pz)
        self.dbg(action="click", x=x, z=z)

    def destroy_at(self, x, z):
        self.dbg(action="run", path="T: Destroy")
        self.dbg(action="click", x=x, z=z)

    # ---------- squad ----------
    def make_squad(self, pawns, place, spacing=2, width=5):
        """Recruit every pawn into the colony and put the squad in formation."""
        for p in pawns:
            self.recruit(p)
        ids = [p["id"] for p in pawns]
        cols = {c["id"] for c in self.rm.call("list_colonists")["colonists"]}
        missing = [i for i in ids if i not in cols]
        if missing:
            raise RimMoltError(f"{len(missing)} squad pawns not recruited: {missing}")
        self.place(ids, self.formation(ids, place, spacing, width))
        return ids

    @staticmethod
    def formation(ids, place, spacing=2, width=5):
        """Rows of `width`, `spacing` apart, centered on `place`."""
        cx, cz = place
        slots = {}
        for n, pid in enumerate(ids):
            row, col = divmod(n, width)
            slots[pid] = (round(cx + (col - (min(width, len(ids)) - 1) / 2) * spacing),
                          cz - row * spacing)
        return slots

    def place(self, ids, slots):
        """Pawns that spawned stacked share a cell and a click may grab the
        wrong one, so keep re-teleporting until everyone is verified in place."""
        for _ in range(4):
            off = [pid for pid in ids if self._pos(pid) != tuple(slots[pid])]
            if not off:
                return
            for pid in off:
                self.teleport(pid, *slots[pid])
        raise RimMoltError(f"could not place {off}")

    def remove_observers(self, observers, ids):
        """Observer leaves; the squad is now the whole colony. Make sure nobody
        else shares its cell before destroying whatever stands there."""
        for oid in observers:
            pos = self._pos(oid)
            if any(self._pos(pid) == pos for pid in ids):
                raise RimMoltError(f"squad pawn on observer cell {pos}")
            self.destroy_at(*pos)
        cols = {c["id"] for c in self.rm.call("list_colonists")["colonists"]}
        if cols != set(ids):
            raise RimMoltError(f"colony after cleanup {cols} != squad {set(ids)}")

    # ---------- scenario ----------
    def build(self, sc, out_dir: Path):
        sid = sc["id"]
        print(f"== {sid}")
        self.load(sc.get("arena", "arena_open"))
        observers = [c["id"] for c in self.rm.call("list_colonists")["colonists"]]

        # Squad: spawn a raid, recruit every raider into the colony.
        sq = sc["squad"]
        ids = self.make_squad(self.spawn_raid(sq["faction"], sq["points"]), sq.get("place", [125, 125]),
                              sq.get("spacing", 2), sq.get("width", 5))
        print(f"   squad {len(ids)} pawns ({sq['faction']} {sq['points']}pt)")
        self.remove_observers(observers, ids)

        # Enemy.
        en = sc["enemy"]
        if en.get("method") == "faction":
            enemy = self.spawn_raid_by_faction(en["faction"], en["points"])
        else:
            enemy = self.spawn_raid(en["faction"], en["points"],
                                    en.get("strategy", "ImmediateAttack"),
                                    en.get("arrival", "EdgeWalkIn"))
        how = ("game-chosen strategy/arrival" if en.get("method") == "faction" else
               f"{en.get('strategy', 'ImmediateAttack')}/{en.get('arrival', 'EdgeWalkIn')}")
        print(f"   enemy {len(enemy)} pawns ({en['faction']} {en['points']}pt, {how})")

        self.rm.call("debug_menu", action="close")
        save = f"scenario_{sid}"
        self.save(save)
        manifest = {
            "id": sid, "save": save, "spec": sc,
            "squad": [self._pawn_row(i) for i in ids],
            "enemy": [{"id": p["id"], "def": p["def"], "x": p["x"], "z": p["z"]}
                      for p in enemy],
        }
        (out_dir / f"{save}.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        print(f"   saved {save}")
        return manifest

    def assaults(self, save, squad_ids, ticks=3000, min_close=0.3):
        """Reload `save`, let time run with no orders, and check the raid actually
        comes for the squad (median distance shrinks by min_close, or someone is
        already aiming at a colonist). Mech raids pick their own strategy and
        sometimes just loiter, which makes a scenario useless."""
        def median_gap():
            # A squad pawn killed (or carried off) during the wait has no position.
            us = [p for p in (self.rm.call("get_pawn", id=i) for i in squad_ids) if "x" in p]
            if not us:
                return 0.0
            cx = sum(p["x"] for p in us) / len(us)
            cz = sum(p["z"] for p in us) / len(us)
            hs = [h for h in self.hostiles().values()]
            ds = sorted(math.dist((h["x"], h["z"]), (cx, cz)) for h in hs)
            return ds[len(ds) // 2] if ds else 0.0

        self.load(save)
        d0 = median_gap()
        self.rm.call("wait_for_event", _timeout=120, maxGameTicks=ticks, maxSeconds=90,
                     pause="always", force=True)
        d1 = median_gap()
        aiming = any((t.get("targeting") or "").startswith(("targeting colonist", "attacking colonist"))
                     for t in self.rm.call("list_things", category="pawn", confirm=True, faction="hostile",
                                           verbose=True)["things"])
        hurt = sum(1 for i in squad_ids
                   if (p := self.rm.call("get_pawn", id=i)).get("dead") or "x" not in p
                   or p.get("downed"))
        ok = aiming or hurt > 0 or d1 <= d0 * (1 - min_close)
        print(f"   assault check: median gap {d0:.0f} -> {d1:.0f}, aiming={aiming}, "
              f"squad down/dead={hurt} -> "
              f"{'ok' if ok else 'LOITERING'}")
        return ok

    def _pawn_row(self, pid):
        p = self.rm.call("get_pawn", id=pid)
        return {"id": pid, "name": p["name"], "weapon": p.get("weapon"),
                "x": p["x"], "z": p["z"], "health": p["health"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("scenarios", type=Path)
    ap.add_argument("--only")
    ap.add_argument("--out", type=Path, default=Path("scenarios_out"))
    a = ap.parse_args()
    a.out.mkdir(exist_ok=True)
    b = Builder(RimMolt())
    for sc in json.loads(a.scenarios.read_text()):
        if a.only and sc["id"] != a.only:
            continue
        for attempt in range(3):
            m = b.build(sc, a.out)
            if b.assaults(m["save"], [p["id"] for p in m["squad"]]):
                break
            print(f"   rebuilding {sc['id']} (attempt {attempt + 2})")
        else:
            print(f"   ! {sc['id']}: enemy never assaulted in 3 builds; check the spec")
