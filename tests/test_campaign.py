import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState, CHUNKS_PER_LIFE, MAX_LIVES
from gravity_ho_matey.gameplay.damage import DamageSource
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.entities import FinishGate, GameStatus, GravityWell, PowerUpPickup, Ship, WorldConfig
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.progress import is_level_selectable, record_level_cleared, reset_progress
from gravity_ho_matey.gameplay.session import wire_world_for_campaign
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld


class CampaignTests(unittest.TestCase):
    def test_new_campaign_has_three_lives(self) -> None:
        campaign = CampaignState.new()
        self.assertEqual(campaign.lives, MAX_LIVES)
        self.assertEqual(campaign.hull_chunks, CHUNKS_PER_LIFE)
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

    def test_pickup_hud_callback_reports_new_vs_duplicate(self) -> None:
        campaign = CampaignState.new()
        events: list[tuple[PowerUpKind, bool]] = []
        world = GameWorld(
            config=WorldConfig(width=200, height=200),
            ship=Ship(pos=Vec2(20, 20)),
            walls=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(150, 150, 25, 25)),
            pickups=[PowerUpPickup(pos=Vec2(20, 20), kind=PowerUpKind.RAPID_FIRE)],
        )
        wire_world_for_campaign(
            world,
            campaign,
            on_powerup_collected_hud=lambda kind, is_new: events.append((kind, is_new)),
        )
        world.update(0.016, ControlIntent())
        self.assertEqual(events, [(PowerUpKind.RAPID_FIRE, True)])

        world.pickups = [PowerUpPickup(pos=Vec2(20, 20), kind=PowerUpKind.RAPID_FIRE)]
        world.update(0.016, ControlIntent())
        self.assertEqual(events, [(PowerUpKind.RAPID_FIRE, True), (PowerUpKind.RAPID_FIRE, False)])


class EnemyTests(unittest.TestCase):
    def test_patrol_steers_toward_waypoints(self) -> None:
        enemy = PatrolEnemy(waypoints=(Vec2(0, 0), Vec2(200, 0)), thrust=300.0, max_speed=140.0)
        for _ in range(30):
            enemy.integrate(0.05, [], gravity_scale=0.5, drag=0.988)
        self.assertGreater(enemy.pos.x, 0)

    def test_patrol_feels_gravity_from_wells(self) -> None:
        enemy = PatrolEnemy(waypoints=(Vec2(200, 200), Vec2(200, 200)), thrust=0.0, max_speed=200.0)
        enemy.pos = Vec2(200, 200)
        enemy.vel = Vec2(0, -80)
        well = GravityWell(Vec2(200, 320), strength=40000, radius=180)
        enemy.integrate(0.05, [well], gravity_scale=0.5, drag=1.0)
        self.assertGreater(enemy.vel.y, -80)

    def test_patrol_resists_black_hole_pull_more_than_passive_drift(self) -> None:
        well = GravityWell(Vec2(480, 320), strength=52000, radius=155, kind="black_hole", maw_radius=22)
        passive = PatrolEnemy(waypoints=(Vec2(480, 260), Vec2(480, 260)), thrust=0.0, max_speed=200.0)
        passive.pos = Vec2(480, 260)
        passive.vel = Vec2(0, 40)

        evasive = PatrolEnemy(waypoints=(Vec2(480, 260), Vec2(480, 260)), thrust=235.0, max_speed=105.0)
        evasive.pos = Vec2(480, 260)
        evasive.vel = Vec2(0, 40)

        for _ in range(25):
            passive.integrate(0.05, [well], gravity_scale=0.45, drag=0.988, well_maw_radius=10.0)
            evasive.integrate(0.05, [well], gravity_scale=0.45, drag=0.988, well_maw_radius=10.0)

        self.assertLess(evasive.pos.y, passive.pos.y)

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
        self.assertEqual(world.status, GameStatus.SHIP_HIT)
        self.assertEqual(world.last_damage.source, DamageSource.OUT_OF_BOUNDS)
        self.assertEqual(world.last_damage.reason, "Drifted beyond the star chart.")


if __name__ == "__main__":
    unittest.main()
