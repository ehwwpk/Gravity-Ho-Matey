from __future__ import annotations

import math
import unittest

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.squid_enemy import SQUID_TENTACLE_COUNT, SquidEnemy
from gravity_ho_matey.render.camera import CameraMode, ViewCamera
from gravity_ho_matey.render.lighting import LightRig
from gravity_ho_matey.render.squid_viz import (
    _mantle_pulse,
    _mantle_screen_points,
    draw_squid_enemy_tactical,
)


class SquidSimTests(unittest.TestCase):
    def test_tentacle_mid_initialized(self) -> None:
        squid = SquidEnemy(pos=Vec2(100, 100))
        squid._ensure_tentacles()
        self.assertEqual(len(squid.tentacle_mid), SQUID_TENTACLE_COUNT)

    def test_tentacle_update_advances_wobble(self) -> None:
        squid = SquidEnemy(pos=Vec2(100, 100))
        before = squid.tentacle_wobble
        squid.update_tentacles(0.1, Vec2(400, 100), 12.0)
        self.assertGreater(squid.tentacle_wobble, before)
        self.assertEqual(len(squid.tentacle_mid), SQUID_TENTACLE_COUNT)


class SquidVizTests(unittest.TestCase):
    def test_mantle_pulse_in_range(self) -> None:
        self.assertGreater(_mantle_pulse(1.0, engaging=False), 0.9)
        self.assertLess(_mantle_pulse(1.0, engaging=True), 1.15)

    def test_mantle_screen_points_follow_facing(self) -> None:
        forward = _mantle_screen_points(100, 100, 0.0, 18.0, 1.0)
        turned = _mantle_screen_points(100, 100, math.pi / 2.0, 18.0, 1.0)
        self.assertNotEqual(forward[0], turned[0])

    def test_tactical_draw_rich_enough(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest("Tk unavailable")
        root.withdraw()
        canvas = tk.Canvas(root, width=960, height=640)
        squid = SquidEnemy(pos=Vec2(2000.0, 1600.0))
        squid.update_tentacles(0.05, Vec2(2000.0, 1750.0), 12.0)
        camera = ViewCamera(mode=CameraMode.TACTICAL)
        camera.set_play_layout(54.0)
        rig = LightRig.for_play(theme="rift", camera_mode=CameraMode.TACTICAL)
        draw_squid_enemy_tactical(
            canvas,
            squid,
            camera=camera,
            ship_pos=Vec2(2000.0, 1750.0),
            ship_radius=12.0,
            hud_top=54.0,
            rig=rig,
            elapsed=1.2,
        )
        self.assertGreater(len(canvas.find_all()), 30)
        root.destroy()


if __name__ == "__main__":
    unittest.main()
