import unittest
import tkinter as tk

from gravity_ho_matey.render.title_deploy_list import title_chrome_layout, compute_deploy_split_layout
from gravity_ho_matey.render.title_info_pages import draw_combat_page, draw_helm_page, draw_mission_page
from gravity_ho_matey.render.title_overlay import TitlePage, TitleScreenOverlay


def _canvas():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise unittest.SkipTest(f"Tk unavailable: {exc}") from exc
    root.withdraw()
    return root, tk.Canvas(root, width=960, height=640)


class TitleInfoPageTests(unittest.TestCase):
    def test_mission_page_shows_campaign_arc(self) -> None:
        root, canvas = _canvas()
        chrome = title_chrome_layout(
            screen_h=640.0, top_bar_h=54.0, footer_h=52.0, rail_h=24.0, shop_h=36.0,
        )
        draw_mission_page(canvas, chrome, screen_w=960.0, accent="#7cff7a", dim="#608080", frame="#304050", elapsed=1.0)
        joined = " ".join(
            str(canvas.itemcget(i, "text")) for i in canvas.find_all() if canvas.type(i) == "text" and canvas.itemcget(i, "text")
        )
        self.assertIn("CAMPAIGN ARC", joined)
        self.assertIn("Brood Moon", joined)
        self.assertIn("YOUR CONTRACT", joined)
        root.destroy()

    def test_helm_page_shows_key_badges(self) -> None:
        root, canvas = _canvas()
        chrome = title_chrome_layout(
            screen_h=640.0, top_bar_h=54.0, footer_h=52.0, rail_h=24.0, shop_h=36.0,
        )
        draw_helm_page(canvas, chrome, screen_w=960.0, accent="#7cff7a", dim="#608080", frame="#304050", elapsed=1.0)
        joined = " ".join(
            str(canvas.itemcget(i, "text")) for i in canvas.find_all() if canvas.type(i) == "text" and canvas.itemcget(i, "text")
        )
        self.assertIn("FLIGHT", joined)
        self.assertIn("Shift", joined)
        self.assertIn("Holo Bazaar", joined)
        root.destroy()

    def test_combat_page_shows_weapon_doctrines(self) -> None:
        root, canvas = _canvas()
        chrome = title_chrome_layout(
            screen_h=640.0, top_bar_h=54.0, footer_h=52.0, rail_h=24.0, shop_h=36.0,
        )
        draw_combat_page(canvas, chrome, screen_w=960.0, accent="#7cff7a", dim="#608080", frame="#304050", elapsed=1.0)
        joined = " ".join(
            str(canvas.itemcget(i, "text")) for i in canvas.find_all() if canvas.type(i) == "text" and canvas.itemcget(i, "text")
        )
        self.assertIn("WEAPON DOCTRINES", joined)
        self.assertIn("LANCE", joined)
        self.assertIn("SCATTER", joined)
        self.assertIn("NOVA", joined)
        self.assertIn("Prismatic Lance", joined)
        self.assertIn("Triple Tap", joined)
        self.assertIn("Supernova", joined)
        root.destroy()

    def test_deploy_split_layout_has_preview_pane(self) -> None:
        chrome = title_chrome_layout(
            screen_h=640.0, top_bar_h=54.0, footer_h=52.0, rail_h=24.0, shop_h=36.0,
        )
        split = compute_deploy_split_layout(chrome, screen_w=960.0)
        self.assertGreater(split.preview.w, 200.0)
        self.assertLess(split.list.panel_w, 620.0)

    def test_deploy_page_shows_sector_dossier(self) -> None:
        root, canvas = _canvas()
        overlay = TitleScreenOverlay()
        from gravity_ho_matey.gameplay.campaign import CampaignState

        overlay.draw(
            canvas,
            page=TitlePage.DEPLOY,
            campaign=CampaignState.new(),
            solar_unlocked=True,
            deploy_focus=0,
        )
        joined = " ".join(
            str(canvas.itemcget(i, "text")) for i in canvas.find_all() if canvas.type(i) == "text" and canvas.itemcget(i, "text")
        )
        self.assertIn("SECTOR DOSSIER", joined)
        self.assertIn("Smuggler", joined)
        root.destroy()


if __name__ == "__main__":
    unittest.main()
