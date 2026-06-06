import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.chart_bounds import (
    CHART_RADIATION_EXPOSURE_LIMIT,
    chart_oob_distance,
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
        cfg = WorldConfig(width=200, height=200)
        self.assertTrue(ship_in_chart(Vec2(0, 0), cfg))
        self.assertTrue(ship_in_chart(Vec2(200, 200), cfg))
        self.assertFalse(ship_in_chart(Vec2(-1, 100), cfg))
        self.assertFalse(ship_in_chart(Vec2(201, 100), cfg))

    def test_oob_distance_zero_inside(self) -> None:
        cfg = WorldConfig(width=200, height=200)
        self.assertAlmostEqual(chart_oob_distance(Vec2(50, 50), cfg), 0.0)

    def test_oob_distance_outside_corner(self) -> None:
        cfg = WorldConfig(width=200, height=200)
        self.assertAlmostEqual(chart_oob_distance(Vec2(210, 220), cfg), 22.361, places=2)


class ChartRadiationTests(unittest.TestCase):
    def test_exposure_accumulates_only_outside_chart(self) -> None:
        world = _open_world(ship_pos=Vec2(-10, 100))
        self.assertFalse(advance_chart_radiation_exposure(world, 2.0))
        self.assertAlmostEqual(world.chart_radiation_exposure, 2.0)

        world.ship.pos = Vec2(50, 50)
        self.assertFalse(advance_chart_radiation_exposure(world, 3.0))
        self.assertAlmostEqual(world.chart_radiation_exposure, 2.0)

        world.ship.pos = Vec2(-10, 100)
        self.assertTrue(advance_chart_radiation_exposure(world, 3.0))
        self.assertAlmostEqual(world.chart_radiation_exposure, 0.0)

    def test_split_oob_sessions_stack_toward_limit(self) -> None:
        world = _open_world(ship_pos=Vec2(-10, 100))
        advance_chart_radiation_exposure(world, 2.0)
        world.ship.pos = Vec2(50, 50)
        advance_chart_radiation_exposure(world, 5.0)
        world.ship.pos = Vec2(-10, 100)
        self.assertFalse(advance_chart_radiation_exposure(world, 2.0))
        self.assertAlmostEqual(world.chart_radiation_exposure, 4.0)
        self.assertTrue(advance_chart_radiation_exposure(world, 1.0))

    def test_radiation_chip_via_world_update(self) -> None:
        world = _open_world(ship_pos=Vec2(-10, 100))
        world.chart_radiation_exposure = CHART_RADIATION_EXPOSURE_LIMIT - 0.5
        remaining = 0.6
        while remaining > 0 and world.status is GameStatus.RUNNING:
            step = min(remaining, 0.05)
            world.update(step, ControlIntent())
            remaining -= step
        self.assertEqual(world.status, GameStatus.SHIP_HIT)
        self.assertAlmostEqual(world.chart_radiation_exposure, 0.0)

    def test_closed_bounds_do_not_accumulate_radiation(self) -> None:
        world = _open_world(ship_pos=Vec2(-10, 100))
        world.config = WorldConfig(width=200, height=200, open_bounds=False)
        self.assertFalse(advance_chart_radiation_exposure(world, 10.0))
        self.assertAlmostEqual(world.chart_radiation_exposure, 0.0)

    def test_exposure_fraction_clamps(self) -> None:
        self.assertAlmostEqual(radiation_exposure_fraction(2.5), 0.5)


if __name__ == "__main__":
    unittest.main()
