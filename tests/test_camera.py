import math
import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GravityWell, WorldConfig
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.chart_bounds import CHART_SECTOR_MARGIN_FRAC, oob_camera_blend
from gravity_ho_matey.render.camera import (
    CHASE_BACK,
    CHASE_PLAY_HUD_TOP,
    CHASE_SCREEN_HEADING,
    CHASE_SHIP_ANCHOR_FRAC,
    CameraMode,
    ViewCamera,
    chase_focal_for_hfov,
    chase_horizontal_fov_deg,
)


class GravityFieldHostileTests(unittest.TestCase):
    def test_bake_matches_runtime_gravity_at_cell_centers(self) -> None:
        wells = [GravityWell(Vec2(200, 200), strength=40000, radius=180, label="Test")]
        field = GravityField.bake(wells, world_width=400, world_height=400, cols=8, rows=8, gravity_scale=0.5)
        for row in range(field.rows):
            for col in range(field.cols):
                wx = field.origin.x + col * field.cell_size
                wy = field.origin.y + row * field.cell_size
                point = Vec2(wx, wy)
                runtime = gravity_acceleration_at(point, wells) * 0.5
                baked = field.sample_at(point).accel
                self.assertAlmostEqual(runtime.x, baked.x, places=4)
                self.assertAlmostEqual(runtime.y, baked.y, places=4)

    def test_empty_wells_yield_zero_field(self) -> None:
        field = GravityField.bake([], world_width=320, world_height=320, cols=4, rows=4)
        sample = field.sample_at(Vec2(160, 160))
        self.assertAlmostEqual(sample.magnitude, 0.0)
        self.assertAlmostEqual(field.normalized_magnitude_at(Vec2(50, 50)), 0.0)

    def test_out_of_bounds_sample_clamps_to_edge_cell(self) -> None:
        wells = [GravityWell(Vec2(50, 50), strength=10000, radius=120)]
        field = GravityField.bake(wells, world_width=100, world_height=100, cols=4, rows=4)
        edge = field.sample_at(Vec2(-999, -999))
        corner = field.cell_at(0, 0)
        self.assertEqual(edge.magnitude, corner.magnitude)


class ViewCameraHostileTests(unittest.TestCase):
    def test_tactical_viewport_sized_world_keeps_unity_scale(self) -> None:
        camera = ViewCamera()
        config = WorldConfig(width=960, height=640, viewport_width=960, viewport_height=640)
        for _ in range(30):
            camera.update_follow(Vec2(480, 320), config, 0.05)
        self.assertAlmostEqual(camera.tactical_scale, 1.0, places=2)
        p = camera.world_to_screen(Vec2(580, 420), Vec2(), 0.0)
        self.assertAlmostEqual(p.x, 580.0, places=1)

    def test_tactical_centers_ship_on_solar_strip_end(self) -> None:
        camera = ViewCamera()
        config = WorldConfig(width=960, height=1680, viewport_width=960, viewport_height=640, open_bounds=True)
        camera.set_play_layout(54.0)
        for _ in range(80):
            camera.update_follow(Vec2(480, 1500), config, 0.05)
        play_h = 640.0 - 54.0
        sy = (1500.0 - camera.center.y) * camera.tactical_scale
        self.assertAlmostEqual(sy, play_h * 0.5, delta=4.0)

    def test_tactical_centers_ship_on_drift_outskirts(self) -> None:
        from gravity_ho_matey.levels.level_registry import build_level

        world = build_level("drift")
        camera = ViewCamera()
        camera.set_play_layout(54.0)
        ship_pos = Vec2(180, 2400)
        for _ in range(80):
            camera.update_follow(ship_pos, world.config, 0.05)
        sx = (ship_pos.x - camera.center.x) * camera.tactical_scale
        self.assertAlmostEqual(sx, 480.0, delta=8.0)

    def test_tactical_tracks_ship_outside_open_chart(self) -> None:
        camera = ViewCamera()
        config = WorldConfig(width=960, height=640, viewport_width=960, viewport_height=640, open_bounds=True)
        camera.set_play_layout(54.0)
        for _ in range(80):
            camera.update_follow(Vec2(1140, 320), config, 0.05)
        vis_w = config.viewport_width / camera.tactical_scale
        self.assertAlmostEqual(camera.center.x, 1140.0 - vis_w * 0.5, delta=8.0)

    def test_tactical_keeps_ship_on_screen_in_bounds(self) -> None:
        camera = ViewCamera(mode=CameraMode.TACTICAL)
        config = WorldConfig(width=960, height=640, viewport_width=960, viewport_height=640, open_bounds=True)
        camera.set_play_layout(54.0)
        camera.tactical_scale = 1.0
        for _ in range(80):
            camera.update_follow(Vec2(880, 550), config, 0.05)
        sx = (880.0 - camera.center.x) * camera.tactical_scale
        sy = (550.0 - camera.center.y) * camera.tactical_scale
        play_h = 640.0 - 54.0
        self.assertGreater(sx, 16.0)
        self.assertLess(sx, config.viewport_width - 16.0)
        self.assertGreater(sy, 16.0)
        self.assertLess(sy, play_h - 16.0)

    def test_oob_camera_blend_ramps_smoothly_past_rim(self) -> None:
        config = WorldConfig(width=960, height=640, open_bounds=True, chart_margin_frac=0.055)
        inside = oob_camera_blend(Vec2(480, 320), config)
        barely = oob_camera_blend(Vec2(-53, 320), config)
        deep = oob_camera_blend(Vec2(-150, 320), config)
        self.assertAlmostEqual(inside, 0.0)
        self.assertGreater(barely, 0.0)
        self.assertLess(barely, 0.35)
        self.assertAlmostEqual(deep, 1.0)

    def test_chase_play_layout_ignores_dynamic_hud_banners(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54 + 26 + 40)
        self.assertAlmostEqual(camera.play_hud_top, CHASE_PLAY_HUD_TOP)
        ax1, ay1 = camera.chase_anchor()
        camera.set_play_layout(54)
        ax2, ay2 = camera.chase_anchor()
        self.assertAlmostEqual(ax1, ax2)
        self.assertAlmostEqual(ay1, ay2)

    def test_chase_update_follow_does_not_pan_tactical_center(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        config = WorldConfig(width=960, height=640, viewport_width=960, viewport_height=640, open_bounds=True)
        camera.center = Vec2(100, 50)
        camera.update_follow(Vec2(1200, 900), config, 0.05)
        self.assertAlmostEqual(camera.center.x, 100.0)
        self.assertAlmostEqual(camera.tactical_scale, 1.0)

    def test_tactical_keeps_ship_on_screen_when_oob(self) -> None:
        camera = ViewCamera(mode=CameraMode.TACTICAL)
        config = WorldConfig(width=960, height=640, viewport_width=960, viewport_height=640, open_bounds=True)
        camera.set_play_layout(54.0)
        camera.tactical_scale = 1.0
        for _ in range(80):
            camera.update_follow(Vec2(1020, 320), config, 0.05)
        sx = (1020.0 - camera.center.x) * camera.tactical_scale
        self.assertGreater(sx, 16.0)
        self.assertLess(sx, config.viewport_width - 16.0)

    def test_tactical_world_to_screen_applies_pan_only(self) -> None:
        camera = ViewCamera(mode=CameraMode.TACTICAL)
        camera.center = Vec2(100, 200)
        camera.tactical_scale = 1.0
        p = camera.world_to_screen(Vec2(150, 260), Vec2(), 0.0)
        self.assertAlmostEqual(p.x, 50.0)
        self.assertAlmostEqual(p.y, 60.0)
        self.assertTrue(p.visible)

    def test_cove_gate_ship_visible_at_unity_scale(self) -> None:
        from gravity_ho_matey.levels.level_data import build_cove_run_level
        from gravity_ho_matey.render.hud_overlay import SciFiHudOverlay

        world = build_cove_run_level()
        camera = ViewCamera(mode=CameraMode.TACTICAL)
        camera.set_play_layout(SciFiHudOverlay.PANEL_H)
        world.ship.pos = Vec2(880, 550)
        camera.snap_tactical_to_ship(world.ship.pos, world.config)
        self.assertAlmostEqual(camera.tactical_scale, 1.0, places=2)
        p = camera.world_to_screen(world.ship.pos, world.ship.pos, 0.0)
        hud = SciFiHudOverlay.PANEL_H
        self.assertGreater(p.x, 16.0)
        self.assertLess(p.x, world.config.viewport_width - 16.0)
        self.assertGreater(p.y + hud, hud + 16.0)
        self.assertLess(p.y + hud, world.config.viewport_height - 16.0)

    def test_tactical_mode_switch_snaps_ship_into_view(self) -> None:
        from gravity_ho_matey.levels.level_data import build_cove_run_level
        from gravity_ho_matey.render.hud_overlay import SciFiHudOverlay

        world = build_cove_run_level()
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.tactical_scale = 1.0
        world.ship.pos = Vec2(880, 550)
        camera.cycle_mode()
        camera.set_play_layout(SciFiHudOverlay.PANEL_H)
        camera.snap_tactical_to_ship(world.ship.pos, world.config)
        p = camera.world_to_screen(world.ship.pos, world.ship.pos, 0.0)
        hud = SciFiHudOverlay.PANEL_H
        self.assertGreater(p.x, 16.0)
        self.assertLess(p.x, world.config.viewport_width - 16.0)
        self.assertGreater(p.y + hud, hud + 16.0)
        self.assertLess(p.y + hud, world.config.viewport_height - 16.0)

    def test_chase_locks_ship_to_fixed_anchor(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        ship = Vec2(500, 500)
        p = camera.world_to_screen(ship, ship, 0.9)
        ax, ay = camera.chase_anchor()
        self.assertAlmostEqual(p.x, ax, places=1)
        self.assertAlmostEqual(p.y, ay, places=1)

    def test_chase_ahead_of_ship_maps_toward_horizon(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        ship = Vec2(500, 500)
        angle = -math.pi / 2
        ahead = camera.world_to_screen(Vec2(500, 300), ship, angle)
        _, anchor_y = camera.chase_anchor()
        self.assertTrue(ahead.visible)
        self.assertLess(ahead.y, anchor_y)

    def test_chase_keeps_forward_centered_when_turning(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        ship = Vec2(400, 400)
        ax, _ = camera.chase_anchor()
        for angle in (-math.pi / 2, 0.0, math.pi / 2, 2.1):
            ahead_world = ship + Vec2.from_angle(angle) * 150.0
            projected = camera.world_to_screen(ahead_world, ship, angle)
            self.assertTrue(projected.visible)
            self.assertAlmostEqual(projected.x, ax, delta=4.0)

    def test_chase_lateral_matches_ship_right_and_left(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        ship = Vec2(500, 500)
        angle = -math.pi / 2
        ax, _ = camera.chase_anchor()
        east = camera.world_to_screen(Vec2(620, 500), ship, angle)
        west = camera.world_to_screen(Vec2(380, 500), ship, angle)
        self.assertTrue(east.visible)
        self.assertTrue(west.visible)
        self.assertGreater(east.x, ax)
        self.assertLess(west.x, ax)

    def test_chase_turn_rate_tracks_heading_delta(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.update_chase_heading(-math.pi / 2, 0.016)
        camera.update_chase_heading(-math.pi / 2 + 0.2, 0.016)
        self.assertGreater(camera.turn_rate, 0.0)

    def test_velocity_lag_shifts_world_not_anchor(self) -> None:
        config = WorldConfig(width=960, height=640, viewport_width=960, viewport_height=640)
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        ship = Vec2(500, 500)
        angle = -math.pi / 2
        ahead = Vec2(500, 300)
        neutral = camera.world_to_screen(ahead, ship, angle)
        ax, ay = camera.chase_anchor()
        camera.velocity_lag_y = 21.0
        lagged = camera.world_to_screen(ahead, ship, angle)
        self.assertAlmostEqual(ax, camera.chase_anchor()[0])
        self.assertAlmostEqual(ay, camera.chase_anchor()[1])
        self.assertAlmostEqual(lagged.y, neutral.y + 21.0, places=1)

    def test_velocity_lag_tracks_forward_speed(self) -> None:
        config = WorldConfig(width=960, height=640, max_ship_speed=330.0)
        camera = ViewCamera(mode=CameraMode.CHASE)
        forward_vel = Vec2.from_angle(-math.pi / 2) * 280.0
        for _ in range(30):
            camera.update_chase_velocity(forward_vel, -math.pi / 2, config, 0.05)
        self.assertGreater(camera.velocity_lag_y, 12.0)

    def test_velocity_lag_resets_on_mode_cycle(self) -> None:
        config = WorldConfig(width=960, height=640, max_ship_speed=330.0)
        camera = ViewCamera(mode=CameraMode.CHASE)
        vel = Vec2.from_angle(-math.pi / 2) * 300.0
        for _ in range(20):
            camera.update_chase_velocity(vel, -math.pi / 2, config, 0.05)
        self.assertGreater(camera.velocity_lag_y, 0.0)
        camera.cycle_mode()
        self.assertEqual(camera.velocity_lag_y, 0.0)

    def test_mode_cycle_toggles_tactical_and_chase_only(self) -> None:
        camera = ViewCamera()
        self.assertEqual(camera.mode, CameraMode.TACTICAL)
        camera.cycle_mode()
        self.assertEqual(camera.mode, CameraMode.CHASE)
        camera.cycle_mode()
        self.assertEqual(camera.mode, CameraMode.TACTICAL)

    def test_mode_flash_decays(self) -> None:
        camera = ViewCamera()
        camera.cycle_mode()
        self.assertGreater(camera.mode_flash_ttl, 0.0)
        camera.tick(2.0)
        self.assertEqual(camera.mode_flash_ttl, 0.0)

    def test_chase_hfov_target_is_105_degrees(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        fov = chase_horizontal_fov_deg(
            viewport_width=float(camera.viewport_width),
            focal_length=camera.focal_length,
        )
        self.assertAlmostEqual(fov, 105.0, places=1)
        self.assertAlmostEqual(camera.focal_length, chase_focal_for_hfov(960.0, 105.0), places=1)

    def test_chase_rig_uses_drone_style_offsets(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        self.assertGreater(camera.chase_lift, camera.chase_back)
        self.assertAlmostEqual(camera.chase_back, CHASE_BACK)
        self.assertAlmostEqual(CHASE_SCREEN_HEADING, -math.pi / 2)
        self.assertGreater(CHASE_SHIP_ANCHOR_FRAC, 0.74)
        self.assertLess(CHASE_SHIP_ANCHOR_FRAC, 0.78)
