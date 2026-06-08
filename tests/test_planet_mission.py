from __future__ import annotations

import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.planet_mission import PlanetBody, in_planet_landing_band, limb_point_toward
from gravity_ho_matey.levels.brood_moon_layout import MOON_CENTER, MOON_RADIUS, build_brood_moon_orbital_layout


class PlanetMissionTests(unittest.TestCase):
    def test_landing_band_accepts_full_limb_ring(self) -> None:
        layout = build_brood_moon_orbital_layout()
        body = layout.planet
        for angle in (0.0, 1.2, 2.5, 4.0, 5.5):
            pos = body.center + Vec2.from_angle(angle) * (body.surface_radius + 90.0)
            self.assertTrue(in_planet_landing_band(pos, body), msg=f"angle {angle}")

    def test_landing_band_rejects_deep_space_and_surface_core(self) -> None:
        layout = build_brood_moon_orbital_layout()
        body = layout.planet
        self.assertFalse(in_planet_landing_band(body.center, body))
        far = body.center + Vec2(1.0, 0.0) * (body.landing_band_outer + 80.0)
        self.assertFalse(in_planet_landing_band(far, body))

    def test_limb_hint_faces_ship(self) -> None:
        body = PlanetBody.from_surface_radius(MOON_CENTER, MOON_RADIUS)
        ship = Vec2(620.0, 1580.0)
        limb = limb_point_toward(ship, body)
        self.assertAlmostEqual((limb - body.center).length(), body.surface_radius, places=3)


class PlanetLandingBandVizTests(unittest.TestCase):
    def test_in_band_tactical_rings_avoid_mass_fill_overlays(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")

        from gravity_ho_matey.levels.level_registry import build_level
        from gravity_ho_matey.render.camera import CameraMode, ViewCamera
        from gravity_ho_matey.render.planet_mission_viz import draw_planet_landing_band_tactical

        world = build_level("brood_moon")
        layout = world.brood_moon
        assert layout is not None and layout.layout is not None
        body = layout.layout.planet
        ship_pos = body.center + Vec2.from_angle(0.9) * (body.surface_radius + 90.0)
        self.assertTrue(in_planet_landing_band(ship_pos, body))

        camera = ViewCamera(mode=CameraMode.TACTICAL)
        camera.snap_tactical_to_ship(ship_pos, world.config)
        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            draw_planet_landing_band_tactical(
                canvas,
                body,
                camera=camera,
                ship_pos=ship_pos,
                ship_angle=0.0,
                hud_top=54.0,
                accent="#c878ff",
                dim="#5a7a94",
                elapsed=1.25,
                show_fog=False,
                show_rings=True,
            )
            for item in canvas.find_all():
                if canvas.type(item) != "oval":
                    continue
                stipple = canvas.itemcget(item, "stipple")
                fill = canvas.itemcget(item, "fill")
                self.assertNotEqual(stipple, "gray25", msg="filled stipple disk blinds gameplay")
                if fill and fill not in ("", " "):
                    outline = canvas.itemcget(item, "outline")
                    self.assertTrue(outline, msg="filled ovals must not cover the playfield")
            self.assertGreater(len(canvas.find_all()), 2)
        finally:
            root.destroy()

    def test_brood_orbital_tactical_draw_keeps_asteroids_above_moon_fog(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")

        from gravity_ho_matey.gameplay.gravity_field import GravityField
        from gravity_ho_matey.levels.level_registry import build_level
        from gravity_ho_matey.render.camera import CameraMode, ViewCamera
        from gravity_ho_matey.render.view_renderers import TacticalViewRenderer

        world = build_level("brood_moon")
        layout = world.brood_moon
        assert layout is not None and layout.layout is not None
        body = layout.layout.planet
        world.ship.pos = body.center + Vec2.from_angle(1.1) * (body.surface_radius + 95.0)
        field = GravityField.bake(
            world.wells,
            world_width=world.config.width,
            world_height=world.config.height,
            cols=24,
            rows=24,
            gravity_scale=world.config.gravity_scale,
        )
        camera = ViewCamera(mode=CameraMode.TACTICAL)
        camera.snap_tactical_to_ship(world.ship.pos, world.config)
        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            TacticalViewRenderer().draw(canvas, world, camera, field, hud_top=54)
            ovals = [i for i in canvas.find_all() if canvas.type(i) == "oval"]
            stippled = [i for i in ovals if canvas.itemcget(i, "stipple") == "gray25"]
            self.assertEqual(stippled, [])
            self.assertGreater(len(ovals), 0)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
