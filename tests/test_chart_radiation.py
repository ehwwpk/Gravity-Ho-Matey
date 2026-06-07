import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.chart_bounds import (
    CHART_RADIATION_EXPOSURE_LIMIT,
    OOB_RING_CRUISE_SPEED,
    OOB_RING_TRAVEL_SECONDS,
    chart_limits,
    chart_oob_distance,
    chart_outer_radius_from_center,
    oob_ring_radius,
    radiation_exposure_fraction,
    ship_in_chart,
)
from gravity_ho_matey.gameplay.chart_radiation import advance_chart_radiation_exposure
from gravity_ho_matey.gameplay.entities import FinishGate, GameStatus, Ship, WorldConfig
from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld


def _open_world(*, ship_pos: Vec2 | None = None) -> GameWorld:
    return GameWorld(
        config=WorldConfig(width=200, height=200, open_bounds=True),
        ship=Ship(pos=ship_pos or Vec2(100, 100)),
        asteroids=[],
        wells=[],
        beacons=[],
        finish_gate=FinishGate(Rect(150, 150, 25, 25)),
    )


class ChartBoundsTests(unittest.TestCase):
    def test_ship_in_chart_respects_edges(self) -> None:
        cfg = WorldConfig(width=200, height=200, chart_margin_frac=0.05)
        self.assertTrue(ship_in_chart(Vec2(0, 0), cfg))
        self.assertTrue(ship_in_chart(Vec2(200, 200), cfg))
        self.assertTrue(ship_in_chart(Vec2(-5, 100), cfg))
        self.assertTrue(ship_in_chart(Vec2(205, 100), cfg))
        self.assertFalse(ship_in_chart(Vec2(-11, 100), cfg))
        self.assertFalse(ship_in_chart(Vec2(211, 100), cfg))

    def test_oob_distance_zero_inside(self) -> None:
        cfg = WorldConfig(width=200, height=200, chart_margin_frac=0.05)
        self.assertAlmostEqual(chart_oob_distance(Vec2(50, 50), cfg), 0.0)

    def test_oob_distance_outside_corner(self) -> None:
        cfg = WorldConfig(width=200, height=200, chart_margin_frac=0.05)
        self.assertAlmostEqual(chart_oob_distance(Vec2(220, 230), cfg), 22.361, places=2)

    def test_oob_ring_sits_beyond_chart(self) -> None:
        cfg = WorldConfig(width=960, height=640, chart_margin_frac=0.05)
        outer = chart_outer_radius_from_center(cfg)
        ring = oob_ring_radius(cfg)
        self.assertGreater(ring, outer)
        self.assertAlmostEqual(ring - outer, OOB_RING_TRAVEL_SECONDS * OOB_RING_CRUISE_SPEED)


class ChartRadiationTests(unittest.TestCase):
    def test_exposure_accumulates_only_outside_chart(self) -> None:
        world = _open_world(ship_pos=Vec2(-20, 100))
        self.assertFalse(advance_chart_radiation_exposure(world, 2.0))
        self.assertAlmostEqual(world.chart_radiation_exposure, 2.0)

        world.ship.pos = Vec2(50, 50)
        self.assertFalse(advance_chart_radiation_exposure(world, 3.0))
        self.assertAlmostEqual(world.chart_radiation_exposure, 2.0)

        world.ship.pos = Vec2(-20, 100)
        self.assertTrue(advance_chart_radiation_exposure(world, 3.0))
        self.assertAlmostEqual(world.chart_radiation_exposure, 0.0)

    def test_split_oob_sessions_stack_toward_limit(self) -> None:
        world = _open_world(ship_pos=Vec2(-20, 100))
        advance_chart_radiation_exposure(world, 2.0)
        world.ship.pos = Vec2(50, 50)
        advance_chart_radiation_exposure(world, 5.0)
        world.ship.pos = Vec2(-20, 100)
        self.assertFalse(advance_chart_radiation_exposure(world, 2.0))
        self.assertAlmostEqual(world.chart_radiation_exposure, 4.0)
        self.assertTrue(advance_chart_radiation_exposure(world, 1.0))

    def test_radiation_chip_via_world_update(self) -> None:
        world = _open_world(ship_pos=Vec2(-20, 100))
        world.chart_radiation_exposure = CHART_RADIATION_EXPOSURE_LIMIT - 0.5
        remaining = 0.6
        while remaining > 0 and world.status is GameStatus.RUNNING:
            step = min(remaining, 0.05)
            world.update(step, ControlIntent())
            remaining -= step
        self.assertEqual(world.status, GameStatus.SHIP_HIT)
        self.assertAlmostEqual(world.chart_radiation_exposure, 0.0)

    def test_closed_bounds_do_not_accumulate_radiation(self) -> None:
        world = _open_world(ship_pos=Vec2(-20, 100))
        world.config = WorldConfig(width=200, height=200, open_bounds=False)
        self.assertFalse(advance_chart_radiation_exposure(world, 10.0))
        self.assertAlmostEqual(world.chart_radiation_exposure, 0.0)

    def test_exposure_fraction_clamps(self) -> None:
        self.assertAlmostEqual(radiation_exposure_fraction(2.5), 0.5)

    def test_level_beacons_have_room_from_chart_edge(self) -> None:
        from gravity_ho_matey.levels.level_registry import build_level

        ship_clearance = 24.0
        for level_id in ("cove", "solar"):
            world = build_level(level_id)
            _x0, y0, x1, y1 = chart_limits(world.config)
            for beacon in world.beacons:
                inset_left = beacon.pos.x - _x0
                inset_right = x1 - beacon.pos.x
                inset_top = beacon.pos.y - y0
                inset_bottom = y1 - beacon.pos.y
                self.assertGreaterEqual(min(inset_left, inset_right, inset_top, inset_bottom), ship_clearance)


if __name__ == "__main__":
    unittest.main()
