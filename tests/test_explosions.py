import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.entities import FinishGate, GameStatus, GravityWell, Projectile, Ship, Wall, WorldConfig
from gravity_ho_matey.gameplay.explosions import (
    ExplosionKind,
    ExplosionSystem,
    spawn_explosion,
    update_explosion,
)
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld


class ExplosionUnitTests(unittest.TestCase):
    def test_spawn_creates_particles_and_ring(self) -> None:
        explosion = spawn_explosion(ExplosionKind.ENEMY_DESTROYED, Vec2(50, 50))
        self.assertGreater(len(explosion.particles), 0)
        self.assertGreater(explosion.ring_max, 0.0)

    def test_explosion_expires_after_update(self) -> None:
        explosion = spawn_explosion(ExplosionKind.PROJECTILE_IMPACT, Vec2(0, 0))
        for _ in range(40):
            update_explosion(explosion, 0.05)
        self.assertFalse(explosion.alive)

    def test_system_prunes_dead_explosions(self) -> None:
        system = ExplosionSystem()
        system.spawn(ExplosionKind.PROJECTILE_IMPACT, Vec2(10, 10))
        for _ in range(30):
            system.update(0.05)
        self.assertEqual(len(system.active), 0)


class ExplosionWorldTests(unittest.TestCase):
    def test_enemy_kill_spawns_impact_and_destroyed_fx(self) -> None:
        enemy = PatrolEnemy(waypoints=(Vec2(50, 50), Vec2(60, 50)))
        world = GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=Vec2(10, 10)),
            walls=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
            enemies=[enemy],
            projectiles=[Projectile(pos=Vec2(50, 50), vel=Vec2(0, 0))],
        )
        world._update_projectiles(0.016)
        kinds = {fx.kind for fx in world.explosions.active}
        self.assertIn(ExplosionKind.PROJECTILE_IMPACT, kinds)
        self.assertIn(ExplosionKind.ENEMY_DESTROYED, kinds)

    def test_wall_impact_spawns_projectile_fx(self) -> None:
        world = GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=Vec2(10, 10)),
            walls=[Wall(Rect(48, 0, 20, 200))],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
            projectiles=[Projectile(pos=Vec2(50, 50), vel=Vec2(200, 0))],
        )
        world._update_projectiles(0.05)
        self.assertGreaterEqual(len(world.explosions.active), 1)
        self.assertEqual(world.explosions.active[0].kind, ExplosionKind.PROJECTILE_IMPACT)

    def test_ship_hit_spawns_struck_fx(self) -> None:
        world = GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=Vec2(-5, 50)),
            walls=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
        )
        world._check_loss()
        self.assertEqual(world.status, GameStatus.SHIP_HIT)
        self.assertEqual(world.explosions.active[0].kind, ExplosionKind.SHIP_STRUCK)

    def test_lethal_well_spawns_destroyed_fx(self) -> None:
        world = GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=Vec2(100, 100)),
            walls=[],
            wells=[GravityWell(Vec2(100, 100), strength=9000, radius=50, kind="black_hole", maw_radius=20)],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
        )
        world._check_loss()
        self.assertEqual(world.explosions.active[0].kind, ExplosionKind.SHIP_DESTROYED)

    def test_explosions_keep_updating_after_ship_hit(self) -> None:
        world = GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=Vec2(-5, 50)),
            walls=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
        )
        world._check_loss()
        count_after_hit = len(world.explosions.active)
        world.update(0.1, ControlIntent())
        self.assertLessEqual(len(world.explosions.active), count_after_hit)


if __name__ == "__main__":
    unittest.main()
