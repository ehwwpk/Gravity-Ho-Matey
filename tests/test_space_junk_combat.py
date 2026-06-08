import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid
from gravity_ho_matey.gameplay.entities import FinishGate, Projectile, Ship, WorldConfig
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.space_junk_prefabs import instantiate_junk
from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld
from gravity_ho_matey.levels.junk_sandbox_layout import build_junk_sandbox_world


class SpaceJunkCombatTests(unittest.TestCase):
    def test_projectile_blocked_by_junk_not_asteroid(self) -> None:
        junk = instantiate_junk("girder_a", Vec2(500.0, 500.0))
        rock = make_asteroid(Vec2(520.0, 500.0), seed=1, drift_kind="slow", velocity=Vec2())
        config = WorldConfig(width=1200, height=1200, open_bounds=True)
        world = GameWorld(
            config=config,
            ship=Ship(pos=Vec2(100.0, 500.0)),
            asteroids=[rock],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(1100, 1100, 40, 40)),
            space_junk=[junk],
            junk_spatial_static=True,
            projectiles=[
                Projectile(pos=Vec2(498.0, 500.0), vel=Vec2(10.0, 0.0), radius=4.0, pierce_remaining=2),
            ],
        )
        world.junk_spatial.rebuild(world.space_junk)
        hits_before = rock.hits_remaining
        world._update_projectiles(1 / 60.0)
        self.assertEqual(len(world.projectiles), 0)
        self.assertEqual(rock.hits_remaining, hits_before)

    def test_laser_pierce_stops_at_junk(self) -> None:
        junk = instantiate_junk("hull_plate_a", Vec2(400.0, 400.0))
        config = WorldConfig(width=900, height=900, open_bounds=True)
        world = GameWorld(
            config=config,
            ship=Ship(pos=Vec2(100.0, 400.0)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(800, 800, 40, 40)),
            space_junk=[junk],
            junk_spatial_static=True,
            projectiles=[
                Projectile(
                    pos=Vec2(398.0, 400.0),
                    vel=Vec2(20.0, 0.0),
                    radius=3.0,
                    pierce_remaining=3,
                    weapon_track=WeaponTrack.LASER,
                ),
            ],
        )
        world.junk_spatial.rebuild(world.space_junk)
        world._update_projectiles(1 / 60.0)
        self.assertEqual(len(world.projectiles), 0)

    def test_hostile_shot_blocked_without_asteroid_combat(self) -> None:
        junk = instantiate_junk("container_a", Vec2(600.0, 600.0))
        rock = make_asteroid(Vec2(610.0, 600.0), seed=2, drift_kind="slow", velocity=Vec2())
        config = WorldConfig(width=1200, height=1200, open_bounds=True)
        world = GameWorld(
            config=config,
            ship=Ship(pos=Vec2(100.0, 600.0)),
            asteroids=[rock],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(1100, 1100, 40, 40)),
            space_junk=[junk],
            junk_spatial_static=True,
            projectiles=[
                Projectile(pos=Vec2(598.0, 600.0), vel=Vec2(8.0, 0.0), radius=4.0, hostile=True),
            ],
        )
        world.junk_spatial.rebuild(world.space_junk)
        before = rock.hits_remaining
        world._update_projectiles(1 / 60.0)
        self.assertEqual(len(world.projectiles), 0)
        self.assertEqual(rock.hits_remaining, before)
        self.assertEqual(len(world.space_junk), 1)

    def test_patrol_blocked_by_wall_over_frames(self) -> None:
        world = build_junk_sandbox_world()
        patrol = world.enemies[0]
        for _ in range(60):
            world.update(1 / 60.0, ControlIntent())
        self.assertGreater(patrol.pos.x, 820.0)
        self.assertLess(patrol.pos.x, 1180.0)

    def test_enemy_passes_asteroid_without_junk(self) -> None:
        rock = make_asteroid(Vec2(500.0, 500.0), seed=3, drift_kind="slow", velocity=Vec2())
        patrol = PatrolEnemy(
            waypoints=(Vec2(500.0, 500.0),),
            pos=Vec2(500.0, 500.0),
            vel=Vec2(30.0, 0.0),
        )
        config = WorldConfig(width=1000, height=1000, open_bounds=True)
        world = GameWorld(
            config=config,
            ship=Ship(pos=Vec2(100.0, 100.0)),
            asteroids=[rock],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(900, 900, 40, 40)),
            enemies=[patrol],
        )
        world.update(1 / 60.0, ControlIntent())
        self.assertGreater((patrol.pos - rock.pos).length(), 0.0)


if __name__ == "__main__":
    unittest.main()
