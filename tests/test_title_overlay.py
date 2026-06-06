import unittest
import tkinter as tk

from gravity_ho_matey.gameplay.progress import is_level_selectable, record_level_cleared, reset_progress
from gravity_ho_matey.render.title_overlay import TITLE_PAGE_ORDER, TitlePage, TitleScreenOverlay
from gravity_ho_matey.scenes.title import TitleScene


def _canvas():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise unittest.SkipTest(f"Tk unavailable: {exc}") from exc
    root.withdraw()
    return root, tk.Canvas(root, width=960, height=640)


class TitleOverlayTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_progress()

    def tearDown(self) -> None:
        reset_progress()

    def test_each_terminal_page_draws_without_error(self) -> None:
        root, canvas = _canvas()
        overlay = TitleScreenOverlay()
        try:
            for page in TITLE_PAGE_ORDER:
                overlay.draw(canvas, page=page, solar_unlocked=False, draw_ship=lambda _x, _y: None)
            overlay.draw(canvas, page=TitlePage.DEPLOY, solar_unlocked=True, draw_ship=lambda _x, _y: None)
        finally:
            root.destroy()

    def test_solar_unlock_reflected_in_progress_gate(self) -> None:
        self.assertFalse(is_level_selectable("solar"))
        record_level_cleared("cove")
        self.assertTrue(is_level_selectable("solar"))


class TitleSceneTests(unittest.TestCase):
    def test_page_navigation_wraps(self) -> None:
        scene = TitleScene()
        self.assertEqual(scene.page, TitlePage.WELCOME)
        scene._step_page(-1)
        self.assertEqual(scene.page, TitlePage.DEPLOY)
        scene._step_page(1)
        self.assertEqual(scene.page, TitlePage.WELCOME)


if __name__ == "__main__":
    unittest.main()
