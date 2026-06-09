from __future__ import annotations

import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.gameplay.expedition_mission import ExpeditionPhase, is_expedition_foot
from gravity_ho_matey.gameplay.expedition_controller import apply_expedition_foot_layout, tick_expedition
from gravity_ho_matey.gameplay.hud_objectives import objective_counters_for_world
from gravity_ho_matey.gameplay.squid_behavior import SquidBehaviorMode
from gravity_ho_matey.gameplay.world import ControlIntent
from gravity_ho_matey.levels.comet_fuel_layout import FUEL_NODES_REQUIRED
from gravity_ho_matey.levels.level_registry import build_level, next_level_id


class CometFuelLevelTests(unittest.TestCase):
    def test_registry_chain(self) -> None:
        self.assertEqual(next_level_id("brood_moon"), "comet_fuel")
        self.assertIsNone(next_level_id("comet_fuel"))

    def test_world_content(self) -> None:
        world = build_level("comet_fuel")
        self.assertEqual(world.config.level_theme, "comet")
        self.assertTrue(world.config.expedition_mission)
        self.assertIsNotNone(world.expedition)
        assert world.expedition is not None
        self.assertEqual(world.expedition.phase, ExpeditionPhase.ORBITAL)

    def test_dev_foot_spawn(self) -> None:
        from gravity_ho_matey.levels.level_data import build_comet_fuel_level

        world = build_comet_fuel_level(dev_foot=True)
        self.assertTrue(is_expedition_foot(world.config))
        self.assertIsNotNone(world.avatar)

    def test_foot_layout_parks_ship_at_lander(self) -> None:
        from gravity_ho_matey.levels.comet_fuel_layout import LANDER_PAD

        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        self.assertFalse(world.config.open_bounds)
        self.assertAlmostEqual(world.ship.pos.x, LANDER_PAD.x)
        self.assertAlmostEqual(world.ship.pos.y, LANDER_PAD.y - 18.0)

    def test_foot_layout_swap(self) -> None:
        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        self.assertTrue(is_expedition_foot(world.config))
        self.assertIsNotNone(world.avatar)
        self.assertEqual(len(world.enemies), 16)
        exp = world.expedition
        assert exp is not None
        self.assertEqual(len(exp.feed_lines), 6)
        self.assertEqual(exp.hostiles_remaining, 16)

    def test_foot_hud_objectives(self) -> None:
        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        counters = objective_counters_for_world(world)
        labels = [c.label for c in counters]
        self.assertIn("HOSTILES", labels)
        self.assertIn("FUEL LOAD", labels)

    def test_feeding_squid_no_dash(self) -> None:
        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        exp = world.expedition
        assert exp is not None
        start = Vec2(world.enemies[0].pos.x, world.enemies[0].pos.y)
        for _ in range(120):
            tick_expedition(world, 0.016, ControlIntent(), interaction_hold=False)
        moved = (world.enemies[0].pos - start).length()
        if exp.squid_entries[0].mode == SquidBehaviorMode.FEEDING.name:
            self.assertLess(moved, 40.0)

    def test_proximity_alert_escalates_feeding_squid(self) -> None:
        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        exp = world.expedition
        assert exp is not None
        avatar = world.avatar
        assert avatar is not None
        feeding_idx = next(
            i for i, entry in enumerate(exp.squid_entries) if entry.mode == SquidBehaviorMode.FEEDING.name
        )
        squid = world.enemies[feeding_idx]
        avatar.pos = Vec2(squid.pos.x + 20.0, squid.pos.y)
        for _ in range(40):
            tick_expedition(world, 0.016, ControlIntent(), interaction_hold=False)
        self.assertIn(
            exp.squid_entries[feeding_idx].mode,
            (SquidBehaviorMode.ALERT.name, SquidBehaviorMode.ENGAGE.name),
        )

    def test_fuel_load_requires_hold_e(self) -> None:
        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        exp = world.expedition
        assert exp is not None
        avatar = world.avatar
        assert avatar is not None
        for enemy in world.enemies:
            enemy.alive = False
        exp.hostiles_remaining = 0
        valve = next(n for n in exp.interact_nodes if n.kind.name == "FUEL_VALVE")
        for _ in range(40):
            avatar.pos = Vec2(valve.pos.x, valve.pos.y)
            avatar.vel = Vec2()
            tick_expedition(world, 0.016, ControlIntent(), interaction_hold=False)
        self.assertEqual(exp.fuel_nodes_loaded, 0)
        for _ in range(80):
            avatar.pos = Vec2(valve.pos.x, valve.pos.y)
            avatar.vel = Vec2()
            tick_expedition(world, 0.016, ControlIntent(), interaction_hold=True)
        self.assertGreaterEqual(exp.fuel_nodes_loaded, 1)

    def test_extract_blocked_until_fuel_loaded(self) -> None:
        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        exp = world.expedition
        assert exp is not None
        avatar = world.avatar
        assert avatar is not None
        pad = next(n for n in exp.interact_nodes if n.kind.name == "EXTRACT_PAD")
        for _ in range(80):
            avatar.pos = Vec2(pad.pos.x, pad.pos.y)
            avatar.vel = Vec2()
            tick_expedition(world, 0.016, ControlIntent(), interaction_hold=True)
        self.assertFalse(exp.extract_pending)
        exp.fuel_nodes_loaded = FUEL_NODES_REQUIRED
        for _ in range(80):
            avatar.pos = Vec2(pad.pos.x, pad.pos.y)
            avatar.vel = Vec2()
            tick_expedition(world, 0.016, ControlIntent(), interaction_hold=True)
        self.assertTrue(exp.fuel_aboard or exp.phase is ExpeditionPhase.UNDOCK_CINEMATIC)

    def test_foot_objectives_met_is_fuel_only(self) -> None:
        from gravity_ho_matey.gameplay.expedition_mission import expedition_foot_objectives_met

        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        exp = world.expedition
        assert exp is not None
        exp.fuel_nodes_loaded = FUEL_NODES_REQUIRED
        exp.hostiles_remaining = 12
        self.assertTrue(expedition_foot_objectives_met(exp))


    def test_foot_movement_with_wasd(self) -> None:
        import math

        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        avatar = world.avatar
        assert avatar is not None
        avatar.face_angle = -math.pi / 2
        avatar.vel = Vec2()
        start = Vec2(avatar.pos.x, avatar.pos.y)
        intent = ControlIntent(thrust=True)
        for _ in range(40):
            tick_expedition(world, 0.016, intent, interaction_hold=False)
        self.assertLess(avatar.pos.y - start.y, -12.0)

    def test_foot_tank_rotation(self) -> None:
        import math

        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        avatar = world.avatar
        assert avatar is not None
        start_angle = avatar.face_angle
        for _ in range(80):
            tick_expedition(world, 0.016, ControlIntent(rotate_left=True), interaction_hold=False)
        delta = avatar.face_angle - start_angle
        self.assertGreater(abs(delta), 2.0)
        self.assertLess(abs(delta), math.tau * 2.0 + 0.5)

    def test_foot_backward_movement(self) -> None:
        import math

        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        avatar = world.avatar
        assert avatar is not None
        avatar.face_angle = -math.pi / 2
        avatar.vel = Vec2()
        start_y = avatar.pos.y
        for _ in range(45):
            tick_expedition(world, 0.016, ControlIntent(reverse=True), interaction_hold=False)
        self.assertGreater(avatar.pos.y - start_y, 12.0)

    def test_foot_full_turnaround(self) -> None:
        import math

        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        avatar = world.avatar
        assert avatar is not None
        avatar.face_angle = 0.0
        avatar.vel = Vec2()
        start = Vec2(avatar.pos.x, avatar.pos.y)
        frames = int(math.pi / (10.0 * 0.016)) + 2
        for _ in range(frames):
            tick_expedition(world, 0.016, ControlIntent(rotate_left=True), interaction_hold=False)
        self.assertAlmostEqual(math.cos(avatar.face_angle), math.cos(math.pi), delta=0.25)
        avatar.vel = Vec2()
        for _ in range(40):
            tick_expedition(world, 0.016, ControlIntent(thrust=True), interaction_hold=False)
        self.assertLess(avatar.pos.x - start.x, -8.0)

    def test_extract_pad_available_after_fuel_loaded(self) -> None:
        from gravity_ho_matey.gameplay.expedition_mission import nearest_interact_node

        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        exp = world.expedition
        assert exp is not None
        avatar = world.avatar
        assert avatar is not None
        exp.fuel_nodes_loaded = 3
        exp.hostiles_remaining = 4
        pad = next(n for n in exp.interact_nodes if n.kind.name == "EXTRACT_PAD")
        avatar.pos = Vec2(pad.pos.x, pad.pos.y)
        node = nearest_interact_node(exp, avatar.pos)
        self.assertIsNotNone(node)
        assert node is not None
        self.assertEqual(node.kind.name, "EXTRACT_PAD")

    def test_extract_with_fuel_despite_remaining_hostiles(self) -> None:
        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        exp = world.expedition
        assert exp is not None
        avatar = world.avatar
        assert avatar is not None
        exp.fuel_nodes_loaded = 3
        exp.hostiles_remaining = 8
        pad = next(n for n in exp.interact_nodes if n.kind.name == "EXTRACT_PAD")
        avatar.pos = Vec2(pad.pos.x, pad.pos.y)
        for _ in range(80):
            tick_expedition(world, 0.016, ControlIntent(), interaction_hold=True)
        self.assertTrue(exp.extract_pending or exp.phase is ExpeditionPhase.UNDOCK_CINEMATIC or exp.fuel_aboard)

    def test_rtb_prompt_resets_when_leaving_pad(self) -> None:
        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        exp = world.expedition
        assert exp is not None
        avatar = world.avatar
        assert avatar is not None
        exp.fuel_nodes_loaded = 3
        tick_expedition(world, 0.1, ControlIntent(), interaction_hold=False)
        self.assertIn("FUEL SECURED", exp.hud_prompt)
        pad = next(n for n in exp.interact_nodes if n.kind.name == "EXTRACT_PAD")
        avatar.pos = Vec2(200.0, 200.0)
        tick_expedition(world, 0.1, ControlIntent(), interaction_hold=False)
        self.assertIn("FUEL SECURED", exp.hud_prompt)

    def test_eva_squid_cling_deals_damage(self) -> None:
        from gravity_ho_matey.gameplay.squid_enemy import SQUID_CLING_DAMAGE_INTERVAL

        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        exp = world.expedition
        assert exp is not None
        avatar = world.avatar
        assert avatar is not None
        engage_idx = next(
            i for i, entry in enumerate(exp.squid_entries) if entry.mode == SquidBehaviorMode.ENGAGE.name
        )
        squid = world.enemies[engage_idx]
        avatar.pos = Vec2(squid.pos.x + 8.0, squid.pos.y + 4.0)
        avatar.vel = Vec2()
        frames = int(SQUID_CLING_DAMAGE_INTERVAL / 0.016) + 30
        for _ in range(frames):
            tick_expedition(world, 0.016, ControlIntent(), interaction_hold=False)
        self.assertEqual(world.status, GameStatus.SHIP_HIT)

    def test_rtb_at_lander_blocked_without_fuel(self) -> None:
        from gravity_ho_matey.levels.comet_fuel_layout import LANDER_PAD

        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        exp = world.expedition
        assert exp is not None
        avatar = world.avatar
        assert avatar is not None
        pad = next(n for n in exp.interact_nodes if n.kind.name == "EXTRACT_PAD")
        avatar.pos = Vec2(pad.pos.x, pad.pos.y)
        tick_expedition(world, 0.1, ControlIntent(), interaction_hold=True)
        self.assertIn("DEPOT", exp.hud_prompt.upper())
        self.assertFalse(exp.extract_pending)

    def test_rotation_left_decreases_angle(self) -> None:
        import math

        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        avatar = world.avatar
        assert avatar is not None
        avatar.face_angle = 0.0
        tick_expedition(world, 0.1, ControlIntent(rotate_left=True), interaction_hold=False)
        self.assertLess(avatar.face_angle, 0.0)
        avatar.face_angle = 0.0
        tick_expedition(world, 0.1, ControlIntent(rotate_right=True), interaction_hold=False)
        self.assertGreater(avatar.face_angle, 0.0)

    def test_transition_asset_no_cove_fallback(self) -> None:
        from gravity_ho_matey.gameplay.expedition_mission import resolve_transition_asset

        self.assertIsNone(resolve_transition_asset("comet_fuel_dock"))
        self.assertIsNone(resolve_transition_asset("comet_fuel_undock"))

    def test_eva_chip_recovers_at_lander(self) -> None:
        from gravity_ho_matey.gameplay.session import recover_eva_in_place
        from gravity_ho_matey.levels.comet_fuel_layout import LANDER_PAD

        world = build_level("comet_fuel")
        apply_expedition_foot_layout(world)
        avatar = world.avatar
        assert avatar is not None
        avatar.pos = Vec2(500.0, 500.0)
        world.status = GameStatus.SHIP_HIT
        recover_eva_in_place(world)
        self.assertEqual(world.status, GameStatus.RUNNING)
        self.assertAlmostEqual(avatar.pos.x, LANDER_PAD.x)
        self.assertGreater(avatar.invuln_remaining, 0.0)


if __name__ == "__main__":
    unittest.main()
