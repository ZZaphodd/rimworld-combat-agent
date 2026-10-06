"""rca.game.live (the battle-start signal through macOS notify) and tools/overlay.parse."""
import sys
import unittest
from pathlib import Path

from rca.game import live

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import overlay  # noqa: E402

NAMES = (b"org.rca.test.episode.start", b"org.rca.test.episode.pid")   # never the real names


@unittest.skipUnless(sys.platform == "darwin", "macOS notify only")
class LiveTest(unittest.TestCase):
    def test_announce_then_read(self):
        self.assertTrue(live.announce(now_ms=1791290000123, pid=4242, names=NAMES))
        self.assertEqual(live.read(names=NAMES), (1791290000123, 4242))
        live.announce(now_ms=1791290000999, pid=4343, names=NAMES)
        self.assertEqual(live.read(names=NAMES), (1791290000999, 4343))

    def test_unset_name_reads_zero(self):
        self.assertEqual(live.read(names=(b"org.rca.test.never.start", b"org.rca.test.never.pid")), (0, 0))


class ParseTest(unittest.TestCase):
    def test_harness_command_lines(self):
        py = "/opt/homebrew/bin/python3 /Users/x/repo/tools/"
        self.assertEqual(overlay.parse(py + "night.py run base2_ith_pirate_2x --agent turtle --max-ticks 30000"),
                         ("base2_ith_pirate_2x", "turtle"))
        self.assertEqual(overlay.parse(py + "run_human.py --manifest scenarios_base/scenario_base_mon_tribe_3x.json "
                                       "--player human --max-ticks 30000"), ("base_mon_tribe_3x", "you"))
        self.assertEqual(overlay.parse(py + "run_human.py --manifest scenarios_rand/scenario_rand_118.json --player claude"),
                         ("rand_118", "claude"))
        self.assertEqual(overlay.parse(py + "run_human.py --scenario t500_pirate_mixed"), ("t500_pirate_mixed", "you"))
        self.assertEqual(overlay.parse(py + "run_drill.py --drill kite"), ("run_drill", None))


if __name__ == "__main__":
    unittest.main()
