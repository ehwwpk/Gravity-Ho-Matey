from __future__ import annotations

import math
import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.brood_moon_controller import apply_surface_layout
from gravity_ho_matey.levels.brood_moon_layout import SURFACE_WRAP_WIDTH
from gravity_ho_matey.levels.level_registry import build_level
from gravity_ho_matey.render.camera import CameraMode, ViewCamera
from gravity_ho_matey.render.edge_hints import _maybe_hint


class PlanetsideEdgeHintTests(unittest.TestCase):
    def test_wrapped_pod_hint_uses_shortest_toroidal_direction(self) -> None:
        world = build_level("brood_moon")
        apply_surface_layout(world)
        ship = Vec2(200.0, 1200.0)
        pod = Vec2(8000.0, 1200.0)

        camera = ViewCamera(
            mode=CameraMode.TACTICAL,
            viewport_width=960,
            viewport_height=640,
            tactical_scale=0.42,
        )
        camera.center = ship

        def hint_angle(wrap_width: float) -> float | None:
            hints: list[tuple[float, str, str]] = []
            _maybe_hint(
                hints,
                camera,
                pod,
                ship,
                0.0,
                "EG",
                "#ffffff",
                960.0,
                640.0,
                48.0,
                wrap_width=wrap_width,
            )
            return hints[0][0] if hints else None

        raw = hint_angle(0.0)
        wrapped = hint_angle(float(SURFACE_WRAP_WIDTH))
        assert raw is not None and wrapped is not None
        self.assertAlmostEqual(raw, 0.0, delta=0.35)
        self.assertAlmostEqual(abs(wrapped), math.pi, delta=0.35)

    def test_on_screen_pod_gets_no_hint(self) -> None:
        world = build_level("brood_moon")
        apply_surface_layout(world)
        world.ship.pos = Vec2(500.0, 1200.0)
        pod = next(pod for pod in world.egg_pods if pod.alive)
        pod.pos = Vec2(620.0, 1235.0)

        camera = ViewCamera(
            mode=CameraMode.TACTICAL,
            viewport_width=960,
            viewport_height=640,
            tactical_scale=0.42,
        )
        camera.center = world.ship.pos
        hints: list[tuple[float, str, str]] = []
        _maybe_hint(
            hints,
            camera,
            pod.pos,
            world.ship.pos,
            world.ship.angle,
            "EG",
            "#ffffff",
            960.0,
            640.0,
            48.0,
            wrap_width=float(SURFACE_WRAP_WIDTH),
        )
        self.assertEqual(hints, [])

    def test_boss_rim_hint_when_spawned_off_screen(self) -> None:
        from gravity_ho_matey.gameplay.mega_squid_boss import MegaSquidBoss
        from gravity_ho_matey.levels.brood_moon_surface import boss_anchor
        from gravity_ho_matey.render.edge_hints import draw_edge_hints

        world = build_level("brood_moon")
        apply_surface_layout(world)
        bm = world.brood_moon
        assert bm is not None
        bm.boss_spawned = True
        anchor = boss_anchor()
        world.mega_squid = MegaSquidBoss(pos=anchor, anchor=anchor)
        world.ship.pos = Vec2(400.0, 1200.0)

        camera = ViewCamera(
            mode=CameraMode.TACTICAL,
            viewport_width=960,
            viewport_height=640,
            tactical_scale=0.42,
        )
        camera.center = world.ship.pos

        try:
            import tkinter as tk

            root = tk.Tk()
        except tk.TclError as exc:
            raise unittest.SkipTest(f"Tk unavailable: {exc}") from exc
        root.withdraw()
        canvas = tk.Canvas(root, width=960, height=640)
        draw_edge_hints(canvas, world, camera, hud_top=48.0)
        text_items = [canvas.itemcget(i, "text") for i in canvas.find_all() if canvas.type(i) == "text"]
        self.assertIn("BOSS", text_items)
        root.destroy()


if __name__ == "__main__":
    unittest.main()
