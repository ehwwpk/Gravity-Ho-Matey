import unittest
from unittest import mock

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_bounce import resolve_rubber_hull_bounce
from gravity_ho_matey.gameplay.asteroid_tiers import AsteroidTier
from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.damage import DamageSource
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.entities import Asteroid, FinishGate, GameStatus, Ship, WorldConfig
from gravity_ho_matey.gameplay.jewel_drops import (
    BEACON_JEWEL_MAX,
    BEACON_JEWEL_MIN,
    jewel_count_for_asteroid,
    jewel_count_for_beacon,
    jewel_count_for_boss,
    jewel_count_for_enemy,
)
from gravity_ho_matey.gameplay.jewel_pickup import JewelPickup, spawn_scattered_jewels, tick_jewels
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.progress import is_level_selectable, record_level_cleared, reset_progress
from gravity_ho_matey.gameplay.session import wire_world_for_campaign
from gravity_ho_matey.gameplay.shop_catalog import shop_price_for
from gravity_ho_matey.gameplay.upgrade_config import (
    ACCEL_BONUS_PER_STACK,
    BOOST_TAP_BONUS_PER_STACK,
    RUBBER_HULL_BOUNCE_CHARGES,
    UPGRADE_MAX_STACKS,
)
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld
from gravity_ho_matey.scenes.chart_briefing import _kind_from_shop_hit



def _asteroid_at(pos: Vec2) -> Asteroid:
    return Asteroid(
        pos=pos,
        vel=Vec2(),
        angle=0.0,
        spin=0.0,
        local_verts=(Vec2(18, 0), Vec2(0, 16), Vec2(-18, 0), Vec2(0, -16)),
        tier=AsteroidTier.LARGE,
    )


def _world_with_asteroid(asteroid: Asteroid, ship_pos: Vec2 | None = None) -> GameWorld:
    return GameWorld(
        config=WorldConfig(width=400, height=400),
        ship=Ship(pos=ship_pos or Vec2(100, 100)),
        asteroids=[asteroid],
        wells=[],
        beacons=[],
        finish_gate=FinishGate(Rect(300, 300, 20, 20)),
    )


class CampaignTests(unittest.TestCase):
    def test_new_campaign_has_three_lives(self) -> None:
        campaign = CampaignState.new()
        self.assertEqual(campaign.lives, 3)
        self.assertEqual(campaign.hull_chunks, 3)
        self.assertEqual(campaign.jewels, 0)
        self.assertEqual(sum(campaign.powerup_stacks.values()), 0)
        self.assertEqual(campaign.rubber_hull_charges, 0)

    def test_lose_life_tracks_campaign_total(self) -> None:
        campaign = CampaignState.new()
        self.assertTrue(campaign.lose_life())
        self.assertEqual(campaign.lives, 2)
        self.assertTrue(campaign.lose_life())
        self.assertEqual(campaign.lives, 1)
        self.assertFalse(campaign.lose_life())
        self.assertEqual(campaign.lives, 0)
        self.assertTrue(campaign.game_over)

    def test_powerups_persist_on_fresh_world(self) -> None:
        campaign = CampaignState.new()
        campaign.powerup_stacks[PowerUpKind.RAPID_FIRE] = 1
        world = _world_with_asteroid(_asteroid_at(Vec2(300, 300)))
        wire_world_for_campaign(world, campaign)
        self.assertLess(world.ship.fire_cooldown_multiplier, 1.0)

    def test_thrust_tiers_add_six_percent_accel_each(self) -> None:
        campaign = CampaignState.new()
        campaign.jewels = 500
        ship = Ship(pos=Vec2(0, 0))
        for _ in range(3):
            self.assertTrue(campaign.try_purchase(PowerUpKind.THRUST_BOOST, ship))
        expected = 1.0 + ACCEL_BONUS_PER_STACK * 3
        self.assertAlmostEqual(ship.thrust_multiplier, expected, places=4)

    def test_thrust_capped_at_six_tiers(self) -> None:
        campaign = CampaignState.new()
        campaign.jewels = 9999
        ship = Ship(pos=Vec2(0, 0))
        for _ in range(UPGRADE_MAX_STACKS):
            self.assertTrue(campaign.try_purchase(PowerUpKind.THRUST_BOOST, ship))
        self.assertFalse(campaign.try_purchase(PowerUpKind.THRUST_BOOST, ship))
        self.assertEqual(campaign.powerup_stacks[PowerUpKind.THRUST_BOOST], UPGRADE_MAX_STACKS)

    def test_boost_tap_tiers_add_eight_percent_shift_burst(self) -> None:
        campaign = CampaignState.new()
        campaign.jewels = 500
        ship = Ship(pos=Vec2(0, 0))
        for _ in range(2):
            self.assertTrue(campaign.try_purchase(PowerUpKind.BOOST_TAP, ship))
        expected = 1.0 + BOOST_TAP_BONUS_PER_STACK * 2
        self.assertAlmostEqual(ship.boost_tap_multiplier, expected, places=4)

    def test_shop_price_doubles_per_tier(self) -> None:
        campaign = CampaignState.new()
        self.assertEqual(campaign.upgrade_price(PowerUpKind.THRUST_BOOST), 12)
        campaign.powerup_stacks[PowerUpKind.THRUST_BOOST] = 1
        self.assertEqual(campaign.upgrade_price(PowerUpKind.THRUST_BOOST), 24)
        campaign.powerup_stacks[PowerUpKind.THRUST_BOOST] = 3
        self.assertEqual(
            campaign.upgrade_price(PowerUpKind.THRUST_BOOST),
            shop_price_for(PowerUpKind.THRUST_BOOST, stacks=3, rubber_hull_purchases=0),
        )

    def test_rubber_hull_purchase_grants_ten_charges(self) -> None:
        campaign = CampaignState.new()
        campaign.jewels = 50
        self.assertTrue(campaign.try_purchase(PowerUpKind.RUBBER_HULL))
        self.assertEqual(campaign.rubber_hull_charges, RUBBER_HULL_BOUNCE_CHARGES)
        self.assertFalse(campaign.can_purchase(PowerUpKind.RUBBER_HULL))

    def test_rubber_hull_consumes_on_bounce(self) -> None:
        campaign = CampaignState.new()
        campaign.rubber_hull_charges = 3
        self.assertTrue(campaign.try_consume_rubber_hull_bounce())
        self.assertEqual(campaign.rubber_hull_charges, 2)

    def test_rubber_hull_blocks_asteroid_chip_damage(self) -> None:
        campaign = CampaignState.new()
        campaign.rubber_hull_charges = 2
        asteroid = _asteroid_at(Vec2(100, 100))
        world = _world_with_asteroid(asteroid, ship_pos=Vec2(100, 100))
        wire_world_for_campaign(world, campaign)
        world._check_loss()
        self.assertEqual(world.status, GameStatus.RUNNING)
        self.assertIsNone(world.last_damage)
        self.assertEqual(campaign.rubber_hull_charges, 1)

    def test_rubber_hull_charges_persist_on_new_world(self) -> None:
        campaign = CampaignState.new()
        campaign.rubber_hull_charges = 5
        world_a = _world_with_asteroid(_asteroid_at(Vec2(300, 300)))
        world_b = _world_with_asteroid(_asteroid_at(Vec2(300, 300)))
        wire_world_for_campaign(world_a, campaign)
        wire_world_for_campaign(world_b, campaign)
        self.assertEqual(campaign.rubber_hull_charges, 5)

    def test_shop_purchase_spends_jewels_and_stacks_powerup(self) -> None:
        campaign = CampaignState.new()
        campaign.jewels = 20
        ship = Ship(pos=Vec2(0, 0))
        self.assertTrue(campaign.try_purchase(PowerUpKind.THRUST_BOOST, ship))
        self.assertEqual(campaign.jewels, 8)
        self.assertEqual(campaign.powerup_stacks[PowerUpKind.THRUST_BOOST], 1)
        self.assertAlmostEqual(ship.thrust_multiplier, 1.0 + ACCEL_BONUS_PER_STACK, places=4)

    def test_shop_purchase_rejects_when_too_poor(self) -> None:
        campaign = CampaignState.new()
        campaign.jewels = 3
        self.assertFalse(campaign.try_purchase(PowerUpKind.THRUST_BOOST))
        self.assertEqual(campaign.jewels, 3)
        self.assertEqual(campaign.powerup_stacks[PowerUpKind.THRUST_BOOST], 0)

    def test_jewel_collection_requires_campaign_wiring(self) -> None:
        campaign = CampaignState.new()
        world = GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=Vec2(20, 20)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
            jewels=[JewelPickup(pos=Vec2(20, 20))],
        )
        world.update(0.016, ControlIntent())
        self.assertEqual(len(world.jewels), 1)
        self.assertEqual(campaign.jewels, 0)

        wire_world_for_campaign(world, campaign)
        world.update(0.016, ControlIntent())
        self.assertEqual(len(world.jewels), 0)
        self.assertEqual(campaign.jewels, 1)

    def test_jewel_hud_callback_reports_amount(self) -> None:
        campaign = CampaignState.new()
        events: list[int] = []
        world = GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=Vec2(20, 20)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
            jewels=[JewelPickup(pos=Vec2(20, 20)), JewelPickup(pos=Vec2(21, 21))],
        )
        wire_world_for_campaign(
            world,
            campaign,
            on_jewels_collected_hud=lambda amount: events.append(amount),
        )
        world.update(0.016, ControlIntent())
        self.assertEqual(events, [2])
        self.assertEqual(campaign.jewels, 2)


class JewelDropTests(unittest.TestCase):
    def test_patrol_drop_range(self) -> None:
        import random

        enemy = PatrolEnemy(waypoints=(Vec2(0, 0), Vec2(10, 0)))
        rng = random.Random(7)
        counts = {jewel_count_for_enemy(enemy, rng) for _ in range(40)}
        self.assertTrue(any(4 <= c <= 9 for c in counts if c > 0))
        self.assertIn(0, counts)

    def test_squid_drop_range(self) -> None:
        import random

        enemy = SquidEnemy(pos=Vec2(50, 50))
        rng = random.Random(11)
        counts = {jewel_count_for_enemy(enemy, rng) for _ in range(40)}
        self.assertTrue(any(1 <= c <= 4 for c in counts if c > 0))

    def test_boss_drop_range(self) -> None:
        import random

        rng = random.Random(3)
        counts = {jewel_count_for_boss(Vec2(100, 200), rng) for _ in range(20)}
        self.assertTrue(all(15 <= c <= 22 for c in counts))

    def test_beacon_always_drops_two_to_five(self) -> None:
        import random

        rng = random.Random(5)
        for _ in range(20):
            count = jewel_count_for_beacon(Vec2(40, 60), rng)
            self.assertGreaterEqual(count, BEACON_JEWEL_MIN)
            self.assertLessEqual(count, BEACON_JEWEL_MAX)

    def test_large_asteroid_always_drops(self) -> None:
        import random

        asteroid = Asteroid(
            pos=Vec2(10, 10),
            vel=Vec2(),
            angle=0.0,
            spin=0.0,
            local_verts=(Vec2(1, 0), Vec2(0, 1), Vec2(-1, 0)),
            tier=AsteroidTier.LARGE,
        )
        rng = random.Random(1)
        for _ in range(10):
            count = jewel_count_for_asteroid(asteroid, rng)
            self.assertGreaterEqual(count, 2)
            self.assertLessEqual(count, 5)


class JewelPickupTests(unittest.TestCase):
    def test_magnet_collects_near_ship(self) -> None:
        ship_pos = Vec2(100, 100)
        jewels = spawn_scattered_jewels(Vec2(180, 100), 1)
        collected = 0
        for _ in range(30):
            jewels, collected = tick_jewels(jewels, ship_pos, 12.0, 0.05)
            if collected:
                break
        self.assertEqual(collected, 1)
        self.assertEqual(len(jewels), 0)

    def test_spawn_scattered_creates_requested_count(self) -> None:
        jewels = spawn_scattered_jewels(Vec2(0, 0), 5)
        self.assertEqual(len(jewels), 5)


class EnemyTests(unittest.TestCase):
    def test_patrol_steers_toward_waypoints(self) -> None:
        enemy = PatrolEnemy(waypoints=(Vec2(0, 0), Vec2(200, 0)), thrust=300.0, max_speed=140.0)
        for _ in range(30):
            enemy.integrate(0.05, [], gravity_scale=0.5, drag=0.988)
        self.assertGreater(enemy.pos.x, 0)

    def test_projectile_kills_enemy_and_drops_jewels(self) -> None:
        import random

        enemy = PatrolEnemy(waypoints=(Vec2(50, 50), Vec2(60, 50)))
        world = GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=Vec2(10, 10)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
            enemies=[enemy],
        )
        from gravity_ho_matey.gameplay.entities import Projectile

        expected = jewel_count_for_enemy(enemy, random.Random(int(50 * 17 + 50 * 31) & 0xFFFFFFFF))
        world.projectiles.append(Projectile(pos=Vec2(50, 50), vel=Vec2(0, 0)))
        world._update_projectiles(0.016)
        self.assertFalse(enemy.alive)
        self.assertEqual(len(world.enemies), 0)
        if expected > 0:
            self.assertEqual(len(world.jewels), expected)


class ProgressTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_progress()
        self._dev_patch = mock.patch("gravity_ho_matey.gameplay.progress.DEV_UNLOCK_ALL_LEVELS", False)
        self._dev_patch.start()

    def test_solar_locked_until_cove_cleared(self) -> None:
        self.assertFalse(is_level_selectable("solar"))
        record_level_cleared("cove")
        self.assertTrue(is_level_selectable("solar"))

    def test_drift_locked_until_solar_cleared(self) -> None:
        self.assertFalse(is_level_selectable("drift"))
        record_level_cleared("solar")
        self.assertTrue(is_level_selectable("drift"))

    def test_rift_locked_until_drift_cleared(self) -> None:
        self.assertFalse(is_level_selectable("rift"))
        record_level_cleared("drift")
        self.assertTrue(is_level_selectable("rift"))

    def tearDown(self) -> None:
        self._dev_patch.stop()
        reset_progress()


class LossCopyTests(unittest.TestCase):
    def test_solar_theme_uses_space_flavor_loss_copy(self) -> None:
        world = GameWorld(
            config=WorldConfig(width=200, height=200, level_theme="solar", open_bounds=False),
            ship=Ship(pos=Vec2(-5, 20)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
        )
        world._check_loss()
        self.assertEqual(world.status, GameStatus.SHIP_HIT)
        self.assertEqual(world.last_damage.source, DamageSource.OUT_OF_BOUNDS)
        self.assertEqual(world.last_damage.reason, "Drifted beyond the star chart.")


class RubberBouncePhysicsTests(unittest.TestCase):
    def test_bounce_separates_ship_from_asteroid(self) -> None:
        ship = Ship(pos=Vec2(100, 100), vel=Vec2(-40, 0))
        asteroid = _asteroid_at(Vec2(100, 100))
        resolve_rubber_hull_bounce(ship, asteroid)
        self.assertGreater((ship.pos - asteroid.pos).length(), ship.radius + asteroid.approximate_radius() - 1.0)


class ShopHitTests(unittest.TestCase):
    def test_shop_hit_id_round_trip(self) -> None:
        self.assertEqual(_kind_from_shop_hit("shop_thrust_boost"), PowerUpKind.THRUST_BOOST)
        self.assertEqual(_kind_from_shop_hit("shop_boost_tap"), PowerUpKind.BOOST_TAP)
        self.assertEqual(_kind_from_shop_hit("shop_rubber_hull"), PowerUpKind.RUBBER_HULL)
        self.assertEqual(_kind_from_shop_hit("shop_drone_wingman"), PowerUpKind.DRONE_WINGMAN)
        self.assertIsNone(_kind_from_shop_hit("launch"))


if __name__ == "__main__":
    unittest.main()
