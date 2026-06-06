import math
import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GravityWell, WorldConfig
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.render.camera import (
    CHASE_BACK,
    CHASE_SCREEN_HEADING,
    CHASE_SHIP_ANCHOR_FRAC,
    TACTICAL_ZOOM_COMPACT,
    CameraMode,
    ViewCamera,
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
    def test_tactical_center_follows_ship_with_compact_zoom(self) -> None:
        camera = ViewCamera()
        config = WorldConfig(width=960, height=640, viewport_width=960, viewport_height=640)
        camera.update_follow(Vec2(80, 70), config, 0.016)
        self.assertAlmostEqual(camera.center.x, 0.0)
        self.assertAlmostEqual(camera.center.y, 0.0)
        camera.update_follow(Vec2(480, 320), config, 1.0)
        self.assertGreater(camera.center.x, 0.0)

    def test_tactical_center_clamps_on_vertical_strip(self) -> None:
        camera = ViewCamera()
        config = WorldConfig(width=960, height=1680, viewport_width=960, viewport_height=640)
        camera.update_follow(Vec2(480, 1500), config, 1.0)
        self.assertAlmostEqual(camera.center.x, 0.0)
        self.assertAlmostEqual(camera.center.y, 1040.0, delta=2.0)

    def test_tactical_world_to_screen_applies_pan_only(self) -> None:
        camera = ViewCamera(mode=CameraMode.TACTICAL)
        camera.center = Vec2(100, 200)
        camera.tactical_scale = 1.0
        p = camera.world_to_screen(Vec2(150, 260), Vec2(), 0.0)
        self.assertAlmostEqual(p.x, 50.0)
        self.assertAlmostEqual(p.y, 60.0)
        self.assertTrue(p.visible)

    def test_tactical_zoom_scales_compact_arena(self) -> None:
        camera = ViewCamera(mode=CameraMode.TACTICAL)
        config = WorldConfig(width=960, height=640, viewport_width=960, viewport_height=640)
        camera.update_follow(Vec2(480, 320), config, 0.016)
        self.assertAlmostEqual(camera.tactical_scale, TACTICAL_ZOOM_COMPACT)
        p = camera.world_to_screen(Vec2(580, 420), Vec2(), 0.0)
        self.assertGreater(p.x, 100.0)

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

    def test_chase_rig_uses_drone_style_offsets(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        self.assertGreater(camera.chase_lift, camera.chase_back)
        self.assertAlmostEqual(camera.chase_back, CHASE_BACK)
        self.assertAlmostEqual(CHASE_SCREEN_HEADING, -math.pi / 2)
        self.assertGreater(CHASE_SHIP_ANCHOR_FRAC, 0.74)
        self.assertLess(CHASE_SHIP_ANCHOR_FRAC, 0.78)
