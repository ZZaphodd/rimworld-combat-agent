"""Episode harness (EVAL_SPEC §1-§3): the harness owns game time.

Each step: the agent observes and orders on a paused game through a sandboxed
client, then the harness advances step_ticks (adaptive: 30 while any live
raider is within 40 cells of a squad pawn without a fate, else 120), reads the
game's messages and the step's _delta, observes fates, and checks the stop
conditions. An agent exception costs it the step; a harness/game exception
retries the episode once after the watchdog has checked the game.
"""
import json
import math
import time
from collections import Counter

from .. import ROOT
from ..game import session
from ..rimmolt import RimMoltError
from ..terrain import Terrain
from . import firelog, scoring
from .kpis import CONTACT
from .progress import ProgressMeter
from .results import SCHEMA, append_row, git_commit, row_config
from .tracker import BattleTracker

SCENARIO_DIR = ROOT / "scenarios_out"
FORBIDDEN = {
    "dev_mode", "debug_menu", "load_game", "save_game", "return_to_title", "main_menu",
    "set_speed", "wait_for_event", "select_scenario", "select_storyteller", "create_world",
    "select_starting_site", "choose_ideoligion", "edit_ideoligion", "edit_starting_pawn",
    "start_game", "reform_ideoligion", "rename_pawn"}
PERMANENT_WORDS = ("missing", "cut off", "shot off", "torn off", "bitten off", "destroyed")


class Sandbox:
    """What an agent may touch: no time, saves or debug (RIMMOLT_API §6)."""

    def __init__(self, rm):
        self._rm = rm

    def call(self, _tool, _timeout=None, **args):
        if _tool in FORBIDDEN:
            raise RimMoltError(f"tool '{_tool}' is not available to agents")
        return self._rm.call(_tool, _timeout, **args)


class Cycle:
    def __init__(self, calm=120, fast=30, radius=40, adaptive=True):
        self.calm, self.fast, self.radius, self.adaptive = calm, fast, radius, adaptive

    @property
    def policy(self):
        return f"adaptive:{self.fast}/{self.calm}@{self.radius}" if self.adaptive else f"fixed:{self.calm}"

    def next(self, live, squad):
        if self.adaptive and any(math.dist((h["x"], h["z"]), (s["x"], s["z"])) <= self.radius
                                 for h in live for s in squad
                                 if s.get("x") is not None and not s["fate"]):
            return self.fast
        return self.calm


def load_manifests(ids="all"):
    """'all' = every non-check scenario: frag_check (tier check) is a drill
    scenario and must be named explicitly (LESSONS bug 13). 'tier:<t>' = every
    scenario of one tier, e.g. tier:t500 (the 500-pt theme set)."""
    ms = [json.loads(p.read_text()) for p in sorted(SCENARIO_DIR.glob("*.json"))]
    if ids == "all":
        return [m for m in ms if m["spec"].get("tier") != "check"]
    if isinstance(ids, str) and ids.startswith("tier:"):
        return [m for m in ms if m["spec"].get("tier") == ids[5:]]
    want = ids.split(",") if isinstance(ids, str) else list(ids)
    by = {m["id"]: m for m in ms}
    missing = [i for i in want if i not in by]
    if missing:
        raise SystemExit(f"unknown scenarios: {missing}")
    return [by[i] for i in want]


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


def measure(before, after, fates):
    """deaths = dead + kidnapped: a colonist carried off is lost either way."""
    m = {"deaths": fates["squad_dead"] + fates["squad_kidnapped"],
         "downed_at_end": sum(after[i]["downed"] for i in after),
         "hp_lost_pct": sum(max(0, before[i]["health"] - after[i]["health"]) for i in after),
         "new_permanent_injuries": sum(sum((after[i]["perm"] - before[i]["perm"]).values())
                                       for i in after if not after[i]["dead"]),
         "squad_size": len(after), **fates}
    m["enemy_neutralized_frac"] = round(scoring.enemy_lost_count(m) / max(1, m["enemies_seen"]), 3)
    return m


def verdict(m, mean_points=None, colonist_enemies=scoring.COLONIST_ENEMIES):
    """Derived fields, stored for the console only: reports recompute them."""
    g = scoring.grade(m)
    t = scoring.trade(m, mean_points, colonist_enemies)
    return {"grade": g, "win": scoring.is_win(g), "score_v1": scoring.score_v1(m, scoring.grade),
            "trade_enemy_points": t["enemy_lost_points"], "trade_our_points": t["our_lost_points"],
            "ler": scoring.json_ler(t["ler"]), "ler_basis": t["ler_basis"],
            "colonist_enemies": colonist_enemies}


def engagement_kpis(tracker, avail_ours, avail_theirs):
    """fire_share / surface per side from the pooled battle log (firelog)."""
    ours = {s["name"] for s in tracker.squad.values() if s["name"]}
    theirs = {e["name"] for e in tracker.enemy.values()}
    both = ours & theirs                       # same short name on both sides: unattributable
    names = (ours | theirs) - both
    off = tracker.log_offset or 0
    fired = firelog.fired_windows(sorted(tracker.combat), off, names)
    fs_o, surf_o = firelog.share(fired, {n: w for n, w in avail_ours.items() if n not in both})
    fs_t, surf_t = firelog.share(fired, {n: w for n, w in avail_theirs.items() if n not in both})
    return {"fire_share": fs_o, "enemy_fire_share": fs_t, "surface_ours": surf_o,
            "surface_theirs": surf_t, "fire_window_ticks": firelog.WINDOW,
            "fire_names_ambiguous": sorted(both), "log_entries": len(tracker.combat)}


def run_episode(rm, manifest, agent, max_ticks, cycle, reflex=True, log=print, options=None):
    session.start_episode(rm, manifest["save"])
    ids = [p["id"] for p in manifest["squad"]]
    before = squad_state(rm, ids)
    tracker = BattleTracker(rm, ids)
    live = tracker.observe(0)
    terrain = Terrain(rm)                       # per episode: never shared (LESSONS §4.2)
    client, errors = Sandbox(rm), 0
    agent.reflex, agent.terrain, agent.now = reflex, terrain, 0
    agent.options = dict(options or {})
    try:
        agent.reset(client, manifest)
    except Exception as e:
        errors += 1
        log(f"   agent reset error: {e!r}")
    t0 = rm.call("get_status")["ticksGame"]
    wall0, think, steps, fast_steps, ticks, outcome = time.time(), 0.0, 0, 0, 0, "timeout"
    eng = Counter()
    progress, avail_o, avail_t = ProgressMeter(), {}, {}
    messages, fled, satisfied, deltas = {}, None, None, Counter()
    while True:
        step = cycle.next(live, tracker.squad.values())
        fast_steps += step < cycle.calm
        agent.step_ticks, agent.now = step, ticks
        s0 = time.time()
        try:
            agent.step(client)
        except Exception as e:                  # an agent crash costs it the step
            errors += 1
            log(f"   agent error: {e!r}")
        think += time.time() - s0
        steps += 1
        ev = rm.wait(step)
        ticks = rm.call("get_status")["ticksGame"] - t0
        for note in ev.get("_notifications") or []:
            text = ((note.get("text") or note.get("label") or "") if isinstance(note, dict)
                    else str(note))[:160]
            if text and text not in messages:
                messages[text] = ticks
                low = text.lower()
                if fled is None and " are fleeing" in low:
                    fled = ticks
                if satisfied is None and "satisfied with the damage" in low:
                    satisfied = ticks
        delta = ev.get("_delta") or {}
        deltas.update(k for k in ("newBuildings", "removedBuildings") if delta.get(k))
        live = tracker.observe(ticks)
        squad_pos = [(s["x"], s["z"]) for s in tracker.squad.values()
                     if s.get("x") is not None and not s["fate"]]
        terrain.update(ticks, delta=delta, squad=squad_pos, contact=step < cycle.calm)
        standing = [(s_["x"], s_["z"]) for s_ in tracker.squad.values()
                    if s_.get("x") is not None and not s_["fate"] and not s_["downed"]]
        contact = any(math.dist(p, (h["x"], h["z"])) <= CONTACT for p in standing for h in live)
        progress.update(ticks, tracker.lost_points(), contact)
        if contact:
            w = ticks // firelog.WINDOW
            for s_ in tracker.squad.values():
                if s_["name"] and not s_["fate"] and not s_["downed"]:
                    avail_o.setdefault(s_["name"], set()).add(w)
            for e in tracker.enemy.values():
                if e["fate"] is None and not e.get("downed"):
                    avail_t.setdefault(e["name"], set()).add(w)
        theirs = sum((t.get("targeting") or "").startswith(("targeting colonist", "attacking colonist"))
                     for t in live)
        squad = [c for c in rm.call("list_colonists")["colonists"] if c["id"] in ids]
        ours = sum((c.get("job") or "").startswith(("attacking", "melee attacking"))
                   for c in squad if not c.get("downed"))
        if ours or theirs:
            eng.update(steps=1, ours=ours, theirs=theirs)
        if not live:
            outcome = "enemies_cleared"
            break
        if not any(not c.get("downed") for c in squad):
            outcome = "squad_down"
            break
        if ticks >= max_ticks:
            break
    rm.call("set_speed", action="pause")
    try:
        kpis = agent.kpis()
    except Exception as e:
        kpis = {"error": repr(e)[:120]}
    m = measure(before, squad_state(rm, ids), tracker.finish())
    signals = list(getattr(agent, "signals", []) or [])
    if m["squad_kidnapped"]:
        outcome = "raid_left_with_captives"
    m.update({
        "schema": SCHEMA, "scenario": manifest["id"], "agent": agent.name,
        "agent_version": agent.version, "commit": git_commit(), "time": time.time(),
        "cycle": cycle.policy, "step_ticks": cycle.calm, "reflex": reflex,
        "reflex_version": getattr(agent, "rx_version", None), "max_ticks": max_ticks,
        "outcome": outcome, "ticks": ticks, "steps": steps, "fast_steps": fast_steps,
        "agent_errors": errors, "agent_think_s": round(think, 2),
        "wall_s": round(time.time() - wall0, 1),
        "raid_fled_tick": fled, "raid_satisfied_tick": satisfied,
        "game_messages": [{"tick": t, "text": x} for x, t in list(messages.items())[:60]],
        "building_deltas": dict(deltas),
        # Biased: fire at will shows 'watching for targets' (EVAL_SPEC §8, LESSONS bug 9).
        "engaged_steps": eng["steps"], "engaged_ours": eng["ours"],
        "engaged_theirs": eng["theirs"],
        "engagement_ratio": round(eng["ours"] / max(1, eng["theirs"]), 3),
        **engagement_kpis(tracker, avail_o, avail_t),
        **progress.summary(),
        "options": agent.effective_options() if hasattr(agent, "effective_options") else {},
        "signals": signals[:10],
        "unattainable_tick": signals[0]["tick"] if signals else None,
        "unattainable_reason": signals[0]["reason"] if signals else None,
        "kpis": kpis})
    m.update(verdict(m, scoring.manifest_mean_points(manifest)))
    return m


def run_batch(rm, manifests, agent_names, runs, results, cycle, reflex=True, max_ticks=15000,
              resume=False, watchdog=None, log=print, options=None):
    """Run each (scenario, agent) up to `runs` rows in `results`; failed
    episodes go to <results>.errors.jsonl and are retried by the next --resume.
    options (e.g. {"vs_throwers": "stand_off"}) apply to agents that offer them
    and are part of the resume key."""
    from ..tactical import make, options_of, version_of
    from .results import canonical, done_counts, read_rows
    names = [canonical(a) for a in agent_names]
    config = (cycle.policy, reflex, make(names[0]).rx_version if reflex else None)
    done = Counter()
    if resume and results.exists():
        done = done_counts(read_rows(results), version_of, config,
                           lambda a: options_of(a, options), lambda a: options_of(a))
    for m in manifests:
        for name in names:
            for run in range(done[(m["id"], name)], runs):
                log(f"== {m['id']} / {name} / run {run + 1} [{cycle.policy}"
                    f"{f' +rx{config[2]}' if reflex else ''}]")
                res = None
                for attempt in range(2):
                    try:
                        if watchdog:
                            watchdog.ensure()
                        res = run_episode(rm, m, make(name), max_ticks, cycle, reflex, log, options)
                        break
                    except Exception as e:
                        log(f"   episode error (attempt {attempt + 1}): {e!r}")
                        time.sleep(5)
                    finally:
                        if watchdog:
                            watchdog.episode_done()
                if res is None:
                    append_row(results.with_suffix(".errors.jsonl"), {
                        "scenario": m["id"], "agent": name, "run": run + 1, "cycle": cycle.policy,
                        "reflex": reflex, "time": time.time()})
                    continue
                append_row(results, res)
                log(f"   {res['outcome']} grade={res['grade']} LER={res['ler']} "
                    f"lost={res['deaths']} downed={res['downed_at_end']} | enemy seen "
                    f"{res['enemies_seen']} killed {res['enemies_killed']}+"
                    f"{res['enemies_killed_inferred']}? downed {res['enemies_downed_end']} "
                    f"escaped {res['enemies_escaped']} active {res['enemies_active_end']} "
                    f"pts {res['trade_enemy_points']}/{res.get('enemy_seen_points')} "
                    f"rate={res['progress_rate']} stall={res['longest_no_progress_ticks']} "
                    f"fire={res['fire_share']}/{res['enemy_fire_share']} "
                    f"contested={(res.get('kpis') or {}).get('longest_contested_ticks')} "
                    f"signal={res['unattainable_reason']} "
                    f"ticks={res['ticks']} wall={res['wall_s']}s")
    return row_config({"cycle": cycle.policy, "reflex": reflex, "reflex_version": config[2]})
