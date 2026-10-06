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



class XenotypeTableTest(unittest.TestCase):
    def test_factions_expected_factor(self):
        import tempfile
        from rca.game import defs
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "Data" / "Biotech" / "Defs"
            d.mkdir(parents=True)
            (d / "x.xml").write_text("""<Defs>
<XenotypeDef><defName>Neanderthal</defName><combatPowerFactor>1.6</combatPowerFactor></XenotypeDef>
<XenotypeDef><defName>Waster</defName></XenotypeDef>
<FactionDef Name="Base" Abstract="True"/>
<FactionDef ParentName="Base"><defName>Plain</defName></FactionDef>
<FactionDef ParentName="Base"><defName>Neander</defName><xenotypeSet><xenotypeChances><Neanderthal>999</Neanderthal></xenotypeChances></xenotypeSet></FactionDef>
<FactionDef ParentName="Base"><defName>Mixed</defName><xenotypeSet><xenotypeChances><Neanderthal>0.5</Neanderthal><Waster>0.25</Waster></xenotypeChances></xenotypeSet></FactionDef>
</Defs>""")
            x = defs.extract_xenotypes(tmp)
        self.assertEqual(x["xenotype"], {"Neanderthal": 1.6, "Waster": 1.0})
        self.assertEqual(x["faction"]["Plain"], 1.0)
        self.assertEqual(x["faction"]["Neander"], 1.6)
        self.assertEqual(x["faction"]["Mixed"], 1.3)          # 0.5 x 1.6 + 0.25 x 1 + 0.25 baseliners


class FakeGame:
    def __init__(self):
        self.pawns = {"player": [{"id": "A", "label": "A"}, {"id": "B", "label": "B", "downed": True}],
                      "hostile": [{"id": "R1", "label": "R1", "kind": "Tribal_Warrior"},
                                  {"id": "R2", "label": "R2", "kind": "Tribal_Warrior", "dead": True}]}
        self.health = {"A": 50, "R1": 80}

    def call(self, name, **kw):
        if name == "list_things":
            return {"things": self.pawns[kw["faction"]]}
        if name == "get_pawn":
            return {"health": self.health[kw["id"]]}
        raise AssertionError(name)


class StrengthTest(unittest.TestCase):
    def test_modes(self):
        s = overlay.Strength(FakeGame(), None)            # no manifest: FALLBACK points for ours
        self.assertEqual(s.basis, "no manifest")
        warrior = overlay.defs.combat_power("Tribal_Warrior")
        full = s.update(FakeGame(), 100, "standing")
        self.assertEqual(full["ours"]["now"], round(s.FALLBACK))            # A standing; B downed counts 0
        self.assertEqual(full["raid"]["now"], round(warrior))               # R2 dead
        hw = s.update(FakeGame(), 160, "health")
        self.assertEqual(hw["ours"]["now"], round(s.FALLBACK * 0.5))
        self.assertEqual(hw["raid"]["now"], round(warrior * 0.8))
        self.assertEqual(hw["ours"]["start"], round(s.FALLBACK))           # the highest total seen
        self.assertEqual(hw["series"][-1][0], 60)


if __name__ == "__main__":
    unittest.main()
