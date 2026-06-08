import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_combat import (
    apply_friendly_projectile_hit,
    apply_projectile_hit,
)
from gravity_ho_matey.gameplay.asteroid_mass import polygon_area, scale_local_verts
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid
from gravity_ho_matey.gameplay.asteroid_tiers import (
    MAX_ASTEROIDS,
    ROCK_MEDIUM_MIN_RADIUS,
    AsteroidTier,
    can_split,
    roll_hits_max,
    tier_for_size_class,
    tier_for_spawn,
)
from gravity_ho_matey.gameplay.entities import FinishGate, GameStatus, Projectile, Ship, WorldConfig
from gravity_ho_matey.gameplay.explosions import ExplosionKind
from gravity_ho_matey.gameplay.threat_snapshot import build_asteroid_threat_snapshots
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.level_registry import build_level


class AsteroidTierTests(unittest.TestCase):
    def test_fixed_size_classes(self) -> None:
        self.assertEqual(tier_for_spawn("boulder", 70.0), AsteroidTier.LARGE)
        self.assertEqual(tier_for_spawn("pebble", 20.0), AsteroidTier.SMALL)

    def test_rock_tier_depends_on_radius(self) -> None:
        self.assertEqual(tier_for_spawn("rock", ROCK_MEDIUM_MIN_RADIUS - 1.0), AsteroidTier.SMALL)
        self.assertEqual(tier_for_spawn("rock", ROCK_MEDIUM_MIN_RADIUS), AsteroidTier.MEDIUM)

    def test_legacy_size_class_helper_defaults_rock_to_small(self) -> None:
        self.assertEqual(tier_for_size_class("rock"), AsteroidTier.SMALL)

    def test_hits_max_seeded_and_in_range(self) -> None:
        import random

        rng = random.Random(601)
        large = roll_hits_max(AsteroidTier.LARGE, rng)
        self.assertGreaterEqual(large, 5)
        self.assertLessEqual(large, 10)

        rng = random.Random(102)
        medium = roll_hits_max(AsteroidTier.MEDIUM, rng)
        self.assertGreaterEqual(medium, 3)
        self.assertLessEqual(medium, 5)

        rng = random.Random(601)
        small = roll_hits_max(AsteroidTier.SMALL, rng)
        self.assertGreaterEqual(small, 1)
        self.assertLessEqual(small, 3)

    def test_generation_cap_blocks_split(self) -> None:
        self.assertTrue(can_split(AsteroidTier.LARGE, 0))
        self.assertTrue(can_split(AsteroidTier.MEDIUM, 0))
        self.assertTrue(can_split(AsteroidTier.LARGE, 1))
        self.assertFalse(can_split(AsteroidTier.LARGE, 2))
        self.assertFalse(can_split(AsteroidTier.MEDIUM, 2))
        self.assertFalse(can_split(AsteroidTier.SMALL, 0))


class AsteroidMassTests(unittest.TestCase):
    def test_polygon_area_positive(self) -> None:
        asteroid = make_asteroid(Vec2(), seed=1, size_class="rock", drift_kind="slow", velocity=Vec2())
        self.assertGreater(polygon_area(asteroid.local_verts), 0.0)

    def test_scale_local_verts_shrinks_area(self) -> None:
        asteroid = make_asteroid(Vec2(), seed=2, size_class="boulder", drift_kind="slow", velocity=Vec2())
        scaled = scale_local_verts(asteroid.local_verts, 0.4)
        self.assertLess(polygon_area(scaled), polygon_area(asteroid.local_verts))

    def test_make_asteroid_assigns_mass(self) -> None:
        boulder = make_asteroid(Vec2(), seed=601, size_class="boulder", drift_kind="slow", velocity=Vec2())
        pebble = make_asteroid(Vec2(), seed=301, size_class="pebble", drift_kind="slow", velocity=Vec2())
        self.assertGreater(boulder.mass, pebble.mass)
        self.assertEqual(boulder.hits_remaining, boulder.hits_max)


class AsteroidCombatUnitTests(unittest.TestCase):
    def test_chip_hit_does_not_remove_asteroid(self) -> None:
        asteroid = make_asteroid(Vec2(50, 50), seed=102, size_class="rock", drift_kind="slow", velocity=Vec2())
        initial_hits = asteroid.hits_remaining
        result = apply_projectile_hit(
            asteroid,
            Vec2(50, 50),
            Vec2(200, 0),
            world_asteroid_count=1,
        )
        self.assertEqual(result.asteroids_removed, [])
        self.assertEqual(asteroid.hits_remaining, initial_hits - 1)
        self.assertEqual(result.fx[0].kind, ExplosionKind.PROJECTILE_IMPACT)

    def test_hostile_hit_applies_same_damage_as_friendly(self) -> None:
        friendly = make_asteroid(Vec2(50, 50), seed=102, size_class="rock", drift_kind="slow", velocity=Vec2())
        hostile = make_asteroid(Vec2(50, 50), seed=102, size_class="rock", drift_kind="slow", velocity=Vec2())
        apply_projectile_hit(friendly, Vec2(50, 50), Vec2(200, 0), world_asteroid_count=1)
        apply_projectile_hit(hostile, Vec2(50, 50), Vec2(200, 0), world_asteroid_count=1)
        self.assertEqual(friendly.hits_remaining, hostile.hits_remaining)

    def test_small_final_hit_removes_asteroid(self) -> None:
        asteroid = make_asteroid(Vec2(50, 50), seed=301, size_class="pebble", drift_kind="slow", velocity=Vec2())
        while asteroid.hits_remaining > 1:
            apply_projectile_hit(
                asteroid,
                Vec2(50, 50),
                Vec2(200, 0),
                world_asteroid_count=1,
            )
        result = apply_projectile_hit(
            asteroid,
            Vec2(50, 50),
            Vec2(200, 0),
            world_asteroid_count=1,
        )
        self.assertIn(asteroid, result.asteroids_removed)
        self.assertEqual(result.asteroids_added, [])
        self.assertEqual(result.fx[-1].kind, ExplosionKind.ASTEROID_DESTROYED)

    def test_medium_rock_splits_into_fragments(self) -> None:
        asteroid = make_asteroid(Vec2(80, 80), seed=401001, size_class="rock", drift_kind="slow", velocity=Vec2())
        self.assertEqual(asteroid.tier, AsteroidTier.MEDIUM)
        parent_mass = asteroid.mass
        while asteroid.hits_remaining > 1:
            apply_projectile_hit(
                asteroid,
                Vec2(80, 80),
                Vec2(250, 0),
                world_asteroid_count=1,
            )
        result = apply_projectile_hit(
            asteroid,
            Vec2(80, 80),
            Vec2(250, 0),
            world_asteroid_count=1,
        )
        self.assertIn(asteroid, result.asteroids_removed)
        self.assertGreaterEqual(len(result.asteroids_added), 2)
        self.assertLessEqual(len(result.asteroids_added), 3)
        self.assertEqual(result.fx[-1].kind, ExplosionKind.ASTEROID_BREAKUP)
        child_mass = sum(child.mass for child in result.asteroids_added)
        self.assertAlmostEqual(child_mass / parent_mass, 0.5, delta=0.08)

    def test_small_rock_vaporizes_without_fragments(self) -> None:
        asteroid = make_asteroid(Vec2(80, 80), seed=401003, size_class="rock", drift_kind="slow", velocity=Vec2())
        self.assertEqual(asteroid.tier, AsteroidTier.SMALL)
        while asteroid.hits_remaining > 1:
            apply_projectile_hit(
                asteroid,
                Vec2(80, 80),
                Vec2(250, 0),
                world_asteroid_count=1,
            )
        result = apply_projectile_hit(
            asteroid,
            Vec2(80, 80),
            Vec2(250, 0),
            world_asteroid_count=1,
        )
        self.assertEqual(result.asteroids_added, [])
        self.assertEqual(result.fx[-1].kind, ExplosionKind.ASTEROID_DESTROYED)

    def test_large_final_hit_splits_into_fragments(self) -> None:
        asteroid = make_asteroid(Vec2(100, 100), seed=601, size_class="boulder", drift_kind="slow", velocity=Vec2())
        parent_mass = asteroid.mass
        while asteroid.hits_remaining > 1:
            apply_projectile_hit(
                asteroid,
                Vec2(100, 100),
                Vec2(300, 0),
                world_asteroid_count=1,
            )
        result = apply_projectile_hit(
            asteroid,
            Vec2(100, 100),
            Vec2(300, 0),
            world_asteroid_count=1,
        )
        self.assertIn(asteroid, result.asteroids_removed)
        self.assertGreaterEqual(len(result.asteroids_added), 2)
        self.assertLessEqual(len(result.asteroids_added), 4)
        self.assertEqual(result.fx[-1].kind, ExplosionKind.ASTEROID_BREAKUP)
        child_mass = sum(child.mass for child in result.asteroids_added)
        self.assertAlmostEqual(child_mass / parent_mass, 0.5, delta=0.08)
        for child in result.asteroids_added:
            self.assertEqual(child.tier, AsteroidTier.SMALL)
            self.assertEqual(child.generation, 1)
            self.assertIsNone(child.ring_anchor)

    def test_generation_cap_vaporizes_instead_of_splitting(self) -> None:
        asteroid = make_asteroid(Vec2(100, 100), seed=601, size_class="boulder", drift_kind="slow", velocity=Vec2())
        asteroid.generation = 2
        while asteroid.hits_remaining > 1:
            apply_projectile_hit(
                asteroid,
                Vec2(100, 100),
                Vec2(300, 0),
                world_asteroid_count=1,
            )
        result = apply_projectile_hit(
            asteroid,
            Vec2(100, 100),
            Vec2(300, 0),
            world_asteroid_count=1,
        )
        self.assertEqual(result.asteroids_added, [])
        self.assertEqual(result.fx[-1].kind, ExplosionKind.ASTEROID_DESTROYED)

    def test_at_asteroid_cap_breakup_vaporizes_without_fragments(self) -> None:
        asteroid = make_asteroid(Vec2(100, 100), seed=601, size_class="boulder", drift_kind="slow", velocity=Vec2())
        while asteroid.hits_remaining > 1:
            apply_projectile_hit(
                asteroid,
                Vec2(100, 100),
                Vec2(300, 0),
                world_asteroid_count=MAX_ASTEROIDS,
            )
        result = apply_projectile_hit(
            asteroid,
            Vec2(100, 100),
            Vec2(300, 0),
            world_asteroid_count=MAX_ASTEROIDS,
        )
        self.assertEqual(result.asteroids_added, [])
        self.assertEqual(result.fx[-1].kind, ExplosionKind.ASTEROID_BREAKUP)
        self.assertGreater(result.fx[-1].scale, 0.9)


class AsteroidCombatWorldTests(unittest.TestCase):
    def _world_with_asteroid(self, asteroid, *, ship_pos: Vec2 | None = None) -> GameWorld:
        return GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=ship_pos or Vec2(10, 10)),
            asteroids=[asteroid],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
        )

    def test_projectile_destroys_small_asteroid(self) -> None:
        asteroid = make_asteroid(Vec2(50, 50), seed=301, size_class="pebble", drift_kind="slow", velocity=Vec2())
        hits_needed = asteroid.hits_max
        world = self._world_with_asteroid(asteroid)
        for _ in range(hits_needed):
            world.projectiles = [Projectile(pos=Vec2(20, 50), vel=Vec2(400, 0))]
            world._update_projectiles(0.05)
        self.assertEqual(len(world.asteroids), 0)

    def test_rock_splits_after_enough_hits_when_medium(self) -> None:
        asteroid = make_asteroid(Vec2(50, 50), seed=401001, size_class="rock", drift_kind="slow", velocity=Vec2())
        self.assertEqual(asteroid.tier, AsteroidTier.MEDIUM)
        hits_needed = asteroid.hits_max
        world = self._world_with_asteroid(asteroid)
        for _ in range(hits_needed):
            world.projectiles = [Projectile(pos=Vec2(20, 50), vel=Vec2(400, 0))]
            world._update_projectiles(0.05)
        self.assertGreater(len(world.asteroids), 1)
        self.assertLessEqual(len(world.asteroids), 3)

    def test_small_rock_vaporizes_in_world(self) -> None:
        asteroid = make_asteroid(Vec2(50, 50), seed=401003, size_class="rock", drift_kind="slow", velocity=Vec2())
        self.assertEqual(asteroid.tier, AsteroidTier.SMALL)
        hits_needed = asteroid.hits_max
        world = self._world_with_asteroid(asteroid)
        for _ in range(hits_needed):
            world.projectiles = [Projectile(pos=Vec2(20, 50), vel=Vec2(400, 0))]
            world._update_projectiles(0.05)
        self.assertEqual(len(world.asteroids), 0)

    def test_boulder_splits_after_enough_hits(self) -> None:
        asteroid = make_asteroid(Vec2(50, 50), seed=601, size_class="boulder", drift_kind="slow", velocity=Vec2())
        hits_needed = asteroid.hits_max
        world = self._world_with_asteroid(asteroid)
        for _ in range(hits_needed):
            world.projectiles = [Projectile(pos=Vec2(20, 50), vel=Vec2(400, 0))]
            world._update_projectiles(0.05)
        self.assertGreater(len(world.asteroids), 1)
        self.assertLessEqual(len(world.asteroids), 4)

    def test_threat_snapshots_exclude_destroyed_parent(self) -> None:
        asteroid = make_asteroid(Vec2(50, 50), seed=301, size_class="pebble", drift_kind="slow", velocity=Vec2())
        world = self._world_with_asteroid(asteroid)
        for _ in range(asteroid.hits_max):
            world.projectiles = [Projectile(pos=Vec2(20, 50), vel=Vec2(400, 0))]
            world._update_projectiles(0.05)
        snapshots = build_asteroid_threat_snapshots(world.asteroids)
        self.assertEqual(len(snapshots), len(world.asteroids))

    def test_hostile_projectile_damages_asteroid(self) -> None:
        asteroid = make_asteroid(Vec2(50, 50), seed=102, size_class="rock", drift_kind="slow", velocity=Vec2())
        initial_hits = asteroid.hits_remaining
        world = self._world_with_asteroid(asteroid)
        world.projectiles = [Projectile(pos=Vec2(20, 50), vel=Vec2(400, 0), hostile=True)]
        world._update_projectiles(0.05)
        self.assertEqual(asteroid.hits_remaining, initial_hits - 1)
        self.assertEqual(len(world.projectiles), 0)

    def test_destroying_overlap_asteroid_avoids_same_frame_chip(self) -> None:
        asteroid = make_asteroid(Vec2(50, 50), seed=888, size_class="pebble", drift_kind="slow", velocity=Vec2())
        asteroid.hits_max = 1
        asteroid.hits_remaining = 1
        world = self._world_with_asteroid(asteroid, ship_pos=Vec2(50, 50))
        world.refresh_threat_snapshots()
        world.projectiles = [Projectile(pos=Vec2(10, 50), vel=Vec2(500, 0))]
        world._update_projectiles(0.05)
        world._check_loss()
        self.assertEqual(world.status, GameStatus.RUNNING)
        self.assertEqual(len(world.asteroids), 0)

    def test_hostile_shot_blocked_from_ship_by_medium_asteroid(self) -> None:
        asteroid = make_asteroid(Vec2(50, 50), seed=401001, size_class="rock", drift_kind="slow", velocity=Vec2())
        self.assertEqual(asteroid.tier, AsteroidTier.MEDIUM)
        while asteroid.hits_remaining > 1:
            apply_friendly_projectile_hit(
                asteroid,
                Vec2(50, 50),
                Vec2(200, 0),
                world_asteroid_count=1,
            )
        world = self._world_with_asteroid(asteroid, ship_pos=Vec2(120, 50))
        world.projectiles = [Projectile(pos=Vec2(10, 50), vel=Vec2(400, 0), hostile=True)]
        world._update_projectiles(0.05)
        self.assertEqual(world.status, GameStatus.RUNNING)
        self.assertGreater(len(world.asteroids), 0)
        self.assertLessEqual(len(world.asteroids), 3)
        self.assertEqual(len(world.projectiles), 0)

    def test_level_field_is_mostly_small_tier(self) -> None:
        for level_id in ("cove", "solar"):
            world = build_level(level_id)
            self.assertGreaterEqual(len(world.asteroids), 3)
            small_count = sum(1 for a in world.asteroids if a.tier is AsteroidTier.SMALL)
            self.assertGreater(small_count, len(world.asteroids) // 2)
            for asteroid in world.asteroids:
                self.assertGreater(asteroid.hits_max, 0)
                self.assertEqual(asteroid.hits_remaining, asteroid.hits_max)
                self.assertGreater(asteroid.mass, 0.0)
                if asteroid.size_class == "boulder":
                    self.assertEqual(asteroid.tier, AsteroidTier.LARGE)
                elif asteroid.size_class == "pebble":
                    self.assertEqual(asteroid.tier, AsteroidTier.SMALL)
                elif asteroid.approximate_radius() >= ROCK_MEDIUM_MIN_RADIUS:
                    self.assertEqual(asteroid.tier, AsteroidTier.MEDIUM)

    def test_cove_has_authored_medium_and_chart_rim(self) -> None:
        world = build_level("cove")
        medium_rocks = [a for a in world.asteroids if a.tier is AsteroidTier.MEDIUM]
        self.assertEqual(len(medium_rocks), 5)
        authored = [a for a in medium_rocks if a.seed == 102]
        self.assertEqual(len(authored), 1)

    def test_cove_has_oob_chart_ring(self) -> None:
        from gravity_ho_matey.gameplay.chart_bounds import (
            COVE_OOB_PLACEMENT_MARGIN_FRAC,
            oob_ring_radius_for_margin_frac,
        )

        world = build_level("cove")
        ring = [a for a in world.asteroids if a.free_bounds]
        self.assertEqual(len(ring), 20)
        expected_radius = oob_ring_radius_for_margin_frac(
            world.config, COVE_OOB_PLACEMENT_MARGIN_FRAC
        )
        anchor = Vec2(world.config.width * 0.5, world.config.height * 0.5)
        main_ring = [a for a in ring if a.ring_radius and abs(a.ring_radius - expected_radius) < 1.0]
        self.assertEqual(len(main_ring), 12)
        for asteroid in main_ring:
            self.assertEqual(asteroid.size_class, "pebble")
            self.assertEqual(asteroid.drift_kind, "ring")
            self.assertAlmostEqual((asteroid.pos - anchor).length(), expected_radius, delta=14.0)


if __name__ == "__main__":
    unittest.main()
