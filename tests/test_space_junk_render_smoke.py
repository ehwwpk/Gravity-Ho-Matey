import unittest
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.space_junk_prefabs import PREFAB_REGISTRY, instantiate_junk
from gravity_ho_matey.render.camera import CameraMode, ViewCamera
from gravity_ho_matey.render.lighting import LightRig
from gravity_ho_matey.render.space_junk_viz import draw_chase_junk, draw_tactical_junk


class SpaceJunkRenderSmokeTests(unittest.TestCase):
    def test_draw_all_prefabs_without_error(self) -> None:
        root = tk.Tk()
        root.withdraw()
        canvas = tk.Canvas(root, width=640, height=480)
        camera = ViewCamera(mode=CameraMode.TACTICAL, viewport_width=640, viewport_height=480)
        rig = LightRig.for_play(theme="drift", camera_mode=CameraMode.TACTICAL)
        ship_pos = Vec2(320, 240)
        for prefab_id in PREFAB_REGISTRY:
            junk = instantiate_junk(prefab_id, Vec2(320, 240))
            draw_tactical_junk(
                canvas,
                junk,
                camera=camera,
                ship_pos=ship_pos,
                hud_top=0.0,
                rig=rig,
                ship_angle=0.0,
                theme="drift",
            )
            draw_chase_junk(
                canvas,
                junk,
                camera=camera,
                ship_pos=ship_pos,
                ship_angle=0.0,
                rig=rig,
                theme="drift",
                elapsed=0.5,
            )
        root.destroy()


if __name__ == "__main__":
    unittest.main()
