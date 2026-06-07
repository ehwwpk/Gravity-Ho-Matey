import unittest
import tkinter as tk
from unittest.mock import patch

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
                overlay.draw(
                    canvas,
                    page=page,
                    solar_unlocked=False,
                    drift_unlocked=False,
                    draw_ship=lambda _x, _y: None,
                )
            overlay.draw(
                canvas,
                page=TitlePage.DEPLOY,
                solar_unlocked=True,
                drift_unlocked=True,
                draw_ship=lambda _x, _y: None,
            )
        finally:
            root.destroy()

    def test_solar_unlock_reflected_in_progress_gate(self) -> None:
        with patch("gravity_ho_matey.gameplay.progress.DEV_UNLOCK_ALL_LEVELS", False):
            self.assertFalse(is_level_selectable("solar"))
            record_level_cleared("cove")
            self.assertTrue(is_level_selectable("solar"))

    def test_drift_unlock_reflected_in_progress_gate(self) -> None:
        with patch("gravity_ho_matey.gameplay.progress.DEV_UNLOCK_ALL_LEVELS", False):
            self.assertFalse(is_level_selectable("drift"))
            record_level_cleared("solar")
            self.assertTrue(is_level_selectable("drift"))

    def test_dev_unlock_all_levels_bypasses_progress(self) -> None:
        with patch("gravity_ho_matey.gameplay.progress.DEV_UNLOCK_ALL_LEVELS", True):
            reset_progress()
            self.assertTrue(is_level_selectable("cove"))
            self.assertTrue(is_level_selectable("solar"))
            self.assertTrue(is_level_selectable("drift"))

    def test_title_hit_map_registers_level_rows(self) -> None:
        root, canvas = _canvas()
        overlay = TitleScreenOverlay()
        try:
            overlay.draw(
                canvas,
                page=TitlePage.DEPLOY,
                solar_unlocked=True,
                drift_unlocked=True,
                draw_ship=lambda _x, _y: None,
            )
            self.assertIsNotNone(overlay.hits.hit(480, 200))
            self.assertTrue(any(r.id.startswith("level:") for r in overlay.hits.regions))
        finally:
            root.destroy()


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
