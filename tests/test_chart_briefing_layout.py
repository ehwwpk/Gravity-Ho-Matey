import unittest

from gravity_ho_matey.render.chart_map_overlay import _chart_body_layout, _group_briefing_sections
from gravity_ho_matey.narrative.chart_briefing_copy import LEVEL_BRIEFING


class ChartBriefingLayoutTests(unittest.TestCase):
    def test_body_layout_prioritizes_briefing_width(self) -> None:
        layout = _chart_body_layout(960.0, 100.0, 400.0)
        self.assertGreater(layout.briefing_w, layout.intel_w)
        self.assertLess(layout.map_w, 540.0)
        self.assertAlmostEqual(
            layout.briefing_x + layout.briefing_w + layout.map_w + layout.intel_w + 24,
            960.0,
            delta=20.0,
        )

    def test_group_briefing_merges_continuations(self) -> None:
        grouped = _group_briefing_sections(LEVEL_BRIEFING["brood_moon"])
        self.assertIn("SURFACE", grouped)
        self.assertIn("Eight pods", grouped["SURFACE"])
        self.assertIn("WIN", grouped)
        self.assertIn("Circumnav", grouped["WIN"])


if __name__ == "__main__":
    unittest.main()
