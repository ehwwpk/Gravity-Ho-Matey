import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.boost_pad import BoostPad
from gravity_ho_matey.gameplay.boost_lane import LaneState, probe_lane
from gravity_ho_matey.gameplay.boost_pad import try_trigger_pad
from gravity_ho_matey.gameplay.entities import Ship, WorldConfig
from gravity_ho_matey.gameplay.lane_physics import lane_modifiers
from gravity_ho_matey.gameplay.mega_squid_boss import MEGA_SQUID_HITS, MegaSquidBoss
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.level_registry import build_level, next_level_id
from gravity_ho_matey.levels.membrane_layout import (
    BOSS_STABLE_RADIUS,
    MEMBRANE_HEIGHT,
    MEMBRANE_WIDTH,
    RIBBON_HALF_WIDTH,
    build_membrane_layout,
    is_in_boss_stable_zone,
    validate_void_clearance,
)


class MembraneLevelTests(unittest.TestCase):
    def test_registry_chain_includes_rift(self) -> None:
        self.assertEqual(next_level_id("drift"), "rift")
        self.assertEqual(next_level_id("rift"), "siege")
        self.assertIsNone(next_level_id("siege"))

    def test_starter_zone_and_off_path_use_neutral_physics(self) -> None:
        layout = build_membrane_layout()
        on = probe_lane(layout.spawn_ship.pos, layout)
        on_mods = lane_modifiers(on, base_drag=0.989, base_max_speed=380.0)
        self.assertEqual(on_mods.center_accel, 0.0)
        self.assertGreater(on_mods.max_speed, 380.0)
        void = probe_lane(Vec2(10.0, 10.0), layout)
        void_mods = lane_modifiers(void, base_drag=0.989, base_max_speed=380.0)
        self.assertEqual(void_mods.thrust_mult, 1.0)
        self.assertEqual(void_mods.max_speed, 380.0)
        self.assertEqual(void_mods.gravity_scale, 1.0)

    def test_void_wells_clear_of_ribbons(self) -> None:
        layout = build_membrane_layout()
        errors = validate_void_clearance(layout)
        self.assertEqual(errors, [], msg="\n".join(errors))

    def test_lane_probe_on_and_off_ribbon(self) -> None:
        layout = build_membrane_layout()
        on = probe_lane(layout.spawn_ship.pos, layout)
        self.assertEqual(on.state, LaneState.ON_RIBBON)
        void = probe_lane(Vec2(10.0, 10.0), layout)
        self.assertEqual(void.state, LaneState.VOID)

    def test_rift_world_content(self) -> None:
        world = build_level("rift")
        self.assertEqual(world.config.level_theme, "rift")
        self.assertEqual(world.config.width, MEMBRANE_WIDTH)
        self.assertEqual(world.config.height, MEMBRANE_HEIGHT)
        self.assertTrue(world.config.exit_requires_boss)
        self.assertFalse(world.finish_unlocked)
        self.assertEqual(len(world.beacons), 0)
        self.assertGreaterEqual(len(world.wells), 10)
        self.assertGreaterEqual(len(world.boost_pads), 4)
        self.assertLessEqual(len(world.boost_pads), 8)
        self.assertEqual(len(world.enemies), 5)
        self.assertIsNotNone(world.mega_squid)
        self.assertIsNotNone(world.membrane_layout)
        self.assertEqual(len(world.allies), 2)

    def test_boss_death_unlocks_portal(self) -> None:
        world = build_level("rift")
        boss = world.mega_squid
        assert boss is not None
        boss.hits_remaining = 1
        from gravity_ho_matey.gameplay.entities import Projectile

        world._projectile_hits_boss(
            Projectile(pos=Vec2(boss.pos.x, boss.pos.y), vel=Vec2(), hostile=False)
        )
        self.assertTrue(world.boss_cleared)
        self.assertTrue(world.finish_unlocked)

    def test_mega_squid_has_eighteen_hp(self) -> None:
        boss = MegaSquidBoss(pos=Vec2(0, 0), anchor=Vec2(0, 0))
        self.assertEqual(boss.hits_max, MEGA_SQUID_HITS)
        self.assertEqual(boss.hits_remaining, 18)

    def test_boost_pad_triggers_on_ribbon(self) -> None:
        layout = build_membrane_layout()
        world = GameWorld(
            config=WorldConfig(width=layout.width, height=layout.height, exit_requires_boss=True),
            ship=Ship(pos=Vec2(layout.boost_pads[0].pos.x, layout.boost_pads[0].pos.y)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=layout.finish_gate,
            membrane_layout=layout,
            boost_pads=[
                BoostPad(
                    pos=Vec2(layout.boost_pads[0].pos.x, layout.boost_pads[0].pos.y),
                    tangent=Vec2(
                        layout.boost_pads[0].tangent.x,
                        layout.boost_pads[0].tangent.y,
                    ),
                    radius=layout.boost_pads[0].radius,
                    kick_speed=layout.boost_pads[0].kick_speed,
                )
            ],
        )
        before = world.ship.vel.length()
        try_trigger_pad(world.boost_pads, world.ship, layout, pad_flash_seconds=0.4)
        self.assertGreater(world.ship.vel.length(), before)

    def test_cove_finish_unlock_unchanged(self) -> None:
        world = build_level("cove")
        self.assertFalse(world.config.exit_requires_boss)
        for beacon in world.beacons:
            beacon.collected = True
        self.assertTrue(world.finish_unlocked)

    def test_spawn_template_not_aliased_to_world_ship(self) -> None:
        world = build_level("rift")
        layout = world.membrane_layout
        assert layout is not None
        anchor_x, anchor_y = layout.spawn_ship.pos.x, layout.spawn_ship.pos.y
        world.ship.pos = Vec2(0.0, 0.0)
        self.assertEqual(layout.spawn_ship.pos.x, anchor_x)
        self.assertEqual(layout.spawn_ship.pos.y, anchor_y)

    def test_off_road_reentry_keeps_free_flight(self) -> None:
        from gravity_ho_matey.gameplay.world import ControlIntent
        from gravity_ho_matey.scenes.play import PlayScene
        from gravity_ho_matey.gameplay.campaign import CampaignState

        scene = PlayScene("rift", CampaignState.new())
        world = scene.world
        layout = world.membrane_layout
        assert layout is not None
        world.ship.pos = Vec2(10.0, 10.0)
        world.update(0.016, ControlIntent())
        self.assertEqual(world.lane_probe.state, LaneState.VOID)
        angle_before = world.ship.angle
        vel_before = Vec2(world.ship.vel.x, world.ship.vel.y)
        world.ship.pos = Vec2(layout.spawn_ship.pos.x, layout.spawn_ship.pos.y)
        world.update(0.016, ControlIntent())
        self.assertEqual(world.lane_probe.state, LaneState.ON_RIBBON)
        self.assertAlmostEqual(world.ship.angle, angle_before)
        self.assertAlmostEqual(world.ship.vel.x, vel_before.x, delta=5.0)
        self.assertAlmostEqual(world.ship.vel.y, vel_before.y, delta=5.0)

    def test_rift_off_road_matches_chart_sector_ship_stats(self) -> None:
        from gravity_ho_matey.levels.level_registry import build_level

        cove = build_level("cove")
        rift = build_level("rift")
        self.assertEqual(rift.config.max_ship_speed, cove.config.max_ship_speed)
        self.assertEqual(rift.config.thrust, cove.config.thrust)
        self.assertAlmostEqual(rift.config.drag, cove.config.drag)
        layout = rift.membrane_layout
        assert layout is not None
        off = probe_lane(Vec2(10.0, 10.0), layout)
        mods = lane_modifiers(off, base_drag=rift.config.drag, base_max_speed=rift.config.max_ship_speed)
        self.assertEqual(mods.max_speed, cove.config.max_ship_speed)
        self.assertEqual(mods.thrust_mult, 1.0)

    def test_ribbon_half_width_increased(self) -> None:
        layout = build_membrane_layout()
        self.assertAlmostEqual(layout.ribbons[0].half_width, RIBBON_HALF_WIDTH)
        self.assertAlmostEqual(RIBBON_HALF_WIDTH, 204.0)
        self.assertEqual(len(layout.ribbons), 3)

    def test_boss_zone_off_lane_uses_neutral_lane_state(self) -> None:
        layout = build_membrane_layout()
        off_lane = Vec2(layout.boss_anchor.x + 420.0, layout.boss_anchor.y + 180.0)
        self.assertTrue(is_in_boss_stable_zone(off_lane, layout))
        probe = probe_lane(off_lane, layout)
        self.assertNotEqual(probe.state, LaneState.ON_RIBBON)
        mods = lane_modifiers(probe, base_drag=0.989, base_max_speed=380.0)
        self.assertEqual(mods.thrust_mult, 1.0)
        self.assertEqual(mods.gravity_scale, 1.0)

    def test_no_boost_pads_near_boss_arena(self) -> None:
        layout = build_membrane_layout()
        for pad in layout.boost_pads:
            self.assertGreaterEqual(pad.pos.y, 1400.0, msg=f"pad at y={pad.pos.y} too close to boss")

    def test_boss_stable_radius_on_layout(self) -> None:
        layout = build_membrane_layout()
        self.assertAlmostEqual(layout.boss_stable_radius, BOSS_STABLE_RADIUS)

    def test_boss_spawn_intervals_slower(self) -> None:
        boss = MegaSquidBoss(pos=Vec2(0, 0), anchor=Vec2(0, 0), hits_remaining=18)
        squid, _ = boss.tick_spawns(5.0, Vec2(0, 0), 0)
        self.assertIsNone(squid, "7.5s interval should not fire at the old 5.0s mark")
        squid, _ = boss.tick_spawns(2.6, Vec2(0, 0), 0)
        self.assertIsNotNone(squid)

    def test_chase_membrane_glow_sizes_bounded(self) -> None:
        from gravity_ho_matey.render.camera import CameraMode, ViewCamera
        from gravity_ho_matey.render.membrane_viz import _CHASE_GLOW_CAP, _chase_world_px, _clamp_glow

        layout = build_membrane_layout()
        camera = ViewCamera(mode=CameraMode.CHASE)
        for ahead in (35.0, 90.0, 220.0, 500.0):
            pad_r = _clamp_glow(_chase_world_px(camera, 54.0, ahead))
            stable_r = _clamp_glow(_chase_world_px(camera, layout.boss_stable_radius * 0.42, ahead))
            self.assertLessEqual(pad_r, _CHASE_GLOW_CAP + 1.0, msg=f"pad at {ahead}")
            self.assertLessEqual(stable_r, _CHASE_GLOW_CAP + 1.0, msg=f"stable at {ahead}")

    def test_ribbon_sample_count_reasonable(self) -> None:
        layout = build_membrane_layout()
        self.assertLessEqual(len(layout.samples), 420)
        self.assertEqual(len(layout.ribbon_chains), 3)

    def test_rift_chase_render_item_budget(self) -> None:
        import tkinter as tk

        from gravity_ho_matey.gameplay.campaign import CampaignState
        from gravity_ho_matey.render.camera import CameraMode
        from gravity_ho_matey.render.tk_renderer import TkRenderer
        from gravity_ho_matey.scenes.play import PlayScene

        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            renderer = TkRenderer(canvas)
            scene = PlayScene("rift", CampaignState.new())
            scene.camera.mode = CameraMode.CHASE
            renderer.draw_world(
                scene.world,
                scene.campaign,
                scene.camera,
                scene.gravity_field,
            )
            item_count = len(canvas.find_all())
            self.assertLess(item_count, 3400, msg=f"chase frame drew {item_count} canvas items")
        finally:
            root.destroy()

    def test_rift_chase_render_does_not_crash(self) -> None:
        import tkinter as tk

        from gravity_ho_matey.gameplay.campaign import CampaignState
        from gravity_ho_matey.render.camera import CameraMode
        from gravity_ho_matey.render.tk_renderer import TkRenderer
        from gravity_ho_matey.scenes.play import PlayScene

        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            renderer = TkRenderer(canvas)
            scene = PlayScene("rift", CampaignState.new())
            scene.camera.mode = CameraMode.CHASE
            scene.world.ship.vel = scene.world.ship.vel + scene.world.ship.vel.normalized() * 80.0
            renderer.draw_world(
                scene.world,
                scene.campaign,
                scene.camera,
                scene.gravity_field,
            )
        finally:
            root.destroy()

    def test_rift_tactical_render_does_not_crash(self) -> None:
        import tkinter as tk

        from gravity_ho_matey.gameplay.campaign import CampaignState
        from gravity_ho_matey.render.tk_renderer import TkRenderer
        from gravity_ho_matey.scenes.play import PlayScene

        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            renderer = TkRenderer(canvas)
            scene = PlayScene("rift", CampaignState.new())
            renderer.draw_world(
                scene.world,
                scene.campaign,
                scene.camera,
                scene.gravity_field,
            )
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
