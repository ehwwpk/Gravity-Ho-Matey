import math
import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import WorldConfig
from gravity_ho_matey.render.camera import (
    CHASE_BOOST_KICK_Y,
    CHASE_FOV_BOOST_MAX,
    CHASE_SCREEN_HEADING,
    CHASE_THRUST_PUNCH_MAX,
    CameraMode,
    ViewCamera,
    chase_horizontal_fov_deg,
)
from gravity_ho_matey.render.chase_rig import BANK_MAX_RAD, chase_bank_offset_rad


class ChaseRigTests(unittest.TestCase):
    def test_bank_offset_zero_when_aligned(self) -> None:
        angle = -math.pi / 2
        vel = Vec2.from_angle(angle) * 120.0
        offset = chase_bank_offset_rad(vel, angle, turn_rate=0.0)
        self.assertAlmostEqual(offset, 0.0, places=3)

    def test_bank_offset_clamped(self) -> None:
        angle = -math.pi / 2
        vel = Vec2(200, -80)
        offset = chase_bank_offset_rad(vel, angle, turn_rate=400.0)
        self.assertLessEqual(abs(offset), BANK_MAX_RAD + 1e-6)

    def test_bank_offset_signs_with_slip_and_turn(self) -> None:
        angle = -math.pi / 2
        right_slip = chase_bank_offset_rad(Vec2(80, -40), angle, turn_rate=0.0)
        left_turn = chase_bank_offset_rad(Vec2.from_angle(angle) * 100, angle, turn_rate=-120.0)
        self.assertGreater(right_slip, 0.0)
        self.assertLess(left_turn, 0.0)


class ChaseDynamicsTests(unittest.TestCase):
    def test_boost_tap_applies_full_kick_same_frame(self) -> None:
        config = WorldConfig(width=960, height=640, max_ship_speed=330.0)
        camera = ViewCamera(mode=CameraMode.CHASE)
        vel = Vec2.from_angle(-math.pi / 2) * 200.0
        camera.update_chase_dynamics(
            vel, -math.pi / 2, config, 0.016, boost_flash=0.35, boost_energy=1.0, boost_tapped=True,
        )
        self.assertAlmostEqual(camera.boost_kick_y, CHASE_BOOST_KICK_Y, places=1)

    def test_mesh_scales_track_fov_boost(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        base_scale, base_lateral, _ = camera.chase_mesh_scales(120.0)
        camera.fov_boost = CHASE_FOV_BOOST_MAX
        widened_scale, widened_lateral, _ = camera.chase_mesh_scales(120.0)
        self.assertLess(widened_scale, base_scale)
        self.assertLess(widened_lateral, base_lateral)

    def test_boost_widens_fov_and_punch(self) -> None:
        config = WorldConfig(width=960, height=640, max_ship_speed=330.0)
        camera = ViewCamera(mode=CameraMode.CHASE)
        vel = Vec2.from_angle(-math.pi / 2) * 280.0
        for i in range(40):
            camera.update_chase_dynamics(
                vel,
                -math.pi / 2,
                config,
                0.05,
                boost_flash=0.3,
                boost_energy=0.9,
                boost_tapped=(i == 0),
            )
        self.assertGreater(camera.chase_thrust_boost, 1.08)
        self.assertLess(camera.chase_thrust_boost, CHASE_THRUST_PUNCH_MAX + 0.01)
        self.assertGreater(camera.fov_boost, CHASE_FOV_BOOST_MAX * 0.35)

    def test_effective_focal_wider_under_boost(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        base = camera.effective_focal_length()
        camera.fov_boost = CHASE_FOV_BOOST_MAX
        self.assertLess(camera.effective_focal_length(), base)
        hfov = chase_horizontal_fov_deg(
            viewport_width=float(camera.viewport_width),
            focal_length=camera.effective_focal_length(),
        )
        base_fov = chase_horizontal_fov_deg(
            viewport_width=float(camera.viewport_width),
            focal_length=camera.focal_length,
        )
        self.assertGreater(hfov, base_fov)

    def test_bank_display_tracks_turn_smoothly(self) -> None:
        config = WorldConfig(width=960, height=640, max_ship_speed=330.0)
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.update_chase_heading(-math.pi / 2, 0.016)
        vel = Vec2.from_angle(-math.pi / 2) * 200.0
        for _ in range(30):
            camera.update_chase_heading(-math.pi / 2 + 0.15, 0.016)
            camera.update_chase_dynamics(
                vel, -math.pi / 2 + 0.15, config, 0.016, boost_flash=0.0,
            )
        self.assertNotAlmostEqual(camera.bank_display, 0.0, places=2)

    def test_boost_kick_shifts_projection_then_decays(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        ship = Vec2(500, 500)
        angle = -math.pi / 2
        neutral = camera.world_to_screen(ship, ship, angle)
        camera.boost_kick_y = CHASE_BOOST_KICK_Y
        kicked = camera.world_to_screen(ship, ship, angle)
        self.assertAlmostEqual(kicked.y, neutral.y + CHASE_BOOST_KICK_Y, places=1)
        for _ in range(60):
            camera.boost_kick_y *= 0.85
        self.assertLess(camera.boost_kick_y, 1.0)

    def test_dynamics_reset_on_mode_cycle(self) -> None:
        config = WorldConfig(width=960, height=640, max_ship_speed=330.0)
        camera = ViewCamera(mode=CameraMode.CHASE)
        vel = Vec2.from_angle(-math.pi / 2) * 300.0
        for _ in range(20):
            camera.update_chase_dynamics(
                vel, -math.pi / 2, config, 0.05, boost_flash=0.3, boost_energy=1.0,
            )
        self.assertGreater(camera.velocity_lag_y, 0.0)
        camera.cycle_mode()
        self.assertEqual(camera.velocity_lag_y, 0.0)
        self.assertEqual(camera.velocity_lag_x, 0.0)
        self.assertEqual(camera.fov_boost, 0.0)
        self.assertEqual(camera.bank_display, 0.0)

    def test_reset_chase_presentation_clears_juice(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.velocity_lag_y = 12.0
        camera.boost_kick_y = 5.0
        camera.fov_boost = 0.04
        camera.turn_rate = 90.0
        camera.reset_chase_presentation()
        self.assertEqual(camera.velocity_lag_y, 0.0)
        self.assertEqual(camera.boost_kick_y, 0.0)
        self.assertEqual(camera.fov_boost, 0.0)
        self.assertEqual(camera.turn_rate, 0.0)
        self.assertFalse(camera._chase_heading_ready)

    def test_tactical_mode_skips_redundant_dynamics_reset(self) -> None:
        camera = ViewCamera(mode=CameraMode.TACTICAL)
        camera.update_chase_dynamics(
            Vec2(0, -200), -math.pi / 2, WorldConfig(width=960, height=640), 0.016,
        )
        self.assertEqual(camera.chase_thrust_boost, 1.0)

    def test_chase_anchor_stable_under_lag_kick_and_fov(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        ship = Vec2(500, 500)
        angle = -math.pi / 2
        ax, ay = camera.chase_anchor()
        camera.velocity_lag_y = 18.0
        camera.velocity_lag_x = -6.0
        camera.boost_kick_y = CHASE_BOOST_KICK_Y
        camera.fov_boost = CHASE_FOV_BOOST_MAX
        camera.chase_thrust_boost = CHASE_THRUST_PUNCH_MAX
        p = camera.world_to_screen(ship, ship, angle)
        self.assertAlmostEqual(p.x, ax + camera.velocity_lag_x + camera.boost_kick_x, places=1)
        self.assertAlmostEqual(p.y, ay + camera.velocity_lag_y + camera.boost_kick_y, places=1)

    def test_screen_depth_scale_shrinks_with_fov_boost(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        base = camera.chase_screen_depth_scale(180.0)
        camera.fov_boost = CHASE_FOV_BOOST_MAX
        widened = camera.chase_screen_depth_scale(180.0)
        self.assertLess(widened, base)

    def test_ship_and_hud_share_bank_display_angle(self) -> None:
        from gravity_ho_matey.render.chase_helm import bank_angle_for_chase

        angle = -math.pi / 2
        vel = Vec2(100, -30)
        instant = bank_angle_for_chase(vel, angle, turn_rate=80.0)
        camera = ViewCamera(mode=CameraMode.CHASE)
        config = WorldConfig(width=960, height=640, max_ship_speed=330.0)
        camera.turn_rate = 80.0
        for _ in range(50):
            camera.update_chase_dynamics(vel, angle, config, 0.016, boost_flash=0.0)
        hud_angle = CHASE_SCREEN_HEADING + camera.bank_display
        self.assertAlmostEqual(instant, hud_angle, delta=0.08)


if __name__ == "__main__":
    unittest.main()
