import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState, MAX_LIVES
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.entities import FinishGate, PowerUpPickup, Ship, WorldConfig
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.progress import is_level_selectable, record_level_cleared, reset_progress
from gravity_ho_matey.gameplay.session import wire_world_for_campaign
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld


class CampaignTests(unittest.TestCase):
    def test_new_campaign_has_three_lives(self) -> None:
        campaign = CampaignState.new()
        self.assertEqual(campaign.lives, MAX_LIVES)
        self.assertEqual(len(campaign.powerups), 0)

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
        campaign.powerups.add(PowerUpKind.RAPID_FIRE)
        world = GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=Vec2(20, 20)),
            walls=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
        )
        wire_world_for_campaign(world, campaign)
        self.assertLess(world.ship.fire_cooldown_multiplier, 1.0)

    def test_pickup_collection_requires_campaign_wiring(self) -> None:
        campaign = CampaignState.new()
        world = GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=Vec2(20, 20)),
            walls=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
            pickups=[PowerUpPickup(pos=Vec2(20, 20), kind=PowerUpKind.THRUST_BOOST)],
        )
        world.update(0.016, ControlIntent())
        self.assertEqual(len(world.pickups), 1)

        wire_world_for_campaign(world, campaign)
        world.update(0.016, ControlIntent())
        self.assertEqual(len(world.pickups), 0)
        self.assertIn(PowerUpKind.THRUST_BOOST, campaign.powerups)


class EnemyTests(unittest.TestCase):
    def test_patrol_advances_along_waypoints(self) -> None:
        enemy = PatrolEnemy(waypoints=(Vec2(0, 0), Vec2(100, 0)), speed=200.0)
        enemy.advance(0.25)
        self.assertGreater(enemy.pos.x, 0)

    def test_projectile_kills_enemy_and_drops_pickup(self) -> None:
        enemy = PatrolEnemy(
            waypoints=(Vec2(50, 50), Vec2(60, 50)),
            drop_kind=PowerUpKind.THRUST_BOOST,
        )
        world = GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=Vec2(10, 10)),
            walls=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
            enemies=[enemy],
        )
        from gravity_ho_matey.gameplay.entities import Projectile

        world.projectiles.append(Projectile(pos=Vec2(50, 50), vel=Vec2(0, 0)))
        world._update_projectiles(0.016)
        self.assertFalse(enemy.alive)
        self.assertEqual(len(world.enemies), 0)
        self.assertEqual(len(world.pickups), 1)
        self.assertEqual(world.pickups[0].kind, PowerUpKind.THRUST_BOOST)


class ProgressTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_progress()

    def test_solar_locked_until_cove_cleared(self) -> None:
        self.assertFalse(is_level_selectable("solar"))
        record_level_cleared("cove")
        self.assertTrue(is_level_selectable("solar"))

    def tearDown(self) -> None:
        reset_progress()


class LossCopyTests(unittest.TestCase):
    def test_solar_theme_uses_space_flavor_loss_copy(self) -> None:
        world = GameWorld(
            config=WorldConfig(width=200, height=200, level_theme="solar"),
            ship=Ship(pos=Vec2(-5, 20)),
            walls=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
        )
        world._check_loss()
        self.assertEqual(world.loss_reason, "Drifted beyond the star chart.")


if __name__ == "__main__":
    unittest.main()
