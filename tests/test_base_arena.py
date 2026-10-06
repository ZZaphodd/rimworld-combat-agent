"""rca.game.builders.base.edit_save: items out by id at any depth, storyteller and difficulty set."""
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


if __name__ == "__main__":
    unittest.main()
