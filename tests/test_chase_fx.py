import unittest
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid
from gravity_ho_matey.gameplay.entities import GravityWell
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.levels.level_data import build_cove_run_level
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode, TACTICAL_ZOOM_COMPACT, ViewCamera, tactical_scale_for
from gravity_ho_matey.render.chase_fx import draw_fog_glow, draw_speed_streaks
from gravity_ho_matey.render.world_draw import gravity_field_color
from gravity_ho_matey.render.asteroid_viz import collect_chase_asteroid_sprites
from gravity_ho_matey.render.field_viz import gravity_emphasis
from gravity_ho_matey.render.hud_overlay import SciFiHudOverlay
from gravity_ho_matey.render.view_renderers import PerspectiveViewRenderer


def _luminance(hex_color: str) -> float:
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _tk_canvas():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise unittest.SkipTest(f"Tk unavailable: {exc}") from exc
    root.withdraw()
    return root, tk.Canvas(root, width=960, height=640)


class ChaseAsteroidTests(unittest.TestCase):
    def test_chase_asteroid_sprites_have_polygon_points(self) -> None:
        world = build_cove_run_level()
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        ship_pos = Vec2(480, 560)
        ship_angle = -1.5708
        sprites = collect_chase_asteroid_sprites(world.asteroids, camera, ship_pos, ship_angle)
        self.assertGreaterEqual(len(sprites), 1)
        for _, points, _, _ in sprites:
            self.assertGreaterEqual(len(points), 3)

    def test_chase_asteroid_sprites_sort_by_depth(self) -> None:
        world = build_cove_run_level()
        world.asteroids.append(make_asteroid(Vec2(480, 200), seed=999, drift_kind="medium"))
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        sprites = collect_chase_asteroid_sprites(world.asteroids, camera, Vec2(480, 560), -1.5708)
        depths = [depth for depth, _, _, _ in sprites]
        self.assertEqual(depths, sorted(depths))


class ChaseGroundTests(unittest.TestCase):
    def test_chase_grid_high_band_is_purple(self) -> None:
        color = gravity_field_color(0.8)
        self.assertIn(color.lower(), {palette.CHASE_GRID_HIGH.lower(), palette.BLACK_HOLE_RING.lower(), "#5a1840"})

    def test_chase_grid_brighter_than_tactical_floor(self) -> None:
        chase = gravity_field_color(0.5)
        tactical = "#0e2230"
        self.assertGreater(_luminance(chase), _luminance(tactical))


class ChaseFogTests(unittest.TestCase):
    def test_black_hole_fog_draws_multiple_layers(self) -> None:
        root, canvas = _tk_canvas()
        draw_fog_glow(canvas, 200, 200, 80, palette.CHASE_FOG_BLACK_HOLE, pulse=0.5)
        oval_items = [i for i in canvas.find_all() if canvas.type(i) == "oval"]
        self.assertGreaterEqual(len(oval_items), len(palette.CHASE_FOG_BLACK_HOLE))
        root.destroy()

    def test_beacon_fog_draws_pulse_layers(self) -> None:
        from gravity_ho_matey.gameplay.entities import Beacon
        from gravity_ho_matey.render.beacon_viz import draw_beacon_play
        from gravity_ho_matey.render.lighting import LightRig

        root, canvas = _tk_canvas()
        rig = LightRig.for_play(theme="cove", camera_mode=CameraMode.TACTICAL)
        draw_beacon_play(
            canvas,
            200,
            200,
            Beacon(Vec2(0, 0)),
            scale=1.0,
            rig=rig,
            elapsed=1.25,
            seed=0.5,
            spark_orbits=True,
        )
        self.assertGreater(len(canvas.find_all()), len(palette.CHASE_FOG_BEACON))
        root.destroy()


class ChaseSpeedTests(unittest.TestCase):
    def test_speed_streaks_when_fast(self) -> None:
        world = build_cove_run_level()
        world.ship.vel = Vec2(0, 220)
        root, canvas = _tk_canvas()
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        draw_speed_streaks(canvas, camera, world, anchor_x=480, anchor_y=500, ship_pos=world.ship.pos, ship_angle=world.ship.angle)
        lines = [i for i in canvas.find_all() if canvas.type(i) == "line"]
        self.assertGreater(len(lines), 0)
        root.destroy()

    def test_no_streaks_when_slow(self) -> None:
        world = build_cove_run_level()
        world.ship.vel = Vec2(0, 10)
        root, canvas = _tk_canvas()
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        draw_speed_streaks(canvas, camera, world, anchor_x=480, anchor_y=500, ship_pos=world.ship.pos, ship_angle=world.ship.angle)
        self.assertEqual(canvas.find_all(), ())
        root.destroy()

    def test_no_vertical_center_streak_artifact(self) -> None:
        world = build_cove_run_level()
        world.ship.vel = Vec2(0, 180)
        root, canvas = _tk_canvas()
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        draw_speed_streaks(canvas, camera, world, anchor_x=480, anchor_y=500, ship_pos=world.ship.pos, ship_angle=world.ship.angle)
        for item in canvas.find_all():
            if canvas.type(item) != "line":
                continue
            x1, y1, x2, y2 = canvas.coords(item)
            if abs(x1 - x2) < 0.01 and abs(x1 - 480) < 2:
                self.fail("vertical center streak should not be drawn")
        root.destroy()


class FieldVizTests(unittest.TestCase):
    def test_gravity_emphasis_falls_off_with_distance(self) -> None:
        near = gravity_emphasis(40.0)
        far = gravity_emphasis(500.0)
        self.assertGreater(near, far)

    def test_cove_uses_compact_tactical_zoom(self) -> None:
        world = build_cove_run_level()
        self.assertAlmostEqual(tactical_scale_for(world.config), TACTICAL_ZOOM_COMPACT)


class ChaseHudLayoutTests(unittest.TestCase):
    def test_command_bar_has_no_sector_or_camera_overlay(self) -> None:
        from gravity_ho_matey.gameplay.campaign import CampaignState

        overlay = SciFiHudOverlay()
        world = build_cove_run_level()
        root, canvas = _tk_canvas()
        overlay.draw(canvas, world, CampaignState.new(), camera_mode=CameraMode.CHASE)
        for item in canvas.find_all():
            if canvas.type(item) != "text":
                continue
            text = canvas.itemcget(item, "text")
            y = float(canvas.coords(item)[1])
            if "SMUGGLER" in text or "CHASE" in text:
                self.assertGreater(y, SciFiHudOverlay.PANEL_H, msg=f"overlay leaked into command bar: {text!r} y={y}")
        root.destroy()

    def test_playfield_chrome_places_badges_below_command_bar(self) -> None:
        overlay = SciFiHudOverlay()
        world = build_cove_run_level()
        root, canvas = _tk_canvas()
        hud_top = SciFiHudOverlay.PANEL_H
        overlay.draw_playfield_chrome(
            canvas,
            world,
            hud_top,
            camera_mode=CameraMode.CHASE,
        )
        texts = [canvas.itemcget(i, "text") for i in canvas.find_all() if canvas.type(i) == "text"]
        self.assertTrue(any("SMUGGLER" in t for t in texts))
        self.assertTrue(any("CHASE" in t for t in texts))
        for item in canvas.find_all():
            if canvas.type(item) != "text":
                continue
            text = canvas.itemcget(item, "text")
            if "SMUGGLER" in text or "CHASE" in text:
                y = float(canvas.coords(item)[1])
                self.assertGreaterEqual(y, hud_top + 6)
        root.destroy()


class ChaseWellScaleTests(unittest.TestCase):
    def test_floor_ring_span_tracks_world_radius(self) -> None:
        import math

        from gravity_ho_matey.render.camera import CameraMode, ViewCamera
        from gravity_ho_matey.render.chase_wells import floor_ring_span, project_floor_ring

        world = build_cove_run_level()
        reef = next(w for w in world.wells if w.label == "Dead Star Reef")
        world.ship.pos = Vec2(reef.pos.x, reef.pos.y + 280)
        world.ship.angle = -math.pi / 2
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        ship_pos = world.ship.pos
        ship_angle = world.ship.angle
        horizon = camera.chase_horizon_y()
        pts = project_floor_ring(camera, reef.pos, reef.radius, ship_pos, ship_angle, horizon=horizon)
        span = floor_ring_span(pts)
        depth = camera.world_to_screen(reef.pos, ship_pos, ship_angle).depth
        expected = 2.0 * reef.radius * camera.perspective_scale(depth)
        self.assertGreater(span, expected * 0.55)
        self.assertLess(span, expected * 1.45)

    def test_ring_segments_skip_behind_camera_chords(self) -> None:
        import math

        from gravity_ho_matey.render.camera import CameraMode, ViewCamera
        from gravity_ho_matey.render.chase_wells import _ring_segments, project_floor_ring

        world = build_cove_run_level()
        reef = next(w for w in world.wells if w.label == "Dead Star Reef")
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        ship_pos = Vec2(reef.pos.x, reef.pos.y + 120.0)
        ship_angle = -math.pi / 2
        pts = project_floor_ring(
            camera, reef.pos, reef.radius, ship_pos, ship_angle, horizon=camera.chase_horizon_y(),
        )
        for x1, y1, x2, y2 in _ring_segments(pts):
            length = math.hypot(x2 - x1, y2 - y1)
            self.assertLessEqual(length, 161.0)
            self.assertGreater(length, 0.5)
            self.assertFalse(x1 == 0.0 and y1 == 0.0)
            self.assertFalse(x2 == 0.0 and y2 == 0.0)

    def test_lateral_well_ring_stays_drawable_between_holes(self) -> None:
        import math

        from gravity_ho_matey.render.camera import CameraMode, ViewCamera
        from gravity_ho_matey.render.chase_wells import _ring_drawable, _ring_segments, project_floor_ring

        world = build_cove_run_level()
        reef = next(w for w in world.wells if w.label == "Dead Star Reef")
        maelstrom = next(w for w in world.wells if w.label == "Maelstrom")
        world.ship.pos = Vec2((reef.pos.x + maelstrom.pos.x) * 0.5, (reef.pos.y + maelstrom.pos.y) * 0.5)
        world.ship.angle = math.atan2(maelstrom.pos.y - reef.pos.y, maelstrom.pos.x - reef.pos.x)
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        horizon = camera.chase_horizon_y()
        drawable = 0
        segments = 0
        for well in (reef, maelstrom):
            pts = project_floor_ring(
                camera, well.pos, well.radius, world.ship.pos, world.ship.angle, horizon=horizon,
            )
            if _ring_drawable(pts, horizon):
                drawable += 1
                segments += len(_ring_segments(pts))
        self.assertGreaterEqual(drawable, 1)
        self.assertGreater(segments, 4)


class ChaseRendererSmokeTests(unittest.TestCase):
    def test_perspective_renderer_draws_without_error(self) -> None:
        world = build_cove_run_level()
        field = GravityField.bake(
            world.wells,
            world_width=world.config.width,
            world_height=world.config.height,
            cols=16,
            rows=16,
            gravity_scale=world.config.gravity_scale,
        )
        camera = ViewCamera(mode=CameraMode.CHASE)
        root, canvas = _tk_canvas()
        PerspectiveViewRenderer().draw(canvas, world, camera, field, hud_top=54)
        self.assertGreater(len(canvas.find_all()), 20)
        root.destroy()


class ChaseGravityFieldTests(unittest.TestCase):
    def test_near_well_sample_uses_high_band(self) -> None:
        wells = [GravityWell(Vec2(480, 320), strength=50000, radius=200, label="Test")]
        field = GravityField.bake(wells, world_width=960, world_height=640, cols=16, rows=16)
        norm = field.normalized_magnitude_at(Vec2(480, 320))
        self.assertGreater(norm, 0.3)


if __name__ == "__main__":
    unittest.main()
