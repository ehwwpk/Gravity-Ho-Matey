import unittest

from gravity_ho_matey.core.geometry import (
    circle_intersects_convex_polygon,
    nearest_point_on_polygon_boundary,
    point_in_convex_polygon,
)
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import integrate_asteroid, make_asteroid, make_ring_cluster, make_shower_cluster
from gravity_ho_matey.gameplay.asteroid_shape import generate_asteroid_verts
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.levels.level_registry import build_level


class AsteroidGeometryTests(unittest.TestCase):
    def test_point_inside_unit_square(self) -> None:
        square = [Vec2(0, 0), Vec2(10, 0), Vec2(10, 10), Vec2(0, 10)]
        self.assertTrue(point_in_convex_polygon(Vec2(5, 5), square))
        self.assertFalse(point_in_convex_polygon(Vec2(15, 5), square))

    def test_nearest_boundary_distance_to_segment(self) -> None:
        square = [Vec2(0, 0), Vec2(10, 0), Vec2(10, 10), Vec2(0, 10)]
        _, dist = nearest_point_on_polygon_boundary(Vec2(5, 15), square)
        self.assertAlmostEqual(dist, 5.0, places=3)


class AsteroidShapeTests(unittest.TestCase):
    def test_same_seed_produces_identical_verts(self) -> None:
        a = generate_asteroid_verts(42, "rock")
        b = generate_asteroid_verts(42, "rock")
        self.assertEqual(a, b)

    def test_different_seeds_differ(self) -> None:
        a = generate_asteroid_verts(1, "rock")
        b = generate_asteroid_verts(2, "rock")
        self.assertNotEqual(a, b)

    def test_boulder_has_more_extent_than_pebble(self) -> None:
        pebble = generate_asteroid_verts(9, "pebble")
        boulder = generate_asteroid_verts(9, "boulder")
        pebble_r = max(v.length() for v in pebble)
        boulder_r = max(v.length() for v in boulder)
        self.assertGreater(boulder_r, pebble_r)


class AsteroidCollisionTests(unittest.TestCase):
    def test_circle_hits_convex_polygon(self) -> None:
        asteroid = make_asteroid(Vec2(100, 100), seed=7, size_class="rock", drift_kind="slow", velocity=Vec2())
        verts = asteroid.world_vertices()
        self.assertTrue(circle_intersects_convex_polygon(Vec2(100, 100), 12.0, verts))

    def test_circle_misses_distant_polygon(self) -> None:
        asteroid = make_asteroid(Vec2(100, 100), seed=7, size_class="rock", drift_kind="slow", velocity=Vec2())
        verts = asteroid.world_vertices()
        self.assertFalse(circle_intersects_convex_polygon(Vec2(300, 300), 12.0, verts))


class AsteroidMotionTests(unittest.TestCase):
    def test_asteroids_drift_over_time(self) -> None:
        asteroid = make_asteroid(Vec2(100, 100), seed=11, drift_kind="medium")
        start = Vec2(asteroid.pos.x, asteroid.pos.y)
        integrate_asteroid(asteroid, 0.5, [], gravity_scale=0.5, world_width=960, world_height=640)
        self.assertGreater((asteroid.pos - start).length(), 0.0)

    def test_ring_cluster_shares_tangential_motion(self) -> None:
        ring = make_ring_cluster(Vec2(400, 400), radius=80, count=4, base_seed=55)
        speeds = [a.vel.length() for a in ring]
        self.assertTrue(all(30.0 < s < 70.0 for s in speeds))

    def test_shower_cluster_has_fast_shared_drift(self) -> None:
        shower = make_shower_cluster(
            Vec2(200, 200),
            count=5,
            base_seed=88,
            direction=Vec2(1.0, 0.0),
        )
        avg_speed = sum(a.vel.length() for a in shower) / len(shower)
        self.assertGreater(avg_speed, 90.0)


class AsteroidWorldTests(unittest.TestCase):
    def test_world_updates_asteroid_positions(self) -> None:
        world = build_level("cove")
        before = [(a.pos.x, a.pos.y) for a in world.asteroids]
        world.update(0.2, ControlIntent())
        after = [(a.pos.x, a.pos.y) for a in world.asteroids]
        self.assertNotEqual(before, after)

    def test_ahead_emphasis_importable(self) -> None:
        from gravity_ho_matey.render.chase_threat import ahead_emphasis

        self.assertGreater(ahead_emphasis(Vec2(), 0.0, Vec2(100, 0)), 0.5)

        for level_id in ("cove", "solar"):
            world = build_level(level_id)
            min_rocks = 3 if level_id == "cove" else 8
            self.assertGreaterEqual(len(world.asteroids), min_rocks)
            kinds = {a.drift_kind for a in world.asteroids}
            self.assertIn("ring", kinds)



if __name__ == "__main__":
    unittest.main()
