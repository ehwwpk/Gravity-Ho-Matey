import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.chart_bounds import (
    chart_edge_hint_distances,
    chart_edge_hint_strength,
    chart_edge_hints_for_ship,
    nudge_ship_into_chart,
    ship_in_chart,
)
from gravity_ho_matey.gameplay.entities import WorldConfig


class ChartEdgeHintTests(unittest.TestCase):
    def test_no_hints_far_from_edge(self) -> None:
        cfg = WorldConfig(width=960, height=640, open_bounds=True)
        hints = chart_edge_hints_for_ship(Vec2(480, 320), cfg)
        self.assertEqual(hints, ())

    def test_hints_appear_when_near_left_edge(self) -> None:
        cfg = WorldConfig(width=960, height=640, open_bounds=True)
        start, _ = chart_edge_hint_distances(cfg)
        hints = chart_edge_hints_for_ship(Vec2(start * 0.5, 320), cfg)
        tags = {tag for tag, _ in hints}
        self.assertIn("left", tags)
        self.assertNotIn("right", tags)

    def test_hint_strength_eases_in(self) -> None:
        start, full = 100.0, 30.0
        self.assertAlmostEqual(chart_edge_hint_strength(120.0, start=start, full=full), 0.0)
        self.assertAlmostEqual(chart_edge_hint_strength(30.0, start=start, full=full), 1.0)
        mid = chart_edge_hint_strength(65.0, start=start, full=full)
        self.assertGreater(mid, 0.0)
        self.assertLess(mid, 1.0)

    def test_nudge_pulls_slightly_oob_positions_inside(self) -> None:
        cfg = WorldConfig(width=200, height=200)
        nudged = nudge_ship_into_chart(Vec2(-2, 100), cfg)
        self.assertAlmostEqual(nudged.x, 6.0)
        self.assertAlmostEqual(nudged.y, 100.0)
        self.assertTrue(ship_in_chart(nudged, cfg))


if __name__ == "__main__":
    unittest.main()
