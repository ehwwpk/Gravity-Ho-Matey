import math
import unittest
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid
from gravity_ho_matey.gameplay.entities import GravityWell
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.levels.level_data import build_cove_run_level
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode, ViewCamera, tactical_scale_for
from gravity_ho_matey.render.chase_fx import _boost_tap_strength, draw_chase_boost_jolt, draw_fog_glow, draw_speed_streaks
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
        draw_speed_streaks(
            canvas, camera, world, anchor_x=480, anchor_y=500,
            display_angle=-math.pi / 2,
        )
        lines = [i for i in canvas.find_all() if canvas.type(i) == "line"]
        self.assertGreater(len(lines), 0)
        root.destroy()

    def test_no_streaks_when_slow(self) -> None:
        world = build_cove_run_level()
        world.ship.vel = Vec2(0, 10)
        root, canvas = _tk_canvas()
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        draw_speed_streaks(
            canvas, camera, world, anchor_x=480, anchor_y=500,
            display_angle=-math.pi / 2,
        )
        self.assertEqual(canvas.find_all(), ())
        root.destroy()

    def test_no_streaks_during_boost(self) -> None:
        world = build_cove_run_level()
        world.ship.vel = Vec2(0, 220)
        world.ship.boost_flash = 0.25
        root, canvas = _tk_canvas()
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        draw_speed_streaks(
            canvas, camera, world, anchor_x=480, anchor_y=500,
            display_angle=-math.pi / 2,
        )
        self.assertEqual(canvas.find_all(), ())
        root.destroy()

    def test_streaks_follow_display_angle_not_slip_velocity(self) -> None:
        """Drift velocity skew must not rotate streaks away from ship rig."""
        world = build_cove_run_level()
        world.ship.vel = Vec2(180, -40)
        root, canvas = _tk_canvas()
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        draw_speed_streaks(
            canvas, camera, world, anchor_x=480, anchor_y=500,
            display_angle=-math.pi / 2,
        )
        for item in canvas.find_all():
            if canvas.type(item) != "line":
                continue
            x1, y1, x2, y2 = canvas.coords(item)
            dx, dy = x2 - x1, y2 - y1
            if abs(dx) < 1e-6 and abs(dy) < 1e-6:
                continue
            angle = math.degrees(math.atan2(dy, dx))
            self.assertGreater(angle, 70.0)
            self.assertLess(angle, 110.0)
        root.destroy()

    def test_streaks_trail_aft_of_ship_rig(self) -> None:
        world = build_cove_run_level()
        world.ship.vel = Vec2(0, 180)
        root, canvas = _tk_canvas()
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        draw_speed_streaks(
            canvas, camera, world, anchor_x=480, anchor_y=500,
            display_angle=-math.pi / 2,
        )
        lines = [i for i in canvas.find_all() if canvas.type(i) == "line"]
        self.assertGreater(len(lines), 0)
        for item in lines:
            x1, y1, x2, y2 = canvas.coords(item)
            self.assertGreater(max(y1, y2), 500.0)
        root.destroy()


class ChaseBoostJoltTests(unittest.TestCase):
    def test_boost_tap_strength_peaks_at_fresh_flash(self) -> None:
        max_flash = 0.35
        self.assertAlmostEqual(_boost_tap_strength(max_flash, max_flash), 1.0)
        window = max_flash * 0.34
        self.assertAlmostEqual(_boost_tap_strength(max_flash - window, max_flash), 0.0, places=5)

    def test_boost_jolt_draws_shock_and_sparks_behind_ship(self) -> None:
        world = build_cove_run_level()
        world.ship.boost_flash = world.config.boost_flash_seconds * 0.99
        root, canvas = _tk_canvas()
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        camera.boost_kick_y = 7.0
        draw_chase_boost_jolt(
            canvas,
            anchor_x=480,
            anchor_y=500,
            display_angle=-math.pi / 2,
            world=world,
            camera=camera,
            intensity=0.8,
            elapsed=1.0,
        )
        lines = [i for i in canvas.find_all() if canvas.type(i) == "line"]
        ovals = [i for i in canvas.find_all() if canvas.type(i) == "oval"]
        self.assertGreater(len(lines), 2)
        self.assertGreaterEqual(len(ovals), 2)
        for item in lines:
            x1, y1, x2, y2 = canvas.coords(item)
            self.assertGreater(y1, 500)
            self.assertGreater(y2, 500)
        plume_colors = {palette.CHASE_BOOST_PLUME_MID.lower(), palette.CHASE_BOOST_PLUME_CORE.lower()}
        for item in lines:
            fill = canvas.itemcget(item, "fill").lower()
            self.assertNotIn(fill, plume_colors)
        root.destroy()

    def test_boost_jolt_skips_when_not_thrusting(self) -> None:
        world = build_cove_run_level()
        world.ship.boost_flash = 0.0
        root, canvas = _tk_canvas()
        camera = ViewCamera(mode=CameraMode.CHASE)
        draw_chase_boost_jolt(
            canvas,
            anchor_x=480,
            anchor_y=500,
            display_angle=-math.pi / 2,
            world=world,
            camera=camera,
            intensity=0.0,
            elapsed=0.0,
        )
        self.assertEqual(canvas.find_all(), ())
        root.destroy()


class FieldVizTests(unittest.TestCase):
    def test_gravity_emphasis_falls_off_with_distance(self) -> None:
        near = gravity_emphasis(40.0)
        far = gravity_emphasis(500.0)
        self.assertGreater(near, far)

    def test_cove_uses_unity_tactical_scale(self) -> None:
        world = build_cove_run_level()
        self.assertAlmostEqual(tactical_scale_for(world.config), 1.0)


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


class ChaseTitanWellTests(unittest.TestCase):
    def test_drift_titan_glow_radius_is_screen_capped(self) -> None:
        import math

        from gravity_ho_matey.levels.level_registry import build_level
        from gravity_ho_matey.render.camera import CameraMode, ViewCamera
        from gravity_ho_matey.render.chase_wells import _CHASE_GLOW_RADIUS_CAP, chase_well_glow_radius

        world = build_level("drift")
        kraken = next(w for w in world.wells if w.label == "Graviton Kraken")
        world.ship.pos = Vec2(kraken.pos.x + 420.0, kraken.pos.y + 260.0)
        world.ship.angle = math.atan2(kraken.pos.y - world.ship.pos.y, kraken.pos.x - world.ship.pos.x)
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        glow = chase_well_glow_radius(
            camera,
            kraken,
            world.ship.pos,
            world.ship.angle,
            scale=0.8,
        )
        self.assertLessEqual(glow, _CHASE_GLOW_RADIUS_CAP)
        self.assertGreater(glow, 20.0)

    def test_drift_titan_draws_ring_strokes_not_only_fog(self) -> None:
        import math

        from gravity_ho_matey.levels.level_registry import build_level
        from gravity_ho_matey.render.camera import CameraMode, ViewCamera
        from gravity_ho_matey.render.chase_wells import (
            _ring_segments,
            chase_well_drawable,
            draw_chase_well,
            project_floor_ring,
        )
        from gravity_ho_matey.render.lighting import LightRig

        world = build_level("drift")
        kraken = next(w for w in world.wells if w.label == "Graviton Kraken")
        world.ship.pos = Vec2(kraken.pos.x + 520.0, kraken.pos.y + 180.0)
        world.ship.angle = math.atan2(kraken.pos.y - world.ship.pos.y, kraken.pos.x - world.ship.pos.x)
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        ship_pos = world.ship.pos
        ship_angle = world.ship.angle
        drawable, anchor, depth = chase_well_drawable(camera, kraken, ship_pos, ship_angle)
        self.assertTrue(drawable)
        horizon = camera.chase_horizon_y()
        outer = project_floor_ring(camera, kraken.pos, kraken.radius, ship_pos, ship_angle, horizon=horizon)
        segments = _ring_segments(outer, max_px=220.0)
        self.assertGreater(len(segments), 8)

        root, canvas = _tk_canvas()
        rig = LightRig.for_play(theme="drift", camera_mode=CameraMode.CHASE)
        draw_chase_well(
            canvas,
            anchor,
            kraken,
            scale=0.6,
            elapsed=0.0,
            depth=depth,
            camera=camera,
            ship_pos=ship_pos,
            ship_angle=ship_angle,
            default_maw=world.config.well_maw_radius,
            rig=rig,
        )
        lines = [i for i in canvas.find_all() if canvas.type(i) == "line"]
        self.assertGreater(len(lines), 6)
        root.destroy()

    def test_drift_chase_heatmap_cells_stay_screen_sized(self) -> None:
        from gravity_ho_matey.gameplay.gravity_field import GravityField
        from gravity_ho_matey.levels.level_registry import build_level
        from gravity_ho_matey.render.camera import CameraMode, ViewCamera
        from gravity_ho_matey.render.chase_ground import _CHASE_HEATMAP_CELL_CAP_PX, draw_chase_gravity_heatmap

        world = build_level("drift")
        field = GravityField.bake(
            world.wells,
            world_width=world.config.width,
            world_height=world.config.height,
            cols=32,
            rows=32,
            gravity_scale=world.config.gravity_scale,
        )
        camera = ViewCamera(mode=CameraMode.CHASE)
        camera.set_play_layout(54.0)
        root, canvas = _tk_canvas()
        draw_chase_gravity_heatmap(
            canvas,
            field,
            camera,
            world.ship.pos,
            world.ship.angle,
            step=4,
            _world=world,
        )
        max_span = 0.0
        for item in canvas.find_all():
            if canvas.type(item) != "rectangle":
                continue
            x0, y0, x1, y1 = canvas.coords(item)
            max_span = max(max_span, abs(x1 - x0), abs(y1 - y0))
        root.destroy()
        self.assertLessEqual(max_span, _CHASE_HEATMAP_CELL_CAP_PX * 2.2)


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
