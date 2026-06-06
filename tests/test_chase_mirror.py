import math
import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.render.camera import CameraMode, ViewCamera
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.levels.level_data import build_cove_run_level
from gravity_ho_matey.render.chase_mirror import mirror_layout, world_to_mirror


class ChaseMirrorTests(unittest.TestCase):
    def test_mirror_pane_is_expanded(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        mx, my, mw, mh = mirror_layout(camera, 54.0)
        self.assertGreaterEqual(mw, 320.0)
        self.assertGreaterEqual(mh, 90.0)
        self.assertAlmostEqual(mx + mw * 0.5, camera.viewport_width * 0.5, places=1)

    def test_clamp_keeps_heatmap_samples_on_glass(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        mx, my, mw, mh = mirror_layout(camera, 54.0)
        ship_pos = Vec2(480, 400)
        ship_angle = -math.pi / 2
        wide = ship_pos + Vec2.from_angle(ship_angle + math.pi) * 120.0 + Vec2(500, 0)
        hit = world_to_mirror(wide, ship_pos, ship_angle, mx, my, mw, mh, clamp=True)
        self.assertIsNotNone(hit)
        assert hit is not None
        px, _, _ = hit
        self.assertGreaterEqual(px, mx + 6)
        self.assertLessEqual(px, mx + mw - 6)

    def test_point_behind_ship_maps_into_mirror(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        mx, my, mw, mh = mirror_layout(camera, 54.0)
        ship_pos = Vec2(480, 400)
        ship_angle = -math.pi / 2
        aft_point = ship_pos + Vec2.from_angle(ship_angle + math.pi) * 120.0
        hit = world_to_mirror(aft_point, ship_pos, ship_angle, mx, my, mw, mh)
        self.assertIsNotNone(hit)
        assert hit is not None
        px, py, _aft = hit
        self.assertGreater(px, mx)
        self.assertLess(px, mx + mw)
        self.assertGreater(py, my)
        self.assertLess(py, my + mh)

    def test_point_ahead_of_ship_is_hidden(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        mx, my, mw, mh = mirror_layout(camera, 54.0)
        ship_pos = Vec2(480, 400)
        ship_angle = -math.pi / 2
        ahead = ship_pos + Vec2.from_angle(ship_angle) * 80.0
        self.assertIsNone(world_to_mirror(ahead, ship_pos, ship_angle, mx, my, mw, mh))

    def test_lateral_offset_moves_blip_left_and_right(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        mx, my, mw, mh = mirror_layout(camera, 54.0)
        ship_pos = Vec2(480, 400)
        ship_angle = -math.pi / 2
        right = ship_pos + Vec2.from_angle(ship_angle + math.pi) * 100.0 + Vec2(80, 0)
        left = ship_pos + Vec2.from_angle(ship_angle + math.pi) * 100.0 + Vec2(-80, 0)
        r_hit = world_to_mirror(right, ship_pos, ship_angle, mx, my, mw, mh)
        l_hit = world_to_mirror(left, ship_pos, ship_angle, mx, my, mw, mh)
        self.assertIsNotNone(r_hit)
        self.assertIsNotNone(l_hit)
        assert r_hit is not None and l_hit is not None
        self.assertGreater(r_hit[0], l_hit[0])

    def test_farther_aft_appears_higher_in_mirror(self) -> None:
        camera = ViewCamera(mode=CameraMode.CHASE)
        mx, my, mw, mh = mirror_layout(camera, 54.0)
        ship_pos = Vec2(480, 400)
        ship_angle = -math.pi / 2
        near = ship_pos + Vec2(0, 80)
        far = ship_pos + Vec2(0, 220)
        near_hit = world_to_mirror(near, ship_pos, ship_angle, mx, my, mw, mh)
        far_hit = world_to_mirror(far, ship_pos, ship_angle, mx, my, mw, mh)
        self.assertIsNotNone(near_hit)
        self.assertIsNotNone(far_hit)
        assert near_hit is not None and far_hit is not None
        self.assertLess(far_hit[1], near_hit[1])

    def test_mirror_draws_with_heatmap(self) -> None:
        try:
            import tkinter as tk
            root = tk.Tk()
        except tk.TclError as exc:
            raise unittest.SkipTest(f"Tk unavailable: {exc}") from exc
        root.withdraw()
        canvas = tk.Canvas(root, width=960, height=640)
        world = build_cove_run_level()
        field = GravityField.bake(
            world.wells,
            world_width=world.config.width,
            world_height=world.config.height,
            cols=16,
            rows=16,
            gravity_scale=world.config.gravity_scale,
        )
        from gravity_ho_matey.render.chase_mirror import draw_rear_view_mirror

        camera = ViewCamera(mode=CameraMode.CHASE)
        draw_rear_view_mirror(
            canvas,
            world,
            camera,
            field,
            ship_pos=world.ship.pos,
            ship_angle=world.ship.angle,
            ship_vel=world.ship.vel,
            hud_top=54.0,
            elapsed=1.0,
        )
        self.assertGreater(len(canvas.find_all()), 14)


if __name__ == "__main__":
    unittest.main()
