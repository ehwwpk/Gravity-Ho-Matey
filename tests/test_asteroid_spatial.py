import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid
from gravity_ho_matey.gameplay.asteroid_spatial import (
    AsteroidSpatialGrid,
    PROJECTILE_INTERACTION_RADIUS,
    SHIP_INTERACTION_RADIUS,
)
from gravity_ho_matey.gameplay.threat_snapshot import build_asteroid_threat_snapshots
from gravity_ho_matey.levels.level_registry import build_level


class AsteroidSpatialGridTests(unittest.TestCase):
    def test_query_circle_finds_nearby_only(self) -> None:
        grid = AsteroidSpatialGrid(cell_size=100.0)
        near = make_asteroid(Vec2(50, 50), seed=1, drift_kind="slow", velocity=Vec2())
        far = make_asteroid(Vec2(900, 900), seed=2, drift_kind="slow", velocity=Vec2())
        grid.rebuild([near, far])
        hits = grid.query_circle(Vec2(50, 50), 80.0)
        self.assertEqual(len(hits), 1)
        self.assertIs(hits[0], near)

    def test_stray_shot_zone_wakes_distant_rock(self) -> None:
        grid = AsteroidSpatialGrid(cell_size=240.0)
        ship = Vec2(2400, 2400)
        far_rock = make_asteroid(Vec2(2400, 500), seed=3, drift_kind="ring", velocity=Vec2())
        grid.rebuild([far_rock])
        ship_zone = grid.query_interaction_zones(ship)
        self.assertEqual(ship_zone, [])
        shot_zone = grid.query_interaction_zones(
            ship,
            projectile_points=(Vec2(2400, 520),),
            projectile_radius=PROJECTILE_INTERACTION_RADIUS,
        )
        self.assertIn(far_rock, shot_zone)

    def test_drift_builds_fewer_snapshots_than_total_rocks(self) -> None:
        world = build_level("drift")
        world.asteroid_spatial.rebuild(world.asteroids)
        active = world.asteroid_spatial.query_interaction_zones(world.ship.pos)
        all_snaps = build_asteroid_threat_snapshots(world.asteroids)
        near_snaps = build_asteroid_threat_snapshots(active)
        self.assertGreater(len(world.asteroids), len(near_snaps))
        self.assertLess(len(near_snaps), len(all_snaps))

    def test_interaction_radius_covers_near_ring_from_spawn(self) -> None:
        world = build_level("drift")
        world.asteroid_spatial.rebuild(world.asteroids)
        inner = min(
            world.asteroids,
            key=lambda a: (a.pos - world.ship.pos).length(),
        )
        dist = (inner.pos - world.ship.pos).length()
        self.assertLessEqual(dist, SHIP_INTERACTION_RADIUS + inner.approximate_radius())


if __name__ == "__main__":
    unittest.main()
