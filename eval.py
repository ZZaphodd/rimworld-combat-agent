"""Evaluation harness for RimMolt combat agents.

The harness owns game time: every step it pauses, lets the agent issue orders,
then advances the step. The cycle is adaptive and the same for every agent:
--fast-ticks (30) while any live raider is within --fast-radius (40) cells of a
squad pawn, else --step-ticks (120); a frag grenade rests ~90 ticks before it
blows, so only a short cycle leaves time to step away (results/hazards.md).
--cycle fixed restores one step size. Agents are told the step size and the
episode tick before each step (agent.step_ticks, agent.now); the reflex layer
(reflexes.py) is on unless --no-reflex; --reflex-version 2 runs the one-shot reflex
rules and the doctrine versions that go with them, 3 (default) the threat-heatmap
reflex (threatmap.py) and the doctrines that position by it. Agents get a client that refuses debug/dev-mode,
save/load and time-control tools. Outcomes are measured from game state only.

  python3 eval.py --agents b0,b1,doctrine --runs 3          # all scenarios
  python3 eval.py --agents b1 --scenarios smoke_pirates_vs_savage_open --runs 1
  python3 eval.py --summary                                  # table from results
  python3 eval.py --results results/theme.jsonl ...          # separate experiment file
  python3 eval.py --results results/theme.jsonl --resume ...  # finish a batch after a crash
  python3 eval.py --cycle fixed --no-reflex ...              # the pre-reflex setting
"""
import argparse
import json
import math
import statistics
import time
from collections import Counter
from pathlib import Path

from combat_agent import CombatAgent, Doctrine
from hold_agent import HoldAgent
from doctrines import Spread, Kite, Close
from battle_tracker import BattleTracker
from kpis import Tally, add_spacing, in_contact
from reflexes import LATEST_VERSION, attach
from rimmolt_client import RimMolt, RimMoltError
from scenario_builder import Builder

SCENARIO_DIR = Path("scenarios_out")
RESULTS = Path("results/results.jsonl")

# Lower is worse. Deaths dominate on purpose: nothing else should buy one back.
# Per-capita terms keep a 20-pawn squad from being punished just for its size.
WEIGHTS = {
    "enemy_neutralized_frac": 150,
    "death": -100,
    "downed_at_end": -5,
    "hp_lost_pct_per_pawn": -1,
    "new_permanent_per_pawn": -50,
}
# How the fight ended. A raid leaving the map is not a win by itself: it also
# leaves once it has beaten us. The game says which it was — "…are fleeing"
# (morale broke) vs "…are satisfied with the damage done and are leaving" — so
# that message decides. Rows without it fall back to thresholds fitted on runs
# that had it: satisfied raids had lost <= 46% of their pawns, fleeing ones >= 71%.
GRADE_BONUS = {"decisive": 50, "repelled": 30, "pyrrhic": 0, "unresolved": 0, "defeat": -50}
BROKE, INTACT, CLEAN_ESCAPE = 0.5, 0.5, 0.1


def grade(m):
    """decisive / repelled / pyrrhic / defeat / unresolved, from raw metrics."""
    if "enemies_escaped" not in m:                     # pre-tracker rows: best effort
        return "decisive" if m["win"] else "defeat"
    n = max(1, m["squad_size"])
    seen = max(1, m["enemies_seen"])
    if m["squad_kidnapped"] or m["deaths"] + m["downed_at_end"] >= n:
        return "defeat"
    if m.get("raid_satisfied_tick") is not None:       # they left because they won
        return "defeat"
    if m["enemies_active_end"] > 0:
        return "unresolved"
    if m["enemies_escaped"] <= CLEAN_ESCAPE * seen:
        return "decisive"
    if m.get("raid_fled_tick") is None:                # no message: fall back
        broken = (m["enemies_killed"] + m["enemies_killed_inferred"]
                  + m["enemies_downed_end"]) / seen
        if broken < BROKE:
            return "defeat"
    standing = (n - m["deaths"] - m["downed_at_end"]) / n
    return "repelled" if standing >= INTACT else "pyrrhic"


def is_win(m):
    return grade(m) in ("decisive", "repelled")


def score(m):
    """Score from raw metrics, so old results are rescored when WEIGHTS change."""
    n = max(1, m["squad_size"])
    return round(
        GRADE_BONUS[grade(m)]
        + WEIGHTS["enemy_neutralized_frac"] * m["enemy_neutralized_frac"]
        + WEIGHTS["death"] * m["deaths"]
        + WEIGHTS["downed_at_end"] * m["downed_at_end"]
        + WEIGHTS["hp_lost_pct_per_pawn"] * m["hp_lost_pct"] / n
        + WEIGHTS["new_permanent_per_pawn"] * m["new_permanent_injuries"] / n, 2)


AGENT_FORBIDDEN = {
    "dev_mode", "debug_menu", "load_game", "save_game", "return_to_title",
    "main_menu", "set_speed", "wait_for_event", "select_scenario",
    "select_storyteller", "create_world", "select_starting_site",
    "choose_ideoligion", "edit_ideoligion", "edit_starting_pawn", "start_game",
    "reform_ideoligion", "rename_pawn",
}
PERMANENT_WORDS = ("missing", "cut off", "shot off", "torn off", "bitten off", "destroyed")


class AgentClient:
    """What an agent is allowed to touch."""

    def __init__(self, rm):
        self._rm = rm

    def call(self, _tool, _timeout=None, **args):
        if _tool in AGENT_FORBIDDEN:
            raise RimMoltError(f"tool '{_tool}' is not available to agents")
        return self._rm.call(_tool, _timeout, **args)


# ---------------------------------------------------------------- agents
class B0:
    """Does nothing: vanilla colonists left to their own hostility response."""
    name = "b0"
    version = 1

    def reset(self, rm, manifest):
        pass

    def step(self, rm):
        pass


class B1:
    """'aggressive': draft everyone able, Auto attack the nearest active enemy
    (rocket carriers first while the reflex layer is on), retarget on loss.
    v2: reflex layer. v3 (with reflex v3): inside elevated-threat areas the map
    places the pawn and it fires from there (fallback: kill the thrower/carrier);
    Auto attack only where the local threat is low."""
    name = "b1"
    version = 2
    versions = {2: 2, 3: 4}     # reflex version -> agent version (3: reflex 3a, 4: 3b)
    reflex = True
    step_ticks, now = 120, 0

    def reset(self, rm, manifest):
        self.target = {}
        self.weapon = {}
        self.drafted = False
        self.rx = attach(self, rm, manifest)

    def step(self, rm):
        hostiles = active_hostiles(rm)
        if not hostiles:
            return
        cols = [c for c in rm.call("list_colonists")["colonists"]
                if not c.get("downed") and not c.get("mentalState")
                and "Violent" not in c.get("incapableOf", "")]
        if not self.drafted:
            rm.call("draft", action="draft", ids=",".join(c["id"] for c in cols))
            self.drafted = True
        alive = {h["id"] for h in hostiles}
        pos = {t["id"]: (t["x"], t["z"]) for t in rm.call(
            "list_things", category="pawn", confirm=True, faction="player", verbose=True)["things"]}
        fighters = [{"id": c["id"], "pos": pos[c["id"]], "job": c.get("job"),
                     "weapon": self.weapon.get(c["id"])} for c in cols if c["id"] in pos]
        busy = self.rx.step(fighters, hostiles, self.now, self.step_ticks)
        v3 = self.rx.version >= 3
        for c in cols:
            if c["id"] in busy:                 # dodging: re-attack once released
                self.target.pop(c["id"], None)
                continue
            if c["id"] not in pos or (self.target.get(c["id"]) in alive and not v3):
                continue
            if c["id"] not in self.weapon:
                self.weapon[c["id"]] = rm.call("get_pawn", id=c["id"]).get("weapon")
            if not self.weapon[c["id"]]:
                continue
            x, z = pos[c["id"]]
            near = min(hostiles, key=lambda h: (h["x"] - x) ** 2 + (h["z"] - z) ** 2)
            near = self.rx.priority_target((x, z), hostiles, near)
            if v3:
                me = {"id": c["id"], "pos": (x, z), "weapon": self.weapon[c["id"]]}
                if self.rx.place(me, hostiles, near, self.now, "kill"):
                    self.target.pop(c["id"], None)          # Auto attack again once it is calm
                    continue
                if self.target.get(c["id"]) in alive:
                    continue
            r = rm.call("do_thing_action", id=c["id"], label="Auto attack (AI)",
                        targetId=near["id"])
            if r.get("ok"):
                self.target[c["id"]] = near["id"]
        self.rx.count_modes(fighters, set(self.target), busy)

    def kpis(self):
        return self.rx.kpis()


class DoctrineAgent:
    """combat_agent.CombatAgent driven one plan_step per harness step ('focus').
    v3: reflex layer; cadences in ticks."""
    name = "doctrine"
    version = 3
    reflex = True
    step_ticks, now = 120, 0

    def reset(self, rm, manifest):
        sq = manifest["squad"]
        anchor = (round(statistics.median(p["x"] for p in sq)),
                  round(statistics.median(p["z"] for p in sq)))
        self.ca = CombatAgent(rm, Doctrine(anchor=anchor, announce=False), live=True)
        self.ca.rx = attach(self, rm, manifest)
        self.tally = Tally()

    def step(self, rm):
        cols, hostiles = self.ca.snapshot()
        self.ca.prev_now, self.ca.now = self.ca.now, self.now
        if hostiles:
            fit = [c for c in cols if self.ca.can_fight(c)]
            self.ca.dodging = self.ca.rx.step(fit, hostiles, self.now, self.step_ticks)
            self.ca.plan_step(cols, hostiles)
            self.ca.rx.count_modes(fit, set(self.ca.assign), self.ca.dodging)
            fighters = [c for c in cols if self.ca.can_fight(c)]
            if fighters and in_contact(fighters, hostiles):
                # Focus = few targets, many guns on each.
                on = [self.ca.assign[c["id"]] for c in fighters if c["id"] in self.ca.assign]
                self.tally.add("assigned_share", len(on) / len(fighters))
                if on:
                    self.tally.add("targets_per_step", len(set(on)))
                    self.tally.add("guns_per_target", len(on) / len(set(on)))
                add_spacing(self.tally, fighters)
                self.tally.add("attacking_share", sum(
                    (c.get("job") or "").startswith(("attacking", "melee attacking"))
                    for c in fighters) / len(fighters))
        self.ca.step += 1

    def kpis(self):
        return self.tally.summary() | self.ca.rx.kpis()


AGENTS = {a.name: a for a in (B0, B1, DoctrineAgent, HoldAgent, Spread, Kite, Close)}
# Renamed agents: old result rows and old command lines keep working.
ALIASES = {"hold": "turtle"}
AGENTS.update({old: AGENTS[new] for old, new in ALIASES.items()})


def canonical(name):
    return ALIASES.get(name, name)


# ---------------------------------------------------------------- measuring
def active_hostiles(rm):
    things = rm.call("list_things", category="pawn", confirm=True, faction="hostile", verbose=True)["things"]
    return [t for t in things if not t.get("downed") and not t.get("dead")]


def permanent_marks(rm, pid):
    h = rm.call("get_pawn", id=pid, tab="health")
    return Counter((d["label"], d.get("part")) for d in h.get("hediffs") or []
                   if d.get("permanent") or any(w in d["label"].lower() for w in PERMANENT_WORDS))


def squad_state(rm, ids):
    out = {}
    for pid in ids:
        p = rm.call("get_pawn", id=pid)
        if "error" in p or p.get("dead"):
            out[pid] = {"dead": True, "downed": False, "health": 0, "perm": Counter()}
        else:
            out[pid] = {"dead": False, "downed": bool(p.get("downed")),
                        "health": p.get("health", 0), "perm": permanent_marks(rm, pid)}
    return out


def squad_engaged(cols):
    """Squad pawns whose current job is shooting/swinging at something.
    ('moving.' — Auto attack repositioning — is not counted; enemies aimed at a
    colonist are, so the ratio is biased toward the enemy, equally for every agent.)"""
    return sum(1 for c in cols if not c.get("downed")
               and (c.get("job") or "").startswith(("attacking", "melee attacking")))


def measure(before, after, fates):
    """fates: BattleTracker.finish(). 'deaths' (what the score charges) = dead +
    kidnapped: a colonist carried off is lost to the colony either way."""
    lost = fates["squad_dead"] + fates["squad_kidnapped"]
    downed = sum(after[i]["downed"] for i in after)
    hp_lost = sum(max(0, before[i]["health"] - after[i]["health"]) for i in after)
    new_perm = sum(sum((after[i]["perm"] - before[i]["perm"]).values())
                   for i in after if not after[i]["dead"])
    neutral = (fates["enemies_killed"] + fates["enemies_killed_inferred"]
               + fates["enemies_downed_end"])
    m = {"deaths": lost, "downed_at_end": downed, "hp_lost_pct": hp_lost,
         "new_permanent_injuries": new_perm, "squad_size": len(after),
         "enemy_neutralized_frac": round(neutral / max(1, fates["enemies_seen"]), 3),
         **fates}
    m["grade"] = grade(m)
    m["win"] = is_win(m)
    m["score"] = score(m)
    return m


# ---------------------------------------------------------------- running
class Cycle:
    """Decision-cycle policy. Adaptive: `fast` ticks while any live raider is
    within `radius` cells of any squad pawn, else `calm`. Fixed: always `calm`."""

    def __init__(self, calm=120, fast=30, radius=40, adaptive=True):
        self.calm, self.fast, self.radius, self.adaptive = calm, fast, radius, adaptive

    @property
    def policy(self):
        """Stored in every row; --resume treats another policy as another config."""
        return (f"adaptive:{self.fast}/{self.calm}@{self.radius}" if self.adaptive
                else f"fixed:{self.calm}")

    def next(self, live, squad):
        if self.adaptive and any(
                math.dist((h["x"], h["z"]), (s["x"], s["z"])) <= self.radius
                for h in live for s in squad if s.get("x") is not None and not s["fate"]):
            return self.fast
        return self.calm


def row_config(r):
    """(cycle policy, reflex on, reflex version) of a result row; rows before the
    cycle change ran a fixed step without the reflex layer, and rows before
    reflex_version was stored ran reflex v1."""
    rx = bool(r.get("reflex"))
    return (r.get("cycle") or f"fixed:{r.get('step_ticks', 120)}", rx,
            r.get("reflex_version", 1) if rx else None)


def agent_version(cls, rx_version):
    """Doctrines changed for reflex v3 carry a version per reflex version."""
    return getattr(cls, "versions", {}).get(rx_version, getattr(cls, "version", None))


def run_episode(rm, manifest, agent, max_ticks, cycle, reflex=True, rx_version=LATEST_VERSION):
    Builder(rm).load(manifest["save"])  # leaves dev mode on
    # Vanilla drops to 1x whenever combat starts; that alone made runs ~10x slower.
    rm.call("debug_menu", action="run", tab="settings",
            path="Never Force Normal Speed", value=True)
    rm.call("debug_menu", action="close")
    rm.call("dev_mode", devMode=False)
    ids = [p["id"] for p in manifest["squad"]]
    before = squad_state(rm, ids)
    tracker = BattleTracker(rm, ids)
    live = tracker.observe(0)
    client = AgentClient(rm)
    errors = 0
    agent.reflex = reflex
    agent.rx_version = rx_version
    agent.version = agent_version(type(agent), rx_version)
    agent.now = 0
    try:
        agent.reset(client, manifest)
    except Exception as e:
        errors += 1
        print(f"   agent reset error: {e}")

    t0 = rm.call("get_status")["ticksGame"]
    wall0, think, steps, outcome = time.time(), 0.0, 0, "timeout"
    ticks, fast_steps = 0, 0
    eng_steps = eng_ours = eng_theirs = 0
    messages, raid_fled, raid_satisfied = {}, None, None
    while True:
        step_ticks = cycle.next(live, tracker.squad.values())
        fast_steps += step_ticks < cycle.calm
        agent.step_ticks, agent.now = step_ticks, ticks   # settings in ticks need both
        s0 = time.time()
        try:
            agent.step(client)
        except Exception as e:  # an agent crash costs it the step, not the run
            errors += 1
            print(f"   agent error: {e}")
        think += time.time() - s0
        steps += 1
        ev = rm.call("wait_for_event", _timeout=90, maxGameTicks=step_ticks, maxSeconds=60,
                     pause="always", force=True)
        ticks = rm.call("get_status")["ticksGame"] - t0
        for note in ev.get("_notifications") or []:     # the game's own account of events
            text = (note.get("text") or note.get("label") or "")[:160] if isinstance(note, dict) \
                else str(note)[:160]
            if text and text not in messages:
                messages[text] = ticks
                low = text.lower()
                if raid_fled is None and " are fleeing" in low:
                    raid_fled = ticks
                if raid_satisfied is None and "satisfied with the damage" in low:
                    raid_satisfied = ticks
        live = tracker.observe(ticks)
        engaged = sum(1 for t in live if (t.get("targeting") or "").startswith(
            ("targeting colonist", "attacking colonist")))
        squad = [c for c in rm.call("list_colonists")["colonists"] if c["id"] in ids]
        standing = [c for c in squad if not c.get("downed")]
        ours = squad_engaged(squad)
        if ours or engaged:
            eng_steps += 1
            eng_ours += ours
            eng_theirs += engaged
        if not live:
            outcome = "enemies_cleared"
            break
        if not standing:
            outcome = "squad_down"
            break
        if ticks >= max_ticks:
            break

    rm.call("set_speed", action="pause")
    try:
        kpis = agent.kpis() if hasattr(agent, "kpis") else None
    except Exception as e:
        kpis = {"error": repr(e)[:120]}
    after = squad_state(rm, ids)
    m = measure(before, after, tracker.finish())
    if m["squad_kidnapped"]:
        outcome = "raid_left_with_captives"
    m.update({"scenario": manifest["id"], "agent": agent.name,
              "agent_version": getattr(agent, "version", None), "kpis": kpis, "outcome": outcome,
              "ticks": ticks, "steps": steps, "agent_errors": errors,
              "agent_think_s": round(think, 2), "wall_s": round(time.time() - wall0, 1),
              "max_ticks": max_ticks, "step_ticks": cycle.calm, "cycle": cycle.policy,
              "reflex": reflex, "reflex_version": rx_version, "fast_steps": fast_steps, "time": time.time(),
              # Lanchester diagnostic: our shooters vs theirs, summed over engaged steps.
              "engaged_steps": eng_steps, "engaged_ours": eng_ours,
              "engaged_theirs": eng_theirs,
              "engagement_ratio": round(eng_ours / max(1, eng_theirs), 3),
              # Kept to validate grade(): does the game say the raid broke and fled?
              "raid_fled_tick": raid_fled, "raid_satisfied_tick": raid_satisfied,
              "game_messages": [{"tick": t, "text": x} for x, t in list(messages.items())[:60]]})
    return m


def superiority(xs, ys):
    """P(a random run from xs scores higher than one from ys); ties count half."""
    return sum((x > y) + 0.5 * (x == y) for x in xs for y in ys) / (len(xs) * len(ys))


def summarize(path=RESULTS, ref="b1"):
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    for r in rows:
        r["score"] = score(r)
        r["win"] = is_win(r)              # stored 'win' predates grading
    by = {}
    mixed = len({row_config(r) for r in rows}) > 1
    for r in rows:
        r["agent"] = canonical(r["agent"])
        if mixed:                         # never pool different cycle/reflex settings
            cyc, rx, rxv = row_config(r)
            r["agent"] += f"[{cyc}{f'+rx{rxv}' if rx else ''}]"
        by.setdefault((r["scenario"], r["agent"]), []).append(r)
    agents = sorted({a for _, a in by})
    scenarios = sorted({s for s, _ in by})

    def eng(v):
        return sum(r.get("engaged_ours", 0) for r in v) / max(1, sum(r.get("engaged_theirs", 0) for r in v))

    w = max(9, max(len(a) for a in agents))
    print(f"{'scenario':32} {'agent':{w}} {'n':>2} {'win%':>5} {'deaths':>6} "
          f"{'median':>7} {'P>' + ref:>6} {'eng':>5}")
    def ref_of(ag):                       # the reference run under the same setting
        return ref + ag[len(ag.split("[")[0]):]

    for (sc, ag), v in sorted(by.items()):
        scores = [r["score"] for r in v]
        refs = [r["score"] for r in by.get((sc, ref_of(ag)), [])]
        p = f"{superiority(scores, refs):6.2f}" if refs and ag != ref_of(ag) else f"{'-':>6}"
        has_eng = any("engaged_ours" in r for r in v)
        print(f"{sc:32} {ag:{w}} {len(v):>2} {100 * sum(r['win'] for r in v) / len(v):>5.0f} "
              f"{statistics.mean(r['deaths'] for r in v):>6.2f} {statistics.median(scores):>7.1f} "
              f"{p} {f'{eng(v):5.2f}' if has_eng else '    -'}")

    print(f"\nheadline (mean over {len(scenarios)} scenarios; P>{ref} 0.4-0.6 ~ tie at n=5)")
    for ag in agents:
        v = [r for r in rows if r["agent"] == ag]
        ps = [superiority([r["score"] for r in by[(sc, ag)]],
                          [r["score"] for r in by[(sc, ref_of(ag))]])
              for sc in scenarios if (sc, ag) in by and (sc, ref_of(ag)) in by]
        p = f"{statistics.mean(ps):.2f}" if ps and ag != ref_of(ag) else "-"
        print(f"  {ag:{w}} P>{ref}={p:>5}  deaths/battle={statistics.mean(r['deaths'] for r in v):.2f}"
              f"  win={statistics.mean(r['win'] for r in v):.2f}"
              f"  eng={f'{eng(v):.2f}' if any('engaged_ours' in r for r in v) else '-'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", default="b0,b1,doctrine")
    ap.add_argument("--scenarios", default="all", help="comma-separated ids or 'all'")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--max-ticks", type=int, default=20000, help="2500 = 1 in-game hour")
    ap.add_argument("--step-ticks", type=int, default=120,
                    help="calm cycle (and the only one with --cycle fixed)")
    ap.add_argument("--fast-ticks", type=int, default=30, help="cycle while raiders are close")
    ap.add_argument("--fast-radius", type=int, default=40,
                    help="cells between a live raider and a squad pawn that switch to --fast-ticks")
    ap.add_argument("--cycle", choices=("adaptive", "fixed"), default="adaptive")
    ap.add_argument("--no-reflex", dest="reflex", action="store_false",
                    help="reflex layer observes and counts but never acts")
    ap.add_argument("--reflex-version", type=int, choices=(2, 3), default=LATEST_VERSION,
                    help="2: one-shot reflex rules (+ the doctrine versions of that time); "
                         "3: threat-heatmap reflex and map positioning")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--results", type=Path, default=RESULTS)
    ap.add_argument("--resume", action="store_true",
                    help="only run what --results is missing to reach --runs per scenario/agent")
    a = ap.parse_args()
    if a.summary:
        summarize(a.results)
        raise SystemExit
    manifests = [json.loads(p.read_text()) for p in sorted(SCENARIO_DIR.glob("*.json"))]
    if a.scenarios != "all":
        want = set(a.scenarios.split(","))
        manifests = [m for m in manifests if m["id"] in want]
    a.results.parent.mkdir(exist_ok=True)
    cycle = Cycle(a.step_ticks, a.fast_ticks, a.fast_radius, a.cycle == "adaptive")
    done = Counter()
    if a.resume and a.results.exists():
        # Only rows from the current implementation and setting count: a changed
        # doctrine bumps its version, and another cycle policy or reflex setting
        # is another configuration; neither gets mixed in silently.
        done = Counter((r["scenario"], canonical(r["agent"])) for r in map(json.loads, filter(
            str.strip, a.results.read_text().splitlines()))
            if r.get("agent_version") == agent_version(AGENTS.get(r["agent"]), a.reflex_version)
            and row_config(r) == (cycle.policy, a.reflex, a.reflex_version if a.reflex else None))
    rm = RimMolt()
    for m in manifests:
        for name in a.agents.split(","):
            for run in range(done[(m["id"], name)], a.runs):
                print(f"== {m['id']} / {name} / run {run + 1} [{cycle.policy}"
                      f"{f' +reflex v{a.reflex_version}' if a.reflex else ''}]", flush=True)
                # A harness/game hiccup (timeout, load failure) costs one retry,
                # then the episode is logged as failed and the batch moves on.
                for attempt in range(2):
                    try:
                        res = run_episode(rm, m, AGENTS[name](), a.max_ticks, cycle, a.reflex,
                                          a.reflex_version)
                        break
                    except Exception as e:
                        print(f"   episode error (attempt {attempt + 1}): {e!r}", flush=True)
                        res = None
                        time.sleep(5)
                if res is None:
                    with a.results.with_suffix(".errors.jsonl").open("a") as f:
                        f.write(json.dumps({"scenario": m["id"], "agent": name,
                                            "run": run + 1, "cycle": cycle.policy,
                                            "reflex": a.reflex, "reflex_version": a.reflex_version,
                                            "time": time.time()}) + "\n")
                    continue
                with a.results.open("a") as f:
                    f.write(json.dumps(res, ensure_ascii=False) + "\n")
                print(f"   {res['outcome']} score={res['score']} win={res['win']} "
                      f"lost={res['deaths']}(dead {res['squad_dead']} kidnapped "
                      f"{res['squad_kidnapped']}) downed={res['downed_at_end']} | enemy "
                      f"seen {res['enemies_seen']} killed {res['enemies_killed']}+"
                      f"{res['enemies_killed_inferred']}? downed {res['enemies_downed_end']} "
                      f"escaped {res['enemies_escaped']} active {res['enemies_active_end']} "
                      f"(kills record {res['kills_record']}) ticks={res['ticks']} "
                      f"wall={res['wall_s']}s steps={res['steps']} fast={res['fast_steps']}",
                      flush=True)
                k = res.get("kpis") or {}
                if "rx_moves" in k:
                    print("   reflex: " + " ".join(f"{x[3:]}={k[x]}" for x in (
                        "rx_frags_seen", "rx_in_blast_at_landing", "rx_escaped",
                        "rx_stayed_in_blast", "rx_moves", "rx_nudges", "rx_too_late",
                        "rx_frag_hit_pawns", "rx_frag_hit_entries")), flush=True)
                    print("   map: " + " ".join(f"{x[3:]}={k.get(x)}" for x in (
                        "tm_returns_to_danger", "tm_high_share", "tm_ms_per_step",
                        "steps_auto", "steps_map", "rx_map_moves", "rx_fire_at")), flush=True)
    summarize(a.results)
