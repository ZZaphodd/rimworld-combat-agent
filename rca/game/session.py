"""Load + ready wait, episode setup and the crash watchdog (PROCEDURES §3, §9, §10)."""
import subprocess
import time

from ..rimmolt import RimMoltError

STEAM_URL = "steam://rungameid/294100"
PROCESS = "RimWorld by Ludeon Studios"     # macOS process name (pgrep -f)
RESTART_EVERY = 100        # episodes; loads degrade the game (~150 loads -> native crash)
# Only these saves may be written: personal colony saves must never be touched.
WRITABLE = ("arena_", "scenario_", "theme_base", "drill_")


def load(rm, save, dev=True):
    """Load `save` and wait until the map really answers. Leaves the game paused
    and dev mode on (builders need it; episode setup turns it off)."""
    r = rm.call("load_game", name=save, confirm=True)
    if not r.get("ok", True) and "error" in r:
        raise RimMoltError(f"load_game {save}: {r['error']}")
    for _ in range(180):
        time.sleep(1)
        try:
            if rm.call("game_setup_status").get("programState") == "Playing":
                break
        except Exception:
            continue                       # busy while the map loads
    else:
        raise TimeoutError(f"{save} did not load")
    # 'Playing' flips before the map is up; wait until queries answer.
    for _ in range(30):
        try:
            if rm.call("get_status").get("loaded") and rm.call("list_colonists").get("colonists"):
                break
        except RimMoltError:
            pass                           # NullReferenceException while settling
        time.sleep(1)
    time.sleep(2)
    rm.call("set_speed", action="pause")
    if dev:
        rm.call("dev_mode", devMode=True)


def save(rm, name):
    if not name.startswith(WRITABLE):
        raise RimMoltError(f"refusing to save over {name!r}: not an arena/scenario save")
    rm.call("set_speed", action="pause")
    r = rm.call("save_game", name=name, overwrite=True)
    if not r.get("ok"):
        raise RimMoltError(f"save_game {name}: {r}")


def never_force_normal_speed(rm):
    """Vanilla drops to 1x whenever combat starts (~10x slower runs). The setting
    has to be set after every load."""
    rm.call("debug_menu", action="run", tab="settings", path="Never Force Normal Speed",
            value=True)
    rm.call("debug_menu", action="close")


def start_episode(rm, save_name):
    """PROCEDURES §9: load, Never Force Normal Speed, dev mode off for the agent."""
    load(rm, save_name)
    never_force_normal_speed(rm)
    rm.call("dev_mode", devMode=False, godMode=False)


def game_process():
    try:
        return subprocess.run(["pgrep", "-f", PROCESS], capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


class Watchdog:
    """Relaunch a dead game (PROCEDURES §10). A live but busy process gets 60 s
    first; more than `max_restarts` crash relaunches stop the batch (two
    failures -> report, never a second game instance). Planned restarts every
    `restart_every` episodes (NullReferenceExceptions grow after ~100 loads, a
    native crash came at ~150) quit the game, wait until the process is gone,
    and relaunch; they don't count against max_restarts."""

    def __init__(self, rm, max_restarts=2, boot_timeout=300, restart_every=RESTART_EVERY,
                 log=print):
        self.rm, self.max_restarts, self.boot_timeout, self.log = rm, max_restarts, boot_timeout, log
        self.restart_every = restart_every
        self.restarts, self.planned, self.episodes = 0, 0, 0

    def episode_done(self):
        self.episodes += 1

    def planned_restart(self):
        """Quit (SIGTERM, then SIGKILL after 60 s) and relaunch. Episodes never
        save, so nothing is lost."""
        self.log(f"   watchdog: planned restart after {self.episodes} episodes")
        subprocess.run(["pkill", "-f", PROCESS], check=False)
        for i in range(24):
            time.sleep(5)
            if not game_process():
                break
            if i == 11:
                subprocess.run(["pkill", "-9", "-f", PROCESS], check=False)
        else:
            raise RimMoltError("game process did not exit for the planned restart")
        self.planned += 1
        self.episodes = 0
        self._launch()

    def _launch(self):
        subprocess.run(["open", STEAM_URL], check=False)
        t0 = time.time()
        while time.time() - t0 < self.boot_timeout:
            time.sleep(5)
            if self.rm.alive():
                time.sleep(20)             # main menu up; let mods finish
                return
        raise RimMoltError("game did not come back within the boot timeout")

    def ensure(self):
        if self.restart_every and self.episodes >= self.restart_every and self.rm.alive():
            self.planned_restart()
            return
        if self.rm.alive():
            return
        if game_process():
            self.log("   watchdog: game process exists but does not answer; waiting 60 s")
            time.sleep(60)
            if self.rm.alive():
                return
            raise RimMoltError("game process alive but RimMolt does not answer")
        if self.restarts >= self.max_restarts:
            raise RimMoltError(f"game down after {self.restarts} restarts; giving up")
        self.restarts += 1
        self.episodes = 0
        self.log(f"   watchdog: relaunching RimWorld (restart {self.restarts})")
        self._launch()
