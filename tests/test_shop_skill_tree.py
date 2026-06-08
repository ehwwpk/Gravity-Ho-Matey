from __future__ import annotations

import unittest

try:
    import tkinter as tk
except tk.TclError:
    tk = None  # type: ignore[assignment]

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.shop_catalog import shop_hit_id
from gravity_ho_matey.render.holo_shop_overlay import HoloShopOverlay
from gravity_ho_matey.render.menu_ui import MenuHitMap, fit_text_to_width, measure_text
from gravity_ho_matey.render.shop_tree_view import ShopTreeView, ZOOM_DEFAULT, apply_shop_tree_view
from gravity_ho_matey.scenes.shop_ui import ShopUiState, shop_on_pointer_down, shop_on_pointer_motion
from gravity_ho_matey.render.shop_skill_tree_layout import (
    compute_fit_viewport,
    compute_viewport,
    node_bounds,
    node_screen_center,
    nodes_overlap,
    shop_tree_rect,
    skill_tree_nodes,
)


def _panel_tree_viewport(campaign: CampaignState, *, open_anim: float = 1.0, view: ShopTreeView | None = None):
    px, py, pw, ph = 20.0, 8.0, 920.0, 624.0
    left, top, width, height = shop_tree_rect(px, py, pw, ph)
    nodes = skill_tree_nodes(campaign)
    viewport = compute_viewport(
        nodes,
        left=left,
        top=top,
        width=width,
        height=height,
        open_anim=open_anim,
        view=view or ShopTreeView(zoom=1.0),
    )
    return px, py, pw, ph, nodes, viewport


@unittest.skipIf(tk is None, "Tk unavailable")
class ShopSkillTreeLayoutTests(unittest.TestCase):
    def test_all_base_nodes_within_panel(self) -> None:
        campaign = CampaignState.new()
        campaign.jewels = 99
        px, py, pw, ph, nodes, viewport = _panel_tree_viewport(campaign)
        margin = 2.0
        for node in nodes:
            x, y, w, h = node_bounds(viewport, node)
            self.assertGreaterEqual(x, px + margin, msg=node.kind.name)
            self.assertGreaterEqual(y, py + margin, msg=node.kind.name)
            self.assertLessEqual(x + w, px + pw - margin, msg=node.kind.name)
            self.assertLessEqual(y + h, py + ph - margin, msg=node.kind.name)

    def test_nodes_do_not_overlap(self) -> None:
        cases = [
            CampaignState.new(),
            CampaignState.new(),
        ]
        cases[1].drone_wingman_pending = True
        from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack

        adv = CampaignState.new()
        adv.weapon_track = WeaponTrack.SHOTGUN
        cases.append(adv)
        for campaign in cases:
            _, _, _, _, nodes, viewport = _panel_tree_viewport(campaign)
            self.assertFalse(nodes_overlap(viewport, nodes), msg=f"overlap {campaign}")

    def test_drone_branch_adds_nodes_when_contract_active(self) -> None:
        base = skill_tree_nodes(CampaignState.new())
        contracted = CampaignState.new()
        contracted.drone_wingman_pending = True
        self.assertEqual(len(base), 9)
        self.assertEqual(len(skill_tree_nodes(contracted)), 11)

    def test_weapon_doctrine_shows_advanced_node(self) -> None:
        from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack

        campaign = CampaignState.new()
        self.assertEqual(len(skill_tree_nodes(campaign)), 9)
        campaign.weapon_track = WeaponTrack.SHOTGUN
        self.assertEqual(len(skill_tree_nodes(campaign)), 10)
        campaign.weapon_advanced = True
        self.assertEqual(len(skill_tree_nodes(campaign)), 9)

    def test_open_anim_starts_zoomed_out(self) -> None:
        campaign = CampaignState.new()
        _, _, _, _, nodes, full = _panel_tree_viewport(campaign, open_anim=1.0, view=ShopTreeView(zoom=1.0))
        _, _, _, _, _, opening = _panel_tree_viewport(campaign, open_anim=0.0, view=ShopTreeView(zoom=1.0))
        self.assertGreater(full.scale, opening.scale)
        self.assertFalse(nodes_overlap(opening, nodes))

    def test_default_shop_zoom_is_readable(self) -> None:
        campaign = CampaignState.new()
        _, _, _, _, _, fit = _panel_tree_viewport(campaign, view=ShopTreeView(zoom=1.0))
        _, _, _, _, _, zoomed = _panel_tree_viewport(campaign, view=ShopTreeView())
        self.assertGreater(zoomed.scale, fit.scale)
        self.assertAlmostEqual(ShopTreeView().zoom, ZOOM_DEFAULT)

    def test_shop_view_zoom_at_point(self) -> None:
        campaign = CampaignState.new()
        left, top, width, height = shop_tree_rect(20.0, 8.0, 920.0, 624.0)
        nodes = skill_tree_nodes(campaign)
        fit = compute_fit_viewport(nodes, left=left, top=top, width=width, height=height, open_anim=1.0)
        view = ShopTreeView(zoom=1.0)
        before = apply_shop_tree_view(fit, view)
        view.zoom_by(1.5, mx=480.0, my=320.0, fit=fit)
        after = apply_shop_tree_view(fit, view)
        self.assertGreater(after.scale, before.scale)

    def test_overlay_registers_clickable_nodes(self) -> None:
        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            hits = MenuHitMap()
            campaign = CampaignState.new()
            campaign.jewels = 80
            view = ShopTreeView()
            HoloShopOverlay().draw(
                canvas,
                vw=960,
                vh=640,
                campaign=campaign,
                hits=hits,
                hover_id=None,
                shop_open_anim=1.0,
                shop_view=view,
            )
            _, _, _, _, nodes, viewport = _panel_tree_viewport(campaign, view=view)
            thrust = next(n for n in nodes if n.kind is PowerUpKind.THRUST_BOOST)
            nx, ny = node_screen_center(viewport, thrust)
            self.assertEqual(hits.hit(nx, ny), shop_hit_id(PowerUpKind.THRUST_BOOST))
            self.assertIsNotNone(hits.hit(20 + 920 - 50, 8 + 624 - 24))
        finally:
            root.destroy()

    def test_tree_pan_drag_moves_view(self) -> None:
        state = ShopUiState()
        shop_on_pointer_down(state, 400.0, 300.0, "shop_tree_pan", shop_open=True)
        self.assertTrue(state.dragging)
        shop_on_pointer_motion(state, 420.0, 310.0, shop_open=True)
        self.assertAlmostEqual(state.view.pan_x, 20.0)
        self.assertAlmostEqual(state.view.pan_y, 10.0)

    def test_node_hit_does_not_start_pan_drag(self) -> None:
        state = ShopUiState()
        shop_on_pointer_down(state, 400.0, 300.0, shop_hit_id(PowerUpKind.THRUST_BOOST), shop_open=True)
        self.assertFalse(state.dragging)

    def test_inspector_hidden_until_node_clicked(self) -> None:
        root = tk.Tk()
        root.withdraw()
        try:
            canvas = tk.Canvas(root, width=960, height=640)
            hits = MenuHitMap()
            campaign = CampaignState.new()
            ui = ShopUiState()
            HoloShopOverlay().draw(
                canvas,
                vw=960,
                vh=640,
                campaign=campaign,
                hits=hits,
                hover_id=None,
                shop_open_anim=1.0,
                shop_ui=ui,
            )
            self.assertNotIn("NODE INSPECTOR", " ".join(
                str(canvas.itemcget(i, "text")) for i in canvas.find_all() if canvas.type(i) == "text"
            ))
            ui.inspector_hit = shop_hit_id(PowerUpKind.THRUST_BOOST)
            canvas.delete("all")
            hits.clear()
            HoloShopOverlay().draw(
                canvas,
                vw=960,
                vh=640,
                campaign=campaign,
                hits=hits,
                hover_id=None,
                shop_open_anim=1.0,
                shop_ui=ui,
            )
            joined = " ".join(
                str(canvas.itemcget(i, "text")) for i in canvas.find_all() if canvas.type(i) == "text"
            )
            self.assertIn("NODE INSPECTOR", joined)
            self.assertIn("THRUST", joined.upper())
        finally:
            root.destroy()

    def test_inspector_drag_moves_offset(self) -> None:
        from gravity_ho_matey.scenes.shop_ui import shop_on_pointer_motion

        state = ShopUiState()
        state.inspector_hit = shop_hit_id(PowerUpKind.THRUST_BOOST)
        shop_on_pointer_down(state, 100.0, 200.0, "shop_inspector_drag", shop_open=True)
        self.assertTrue(state.inspector_dragging)
        shop_on_pointer_motion(state, 130.0, 220.0, shop_open=True)
        self.assertAlmostEqual(state.inspector_offset_x, 30.0)
        self.assertAlmostEqual(state.inspector_offset_y, 20.0)

    def test_fitted_text_uses_font_metrics(self) -> None:
        if tk is None:
            self.skipTest("Tk unavailable")
        root = tk.Tk()
        root.withdraw()
        try:
            font = ("Courier New", 10)
            long = "Plunder Thrusters — +18% main engine output"
            fitted = fit_text_to_width(long, 120.0, font)
            self.assertLessEqual(measure_text(fitted, font), 120.5)
            self.assertIn("Plunder", fitted)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
