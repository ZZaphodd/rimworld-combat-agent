"""Labelled frames (rca/eval/frames.py): cell-to-pixel mapping and the SVG overlay."""
import unittest

from rca.eval import frames


class FramesTest(unittest.TestCase):
    def test_rect_and_cell_mapping(self):
        rect = frames.parse_rect("rect x171-211 z91-127")
        self.assertEqual(rect, (171, 211, 91, 127))
        self.assertEqual(frames.cell_px(191, 102, rect, 18), (369.0, 441.0))   # north is up

    def test_svg_labels_and_landscape_canvas(self):
        rect = (0, 40, 0, 48)                         # 720 x 864: taller than wide
        doc = frames.svg("AAAA", (720, 864), rect,
                         pawns=[{"n": "Bog", "x": 5, "z": 5, "side": "ours", "d": False},
                                {"n": "Jake", "x": 9, "z": 9, "side": "them", "d": True},
                                {"n": "Far", "x": 99, "z": 5, "side": "them", "d": False}],
                         notes=[(20, 20, "rock hill")], caption="1. t100 test",
                         paths=[("ours", [(1, 1, "S"), (5, 5, "1,2")], True)])
        self.assertIn(">Bog<", doc)
        self.assertIn(">Jake (down)<", doc)
        self.assertNotIn(">Far<", doc)                # outside the frame
        self.assertIn(">rock hill<", doc)
        self.assertIn('stroke-dasharray="8,6"', doc)
        self.assertIn(f'width="{864 + frames.BAR}"', doc)   # canvas never narrower than tall


if __name__ == "__main__":
    unittest.main()
