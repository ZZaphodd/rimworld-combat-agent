"""tools/cases.py: tags computed from a manifest, card parsing and the similarity score."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))                      # tools/_path
_spec = importlib.util.spec_from_file_location("cases", TOOLS / "cases.py")
cases = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cases)


def manifest(ours, raid, sq, en, n_sq, n_en, arena="arena_open_night", **f):
    feats = {"squad_n": n_sq, "squad_classes": sq, "enemy_n": n_en, "enemy_classes": en,
             "count_ratio": round(n_sq / n_en, 2), "distance": 150, "squad_range_median": 1.5,
             "enemy_melee_share": en.get("melee", 0) / n_en, "enemy_outrange_share": 0.0, "mech": False}
    feats.update(f)
    return {"spec": {"arena": arena, "squad": {"faction": ours}, "enemy": {"faction": raid}},
            "enemy": [{"weapon": "Steel knife"}] * n_en, "briefing": {"features": feats}}


class AutoTags(unittest.TestCase):
    def test_melee_mirror(self):
        m = manifest("TribeRough", "TribeRoughNeanderthal", {"melee": 11}, {"melee": 6}, 11, 6)
        t = cases.auto_tags(m)
        self.assertTrue({"open-arena", "raid-far", "raid-melee", "raid-strong-1v1", "us-melee-pawns",
                         "us-outnumber"} <= t)
        self.assertNotIn("us-bows", t)

    def test_throwers_counted_from_weapons(self):
        m = manifest("Pirate", "OutlanderCivil", {"short": 8}, {"short": 6, "explosive": 2}, 8, 8)
        m["enemy"] = [{"weapon": "Frag grenades"}, {"weapon": "Molotov cocktails"}] + [{"weapon": "Revolver"}] * 6
        self.assertIn("raid-throwers", cases.auto_tags(m))


class Card(unittest.TestCase):
    def test_parse(self):
        text = ("# rand_999 · a vs b · open\n\n**Situation:** `open-arena` `raid-melee`\n"
                "**Plays seen:** `mouth-hold` `rotation`\n\n## Plays and results\n"
                "| who | play | site | result | lost | badness |\n|---|---|---|---|---|---|\n"
                "| agent `kite` | kite | open | squad down | 9 downed | 93.2 |\n"
                "| Claude | door hold | R2 | **won** | 0 | **28.2** |\n\n## Scenes\n- x\n")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "rand_999.md"
            p.write_text(text)
            c = cases.parse_card(p)
        self.assertEqual(c["situation"], ["open-arena", "raid-melee"])
        self.assertEqual(c["plays"], ["mouth-hold", "rotation"])
        self.assertEqual([r["badness"] for r in c["results"]], ["93.2", "**28.2**"])

    def test_score_prefers_same_matchup(self):
        q = manifest("TribeRough", "TribeRoughNeanderthal", {"melee": 11}, {"melee": 6}, 11, 6)
        def row(ours, raid, sq, en, n_sq, n_en):
            m = manifest(ours, raid, sq, en, n_sq, n_en)
            return {"arena": "arena_open_night", "ours": ours, "raid": raid,
                    "auto": sorted(cases.auto_tags(m)), "features": m["briefing"]["features"]}
        near = row("TribeSavage", "TribeRoughNeanderthal", {"melee": 4, "bow": 6}, {"melee": 7}, 10, 7)
        far = row("Pirate", "Mechanoid", {"short": 9}, {"long": 3}, 9, 3)
        self.assertGreater(cases.score(q, near)[0], cases.score(q, far)[0])


if __name__ == "__main__":
    unittest.main()
