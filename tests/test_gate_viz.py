import tkinter as tk
import unittest

from gravity_ho_matey.render.camera import CameraMode
from gravity_ho_matey.render.gate_viz import draw_gate_portal_map, draw_gate_portal_play
from gravity_ho_matey.render.lighting import LightRig


def _tk_canvas():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise unittest.SkipTest(f"Tk unavailable: {exc}") from exc
    root.withdraw()
    return root, tk.Canvas(root, width=960, height=640)


class GateVizTests(unittest.TestCase):
    def test_locked_portal_draws_layers(self) -> None:
        root, canvas = _tk_canvas()
        rig = LightRig.for_play(theme="cove", camera_mode=CameraMode.TACTICAL)
        draw_gate_portal_play(
            canvas,
            480.0,
            320.0,
            size=54.0,
            unlocked=False,
            solar=False,
            scale=1.0,
            rig=rig,
            elapsed=2.0,
            label="LOCK",
        )
        self.assertGreater(len(canvas.find_all()), 8)
        root.destroy()

    def test_open_wormhole_chase_draws_layers(self) -> None:
        root, canvas = _tk_canvas()
        rig = LightRig.for_play(theme="solar", camera_mode=CameraMode.CHASE)
        draw_gate_portal_play(
            canvas,
            480.0,
            320.0,
            size=50.0,
            unlocked=True,
            solar=True,
            scale=1.1,
            rig=rig,
            elapsed=1.5,
            label="WORMHOLE",
        )
        self.assertGreater(len(canvas.find_all()), 12)
        root.destroy()

    def test_map_glyph_compact(self) -> None:
        root, canvas = _tk_canvas()
        draw_gate_portal_map(
            canvas,
            120.0,
            80.0,
            size=54.0,
            unlocked=False,
            solar=False,
            scale=0.35,
            label="LOCK",
        )
        self.assertGreater(len(canvas.find_all()), 4)
        root.destroy()


if __name__ == "__main__":
    unittest.main()
