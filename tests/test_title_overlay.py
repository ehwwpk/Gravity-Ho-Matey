import unittest
import tkinter as tk

from gravity_ho_matey.gameplay.progress import is_level_selectable, record_level_cleared, reset_progress
from gravity_ho_matey.render.title_overlay import TitleScreenOverlay


class TitleOverlayTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_progress()

    def tearDown(self) -> None:
        reset_progress()

    def test_draw_title_layout_does_not_raise(self) -> None:
        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            TitleScreenOverlay().draw(canvas, solar_unlocked=False)
            TitleScreenOverlay().draw(canvas, solar_unlocked=True, draw_ship=lambda _x, _y: None)
        finally:
            root.destroy()

    def test_solar_unlock_reflected_in_progress_gate(self) -> None:
        self.assertFalse(is_level_selectable("solar"))
        record_level_cleared("cove")
        self.assertTrue(is_level_selectable("solar"))


if __name__ == "__main__":
    unittest.main()
