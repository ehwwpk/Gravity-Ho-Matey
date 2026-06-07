from __future__ import annotations

import unittest

from gravity_ho_matey.levels.level_registry import LEVEL_ORDER
from gravity_ho_matey.render.title_deploy_list import (
    compute_deploy_list_layout,
    row_visible,
    scroll_to_show_index,
    scroll_wheel_delta,
    title_chrome_layout,
)


class TitleDeployListTests(unittest.TestCase):
    def test_six_levels_require_scroll(self) -> None:
        chrome = title_chrome_layout(
            screen_h=640.0,
            top_bar_h=54.0,
            footer_h=52.0,
            rail_h=24.0,
            shop_h=36.0,
        )
        layout = compute_deploy_list_layout(chrome, screen_w=960.0)
        self.assertEqual(layout.level_count, len(LEVEL_ORDER))
        self.assertGreater(layout.content_h, layout.viewport_h)
        self.assertGreater(layout.max_scroll, 0.0)

    def test_scroll_reveals_last_level(self) -> None:
        chrome = title_chrome_layout(
            screen_h=640.0,
            top_bar_h=54.0,
            footer_h=52.0,
            rail_h=24.0,
            shop_h=36.0,
        )
        layout = compute_deploy_list_layout(chrome, screen_w=960.0)
        scroll = scroll_to_show_index(0.0, layout, len(LEVEL_ORDER) - 1)
        self.assertTrue(row_visible(layout, len(LEVEL_ORDER) - 1, scroll))

    def test_chrome_zones_do_not_overlap(self) -> None:
        chrome = title_chrome_layout(
            screen_h=640.0,
            top_bar_h=54.0,
            footer_h=52.0,
            rail_h=24.0,
            shop_h=36.0,
        )
        self.assertLess(chrome.body_bottom, chrome.shop_y)
        self.assertLess(chrome.shop_y + chrome.shop_h, chrome.rail_y)
        self.assertLess(chrome.rail_y + chrome.rail_h, chrome.footer_y)

    def test_visible_row_hit_rect_clips_bleed(self) -> None:
        from gravity_ho_matey.render.title_deploy_list import (
            row_screen_y,
            visible_row_hit_rect,
        )

        chrome = title_chrome_layout(
            screen_h=640.0,
            top_bar_h=54.0,
            footer_h=52.0,
            rail_h=24.0,
            shop_h=36.0,
        )
        layout = compute_deploy_list_layout(chrome, screen_w=960.0)
        scroll = scroll_to_show_index(0.0, layout, len(LEVEL_ORDER) - 1)
        ry = row_screen_y(layout, len(LEVEL_ORDER) - 1, scroll)
        hit = visible_row_hit_rect(layout, len(LEVEL_ORDER) - 1, scroll)
        self.assertIsNotNone(hit)
        _, hy, _, hh = hit
        self.assertGreaterEqual(hy, layout.viewport_y)
        self.assertLessEqual(hy + hh, layout.viewport_y + layout.viewport_h)
        self.assertLess(ry + layout.row_h, layout.viewport_y + layout.viewport_h + 1)

    def test_wheel_delta_clamps(self) -> None:
        chrome = title_chrome_layout(
            screen_h=640.0,
            top_bar_h=54.0,
            footer_h=52.0,
            rail_h=24.0,
            shop_h=36.0,
        )
        layout = compute_deploy_list_layout(chrome, screen_w=960.0)
        scrolled = scroll_wheel_delta(layout.max_scroll, layout, 1)
        self.assertAlmostEqual(scrolled, layout.max_scroll)
        back = scroll_wheel_delta(0.0, layout, -1)
        self.assertAlmostEqual(back, 0.0)


if __name__ == "__main__":
    unittest.main()
