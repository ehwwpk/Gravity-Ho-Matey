from __future__ import annotations

import unittest

from gravity_ho_matey.render.title_home_layout import (
    BODY_MARGIN,
    compute_body_panel,
    compute_welcome_home_layout,
    compute_welcome_left_layout,
)
from gravity_ho_matey.render.title_overlay import TitleScreenOverlay


class TitleHomeLayoutTests(unittest.TestCase):
    def _chrome(self):
        return TitleScreenOverlay.chrome_layout()

    def test_body_panel_fills_chrome_body(self) -> None:
        chrome = self._chrome()
        panel = compute_body_panel(chrome, screen_w=960.0)
        self.assertAlmostEqual(panel.x, BODY_MARGIN)
        self.assertAlmostEqual(panel.y, chrome.body_top)
        self.assertAlmostEqual(panel.w, 960.0 - BODY_MARGIN * 2.0)
        self.assertAlmostEqual(panel.h, chrome.body_bottom - chrome.body_top)

    def test_welcome_hangar_uses_majority_of_panel(self) -> None:
        chrome = self._chrome()
        layout = compute_welcome_home_layout(chrome, screen_w=960.0)
        self.assertGreater(layout.hangar_w, layout.left_w)
        self.assertGreater(layout.deck_y, layout.panel.y + layout.panel.h * 0.75)

    def test_welcome_left_block_fits_inside_panel(self) -> None:
        chrome = self._chrome()
        layout = compute_welcome_home_layout(chrome, screen_w=960.0)
        left = compute_welcome_left_layout(layout.panel, layout.left_x, layout.left_w)
        self.assertGreaterEqual(left.pitch_y, layout.panel.y)
        self.assertLessEqual(left.btn_y + left.btn_h, layout.panel.y + layout.panel.h)

    def test_welcome_ship_sits_in_hangar_column(self) -> None:
        chrome = self._chrome()
        layout = compute_welcome_home_layout(chrome, screen_w=960.0)
        self.assertGreaterEqual(layout.ship_x, layout.hangar_x)
        self.assertLessEqual(layout.ship_x, layout.hangar_x + layout.hangar_w)


if __name__ == "__main__":
    unittest.main()
