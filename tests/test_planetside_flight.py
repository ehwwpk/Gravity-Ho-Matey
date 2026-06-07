from __future__ import annotations

import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.brood_moon_controller import apply_surface_layout
from gravity_ho_matey.gameplay.explosions import ExplosionKind
from gravity_ho_matey.gameplay.planetside_flight import (
    PLANETSIDE_FLIGHT_DEFAULTS,
    hint_world_pos,
    is_planetside,
    wrap_shortest_delta,
)
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.levels.brood_moon_layout import SURFACE_WRAP_WIDTH
from gravity_ho_matey.levels.level_registry import build_level


class PlanetsideFlightTests(unittest.TestCase):
    def test_wrap_shortest_delta_prefers_forward_wrap(self) -> None:
        ship = Vec2(200.0, 1000.0)
        pod = Vec2(SURFACE_WRAP_WIDTH - 100.0, 1000.0)
        delta = wrap_shortest_delta(ship, pod, float(SURFACE_WRAP_WIDTH))
        self.assertAlmostEqual(delta.x, -300.0)
        self.assertAlmostEqual(delta.y, 0.0)

    def test_wrap_shortest_delta_prefers_backward_wrap(self) -> None:
        ship = Vec2(SURFACE_WRAP_WIDTH - 100.0, 1000.0)
        pod = Vec2(200.0, 1000.0)
        delta = wrap_shortest_delta(ship, pod, float(SURFACE_WRAP_WIDTH))
        self.assertAlmostEqual(delta.x, 300.0)

    def test_hint_world_pos_aims_along_shortest_path(self) -> None:
        ship = Vec2(200.0, 1000.0)
        pod = Vec2(SURFACE_WRAP_WIDTH - 100.0, 1000.0)
        hint = hint_world_pos(ship, pod, float(SURFACE_WRAP_WIDTH))
        self.assertAlmostEqual(hint.x, -100.0)
        self.assertAlmostEqual(hint.y, 1000.0)

    def test_brood_surface_uses_planetside_profile(self) -> None:
        world = build_level("brood_moon")
        apply_surface_layout(world)
        self.assertTrue(is_planetside(world.config))
        self.assertAlmostEqual(world.config.max_ship_speed, PLANETSIDE_FLIGHT_DEFAULTS["max_ship_speed"])
        self.assertAlmostEqual(world.config.boost_burst_fraction, PLANETSIDE_FLIGHT_DEFAULTS["boost_burst_fraction"])
        self.assertAlmostEqual(world.config.boost_overspeed_cap, PLANETSIDE_FLIGHT_DEFAULTS["boost_overspeed_cap"])

    def test_planetside_boost_spawns_reactor_burst(self) -> None:
        world = build_level("brood_moon")
        apply_surface_layout(world)
        world.ship.boost_energy = 1.0
        world.ship.angle = 0.0
        before = len(world.explosions.active)
        world.update(0.016, ControlIntent(boost_tap=True))
        self.assertGreater(world.ship.boost_flash, 0.0)
        self.assertGreater(world.ship.boost_jolt, 0.0)
        self.assertGreater(len(world.explosions.active), before)
        self.assertEqual(world.explosions.active[-1].kind, ExplosionKind.REACTOR_BURST)

    def test_orbital_world_is_not_planetside(self) -> None:
        world = build_level("brood_moon")
        self.assertFalse(is_planetside(world.config))


if __name__ == "__main__":
    unittest.main()
