import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import integrate_asteroid, make_ring_cluster
from gravity_ho_matey.gameplay.chart_bounds import ship_in_chart
from gravity_ho_matey.gameplay.entities import FinishGate, Ship, WorldConfig
from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld


class OobAsteroidRingTests(unittest.TestCase):
    def test_free_bounds_skips_level_box_clamp(self) -> None:
        ring = make_ring_cluster(Vec2(480, 320), radius=900.0, count=1, base_seed=77, size_class="pebble")
        asteroid = ring[0]
        asteroid.free_bounds = True
        asteroid.pos = Vec2(-200.0, 320.0)
        start = Vec2(asteroid.pos.x, asteroid.pos.y)
        integrate_asteroid(
            asteroid,
            0.05,
            [],
            gravity_scale=0.5,
            world_width=960.0,
            world_height=640.0,
        )
        self.assertLess(asteroid.pos.x, 0.0)
        self.assertNotAlmostEqual(asteroid.pos.x, start.x)

    def test_free_bounds_frozen_while_ship_in_chart(self) -> None:
        ring = make_ring_cluster(Vec2(480, 320), radius=900.0, count=1, base_seed=88, size_class="pebble")
        asteroid = ring[0]
        asteroid.free_bounds = True
        start = Vec2(asteroid.pos.x, asteroid.pos.y)
        world = GameWorld(
            config=WorldConfig(width=960, height=640, open_bounds=True),
            ship=Ship(pos=Vec2(100, 100)),
            asteroids=[asteroid],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(800, 500, 40, 40)),
        )
        self.assertTrue(ship_in_chart(world.ship.pos, world.config))
        world.update(0.1, ControlIntent())
        self.assertAlmostEqual(asteroid.pos.x, start.x)
        self.assertAlmostEqual(asteroid.pos.y, start.y)

    def test_free_bounds_simulates_when_ship_leaves_chart(self) -> None:
        ring = make_ring_cluster(Vec2(480, 320), radius=900.0, count=1, base_seed=99, size_class="pebble")
        asteroid = ring[0]
        asteroid.free_bounds = True
        start = Vec2(asteroid.pos.x, asteroid.pos.y)
        world = GameWorld(
            config=WorldConfig(width=960, height=640, open_bounds=True),
            ship=Ship(pos=Vec2(-120, 320)),
            asteroids=[asteroid],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(800, 500, 40, 40)),
        )
        self.assertFalse(ship_in_chart(world.ship.pos, world.config))
        world.update(0.1, ControlIntent())
        moved = (asteroid.pos - start).length()
        self.assertGreater(moved, 0.5)


if __name__ == "__main__":
    unittest.main()
