"""Episode harness (EVAL_SPEC §1-§3): the harness owns game time.

Each step: the agent observes and orders on a paused game through a sandboxed
client, then the harness advances step_ticks (adaptive: 30 while any live
raider is within 40 cells of a squad pawn without a fate, else 120), reads the
game's messages and the step's _delta, observes fates, and checks the stop
conditions. An agent exception costs it the step; a harness/game exception
retries the episode once after the watchdog has checked the game.

Strive to Survive lets the storyteller send its own threats: a hostile pawn
that was not on the map at the start ends the episode as 'invalid' (kept in
the file, skipped by every reader, re-run by run_batch). The game's difficulty
is checked at every episode start and stored in the row.
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
from .results import INVALID, SCHEMA, append_row, git_commit, row_config
from .tracker import BattleTracker

SCENARIO_DIR = ROOT / "scenarios_out"
FORBIDDEN = {
    "dev_mode", "debug_menu", "load_game", "save_game", "return_to_title", "main_menu",
    "set_speed", "wait_for_event", "select_scenario", "select_storyteller", "create_world",
    "select_starting_site", "choose_ideoligion", "edit_ideoligion", "edit_starting_pawn",
    "start_game", "reform_ideoligion", "rename_pawn"}
PERMANENT_WORDS = ("missing", "cut off", "shot off", "torn off", "bitten off", "destroyed")
STANDARD_DIFFICULTY = "strive to survive"         # WORKFLOW "Evaluation standard"
INVALID_TRIES = 3                                 # re-runs of a run disturbed by the storyteller


class WrongDifficulty(RuntimeError):
    """The loaded save is not on the evaluation difficulty: stop the batch."""


def unexpected_hostiles(start_ids, enemies):
    """Hostiles the tracker has seen that were not on the map at the episode
    start: a storyteller threat (raid, manhunter, mech cluster), not the scenario."""
    return {eid: e for eid, e in enemies.items() if eid not in start_ids}


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


def run_episode(rm, manifest, agent, max_ticks, cycle, reflex=True, log=print, options=None,
                difficulty=STANDARD_DIFFICULTY):
    session.start_episode(rm, manifest["save"])
    found = (rm.call("get_status").get("difficulty") or "").lower()
    if difficulty and found != difficulty:
        raise WrongDifficulty(f"{manifest['save']} is on {found!r}, not {difficulty!r}")
    ids = [p["id"] for p in manifest["squad"]]
    before = squad_state(rm, ids)
    tracker = BattleTracker(rm, ids)
    live = tracker.observe(0)
    start_ids, intruders = set(tracker.enemy), {}
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
        intruders = unexpected_hostiles(start_ids, tracker.enemy)
        if intruders:
            outcome = INVALID
            log(f"   invalid: {len(intruders)} unexpected hostiles at tick {ticks} "
                f"({sorted({e['kind'] for e in intruders.values()})})")
            break
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
    if m["squad_kidnapped"] and outcome != INVALID:
        outcome = "raid_left_with_captives"
    m.update({
        "schema": SCHEMA, "scenario": manifest["id"], "agent": agent.name,
        "agent_version": agent.version, "commit": git_commit(), "time": time.time(),
        "cycle": cycle.policy, "step_ticks": cycle.calm, "reflex": reflex,
        "reflex_version": getattr(agent, "rx_version", None), "max_ticks": max_ticks,
        "difficulty": found, "outcome": outcome,
        "invalid": ({"reason": "unexpected_hostiles", "tick": ticks,
                     "kinds": dict(Counter(e["kind"] for e in intruders.values()))}
                    if outcome == INVALID else None),
        "ticks": ticks, "steps": steps, "fast_steps": fast_steps,
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


def run_observed_episode(rm, manifest, max_ticks=15000, poll_s=1.0, log=print,
                         difficulty=STANDARD_DIFFICULTY, player="human", trace=None):
    """Observe-only episode: a person plays, the harness never pauses or
    advances time. It loads the scenario (paused; the player unpauses), then
    polls every poll_s seconds of wall time: fates, contact windows, the
    storyteller guard and the stop conditions, and writes the same row as
    run_episode (agent = player, cycle 'observed'). Game messages come from
    get_alerts' recent messages (there is no wait_for_event to carry them).
    trace (rca.eval.trace.Trace) records every poll: positions, weapons, jobs."""
    session.start_episode(rm, manifest["save"])
    found = (rm.call("get_status").get("difficulty") or "").lower()
    if difficulty and found != difficulty:
        raise WrongDifficulty(f"{manifest['save']} is on {found!r}, not {difficulty!r}")
    ids = [p["id"] for p in manifest["squad"]]
    before = squad_state(rm, ids)
    tracker = BattleTracker(rm, ids)
    live = tracker.observe(0)
    start_ids, intruders = set(tracker.enemy), {}
    t0 = rm.call("get_status")["ticksGame"]
    wall0, polls, ticks, last, outcome = time.time(), 0, 0, -1, "timeout"
    progress, avail_o, avail_t = ProgressMeter(), {}, {}
    messages, fled, satisfied = {}, None, None
    # Toasts from before the load (the previous battle's "... are fleeing") are still in
    # recentMessages; skip exactly those (tick, text) pairs. A new message with the same
    # text has another tick and still counts.
    stale = {(n.get("tick"), (n.get("text") or "")[:160])
             for n in (rm.call("get_alerts").get("recentMessages") or [])}
    log(f"   {manifest['id']} loaded and paused: play when ready (the harness only watches)")
    while True:
        time.sleep(poll_s)
        try:
            ticks = rm.call("get_status")["ticksGame"] - t0
        except RimMoltError:
            continue
        if ticks == last:                       # paused: nothing to observe
            continue
        last, polls, new = ticks, polls + 1, []
        for note in (rm.call("get_alerts").get("recentMessages") or []):
            text = (note.get("text") or "")[:160]
            if (note.get("tick"), text) in stale:
                continue
            if text and text not in messages:
                messages[text] = ticks
                new.append(text)
                low = text.lower()
                if fled is None and " are fleeing" in low:
                    fled = ticks
                if satisfied is None and "satisfied with the damage" in low:
                    satisfied = ticks
        live = tracker.observe(ticks)
        if trace:
            trace.poll(rm, ticks, new)
        intruders = unexpected_hostiles(start_ids, tracker.enemy)
        if intruders:
            outcome = INVALID
            log(f"   invalid: {len(intruders)} unexpected hostiles at tick {ticks}")
            break
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
        squad = [c for c in rm.call("list_colonists")["colonists"] if c["id"] in ids]
        if not live:
            outcome = "enemies_cleared"
            break
        if not any(not c.get("downed") for c in squad):
            outcome = "squad_down"
            break
        if ticks >= max_ticks:
            break
    rm.call("set_speed", action="pause")
    m = measure(before, squad_state(rm, ids), tracker.finish())
    if m["squad_kidnapped"] and outcome != INVALID:
        outcome = "raid_left_with_captives"
    m.update({
        "schema": SCHEMA, "scenario": manifest["id"], "agent": player, "agent_version": 1,
        "commit": git_commit(), "time": time.time(), "cycle": "observed", "step_ticks": None,
        "reflex": False, "reflex_version": None, "max_ticks": max_ticks,
        "difficulty": found, "outcome": outcome,
        "invalid": ({"reason": "unexpected_hostiles", "tick": ticks,
                     "kinds": dict(Counter(e["kind"] for e in intruders.values()))}
                    if outcome == INVALID else None),
        "ticks": ticks, "steps": polls, "fast_steps": 0, "agent_errors": 0, "agent_think_s": None,
        "wall_s": round(time.time() - wall0, 1),
        "raid_fled_tick": fled, "raid_satisfied_tick": satisfied,
        "game_messages": [{"tick": t, "text": x} for x, t in list(messages.items())[:60]],
        "building_deltas": {}, "engaged_steps": 0, "engaged_ours": 0, "engaged_theirs": 0,
        "engagement_ratio": None,
        **engagement_kpis(tracker, avail_o, avail_t),
        **progress.summary(),
        "options": {}, "signals": [], "unattainable_tick": None, "unattainable_reason": None,
        "kpis": {"observed": True, "poll_s": poll_s, "polls": polls}})
    m.update(verdict(m, scoring.manifest_mean_points(manifest)))
    if trace:
        trace.end(m)
    return m


def run_batch(rm, manifests, agent_names, runs, results, cycle, reflex=True, max_ticks=15000,
              resume=False, watchdog=None, log=print, options=None,
              difficulty=STANDARD_DIFFICULTY):
    """Run each (scenario, agent) up to `runs` rows in `results`; failed
    episodes go to <results>.errors.jsonl and are retried by the next --resume.
    options (e.g. {"vs_throwers": "stand_off"}) apply to agents that offer them
    and are part of the resume key, as is the difficulty (None = don't check).
    An invalid episode (storyteller threat) is written and the run repeated, up
    to INVALID_TRIES times. A save on the wrong difficulty stops the batch."""
    from ..tactical import make, options_of, version_of
    from .results import canonical, done_counts, read_rows
    names = [canonical(a) for a in agent_names]
    config = (cycle.policy, reflex, make(names[0]).rx_version if reflex else None)
    done = Counter()
    if resume and results.exists():
        done = done_counts(read_rows(results), version_of, config,
                           lambda a: options_of(a, options), lambda a: options_of(a),
                           difficulty)
    for m in manifests:
        for name in names:
            for run in range(done[(m["id"], name)], runs):
                log(f"== {m['id']} / {name} / run {run + 1} [{cycle.policy}"
                    f"{f' +rx{config[2]}' if reflex else ''}]")
                for _ in range(INVALID_TRIES):
                    res = run_attempts(rm, m, name, max_ticks, cycle, reflex, log, options,
                                       difficulty, watchdog)
                    if res is None or res["outcome"] != INVALID:
                        break
                    append_row(results, res)
                    log("   re-running the invalid episode")
                if res is not None and res["outcome"] == INVALID:
                    log(f"   still invalid after {INVALID_TRIES} tries; a later --resume retries")
                    continue
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


def run_attempts(rm, m, name, max_ticks, cycle, reflex, log, options, difficulty, watchdog):
    """One episode, retried once on a harness/game error; None if both failed."""
    from ..tactical import make
    for attempt in range(2):
        try:
            if watchdog:
                watchdog.ensure()
            return run_episode(rm, m, make(name), max_ticks, cycle, reflex, log, options,
                               difficulty)
        except WrongDifficulty:
            raise
        except Exception as e:
            log(f"   episode error (attempt {attempt + 1}): {e!r}")
            time.sleep(5)
        finally:
            if watchdog:
                watchdog.episode_done()
    return None
