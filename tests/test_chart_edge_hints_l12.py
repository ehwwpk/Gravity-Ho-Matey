import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.chart_bounds import (
    CHART_EDGE_HINT_START_FRAC,
    CHART_EDGE_HINT_START_FRAC_L12,
    chart_edge_hint_distances,
    chart_edge_hints_for_ship,
    chart_limits,
    ship_in_chart,
)
from gravity_ho_matey.gameplay.entities import WorldConfig
from gravity_ho_matey.levels.level_registry import build_level


class ChartEdgeHintL12Tests(unittest.TestCase):
    def test_cove_edge_hints_start_closer_to_rim_than_default(self) -> None:
        world = build_level("cove")
        l12_start, _ = chart_edge_hint_distances(world.config)
        default_start, _ = chart_edge_hint_distances(
            WorldConfig(
                width=world.config.width,
                height=world.config.height,
                level_theme="drift",
            )
        )
        self.assertLess(l12_start, default_start)
        self.assertLess(CHART_EDGE_HINT_START_FRAC_L12, CHART_EDGE_HINT_START_FRAC)

    def test_mid_chart_cove_has_no_edge_hints(self) -> None:
        world = build_level("cove")
        x0, y0, x1, y1 = chart_limits(world.config)
        center = Vec2((x0 + x1) * 0.5, (y0 + y1) * 0.5)
        self.assertTrue(ship_in_chart(center, world.config))
        self.assertEqual(chart_edge_hints_for_ship(center, world.config), ())

    def test_solar_horizontal_edge_hints_fire_later_than_old_default(self) -> None:
        world = build_level("solar")
        x0, _, x1, _ = chart_limits(world.config)
        start, _ = chart_edge_hint_distances(world.config)
        # Old default would begin hints ~134 wu from the left edge on a 960-wide strip.
        probe_old = Vec2(x0 + 120.0, world.config.height * 0.5)
        probe_new = Vec2(x0 + start * 0.55, world.config.height * 0.5)
        self.assertTrue(ship_in_chart(probe_old, world.config))
        self.assertEqual(chart_edge_hints_for_ship(probe_old, world.config), ())
        hints = chart_edge_hints_for_ship(probe_new, world.config)
        self.assertTrue(any(tag == "left" for tag, _ in hints))


if __name__ == "__main__":
    unittest.main()
