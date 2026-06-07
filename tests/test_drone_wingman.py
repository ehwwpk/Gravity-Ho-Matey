import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.drone_config import (
    DRONE_ASTEROID_AVOID_RADIUS,
    DRONE_OVERHEAT_COOLDOWN,
    DRONE_WINGMAN_HITS_MAX,
    DRONE_WINGMAN_SHOP_PRICE,
)
from gravity_ho_matey.gameplay.drone_session import deploy_drone_wingman, sync_drone_wingman_to_campaign
from gravity_ho_matey.gameplay.drone_wingman import DroneWingman
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.entities import FinishGate, GameStatus, Ship, WorldConfig
from gravity_ho_matey.gameplay.friendly_fighter import ThreatTarget
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.session import wire_world_for_campaign
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld


def _empty_world(*, ship_pos: Vec2 | None = None) -> GameWorld:
    return GameWorld(
        config=WorldConfig(width=800, height=600),
        ship=Ship(pos=ship_pos or Vec2(400, 300)),
        asteroids=[],
        wells=[],
        beacons=[],
        finish_gate=FinishGate(Rect(700, 500, 20, 20)),
    )


class DroneShopTests(unittest.TestCase):
    def test_drone_purchase_costs_twenty_jewels_and_sets_pending(self) -> None:
        campaign = CampaignState.new()
        campaign.jewels = DRONE_WINGMAN_SHOP_PRICE
        self.assertTrue(campaign.try_purchase(PowerUpKind.DRONE_WINGMAN))
        self.assertEqual(campaign.jewels, 0)
        self.assertTrue(campaign.drone_wingman_pending)
        self.assertFalse(campaign.can_purchase(PowerUpKind.DRONE_WINGMAN))

    def test_drone_price_does_not_double(self) -> None:
        campaign = CampaignState.new()
        self.assertEqual(campaign.upgrade_price(PowerUpKind.DRONE_WINGMAN), DRONE_WINGMAN_SHOP_PRICE)


class DroneDeployTests(unittest.TestCase):
    def test_pending_deploy_spawns_full_hp_drone(self) -> None:
        campaign = CampaignState.new()
        campaign.drone_wingman_pending = True
        world = _empty_world()
        deploy_drone_wingman(world, campaign)
        self.assertIsNotNone(world.drone_wingman)
        assert world.drone_wingman is not None
        self.assertEqual(world.drone_wingman.hits_remaining, DRONE_WINGMAN_HITS_MAX)
        self.assertFalse(campaign.drone_wingman_pending)
        self.assertEqual(campaign.drone_wingman_hp, DRONE_WINGMAN_HITS_MAX)

    def test_carried_hp_restored_on_level_start(self) -> None:
        campaign = CampaignState.new()
        campaign.drone_wingman_hp = 3
        world = _empty_world()
        deploy_drone_wingman(world, campaign)
        self.assertIsNotNone(world.drone_wingman)
        assert world.drone_wingman is not None
        self.assertEqual(world.drone_wingman.hits_remaining, 3)

    def test_wire_world_deploys_pending_drone(self) -> None:
        campaign = CampaignState.new()
        campaign.drone_wingman_pending = True
        world = _empty_world()
        wire_world_for_campaign(world, campaign)
        self.assertIsNotNone(world.drone_wingman)


class DroneCombatTests(unittest.TestCase):
    def test_overheat_blocks_firing(self) -> None:
        drone = DroneWingman.spawn_behind_player(Ship(pos=Vec2(100, 100)))
        drone.overheat_timer = DRONE_OVERHEAT_COOLDOWN
        threat = ThreatTarget(pos=Vec2(140, 100), vel=Vec2(), radius=10.0)
        self.assertIsNone(drone.try_fire(threat))

    def test_sustained_fire_triggers_overheat(self) -> None:
        drone = DroneWingman.spawn_behind_player(Ship(pos=Vec2(100, 100)))
        threat = ThreatTarget(pos=Vec2(160, 100), vel=Vec2(), radius=10.0)
        for _ in range(10):
            drone.fire_cooldown = 0.0
            drone.try_fire(threat)
        self.assertTrue(drone.is_overheated)
        self.assertIsNone(drone.try_fire(threat))

    def test_hostile_projectile_damages_drone(self) -> None:
        world = _empty_world()
        world.drone_wingman = DroneWingman.spawn_behind_player(world.ship)
        from gravity_ho_matey.gameplay.entities import Projectile

        bolt = Projectile(
            pos=Vec2(world.drone_wingman.pos.x, world.drone_wingman.pos.y),
            vel=Vec2(),
            ttl=1.0,
            hostile=True,
        )
        world._projectile_hits_drone(bolt)
        assert world.drone_wingman is not None
        self.assertEqual(world.drone_wingman.hits_remaining, DRONE_WINGMAN_HITS_MAX - 1)

    def test_drone_destroyed_after_five_hits(self) -> None:
        world = _empty_world()
        world.drone_wingman = DroneWingman.spawn_behind_player(world.ship)
        from gravity_ho_matey.gameplay.entities import Projectile

        for _ in range(DRONE_WINGMAN_HITS_MAX):
            assert world.drone_wingman is not None
            bolt = Projectile(
                pos=Vec2(world.drone_wingman.pos.x, world.drone_wingman.pos.y),
                vel=Vec2(),
                ttl=1.0,
                hostile=True,
            )
            world._projectile_hits_drone(bolt)
        self.assertIsNone(world.drone_wingman)

    def test_drone_auto_targets_nearby_enemy(self) -> None:
        world = _empty_world()
        world.drone_wingman = DroneWingman.spawn_behind_player(world.ship)
        enemy = PatrolEnemy(waypoints=(Vec2(500, 280), Vec2(540, 320)), pos=Vec2(520, 300))
        world.enemies.append(enemy)
        before = len(world.projectiles)
        for _ in range(40):
            world.update(0.05, ControlIntent())
        self.assertGreater(len(world.projectiles), before)


class DroneAsteroidTests(unittest.TestCase):
    def test_pick_threat_prioritizes_imminent_asteroid(self) -> None:
        drone = DroneWingman.spawn_behind_player(Ship(pos=Vec2(400, 300)))
        rock = make_asteroid(Vec2(418, 300), seed=77, size_class="rock", drift_kind="slow")
        rock.vel = Vec2(-30, 0)
        enemy = PatrolEnemy(waypoints=(Vec2(900, 300), Vec2(920, 320)), pos=Vec2(880, 300))
        threat = drone.pick_threat(
            [enemy],
            None,
            player_pos=Vec2(400, 300),
            asteroids=[rock],
        )
        self.assertIsNotNone(threat)
        assert threat is not None
        self.assertTrue(threat.is_asteroid)

    def test_avoidance_pushes_away_from_closing_rock(self) -> None:
        drone = DroneWingman.spawn_behind_player(Ship(pos=Vec2(400, 300)))
        rock = make_asteroid(Vec2(460, 300), seed=88, size_class="rock", drift_kind="slow")
        rock.vel = Vec2(-120, 0)
        start_gap = (rock.pos - drone.pos).length() - rock.approximate_radius() - drone.radius
        for _ in range(24):
            drone.integrate(
                0.05,
                player_pos=Vec2(400, 300),
                player_vel=Vec2(),
                player_angle=0.0,
                wells=[],
                gravity_scale=1.0,
                drag=0.98,
                well_maw_radius=10.0,
                threat=None,
                asteroids=[rock],
            )
            rock.pos = rock.pos + rock.vel * 0.05
        end_gap = (rock.pos - drone.pos).length() - rock.approximate_radius() - drone.radius
        self.assertGreater(end_gap, start_gap - 8.0)

    def test_drone_shoots_nearby_asteroid(self) -> None:
        world = _empty_world(ship_pos=Vec2(200, 200))
        world.drone_wingman = DroneWingman.spawn_behind_player(world.ship)
        rock = make_asteroid(Vec2(260, 200), seed=99, size_class="rock", drift_kind="slow")
        hits_start = rock.hits_remaining
        world.asteroids.append(rock)
        world.asteroid_spatial.rebuild(world.asteroids)
        peak_projectiles = 0
        for _ in range(50):
            world.update(0.05, ControlIntent())
            peak_projectiles = max(peak_projectiles, len(world.projectiles))
        chipped = rock.hits_remaining < hits_start
        self.assertTrue(peak_projectiles > 0 or chipped)


class DroneSyncTests(unittest.TestCase):
    def test_sync_persists_hp_to_campaign(self) -> None:
        campaign = CampaignState.new()
        world = _empty_world()
        world.drone_wingman = DroneWingman.spawn_behind_player(world.ship, hits_remaining=4)
        sync_drone_wingman_to_campaign(world, campaign)
        self.assertEqual(campaign.drone_wingman_hp, 4)

    def test_sync_clears_campaign_when_drone_destroyed(self) -> None:
        campaign = CampaignState.new()
        campaign.drone_wingman_hp = 2
        world = _empty_world()
        world.drone_wingman = DroneWingman.spawn_behind_player(world.ship, hits_remaining=1)
        from gravity_ho_matey.gameplay.entities import Projectile

        bolt = Projectile(
            pos=Vec2(world.drone_wingman.pos.x, world.drone_wingman.pos.y),
            vel=Vec2(),
            ttl=1.0,
            hostile=True,
        )
        world._projectile_hits_drone(bolt)
        sync_drone_wingman_to_campaign(world, campaign)
        self.assertEqual(campaign.drone_wingman_hp, 0)
        self.assertIsNone(world.drone_wingman)


if __name__ == "__main__":
    unittest.main()
