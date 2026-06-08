import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid
from gravity_ho_matey.gameplay.entities import FinishGate, GameStatus, Projectile, Ship, WorldConfig
from gravity_ho_matey.gameplay.friendly_fighter import FriendlyFighter
from gravity_ho_matey.gameplay.hostile_fighter import HostileFighter
from gravity_ho_matey.gameplay.space_junk import junk_hit_at
from gravity_ho_matey.gameplay.space_junk_prefabs import instantiate_junk
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld
from gravity_ho_matey.levels.junk_sandbox_layout import build_junk_sandbox_world
from gravity_ho_matey.levels.space_junk_placements import junk_wall_line


def _corridor_world(*, space_junk_enabled: bool = True) -> GameWorld:
    left = junk_wall_line(Vec2(800.0, 400.0), Vec2(800.0, 1800.0), prefab="girder_a", angle=0.0)
    right = junk_wall_line(Vec2(1200.0, 400.0), Vec2(1200.0, 1800.0), prefab="girder_a", angle=0.0)
    config = WorldConfig(width=2000, height=2200, open_bounds=True, space_junk_enabled=space_junk_enabled)
    world = GameWorld(
        config=config,
        ship=Ship(pos=Vec2(1000.0, 350.0)),
        asteroids=[],
        wells=[],
        beacons=[],
        finish_gate=FinishGate(Rect(980, 2100, 40, 40)),
        space_junk=left + right,
        junk_spatial_static=True,
    )
    world.junk_spatial.rebuild(world.space_junk)
    return world


class SpaceJunkIntegrationTests(unittest.TestCase):
    def test_ally_survives_when_separation_clears_overlap(self) -> None:
        junk = instantiate_junk("girder_a", Vec2(1000.0, 900.0))
        ally = FriendlyFighter(wing_id=1, pos=Vec2(1000.0, 900.0))
        world = GameWorld(
            config=WorldConfig(width=1600, height=1600, open_bounds=True),
            ship=Ship(pos=Vec2(1000.0, 500.0)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(1500, 1500, 40, 40)),
            allies=[ally],
            space_junk=[junk],
            junk_spatial_static=True,
        )
        world.junk_spatial.rebuild(world.space_junk)
        world.update(1 / 60.0, ControlIntent())
        self.assertTrue(ally.alive)

    def test_ally_destroyed_when_still_overlapping_junk_after_separation(self) -> None:
        junk = instantiate_junk("girder_a", Vec2(1000.0, 900.0))
        ally = FriendlyFighter(wing_id=1, pos=Vec2(1000.0, 900.0))
        world = GameWorld(
            config=WorldConfig(width=1600, height=1600, open_bounds=True),
            ship=Ship(pos=Vec2(1000.0, 500.0)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(1500, 1500, 40, 40)),
            allies=[ally],
            space_junk=[junk],
            junk_spatial_static=True,
        )
        world.junk_spatial.rebuild(world.space_junk)
        world._resolve_units_against_junk(1 / 60.0)
        ally.pos = Vec2(1000.0, 900.0)
        world._check_ally_hazards()
        self.assertFalse(ally.alive)

    def test_squid_blocked_by_junk_corridor(self) -> None:
        world = _corridor_world()
        squid = SquidEnemy(pos=Vec2(1000.0, 700.0), vel=Vec2(0.0, 120.0))
        world.enemies = [squid]
        for _ in range(60):
            world.update(1 / 60.0, ControlIntent())
        self.assertGreater(squid.pos.x, 820.0)
        self.assertLess(squid.pos.x, 1180.0)

    def test_hostile_fighter_blocked_by_junk_wall(self) -> None:
        world = _corridor_world()
        world.ship.pos = Vec2(400.0, 900.0)
        fighter = HostileFighter(pos=Vec2(950.0, 900.0), vel=Vec2(-30.0, 0.0))
        world.enemies = [fighter]
        for _ in range(90):
            world.update(1 / 60.0, ControlIntent())
        self.assertGreaterEqual(fighter.pos.x, 860.0)
        self.assertIsNone(junk_hit_at(world.space_junk, world.junk_spatial, fighter.pos, fighter.radius))

    def test_explosive_on_junk_face_leaves_junk_unchanged(self) -> None:
        junk = instantiate_junk("girder_a", Vec2(500.0, 500.0))
        rock = make_asteroid(Vec2(560.0, 500.0), seed=9, drift_kind="slow", velocity=Vec2())
        hits_before = rock.hits_remaining
        world = GameWorld(
            config=WorldConfig(width=1200, height=1200, open_bounds=True),
            ship=Ship(pos=Vec2(100.0, 500.0)),
            asteroids=[rock],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(1100, 1100, 40, 40)),
            space_junk=[junk],
            junk_spatial_static=True,
            projectiles=[
                Projectile(
                    pos=Vec2(498.0, 500.0),
                    vel=Vec2(10.0, 0.0),
                    radius=4.0,
                    explosive_radius=72.0,
                    weapon_track=WeaponTrack.EXPLOSIVE,
                ),
            ],
        )
        world.junk_spatial.rebuild(world.space_junk)
        world._update_projectiles(1 / 60.0)
        self.assertEqual(len(world.space_junk), 1)
        self.assertLess(rock.hits_remaining, hits_before)

    def test_junk_list_stable_after_500_frames_of_combat(self) -> None:
        world = build_junk_sandbox_world()
        initial = len(world.space_junk)
        intent = ControlIntent(fire=True)
        for _ in range(500):
            world.update(1 / 60.0, intent)
            if world.status is not GameStatus.RUNNING:
                world.status = GameStatus.RUNNING
        self.assertEqual(len(world.space_junk), initial)

    def test_space_junk_disabled_skips_collision(self) -> None:
        junk = instantiate_junk("girder_a", Vec2(300.0, 300.0))
        config = WorldConfig(width=800, height=800, open_bounds=True, space_junk_enabled=False)
        world = GameWorld(
            config=config,
            ship=Ship(pos=Vec2(300.0, 300.0)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(700, 700, 40, 40)),
            space_junk=[junk],
            junk_spatial_static=True,
        )
        world.junk_spatial.rebuild(world.space_junk)
        self.assertIsNone(world._junk_hit_at(world.ship.pos, world.ship.radius))
        world._check_loss()
        self.assertEqual(world.status, GameStatus.RUNNING)

    def test_squid_cling_does_not_tunnel_through_junk(self) -> None:
        wall = instantiate_junk("girder_a", Vec2(900.0, 1000.0), angle=1.5708)
        ship = Ship(pos=Vec2(1100.0, 1000.0))
        squid = SquidEnemy(pos=Vec2(950.0, 1000.0), vel=Vec2(80.0, 0.0))
        world = GameWorld(
            config=WorldConfig(width=1600, height=1600, open_bounds=True),
            ship=ship,
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(1500, 1500, 40, 40)),
            space_junk=[wall],
            junk_spatial_static=True,
            enemies=[squid],
        )
        world.junk_spatial.rebuild(world.space_junk)
        for _ in range(90):
            world.update(1 / 60.0, ControlIntent())
        self.assertIsNone(junk_hit_at(world.space_junk, world.junk_spatial, squid.pos, squid.radius))


if __name__ == "__main__":
    unittest.main()
