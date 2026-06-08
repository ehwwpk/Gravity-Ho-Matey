from __future__ import annotations

import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.entities import Ship
from gravity_ho_matey.gameplay.jewel_pickup import JewelPickup, tick_jewels
from gravity_ho_matey.gameplay.nifflerp import Nifflerp
from gravity_ho_matey.gameplay.nifflerp_config import NIFFLERP_HITS_MAX, NIFFLERP_SEEK_RADIUS
from gravity_ho_matey.gameplay.nifflerp_session import deploy_nifflerp, sync_nifflerp_to_campaign
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.levels.level_registry import build_level


class NifflerpTests(unittest.TestCase):
    def test_shop_purchase_sets_pending(self) -> None:
        campaign = CampaignState.new()
        campaign.jewels = 50
        self.assertTrue(campaign.try_purchase(PowerUpKind.NIFFLERP))
        self.assertTrue(campaign.nifflerp_pending)
        self.assertFalse(campaign.can_purchase(PowerUpKind.NIFFLERP))

    def test_deploy_spawns_with_three_hp(self) -> None:
        campaign = CampaignState.new()
        campaign.nifflerp_pending = True
        world = build_level("cove")
        deploy_nifflerp(world, campaign)
        self.assertIsNotNone(world.nifflerp)
        assert world.nifflerp is not None
        self.assertEqual(world.nifflerp.hits_remaining, NIFFLERP_HITS_MAX)
        self.assertFalse(campaign.nifflerp_pending)

    def test_jewel_seek_respects_player_radius(self) -> None:
        buddy = Nifflerp.spawn_beside_player(Ship(pos=Vec2(100.0, 100.0)))
        player = Vec2(400.0, 400.0)
        near = JewelPickup(pos=Vec2(450.0, 420.0))
        far = JewelPickup(pos=Vec2(400.0 + NIFFLERP_SEEK_RADIUS + 80.0, 400.0))
        target = buddy.nearest_jewel_target([near, far], player)
        self.assertIsNotNone(target)
        assert target is not None
        self.assertAlmostEqual((target - near.pos).length(), 0.0, delta=1.0)

    def test_play_target_orbits_player(self) -> None:
        buddy = Nifflerp.spawn_beside_player(Ship(pos=Vec2(200.0, 200.0)))
        player = Vec2(500.0, 500.0)
        a = buddy.play_target(player, 0.0)
        buddy.play_phase = 1.7
        b = buddy.play_target(player, 0.5)
        self.assertGreater((a - player).length(), 20.0)
        self.assertGreater((b - player).length(), 20.0)
        self.assertGreater((a - b).length(), 5.0)

    def test_apply_shot_kills_after_three_hits(self) -> None:
        buddy = Nifflerp.spawn_beside_player(Ship(pos=Vec2(0.0, 0.0)))
        for _ in range(NIFFLERP_HITS_MAX - 1):
            buddy.hit_invuln = 0.0
            destroyed = buddy.apply_shot()
            self.assertFalse(destroyed)
            self.assertTrue(buddy.alive)
        buddy.hit_invuln = 0.0
        self.assertTrue(buddy.apply_shot())
        self.assertFalse(buddy.alive)

    def test_nifflerp_collects_jewels_for_treasury(self) -> None:
        world = build_level("cove")
        collected: list[int] = []

        def on_collect(amount: int) -> None:
            collected.append(amount)

        world.on_jewels_collected = on_collect
        world.nifflerp = Nifflerp.spawn_beside_player(world.ship)
        world.jewels = [JewelPickup(pos=Vec2(world.nifflerp.pos.x, world.nifflerp.pos.y))]
        world._update_jewels(0.05)
        self.assertEqual(collected, [1])
        self.assertEqual(len(world.jewels), 0)

    def test_tick_jewels_helper_collector(self) -> None:
        ship_pos = Vec2(0.0, 0.0)
        helper = Vec2(30.0, 0.0)
        jewels = [JewelPickup(pos=Vec2(31.0, 0.0))]
        remaining, count = tick_jewels(
            jewels,
            ship_pos,
            12.0,
            0.05,
            helper_pos=helper,
            helper_radius=6.5,
        )
        self.assertEqual(count, 1)
        self.assertEqual(len(remaining), 0)

    def test_sync_clears_dead_buddy(self) -> None:
        campaign = CampaignState.new()
        world = build_level("cove")
        world.nifflerp = Nifflerp.spawn_beside_player(world.ship, hits_remaining=1)
        world.nifflerp.alive = False
        sync_nifflerp_to_campaign(world, campaign)
        self.assertIsNone(world.nifflerp)
        self.assertEqual(campaign.nifflerp_hp, 0)


if __name__ == "__main__":
    unittest.main()
