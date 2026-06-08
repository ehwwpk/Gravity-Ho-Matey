from __future__ import annotations

import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Asteroid
from gravity_ho_matey.levels.brood_moon_asteroids import orbital_debris_asteroids
from gravity_ho_matey.levels.brood_moon_layout import (
    MOON_CENTER,
    ORBITAL_DEBRIS_EXCLUDE_INNER,
    ORBITAL_DEBRIS_EXCLUDE_OUTER,
    build_brood_moon_orbital_layout,
)
from gravity_ho_matey.levels.level_profiles import brood_moon_orbital_config
from gravity_ho_matey.render.asteroid_viz import asteroid_threat_drawable
from gravity_ho_matey.render.brood_moon_surface_viz import (
    CHASE_BROOD_CENTER_FOG_MAX,
    draw_brood_chase_surface_band,
)


class BroodSurfaceVizTests(unittest.TestCase):
    def test_chase_fog_radius_capped(self) -> None:
        self.assertLessEqual(CHASE_BROOD_CENTER_FOG_MAX, 96.0)

    def test_chase_surface_band_callable(self) -> None:
        self.assertTrue(callable(draw_brood_chase_surface_band))

    def test_sinkhole_rim_mesh_no_crash(self) -> None:
        from gravity_ho_matey.render.brood_surface_mesh import mesh_for

        verts = mesh_for("sinkhole_rim", seed=42, scale=1.0)
        self.assertGreaterEqual(len(verts), 3)

    def test_brood_viz_helpers_callable(self) -> None:
        from gravity_ho_matey.render.brood_ambient_viz import draw_brood_ambient_tactical
        from gravity_ho_matey.render.brood_fauna_viz import draw_brood_fauna_tactical
        from gravity_ho_matey.render.chase_fx import draw_brood_orbital_chase_floor_wash
        from gravity_ho_matey.render.squid_viz import draw_squid_coil_ring

        self.assertTrue(callable(draw_brood_ambient_tactical))
        self.assertTrue(callable(draw_brood_fauna_tactical))
        self.assertTrue(callable(draw_brood_orbital_chase_floor_wash))
        self.assertTrue(callable(draw_squid_coil_ring))

    def test_brood_ambient_tactical_draws_larva_motes(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")
        from gravity_ho_matey.gameplay.brood_moon_mission import BroodPhase
        from gravity_ho_matey.levels.brood_moon_layout import SURFACE_FLOOR_Y, SURFACE_WRAP_WIDTH
        from gravity_ho_matey.levels.level_registry import build_level
        from gravity_ho_matey.render.brood_ambient_viz import draw_brood_ambient_tactical
        from gravity_ho_matey.render.camera import CameraMode, ViewCamera
        from gravity_ho_matey.render.lighting import LightRig

        world = build_level("brood_moon")
        bm = world.brood_moon
        assert bm is not None
        bm.phase = BroodPhase.SURFACE
        world.ship.pos = Vec2(SURFACE_WRAP_WIDTH * 0.11, SURFACE_FLOOR_Y - 140.0)
        camera = ViewCamera(mode=CameraMode.TACTICAL)
        camera.snap_tactical_to_ship(world.ship.pos, world.config)
        rig = LightRig.for_play(theme="brood_moon", camera_mode=CameraMode.TACTICAL)
        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            draw_brood_ambient_tactical(
                canvas,
                camera,
                world,
                hud_top=54.0,
                ship_pos=world.ship.pos,
                ship_angle=world.ship.angle,
                rig=rig,
            )
            self.assertGreater(len(canvas.find_all()), 0)
        finally:
            root.destroy()

    def test_brood_fauna_tactical_draws_drift_ribbon_without_error(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")
        from gravity_ho_matey.gameplay.brood_moon_mission import BroodPhase
        from gravity_ho_matey.levels.brood_moon_layout import SURFACE_FLOOR_Y, SURFACE_WRAP_WIDTH
        from gravity_ho_matey.levels.level_registry import build_level
        from gravity_ho_matey.render.brood_fauna_viz import draw_brood_fauna_tactical
        from gravity_ho_matey.render.camera import CameraMode, ViewCamera
        from gravity_ho_matey.render.lighting import LightRig

        world = build_level("brood_moon")
        bm = world.brood_moon
        assert bm is not None
        bm.phase = BroodPhase.SURFACE
        # Near drift_ribbon anchor (frac 0.252) so _draw_drift_ribbon runs.
        world.ship.pos = Vec2(SURFACE_WRAP_WIDTH * 0.252, SURFACE_FLOOR_Y - 140.0)
        camera = ViewCamera(mode=CameraMode.TACTICAL)
        camera.snap_tactical_to_ship(world.ship.pos, world.config)
        rig = LightRig.for_play(theme="brood_moon", camera_mode=CameraMode.TACTICAL)
        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            draw_brood_fauna_tactical(
                canvas,
                camera,
                world,
                hud_top=54.0,
                ship_pos=world.ship.pos,
                ship_angle=world.ship.angle,
                rig=rig,
            )
            self.assertGreater(len(canvas.find_all()), 0)
        finally:
            root.destroy()


class BroodHazardVisibilityTests(unittest.TestCase):
    def test_orbital_debris_outside_exclusion_band(self) -> None:
        layout = build_brood_moon_orbital_layout()
        config = brood_moon_orbital_config(width=layout.width, height=layout.height)
        rocks = orbital_debris_asteroids(layout, config)
        moon = layout.moon_well.pos
        for rock in rocks:
            dist = (rock.pos - moon).length()
            in_exclusion = ORBITAL_DEBRIS_EXCLUDE_INNER <= dist <= ORBITAL_DEBRIS_EXCLUDE_OUTER
            self.assertFalse(in_exclusion, f"rock at dist {dist} inside exclusion band")

    def test_asteroid_threat_drawable_within_radius(self) -> None:
        rock = Asteroid(
            pos=Vec2(100.0, 100.0),
            vel=Vec2(0.0, 0.0),
            angle=0.0,
            spin=0.0,
            local_verts=(Vec2(10, 0), Vec2(-5, 8), Vec2(-5, -8)),
        )
        ship = Vec2(120.0, 100.0)
        self.assertTrue(asteroid_threat_drawable(rock, ship, threat_radius=40.0))
        self.assertFalse(asteroid_threat_drawable(rock, ship, threat_radius=5.0))

    def test_nearest_closing_asteroid_helper(self) -> None:
        from gravity_ho_matey.levels.level_registry import build_level
        from gravity_ho_matey.render.edge_hints import _nearest_closing_asteroid

        world = build_level("brood_moon")
        world.ship.pos = Vec2(620.0, 1580.0)
        hint = _nearest_closing_asteroid(world, world.ship.pos, 520.0)
        self.assertTrue(hint is None or (hint - MOON_CENTER).length() > 0.0)
