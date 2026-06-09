import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.damage import DamageSource
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.entities import FinishGate, GameStatus, Ship, WorldConfig
from gravity_ho_matey.gameplay.session import capture_level_spawn
from gravity_ho_matey.gameplay.squid_enemy import SQUID_HITS_MAX, SquidEnemy
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld
from gravity_ho_matey.levels.drift_belt_layout import (
    CENTER,
    FINAL_RING_RADIUS,
    FINISH_ORBIT_RADIUS,
    RING_SPECS,
    build_drift_layout,
)
from gravity_ho_matey.levels.level_registry import build_level, next_level_id


class DriftLevelTests(unittest.TestCase):
    def test_registry_includes_drift_after_solar(self) -> None:
        self.assertEqual(next_level_id("solar"), "drift")
        self.assertEqual(next_level_id("drift"), "rift")

    def test_drift_layout_has_seven_rings_and_north_exit(self) -> None:
        self.assertEqual(len(RING_SPECS), 7)
        layout = build_drift_layout()
        finish_c = Vec2(
            layout.finish_gate.rect.x + layout.finish_gate.rect.w * 0.5,
            layout.finish_gate.rect.y + layout.finish_gate.rect.h * 0.5,
        )
        self.assertAlmostEqual((finish_c - layout.center).length(), FINISH_ORBIT_RADIUS, delta=2.0)
        self.assertGreater(FINISH_ORBIT_RADIUS, FINAL_RING_RADIUS + 300.0)
        self.assertLess(finish_c.y, layout.center.y)

    def test_drift_world_content(self) -> None:
        world = build_level("drift")
        self.assertEqual(world.config.level_theme, "drift")
        self.assertEqual(world.config.width, 4800)
        self.assertTrue(world.config.open_bounds)
        self.assertFalse(world.config.radiation_enabled)
        self.assertEqual(world.config.max_asteroids, 200)
        self.assertEqual(len(world.beacons), 0)
        self.assertTrue(world.finish_unlocked)
        expected_rocks = sum(spec[1] for spec in RING_SPECS)
        self.assertEqual(len(world.asteroids), expected_rocks)
        self.assertEqual(len(world.wells), 4)
        self.assertTrue(all(w.kind == "black_hole" for w in world.wells))
        self.assertEqual(len(world.enemies), 12)
        self.assertEqual(len(build_drift_layout().squid_angles_deg), 7)
        self.assertEqual(len(build_drift_layout().ring_lurker_specs), 5)
        self.assertTrue(all(e.kind is EnemyKind.SQUID for e in world.enemies))

    def test_drift_ring_lurkers_hide_on_belts_past_ring_two(self) -> None:
        layout = build_drift_layout()
        world = build_level("drift")
        lurker_radii = {RING_SPECS[ring_index][0] for ring_index, _ in layout.ring_lurker_specs}
        self.assertEqual(len(lurker_radii), 5)
        for enemy in world.enemies:
            if enemy.kind is not EnemyKind.SQUID:
                continue
            dist = (enemy.pos - layout.center).length()
            if abs(dist - layout.squid_ring_radius) <= 4.0:
                continue
            self.assertTrue(
                any(abs(dist - radius) < 1.0 for radius in lurker_radii),
                msg=f"enemy at radius {dist} not on a lurker belt",
            )

    def test_nearby_rocks_have_collision_meshes(self) -> None:
        world = build_level("drift")
        world.asteroid_spatial.rebuild(world.asteroids)
        world.refresh_threat_snapshots()
        for asteroid in world.asteroid_spatial.query_interaction_zones(world.ship.pos):
            self.assertIn(
                asteroid,
                [snap.asteroid for snap in world.asteroid_threat_snapshots],
            )

    def test_spawn_bubble_clear(self) -> None:
        world = build_level("drift")
        for asteroid in world.asteroids:
            self.assertGreaterEqual((asteroid.pos - CENTER).length(), 170.0)

    def test_ring_radii_distinct(self) -> None:
        world = build_level("drift")
        anchor = CENTER
        radii: set[int] = set()
        for asteroid in world.asteroids:
            if asteroid.ring_anchor is None:
                continue
            if (asteroid.ring_anchor - anchor).length_sq() > 1.0:
                continue
            radii.add(int(round(asteroid.ring_radius)))
        for spec in RING_SPECS:
            self.assertIn(int(round(spec[0])), radii)


class SquidEnemyTests(unittest.TestCase):
    @staticmethod
    def _attach_tentacles_to_hull(squid: SquidEnemy, ship_pos: Vec2) -> None:
        squid.tip_pos = [Vec2(ship_pos.x + 2, ship_pos.y + (i % 3) - 1) for i in range(8)]

    def test_squid_never_fires(self) -> None:
        squid = SquidEnemy(pos=Vec2(100, 100))
        self.assertIsNone(squid.try_fire(Vec2(200, 100), Vec2()))

    def test_player_shot_requires_three_body_hits(self) -> None:
        from gravity_ho_matey.gameplay.entities import Projectile

        squid = SquidEnemy(pos=Vec2(50, 50))
        world = GameWorld(
            config=WorldConfig(width=4800, height=4800, level_theme="drift"),
            ship=Ship(pos=Vec2(80, 50)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(100, 100, 40, 40)),
            enemies=[squid],
        )
        for i in range(2):
            world.projectiles.append(Projectile(pos=Vec2(50, 50), vel=Vec2(), hostile=False))
            world._update_projectiles(0.016)
            self.assertTrue(squid.alive)
            self.assertEqual(squid.hits_remaining, SQUID_HITS_MAX - (i + 1))
        world.projectiles.append(Projectile(pos=Vec2(50, 50), vel=Vec2(), hostile=False))
        world._update_projectiles(0.016)
        self.assertFalse(squid.alive)
        self.assertEqual(len(world.enemies), 0)

    def test_tentacle_span_wider_than_body_shot(self) -> None:
        squid = SquidEnemy(pos=Vec2(100, 100))
        self.assertTrue(squid.coils_ship(Vec2(190, 100), 12.0))
        self.assertFalse(squid.body_hit_by_projectile(Vec2(190, 100), 4.0))

    def test_body_contact_without_tentacles_is_not_clinging(self) -> None:
        squid = SquidEnemy(pos=Vec2(100, 100))
        ship = Vec2(140, 100)
        self.assertTrue(squid.coils_ship(ship, 12.0))
        self.assertFalse(squid.is_clinging(ship, 12.0))

    def test_cling_damage_chips_hull_after_two_seconds(self) -> None:
        squid = SquidEnemy(pos=Vec2(100, 100))
        world = GameWorld(
            config=WorldConfig(width=4800, height=4800, level_theme="drift"),
            ship=Ship(pos=Vec2(140, 100)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(200, 200, 40, 40)),
            enemies=[squid],
        )
        capture_level_spawn(world)
        self._attach_tentacles_to_hull(squid, world.ship.pos)
        self.assertTrue(squid.is_clinging(world.ship.pos, world.ship.radius))
        world._check_enemy_collisions(1.95)
        self.assertEqual(world.status, GameStatus.RUNNING)
        world._check_enemy_collisions(0.1)
        self.assertEqual(world.status, GameStatus.SHIP_HIT)
        self.assertEqual(world.last_damage.source, DamageSource.SQUID_CLING)
        self.assertTrue(squid.alive)

    def test_cling_damage_requires_latch(self) -> None:
        squid = SquidEnemy(pos=Vec2(100, 100))
        world = GameWorld(
            config=WorldConfig(width=4800, height=4800, level_theme="drift"),
            ship=Ship(pos=Vec2(400, 100)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(200, 200, 40, 40)),
            enemies=[squid],
        )
        capture_level_spawn(world)
        world._check_enemy_collisions(2.5)
        self.assertEqual(world.status, GameStatus.RUNNING)

    def test_cling_damage_respects_two_second_interval(self) -> None:
        squid = SquidEnemy(pos=Vec2(100, 100))
        world = GameWorld(
            config=WorldConfig(width=4800, height=4800, level_theme="drift"),
            ship=Ship(pos=Vec2(140, 100)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(200, 200, 40, 40)),
            enemies=[squid],
        )
        capture_level_spawn(world)
        self._attach_tentacles_to_hull(squid, world.ship.pos)
        world._check_enemy_collisions(2.0)
        self.assertEqual(world.status, GameStatus.SHIP_HIT)
        world.status = GameStatus.RUNNING
        world.last_damage = None
        world.invuln_remaining = 0.0
        world._check_enemy_collisions(1.9)
        self.assertEqual(world.status, GameStatus.RUNNING)
        world._check_enemy_collisions(0.2)
        self.assertEqual(world.status, GameStatus.SHIP_HIT)

    def test_multiple_squids_share_one_cling_tick(self) -> None:
        squids = [
            SquidEnemy(pos=Vec2(100, 100)),
            SquidEnemy(pos=Vec2(100, 160)),
        ]
        ship_pos = Vec2(140, 130)
        world = GameWorld(
            config=WorldConfig(width=4800, height=4800, level_theme="drift"),
            ship=Ship(pos=ship_pos),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(200, 200, 40, 40)),
            enemies=squids,
        )
        for squid in squids:
            self._attach_tentacles_to_hull(squid, ship_pos)
            self.assertTrue(squid.is_clinging(ship_pos, world.ship.radius))
        world._check_enemy_collisions(2.0)
        self.assertEqual(world.status, GameStatus.SHIP_HIT)

    def test_squid_cling_play_flow_recovers_in_place(self) -> None:
        from gravity_ho_matey.gameplay.campaign import CampaignState
        from gravity_ho_matey.gameplay.session import recover_ship_in_place
        from gravity_ho_matey.scenes.game_flow import start_play

        scene = start_play("drift", CampaignState.new())
        squid = scene.world.enemies[0]
        ship_pos = Vec2(squid.pos.x + 36, squid.pos.y)
        scene.world.ship.pos = ship_pos
        scene.world.asteroids = [
            asteroid for asteroid in scene.world.asteroids if (asteroid.pos - ship_pos).length() > 140.0
        ]
        scene.world.asteroid_spatial.rebuild(scene.world.asteroids)
        chunks_before = scene.campaign.hull_chunks

        for _ in range(200):
            scene.world.update(0.016, ControlIntent())
            if scene.world.status is GameStatus.SHIP_HIT:
                break
        else:
            self.fail("expected squid cling damage after sustained latch")

        self.assertEqual(scene.world.last_damage.source, DamageSource.SQUID_CLING)
        hit_pos = Vec2(scene.world.ship.pos.x, scene.world.ship.pos.y)
        result = scene.campaign.apply_damage(scene.world.last_damage)
        recover_ship_in_place(scene.world)
        self.assertFalse(result.life_lost)
        self.assertEqual(scene.campaign.hull_chunks, chunks_before - 1)
        self.assertEqual(scene.world.status, GameStatus.RUNNING)
        self.assertEqual(scene.world.ship.pos.x, hit_pos.x)
        self.assertEqual(scene.world.ship.pos.y, hit_pos.y)
        self.assertTrue(squid.alive)


if __name__ == "__main__":
    unittest.main()
