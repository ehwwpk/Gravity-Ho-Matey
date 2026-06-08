import unittest
import tkinter as tk
from unittest.mock import patch

from gravity_ho_matey.gameplay.progress import is_level_selectable, record_level_cleared, reset_progress
from gravity_ho_matey.gameplay.campaign import CampaignState
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

    def test_page_rail_shows_full_tab_labels(self) -> None:
        root, canvas = _canvas()
        overlay = TitleScreenOverlay()
        campaign = CampaignState.new()
        overlay.draw(
            canvas,
            page=TitlePage.WELCOME,
            campaign=campaign,
            solar_unlocked=True,
            drift_unlocked=True,
            elapsed=1.0,
        )
        texts = [canvas.itemcget(i, "text") for i in canvas.find_all() if canvas.type(i) == "text"]
        joined = " ".join(str(t) for t in texts if t)
        for label in ("WELCOME", "MISSION", "CONTROLS", "COMBAT", "SELECT LEVEL", "HOLO BAZAAR", "MERCHANT TREE"):
            self.assertIn(label, joined, msg=f"missing tab/shop label: {label}")
        for bad in ("WELCO…", "WELCO...", "MISSI…", "SELEC…"):
            self.assertNotIn(bad, joined)
        root.destroy()

    def test_each_terminal_page_draws_without_error(self) -> None:
        root, canvas = _canvas()
        overlay = TitleScreenOverlay()
        campaign = CampaignState.new()
        try:
            for page in TITLE_PAGE_ORDER:
                overlay.draw(
                    canvas,
                    page=page,
                    campaign=campaign,
                    solar_unlocked=False,
                    drift_unlocked=False,
                )
            overlay.draw(
                canvas,
                page=TitlePage.DEPLOY,
                campaign=campaign,
                solar_unlocked=True,
                drift_unlocked=True,
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

    def test_brood_moon_row_hit_when_scrolled(self) -> None:
        from gravity_ho_matey.levels.level_registry import LEVEL_ORDER
        from gravity_ho_matey.render.title_deploy_list import (
            compute_deploy_list_layout,
            row_screen_y,
            scroll_to_show_index,
            title_chrome_layout,
        )

        root, canvas = _canvas()
        overlay = TitleScreenOverlay()
        campaign = CampaignState.new()
        try:
            chrome = title_chrome_layout(
                screen_h=640.0, top_bar_h=54.0, footer_h=52.0, rail_h=24.0, shop_h=36.0,
            )
            layout = compute_deploy_list_layout(chrome, screen_w=960.0)
            scroll = scroll_to_show_index(0.0, layout, len(LEVEL_ORDER) - 1)
            overlay.draw(
                canvas,
                page=TitlePage.DEPLOY,
                campaign=campaign,
                solar_unlocked=True,
                drift_unlocked=True,
                rift_unlocked=True,
                siege_unlocked=True,
                brood_unlocked=True,
                deploy_focus=5,
                deploy_scroll=scroll,
            )
            ry = row_screen_y(layout, 5, scroll) + 20.0
            self.assertEqual(overlay.hits.hit(480, ry), "level:brood_moon")
        finally:
            root.destroy()

    def test_title_hit_map_registers_level_rows(self) -> None:
        root, canvas = _canvas()
        overlay = TitleScreenOverlay()
        campaign = CampaignState.new()
        try:
            overlay.draw(
                canvas,
                page=TitlePage.DEPLOY,
                campaign=campaign,
                solar_unlocked=True,
                drift_unlocked=True,
            )
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

    def test_b_key_toggles_shop(self) -> None:
        scene = TitleScene()
        self.assertFalse(scene.shop_open)
        scene.on_key_press(_FakeHost(), "b")
        self.assertTrue(scene.shop_open)
        scene.on_key_press(_FakeHost(), "b")
        self.assertFalse(scene.shop_open)

    def test_deploy_scroll_follows_focus(self) -> None:
        scene = TitleScene()
        scene.page = TitlePage.DEPLOY
        scene.deploy_focus = 5
        scene._sync_deploy_scroll()
        layout = scene._deploy_layout()
        from gravity_ho_matey.render.title_deploy_list import row_visible

        self.assertTrue(row_visible(layout, 5, scene.deploy_scroll))

    def test_shop_open_blocks_page_navigation(self) -> None:
        scene = TitleScene()
        scene.shop_open = True
        scene.page = TitlePage.WELCOME
        scene.on_key_press(_FakeHost(), "right")
        self.assertEqual(scene.page, TitlePage.WELCOME)

    def test_welcome_goto_deploy_hit_registered(self) -> None:
        root, canvas = _canvas()
        overlay = TitleScreenOverlay()
        try:
            overlay.draw(
                canvas,
                page=TitlePage.WELCOME,
                campaign=CampaignState.new(),
                solar_unlocked=True,
            )
            self.assertEqual(overlay.hits.hit(120, 200), "goto_deploy")
        finally:
            root.destroy()

    def test_title_bazaar_hit_region_registered(self) -> None:
        root, canvas = _canvas()
        overlay = TitleScreenOverlay()
        try:
            overlay.draw(
                canvas,
                page=TitlePage.WELCOME,
                campaign=CampaignState.new(),
                solar_unlocked=True,
            )
            shop = next(r for r in overlay.hits.regions if r.id == "shop_open")
            cx = (shop.x0 + shop.x1) / 2
            cy = (shop.y0 + shop.y1) / 2
            self.assertEqual(overlay.hits.hit(cx, cy), "shop_open")
        finally:
            root.destroy()

    def test_launch_passes_session_campaign(self) -> None:
        from unittest.mock import MagicMock

        from gravity_ho_matey.scenes.chart_briefing import ChartBriefingScene

        host = MagicMock()
        campaign = CampaignState.new()
        campaign.jewels = 42
        scene = TitleScene(campaign=campaign)
        scene._launch_level(host, "cove")
        host.set_scene.assert_called_once()
        next_scene = host.set_scene.call_args[0][0]
        self.assertIsInstance(next_scene, ChartBriefingScene)
        self.assertIs(next_scene.campaign, campaign)
        self.assertEqual(next_scene.campaign.jewels, 42)


class _FakeHost:
    renderer = None


if __name__ == "__main__":
    unittest.main()
