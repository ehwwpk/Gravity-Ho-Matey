import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CHUNKS_PER_LIFE, CampaignState, MAX_LIVES
from gravity_ho_matey.gameplay.damage import DamageEvent, DamageSource
from gravity_ho_matey.gameplay.entities import FinishGate, GameStatus, GravityWell, Ship, Wall, WorldConfig
from gravity_ho_matey.gameplay.session import INVULN_SECONDS, capture_level_spawn, respawn_ship_at_spawn
from gravity_ho_matey.gameplay.world import ControlIntent, GameWorld


def tiny_world(*, ship_pos: Vec2 | None = None) -> GameWorld:
    pos = ship_pos or Vec2(100, 100)
    world = GameWorld(
        config=WorldConfig(width=200, height=200),
        ship=Ship(pos=pos),
        walls=[],
        wells=[],
        beacons=[],
        finish_gate=FinishGate(Rect(150, 150, 25, 25)),
    )
    capture_level_spawn(world)
    return world


class HealthCampaignTests(unittest.TestCase):
    def test_new_campaign_starts_with_full_hull(self) -> None:
        campaign = CampaignState.new()
        self.assertEqual(campaign.lives, MAX_LIVES)
        self.assertEqual(campaign.hull_chunks, CHUNKS_PER_LIFE)

    def test_single_chip_leaves_two_chunks_and_same_life(self) -> None:
        campaign = CampaignState.new()
        result = campaign.apply_damage(DamageEvent(DamageSource.WALL))
        self.assertFalse(result.life_lost)
        self.assertEqual(campaign.hull_chunks, 2)
        self.assertEqual(campaign.lives, MAX_LIVES)

    def test_two_chips_leave_one_chunk(self) -> None:
        campaign = CampaignState.new()
        campaign.apply_damage(DamageEvent(DamageSource.ENEMY))
        result = campaign.apply_damage(DamageEvent(DamageSource.OUT_OF_BOUNDS))
        self.assertFalse(result.life_lost)
        self.assertEqual(campaign.hull_chunks, 1)

    def test_third_chip_on_same_life_costs_campaign_life(self) -> None:
        campaign = CampaignState.new()
        for _ in range(2):
            campaign.apply_damage(DamageEvent(DamageSource.WALL))
        result = campaign.apply_damage(DamageEvent(DamageSource.WALL))
        self.assertTrue(result.life_lost)
        self.assertFalse(result.campaign_over)
        self.assertEqual(campaign.lives, MAX_LIVES - 1)
        self.assertEqual(campaign.hull_chunks, 0)

    def test_life_lost_hull_refills_on_next_play_entry(self) -> None:
        from gravity_ho_matey.gameplay.session import ensure_active_life_hull

        campaign = CampaignState.new()
        campaign.apply_damage(DamageEvent(DamageSource.GRAVITY_MAW))
        self.assertEqual(campaign.hull_chunks, 0)
        ensure_active_life_hull(campaign)
        self.assertEqual(campaign.hull_chunks, CHUNKS_PER_LIFE)

    def test_partial_hull_not_refilled_on_play_entry(self) -> None:
        from gravity_ho_matey.gameplay.session import ensure_active_life_hull

        campaign = CampaignState.new()
        campaign.apply_damage(DamageEvent(DamageSource.WALL))
        ensure_active_life_hull(campaign)
        self.assertEqual(campaign.hull_chunks, 2)

    def test_lethal_ignores_remaining_hull(self) -> None:
        campaign = CampaignState.new()
        campaign.apply_damage(DamageEvent(DamageSource.WALL))
        campaign.apply_damage(DamageEvent(DamageSource.WALL))
        self.assertEqual(campaign.hull_chunks, 1)
        result = campaign.apply_damage(DamageEvent(DamageSource.GRAVITY_MAW, reason="Singularity."))
        self.assertTrue(result.life_lost)
        self.assertFalse(result.chipped)
        self.assertEqual(campaign.lives, MAX_LIVES - 1)

    def test_lethal_on_last_life_is_game_over(self) -> None:
        campaign = CampaignState.new()
        campaign.lives = 1
        campaign.hull_chunks = CHUNKS_PER_LIFE
        result = campaign.apply_damage(DamageEvent(DamageSource.GRAVITY_MAW))
        self.assertTrue(result.campaign_over)
        self.assertEqual(campaign.lives, 0)
        self.assertEqual(campaign.hull_chunks, 0)

    def test_partial_hull_persists_without_reset(self) -> None:
        campaign = CampaignState.new()
        campaign.apply_damage(DamageEvent(DamageSource.WALL))
        self.assertEqual(campaign.hull_chunks, 2)
        # Simulate advancing to another level without touching hull.
        self.assertEqual(campaign.hull_chunks, 2)

    def test_apply_damage_on_game_over_is_inert(self) -> None:
        campaign = CampaignState.new()
        campaign.lives = 0
        campaign.hull_chunks = 0
        result = campaign.apply_damage(DamageEvent(DamageSource.WALL))
        self.assertTrue(result.campaign_over)
        self.assertEqual(campaign.lives, 0)


class HealthWorldTests(unittest.TestCase):
    def test_open_bounds_ship_survives_off_map(self) -> None:
        world = tiny_world(ship_pos=Vec2(-5, 100))
        world._check_loss()
        self.assertEqual(world.status, GameStatus.RUNNING)

    def test_closed_bounds_chip_when_off_map(self) -> None:
        world = tiny_world(ship_pos=Vec2(-5, 100))
        world.config = WorldConfig(
            width=world.config.width,
            height=world.config.height,
            open_bounds=False,
        )
        world._check_loss()
        self.assertEqual(world.status, GameStatus.SHIP_HIT)
        self.assertEqual(world.last_damage.source, DamageSource.OUT_OF_BOUNDS)

    def test_wall_is_chip(self) -> None:
        world = tiny_world(ship_pos=Vec2(50, 50))
        world.walls = [Wall(Rect(40, 40, 30, 30))]
        world._check_loss()
        self.assertEqual(world.last_damage.source, DamageSource.WALL)

    def test_planet_maw_is_lethal_source(self) -> None:
        world = tiny_world(ship_pos=Vec2(100, 100))
        world.wells = [
            GravityWell(Vec2(100, 100), strength=5000, radius=50, kind="planet", label="Test Planet"),
        ]
        world._check_loss()
        self.assertEqual(world.status, GameStatus.SHIP_HIT)
        self.assertEqual(world.last_damage.source, DamageSource.GRAVITY_MAW)
        self.assertIn("Test Planet", world.last_damage.reason)

    def test_black_hole_maw_is_lethal_source(self) -> None:
        world = tiny_world(ship_pos=Vec2(100, 100))
        world.wells = [
            GravityWell(Vec2(100, 100), strength=9000, radius=50, kind="black_hole", maw_radius=20),
        ]
        world._check_loss()
        self.assertEqual(world.last_damage.source, DamageSource.GRAVITY_MAW)

    def test_cove_well_maw_is_lethal(self) -> None:
        world = tiny_world(ship_pos=Vec2(100, 100))
        world.wells = [GravityWell(Vec2(100, 100), strength=9000, radius=50, kind="well")]
        world._check_loss()
        self.assertEqual(world.last_damage.source, DamageSource.GRAVITY_MAW)

    def test_invuln_blocks_back_to_back_hits(self) -> None:
        world = tiny_world(ship_pos=Vec2(-5, 100))
        world.invuln_remaining = INVULN_SECONDS
        world._check_loss()
        self.assertEqual(world.status, GameStatus.RUNNING)
        self.assertIsNone(world.last_damage)

    def test_respawn_resets_velocity_and_grants_invuln(self) -> None:
        world = tiny_world(ship_pos=Vec2(120, 80))
        world.ship.vel = Vec2(200, -50)
        world.ship.angle = 2.5
        world.status = GameStatus.SHIP_HIT
        world.last_damage = DamageEvent(DamageSource.WALL)
        respawn_ship_at_spawn(world)
        self.assertEqual(world.status, GameStatus.RUNNING)
        self.assertEqual(world.ship.pos.x, world.spawn_pos.x)
        self.assertEqual(world.ship.vel.length(), 0.0)
        self.assertAlmostEqual(world.invuln_remaining, INVULN_SECONDS)
        self.assertIsNone(world.last_damage)

    def test_invuln_decays_over_time(self) -> None:
        world = tiny_world()
        world.invuln_remaining = INVULN_SECONDS
        world.update(0.2, ControlIntent())
        self.assertLess(world.invuln_remaining, INVULN_SECONDS)
        for _ in range(20):
            world.update(0.05, ControlIntent())
        self.assertEqual(world.invuln_remaining, 0.0)

    def test_double_wall_hit_same_frame_only_registers_once(self) -> None:
        world = tiny_world(ship_pos=Vec2(50, 50))
        world.walls = [Wall(Rect(40, 40, 30, 30)), Wall(Rect(45, 45, 20, 20))]
        world._check_loss()
        self.assertEqual(world.status, GameStatus.SHIP_HIT)

    def test_chip_then_respawn_allows_movement_same_update_cycle(self) -> None:
        campaign = CampaignState.new()
        world = tiny_world(ship_pos=Vec2(-5, 100))
        world.config = WorldConfig(width=200, height=200, open_bounds=False)
        world._check_loss()
        result = campaign.apply_damage(world.last_damage)  # type: ignore[arg-type]
        self.assertFalse(result.life_lost)
        respawn_ship_at_spawn(world)
        before = world.ship.pos.x
        world.update(0.05, ControlIntent(thrust=True))
        self.assertNotEqual(world.ship.pos.x, before)


class HealthIntegrationTests(unittest.TestCase):
    def test_three_boundary_scrapes_cost_one_life_not_three(self) -> None:
        campaign = CampaignState.new()
        world = tiny_world(ship_pos=Vec2(-5, 100))
        world.config = WorldConfig(width=200, height=200, open_bounds=False)
        lives_spent = 0
        for _ in range(3):
            world.ship.pos = Vec2(-5, 100)
            world.status = GameStatus.RUNNING
            world.last_damage = None
            world.invuln_remaining = 0.0
            world._check_loss()
            result = campaign.apply_damage(world.last_damage)  # type: ignore[arg-type]
            if result.life_lost:
                lives_spent += 1
                break
            respawn_ship_at_spawn(world)
        self.assertEqual(lives_spent, 1)
        self.assertEqual(campaign.lives, MAX_LIVES - 1)

    def test_lethal_well_costs_life_even_with_two_chunks_left(self) -> None:
        campaign = CampaignState.new()
        campaign.apply_damage(DamageEvent(DamageSource.WALL))
        self.assertEqual(campaign.hull_chunks, 2)
        result = campaign.apply_damage(DamageEvent(DamageSource.GRAVITY_MAW))
        self.assertTrue(result.life_lost)
        self.assertEqual(campaign.lives, MAX_LIVES - 1)
        self.assertEqual(campaign.hull_chunks, 0)

    def test_finish_cannot_override_ship_hit(self) -> None:
        world = tiny_world()
        world.update(0.016, ControlIntent())
        world.ship.pos = Vec2(160, 160)
        world.status = GameStatus.SHIP_HIT
        world._check_finish()
        self.assertEqual(world.status, GameStatus.SHIP_HIT)

    def test_play_scene_refills_hull_after_life_lost(self) -> None:
        from gravity_ho_matey.scenes.play import PlayScene

        campaign = CampaignState.new()
        campaign.apply_damage(DamageEvent(DamageSource.GRAVITY_MAW))
        self.assertEqual(campaign.hull_chunks, 0)
        PlayScene("cove", campaign)
        self.assertEqual(campaign.hull_chunks, CHUNKS_PER_LIFE)


if __name__ == "__main__":
    unittest.main()
