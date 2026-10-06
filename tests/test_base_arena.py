"""rca.game.builders.base: edit_save (items out by id at any depth, storyteller set), the make/strip
name guards, strip_targets (shelves, basins and bill-takers; one list_recipes per def)."""
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from rca.game.builders import base

SAVE = """<?xml version="1.0" encoding="utf-8"?>
<savegame><meta><gameVersion>1.6</gameVersion></meta><game>
<storyteller><def>Cassandra</def><difficulty>Custom</difficulty><difficultyValues><threatScale>2</threatScale></difficultyValues></storyteller>
<maps><li><things>
<thing Class="ThingWithComps"><def>Steel</def><id>Steel1</id></thing>
<thing Class="Building_Turret"><def>Turret_MiniTurret</def><id>Turret_MiniTurret2</id></thing>
<thing Class="MinifiedThing"><def>MinifiedThing</def><id>MinifiedThing3</id><innerContainer><innerList><li><def>Bed</def><id>Bed4</id></li></innerList></innerContainer></thing>
<thing Class="Building_Storage"><def>Shelf</def><id>Shelf5</id><innerContainer><innerList><li><def>MealSimple</def><id>MealSimple6</id></li></innerList></innerContainer></thing>
<thing Class="Thing"><def>ChunkGranite</def><id>ChunkGranite7</id></thing>
</things></li></maps></game></savegame>
"""


class EditSaveTest(unittest.TestCase):
    def test_items_out_buildings_kept_storyteller_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "arena_col_x.rws"
            p.write_text(SAVE)
            n = base.edit_save(p, {"Steel1", "MinifiedThing3", "MealSimple6"})
            root = ET.parse(p).getroot()
            ids = {e.text for e in root.iter("id")}
            self.assertEqual(n, 3)
            self.assertEqual(ids, {"Turret_MiniTurret2", "Shelf5", "ChunkGranite7"})
            st = root.find("game/storyteller")
            self.assertEqual((st.findtext("def"), st.findtext("difficulty")), ("Phoebe", "Rough"))
            self.assertIsNone(st.find("difficultyValues"))

    def test_only_arena_col_names(self):
        with self.assertRaises(Exception):
            base.make(None, "Ithfunda", "Ithfunda", (1, 1))


class FakeRm:
    """list_recipes answers from a table; other calls are not expected."""
    def __init__(self, bills):
        self.bills, self.asked = bills, []

    def call(self, name, **kw):
        assert name == "list_recipes", name
        self.asked.append(kw["id"])
        if kw["id"] not in self.bills:
            raise base.RimMoltError("not a work table")
        return {"recipes": self.bills[kw["id"]]}


class StripTargetsTest(unittest.TestCase):
    def test_shelves_hydroponics_and_bill_takers_go(self):
        b = [{"id": "Shelf1", "def": "Shelf"}, {"id": "Shelf2", "def": "Shelf"},
             {"id": "Bookcase3", "def": "Bookcase"}, {"id": "Hydro4", "def": "HydroponicsBasin"},
             {"id": "Smithy5", "def": "ElectricSmithy"}, {"id": "Smithy6", "def": "ElectricSmithy"},
             {"id": "Research7", "def": "HiTechResearchBench"}, {"id": "Wall8", "def": "Wall"},
             {"id": "Turret9", "def": "Turret_MiniTurret"}, {"id": "Barrel10", "def": "FermentingBarrel"},
             {"id": "Bookcase11", "def": "BookcaseSmall"}]
        rm = FakeRm({"Smithy5": ["MakeSword"], "Research7": [], "Barrel10": []})
        gone = {t["id"] for t in base.strip_targets(rm, b)}
        self.assertEqual(gone, {"Shelf1", "Shelf2", "Bookcase3", "Hydro4", "Smithy5", "Smithy6", "Bookcase11"})
        self.assertEqual(sorted(rm.asked), sorted({"Smithy5", "Research7", "Wall8", "Turret9", "Barrel10"}))

    def test_strip_reads_and_writes_arena_col_only(self):
        for src, name in (("Ithfunda", "Ithfunda2"), ("arena_col_x", "Ithfunda2"), ("arena_col_x", "arena_col_x"),
                          ("arena_col_x", "arena_col_X"), ("arena_col_x2", "arena_col_x"), ("arena_col_y", "arena_col_x2")):
            with self.assertRaises(base.RimMoltError):
                base.strip(None, src, name)



class ClearConditionsTest(unittest.TestCase):
    XML = ("<?xml version='1.0' encoding='utf-8'?><savegame><game><world><gameConditionManager><activeConditions>"
           "<li Class='GameCondition_DisableElectricity'><def>SolarFlare</def><startTick>1</startTick></li>"
           "<li><def>Aurora</def></li></activeConditions></gameConditionManager></world></game></savegame>")

    def test_removes_only_the_named_condition_and_backs_up(self):
        import tempfile
        from pathlib import Path
        d = Path(tempfile.mkdtemp())
        (d / "scenario_base2_x.rws").write_text(self.XML)
        out = base.clear_conditions(["scenario_base2_x"], ("SolarFlare",), backup=d / "bk", saves=d, log=lambda *_: None)
        self.assertEqual(out, {"scenario_base2_x": ["SolarFlare"]})
        text = (d / "scenario_base2_x.rws").read_text()
        self.assertNotIn("SolarFlare", text)
        self.assertIn("Aurora", text)
        self.assertIn("SolarFlare", (d / "bk" / "scenario_base2_x.rws").read_text())

    def test_refuses_a_colony_save(self):
        with self.assertRaises(base.RimMoltError):
            base.clear_conditions(["Monler Alliance"], log=lambda *_: None)

if __name__ == "__main__":
    unittest.main()
