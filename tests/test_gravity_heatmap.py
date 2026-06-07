import unittest

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import FinishGate, Ship, WorldConfig
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render.camera import CameraMode, ViewCamera
from gravity_ho_matey.render.world_draw import draw_gravity_heatmap


class GravityHeatmapTests(unittest.TestCase):
    def test_tactical_heatmap_uses_projected_cell_size_not_world_units(self) -> None:
        try:
            import tkinter as tk
        except tk.TclError:
            self.skipTest("Tk unavailable")

        world = GameWorld(
            config=WorldConfig(width=4800, height=3200, viewport_width=960, viewport_height=640),
            ship=Ship(pos=Vec2(2400, 1600)),
            asteroids=[],
            wells=[],
            beacons=[],
            finish_gate=FinishGate(Rect(0, 0, 10, 10)),
        )
        field = GravityField.bake(
            world.wells,
            world_width=world.config.width,
            world_height=world.config.height,
            cols=32,
            rows=32,
            gravity_scale=world.config.gravity_scale,
        )
        camera = ViewCamera(mode=CameraMode.TACTICAL)
        camera.set_play_layout(54)
        camera.update_follow(world.ship.pos, world.config, 0.016)

        root = tk.Tk()
        root.withdraw()
        canvas = tk.Canvas(root, width=960, height=640)
        draw_gravity_heatmap(canvas, field, camera, y_offset=54, alpha_step=4, ship_pos=world.ship.pos)

        max_span = 0.0
        for item in canvas.find_all():
            if canvas.type(item) != "oval":
                continue
            x0, y0, x1, y1 = canvas.coords(item)
            max_span = max(max_span, abs(x1 - x0), abs(y1 - y0))

        root.destroy()
        self.assertLess(max_span, 120.0, msg=f"heatmap ovals should be screen-sized, got {max_span}px span")


if __name__ == "__main__":
    unittest.main()
