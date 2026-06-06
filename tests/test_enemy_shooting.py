import math
import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CHUNKS_PER_LIFE, CampaignState
from gravity_ho_matey.gameplay.damage import DamageSource
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.entities import FinishGate, GameStatus, Projectile, Ship, WorldConfig
from gravity_ho_matey.gameplay.session import capture_level_spawn, respawn_ship_at_spawn
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld
from gravity_ho_matey.levels.solar_patrols import solar_patrol_enemies


def combat_world(
    *,
    ship_pos: Vec2 | None = None,
    ship_vel: Vec2 | None = None,
    enemies: list[PatrolEnemy] | None = None,
) -> GameWorld:
    world = GameWorld(
        config=WorldConfig(width=960, height=1680, level_theme="solar"),
        ship=Ship(pos=ship_pos or Vec2(480, 840), vel=ship_vel or Vec2()),
        walls=[],
        wells=[],
        beacons=[],
        finish_gate=FinishGate(Rect(900, 1600, 40, 40)),
        enemies=enemies or [],
    )
    capture_level_spawn(world)
    return world


class EnemyShootingTests(unittest.TestCase):
    def test_armed_enemy_fires_when_in_range(self) -> None:
        enemy = PatrolEnemy(
            waypoints=(Vec2(100, 100), Vec2(200, 100)),
            can_shoot=True,
            fire_cooldown=0.0,
            fire_interval=2.0,
        )
        enemy.pos = Vec2(100, 100)
        world = combat_world(ship_pos=Vec2(280, 100))
        world.enemies = [enemy]
        world.update(0.016, ControlIntent())
        hostile = [p for p in world.projectiles if p.hostile]
        self.assertEqual(len(hostile), 1)
        self.assertGreater(hostile[0].vel.length(), 180.0)

    def test_unarmed_enemy_never_fires(self) -> None:
        enemy = PatrolEnemy(waypoints=(Vec2(100, 100), Vec2(200, 100)))
        enemy.pos = Vec2(100, 100)
        world = combat_world(ship_pos=Vec2(280, 100), enemies=[enemy])
        world.update(0.016, ControlIntent())
        self.assertEqual(len(world.projectiles), 0)

    def test_fire_respects_cooldown(self) -> None:
        enemy = PatrolEnemy(
            waypoints=(Vec2(100, 100), Vec2(200, 100)),
            can_shoot=True,
            fire_cooldown=0.0,
            fire_interval=2.0,
        )
        enemy.pos = Vec2(100, 100)
        world = combat_world(ship_pos=Vec2(280, 100), enemies=[enemy])
        world.update(0.016, ControlIntent())
        self.assertEqual(len(world.projectiles), 1)
        world.update(0.016, ControlIntent())
        self.assertEqual(len(world.projectiles), 1)

    def test_hostile_projectile_chips_hull_one_chunk(self) -> None:
        world = combat_world()
        world.projectiles.append(
            Projectile(pos=Vec2(world.ship.pos.x, world.ship.pos.y), vel=Vec2(), hostile=True)
        )
        world._update_projectiles(0.016)
        self.assertEqual(world.status, GameStatus.SHIP_HIT)
        self.assertEqual(world.last_damage.source, DamageSource.ENEMY_PROJECTILE)

        campaign = CampaignState.new()
        result = campaign.apply_damage(world.last_damage)
        self.assertTrue(result.chipped)
        self.assertEqual(campaign.hull_chunks, CHUNKS_PER_LIFE - 1)

    def test_invuln_blocks_hostile_projectile(self) -> None:
        world = combat_world()
        world.invuln_remaining = 0.5
        world.projectiles.append(
            Projectile(pos=Vec2(world.ship.pos.x, world.ship.pos.y), vel=Vec2(), hostile=True)
        )
        world._update_projectiles(0.016)
        self.assertEqual(world.status, GameStatus.RUNNING)
        self.assertEqual(len(world.projectiles), 0)

    def test_hostile_shots_do_not_hit_enemies(self) -> None:
        enemy = PatrolEnemy(waypoints=(Vec2(50, 50), Vec2(60, 50)))
        enemy.pos = Vec2(50, 50)
        world = combat_world(enemies=[enemy])
        world.projectiles.append(Projectile(pos=Vec2(50, 50), vel=Vec2(), hostile=True))
        world._update_projectiles(0.016)
        self.assertTrue(enemy.alive)

    def test_player_shots_still_kill_enemies(self) -> None:
        enemy = PatrolEnemy(waypoints=(Vec2(50, 50), Vec2(60, 50)))
        world = combat_world(enemies=[enemy])
        world.projectiles.append(Projectile(pos=Vec2(50, 50), vel=Vec2(), hostile=False))
        world._update_projectiles(0.016)
        self.assertFalse(enemy.alive)

    def test_lead_fire_tags_moving_ship(self) -> None:
        enemy = PatrolEnemy(
            waypoints=(Vec2(0, 400), Vec2(200, 400)),
            can_shoot=True,
            fire_cooldown=0.0,
            fire_interval=2.0,
            shot_speed=260.0,
            engage_range=500.0,
        )
        enemy.pos = Vec2(0, 400)
        world = combat_world(ship_pos=Vec2(350, 400), ship_vel=Vec2(0, -140))
        world.enemies = [enemy]
        world.update(0.016, ControlIntent())
        self.assertEqual(len(world.projectiles), 1)
        shot = world.projectiles[0]
        self.assertLess(shot.vel.y, -10.0)

    def test_solar_patrols_are_armed(self) -> None:
        enemies = solar_patrol_enemies(1680)
        self.assertGreaterEqual(len(enemies), 3)
        self.assertTrue(all(enemy.can_shoot for enemy in enemies))

    def test_hostile_engagement_simulation_scores_hits(self) -> None:
        enemy = PatrolEnemy(
            waypoints=(Vec2(400, 400), Vec2(500, 400)),
            can_shoot=True,
            fire_cooldown=0.0,
            fire_interval=2.8,
            engage_range=480.0,
            shot_speed=255.0,
            aim_lead_factor=1.0,
            aim_spread_rad=0.0,
        )
        enemy.pos = Vec2(400, 400)
        world = combat_world(ship_pos=Vec2(620, 430), ship_vel=Vec2(-90, 40))
        world.enemies = [enemy]
        hits = 0
        for _ in range(400):
            if world.status is not GameStatus.RUNNING:
                world.status = GameStatus.RUNNING
                world.last_damage = None
                respawn_ship_at_spawn(world)
            world.update(0.05, ControlIntent())
            if world.last_damage and world.last_damage.source is DamageSource.ENEMY_PROJECTILE:
                hits += 1
                world.status = GameStatus.RUNNING
                world.last_damage = None
                world.invuln_remaining = 0.0
        self.assertGreaterEqual(hits, 2)


if __name__ == "__main__":
    unittest.main()
