from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.shop_catalog import shop_hit_id
from gravity_ho_matey.gameplay.shop_display import shop_button_label, shop_card_hint, shop_owned_status
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.menu_ui import MenuHitMap, draw_fitted_text, draw_holo_corners, draw_menu_button, draw_wrapped_text, draw_wrapped_text
from gravity_ho_matey.render.shop_skill_tree_layout import (
    BRANCHES,
    SkillTreeNode,
    SkillTreeViewport,
    branch_label_position,
    compute_fit_viewport,
    hub_screen_center,
    hub_screen_radius,
    item_for_node,
    node_bounds,
    node_screen_center,
    nodes_in_branch,
    shop_tree_rect,
    skill_tree_nodes,
)
from gravity_ho_matey.render.shop_tree_view import ShopTreeView, apply_shop_tree_view
from gravity_ho_matey.scenes.shop_ui import ShopUiState


class HoloShopOverlay:
    """Radial skill-tree bazaar — captain at center, branches for doctrine / drive / hull / escort."""

    _INSPECTOR_W = 420.0
    _INSPECTOR_H = 112.0
    _INSPECTOR_DRAG_H = 22.0

    @classmethod
    def inspector_default_rect(
        cls,
        px: float,
        py: float,
        pw: float,
        ph: float,
        *,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> tuple[float, float, float, float]:
        """Lower-left dock — keeps escort/drone branch on the right readable."""
        footer_h = 44.0
        panel_w = min(cls._INSPECTOR_W, pw - 160.0)
        panel_h = cls._INSPECTOR_H
        header_h = 48.0
        base_x = px + 14.0
        base_y = py + ph - footer_h - panel_h - 44.0
        panel_x = max(px + 8.0, min(px + pw - panel_w - 8.0, base_x + offset_x))
        panel_y = max(py + header_h + 8.0, min(py + ph - footer_h - panel_h - 8.0, base_y + offset_y))
        return panel_x, panel_y, panel_w, panel_h

    _PANEL_W = 920.0
    _PANEL_H = 624.0

    @classmethod
    def panel_rect(cls, vw: int, vh: int) -> tuple[float, float, float, float]:
        px = (vw - cls._PANEL_W) * 0.5
        py = (vh - cls._PANEL_H) * 0.5
        return px, py, cls._PANEL_W, cls._PANEL_H

    @classmethod
    def tree_content_rect(
        cls,
        panel_x: float,
        panel_y: float,
        panel_w: float,
        panel_h: float,
    ) -> tuple[float, float, float, float]:
        return shop_tree_rect(panel_x, panel_y, panel_w, panel_h)

    def draw_bazaar_cta(
        self,
        canvas: tk.Canvas,
        *,
        x: float,
        y: float,
        w: float,
        h: float,
        campaign: CampaignState,
        hits: MenuHitMap,
        accent: str,
        hover_id: str | None,
        elapsed: float = 0.0,
    ) -> None:
        pulse = 0.72 + 0.28 * math.sin(elapsed * 3.2)
        border = palette.JEWEL_CORE if hover_id == "shop_open" else accent
        fill = "#122838" if hover_id == "shop_open" else "#0e2030"
        canvas.create_rectangle(x, y, x + w, y + h, fill=fill, outline=border, width=2 if pulse > 0.88 else 1)
        canvas.create_line(x + 6, y + 2, x + 36, y + 2, fill=palette.JEWEL_CORE if pulse > 0.8 else accent)
        canvas.create_line(x + w - 36, y + h - 2, x + w - 6, y + h - 2, fill=palette.JEWEL_CORE if pulse > 0.8 else accent)
        hits.add("shop_open", x, y, w, h)
        label = f"◈  MERCHANT TREE  ·  ★ {campaign.jewels} TREASURY  ·  UPGRADE TREE  ◈"
        draw_fitted_text(
            canvas,
            x + w / 2,
            y + h / 2 - 1,
            label,
            max_width=w - 24,
            color=palette.JEWEL_CORE if hover_id == "shop_open" else accent,
            font=("Courier New", 11, "bold"),
            anchor="center",
        )
        canvas.create_text(
            x + w - 12,
            y + h / 2,
            anchor="e",
            text="▶",
            fill=border,
            font=hp.FONT_BODY_BOLD,
        )

    def draw_welcome_bazaar_card(
        self,
        canvas: tk.Canvas,
        *,
        x: float,
        y: float,
        w: float,
        h: float,
        campaign: CampaignState,
        hits: MenuHitMap,
        accent: str,
        dim: str,
        frame: str,
        hover_id: str | None,
        elapsed: float = 0.0,
    ) -> None:
        """Embedded Holo Bazaar on the welcome column — primary trade entry."""
        hover = hover_id == "shop_open"
        pulse = 0.65 + 0.35 * math.sin(elapsed * 3.0)
        border = palette.JEWEL_CORE if hover else accent
        fill = "#142838" if hover else "#0c1828"
        hp.draw_panel(canvas, x, y, w, h, frame=border if hover else frame, accent=accent, fill=fill)
        draw_holo_corners(canvas, x, y, w, h, accent=palette.JEWEL_CORE if pulse > 0.75 else accent, elapsed=elapsed)
        hits.add("shop_open", x, y, w, h)

        hp.draw_panel_title(canvas, x + 12, y + 10, "HOLO BAZAAR", color=dim)
        canvas.create_text(
            x + w - 12,
            y + 10,
            anchor="e",
            text="B",
            fill=palette.JEWEL_CORE if hover else accent,
            font=hp.FONT_BODY_BOLD,
        )
        canvas.create_line(x + 12, y + 26, x + w - 12, y + 26, fill=frame, width=1)

        canvas.create_text(
            x + 14,
            y + 40,
            anchor="w",
            text="◈ MERCHANT TREE",
            fill=accent,
            font=hp.FONT_BODY_BOLD,
        )
        canvas.create_text(
            x + 14,
            y + 58,
            anchor="w",
            text=f"★ {campaign.jewels} treasury jewels",
            fill=palette.JEWEL_CORE,
            font=hp.FONT_DISPLAY,
        )
        draw_wrapped_text(
            canvas,
            x + 14,
            y + 78,
            "Doctrine · drive · hull · escort — fittings persist for the run.",
            max_width=w - 28,
            line_height=13.0,
            color=dim,
            font=hp.FONT_SMALL,
            max_lines=2,
        )

        btn_y = y + h - 36.0
        btn_h = 28.0
        btn_fill = palette.JEWEL_CORE if hover else accent
        canvas.create_rectangle(x + 10, btn_y, x + w - 10, btn_y + btn_h, outline=btn_fill, fill="#0e2030", width=2 if hover else 1)
        draw_fitted_text(
            canvas,
            x + w / 2,
            btn_y + btn_h / 2,
            "OPEN UPGRADE TREE →",
            max_width=w - 28,
            color=btn_fill,
            font=hp.FONT_BODY_BOLD,
            anchor="center",
        )

    def draw_compact_bazaar_strip(
        self,
        canvas: tk.Canvas,
        *,
        x: float,
        y: float,
        w: float,
        h: float,
        campaign: CampaignState,
        hits: MenuHitMap,
        accent: str,
        hover_id: str | None,
        elapsed: float = 0.0,
    ) -> None:
        """Slim trade strip above the tab rail on briefing pages."""
        hover = hover_id == "shop_open"
        border = palette.JEWEL_CORE if hover else accent
        hp.draw_panel(canvas, x, y, w, h, frame=border, accent=accent, fill="#0e2030" if hover else "#0a1420")
        hits.add("shop_open", x, y, w, h)
        draw_fitted_text(
            canvas,
            x + 14,
            y + h / 2,
            f"◈ HOLO BAZAAR · ★ {campaign.jewels} · MERCHANT TREE",
            max_width=w - 56,
            color=palette.JEWEL_CORE if hover else accent,
            font=hp.FONT_BODY_BOLD,
            anchor="w",
        )
        canvas.create_text(
            x + w - 14,
            y + h / 2,
            anchor="e",
            text="B · OPEN ▶",
            fill=border,
            font=hp.FONT_BODY,
        )

    @staticmethod
    def _powerup_color(kind: PowerUpKind) -> str:
        return {
            PowerUpKind.THRUST_BOOST: palette.PICKUP_THRUST,
            PowerUpKind.RAPID_FIRE: palette.PICKUP_RAPID,
            PowerUpKind.BOOST_TAP: palette.PICKUP_BOOST,
            PowerUpKind.RUBBER_HULL: palette.PICKUP_RUBBER,
            PowerUpKind.DRONE_WINGMAN: palette.DRONE_CORE,
            PowerUpKind.HULL_REINFORCE: palette.HUD_WARN,
            PowerUpKind.DRONE_REPAIR: palette.DRONE_TRIM,
            PowerUpKind.DRONE_ARMOR: palette.DRONE_BODY,
            PowerUpKind.WEAPON_LASER: palette.WEAPON_LASER_MID,
            PowerUpKind.WEAPON_SHOTGUN: palette.WEAPON_SHOTGUN_MID,
            PowerUpKind.WEAPON_ADV_LASER: palette.WEAPON_LASER_MID,
            PowerUpKind.WEAPON_ADV_SHOTGUN: palette.WEAPON_SHOTGUN_MID,
            PowerUpKind.WEAPON_ADV_EXPLOSIVE: palette.WEAPON_EXPLOSIVE_MID,
        }.get(kind, palette.HUD_LOOT_NEW)

    def draw(
        self,
        canvas: tk.Canvas,
        *,
        vw: int,
        vh: int,
        campaign: CampaignState,
        hits: MenuHitMap,
        hover_id: str | None,
        elapsed: float = 0.0,
        shop_open_anim: float = 1.0,
        shop_view: ShopTreeView | None = None,
        shop_ui: ShopUiState | None = None,
    ) -> None:
        accent = palette.HUD_ACCENT
        dim = palette.HUD_DIM
        frame = palette.HUD_FRAME

        canvas.create_rectangle(0, 0, vw, vh, fill="#040810", outline="", stipple="gray50")
        canvas.create_rectangle(0, 0, vw, vh, fill="#060a14", outline="")

        px, py, pw, ph = self.panel_rect(vw, vh)

        hp.draw_panel(canvas, px, py, pw, ph, frame=accent, accent=accent, fill=palette.HUD_BG)
        draw_holo_corners(canvas, px, py, pw, ph, accent=accent, elapsed=elapsed)
        hp.draw_scanlines(canvas, px, py, pw, ph)

        header_h = 48.0
        canvas.create_rectangle(px, py, px + pw, py + header_h, fill="#0a1420", outline="")
        canvas.create_line(px, py + header_h, px + pw, py + header_h, fill=accent, width=1)
        hp.draw_panel_title(canvas, px + 16, py + 10, "CAPTAIN UPGRADE TREE", color=dim)
        canvas.create_text(
            px + pw - 16,
            py + 26,
            anchor="e",
            text=f"TREASURY  ★ {campaign.jewels}",
            fill=palette.JEWEL_CORE,
            font=hp.FONT_BODY_BOLD,
        )

        close_w = 88.0
        close_h = 28.0
        close_x = px + pw - close_w - 14
        close_y = py + ph - close_h - 12
        hits.add("shop_close", close_x, close_y, close_w, close_h)
        draw_menu_button(
            canvas,
            close_x,
            close_y,
            close_w,
            close_h,
            "CLOSE",
            accent=dim,
            dim=dim,
            frame=frame,
            hover=hover_id == "shop_close",
        )

        tree_left, tree_top, tree_w, tree_h = shop_tree_rect(px, py, pw, ph)
        hits.add("shop_tree_pan", tree_left, tree_top, tree_w, tree_h)
        nodes = skill_tree_nodes(campaign)
        view = shop_ui.view if shop_ui is not None else (shop_view or ShopTreeView())
        fit = compute_fit_viewport(
            nodes,
            left=tree_left,
            top=tree_top,
            width=tree_w,
            height=tree_h,
            open_anim=shop_open_anim,
        )
        viewport = apply_shop_tree_view(fit, view)
        cx, cy = hub_screen_center(viewport)

        self._draw_tree_backdrop(canvas, viewport, accent=accent, dim=dim, elapsed=elapsed)
        self._draw_branch_spines(canvas, viewport, nodes, campaign=campaign, dim=dim)

        for branch in BRANCHES:
            if branch.branch_id == "escort" and not any(n.branch_id == "escort" for n in nodes):
                continue
            lx, ly = branch_label_position(viewport, branch)
            canvas.create_text(lx, ly, text=branch.label, fill=dim, font=hp.FONT_SMALL)

        self._draw_captain_hub(
            canvas,
            viewport,
            campaign=campaign,
            accent=accent,
            dim=dim,
            frame=frame,
            elapsed=elapsed,
        )

        for node in nodes:
            self._draw_skill_node(
                canvas,
                node,
                viewport=viewport,
                campaign=campaign,
                hits=hits,
                hover_id=hover_id,
                accent=accent,
                dim=dim,
                frame=frame,
            )

        self._draw_zoom_controls(
            canvas,
            px=px,
            py=py,
            pw=pw,
            ph=ph,
            hits=hits,
            hover_id=hover_id,
            accent=accent,
            dim=dim,
            frame=frame,
            zoom=view.zoom,
        )
        self._draw_node_inspector(
            canvas,
            px=px,
            py=py,
            pw=pw,
            ph=ph,
            hits=hits,
            campaign=campaign,
            shop_ui=shop_ui,
            accent=accent,
            dim=dim,
            frame=frame,
        )

        canvas.create_text(
            px + pw / 2,
            py + ph - 10,
            text="Click a node for details · drag inspector header to move · scroll zoom · Esc closes",
            fill=dim,
            font=hp.FONT_SMALL,
        )

    def _draw_tree_backdrop(
        self,
        canvas: tk.Canvas,
        viewport: SkillTreeViewport,
        *,
        accent: str,
        dim: str,
        elapsed: float,
    ) -> None:
        cx, cy = hub_screen_center(viewport)
        pulse = 0.9 + 0.1 * math.sin(elapsed * 2.4)
        scale = viewport.scale
        for ring_r, tone in ((88.0, dim), (168.0, "#1a3048"), (252.0, "#142838"), (332.0, "#101e30")):
            r = ring_r * scale * pulse
            canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=tone, width=1, dash=(5, 7) if ring_r > 120 else (3, 5))
        hr = 5.0 * scale
        canvas.create_oval(cx - hr, cy - hr, cx + hr, cy + hr, fill=accent, outline="")

    def _draw_branch_spines(
        self,
        canvas: tk.Canvas,
        viewport: SkillTreeViewport,
        nodes: tuple[SkillTreeNode, ...],
        *,
        campaign: CampaignState,
        dim: str,
    ) -> None:
        from gravity_ho_matey.gameplay.weapon_kinds import (
            is_weapon_advanced_powerup,
            weapon_kind_for_track,
        )

        hx, hy = hub_screen_center(viewport)
        for branch_id in ("weapons", "drive", "hull", "escort"):
            branch_nodes = nodes_in_branch(nodes, branch_id)
            if not branch_nodes:
                continue
            if branch_id == "weapons":
                base_nodes = sorted(
                    (n for n in branch_nodes if not is_weapon_advanced_powerup(n.kind)),
                    key=lambda n: n.chain_index,
                )
                adv_nodes = [n for n in branch_nodes if is_weapon_advanced_powerup(n.kind)]
                if len(base_nodes) >= 3:
                    a = node_screen_center(viewport, base_nodes[0])
                    b = node_screen_center(viewport, base_nodes[2])
                    canvas.create_line(a[0], a[1], b[0], b[1], fill="#1a2838", width=1, dash=(2, 6))
                if campaign.weapon_track is not None:
                    try:
                        base_node = next(n for n in base_nodes if n.kind is weapon_kind_for_track(campaign.weapon_track))
                        bx, by = node_screen_center(viewport, base_node)
                        canvas.create_line(hx, hy, bx, by, fill=dim, width=2)
                        if adv_nodes:
                            ax, ay = node_screen_center(viewport, adv_nodes[0])
                            canvas.create_line(bx, by, ax, ay, fill=dim, width=2)
                    except StopIteration:
                        pass
                elif base_nodes:
                    nx, ny = node_screen_center(viewport, base_nodes[1])
                    canvas.create_line(hx, hy, nx, ny, fill=dim, width=2)
                continue
            nx, ny = node_screen_center(viewport, branch_nodes[0])
            canvas.create_line(hx, hy, nx, ny, fill=dim, width=2)
            for i in range(len(branch_nodes) - 1):
                a = node_screen_center(viewport, branch_nodes[i])
                b = node_screen_center(viewport, branch_nodes[i + 1])
                canvas.create_line(a[0], a[1], b[0], b[1], fill=dim, width=2, dash=(4, 4))

    def _draw_captain_hub(
        self,
        canvas: tk.Canvas,
        viewport: SkillTreeViewport,
        *,
        campaign: CampaignState,
        accent: str,
        dim: str,
        frame: str,
        elapsed: float,
    ) -> None:
        cx, cy = hub_screen_center(viewport)
        r = hub_screen_radius(viewport)
        pulse = 0.92 + 0.08 * math.sin(elapsed * 3.0)
        hp.draw_panel(canvas, cx - r, cy - r, r * 2, r * 2, frame=accent, accent=accent, fill="#0c1828")
        canvas.create_polygon(
            cx,
            cy - 16 * pulse,
            cx + 14 * pulse,
            cy + 12 * pulse,
            cx - 14 * pulse,
            cy + 12 * pulse,
            fill=accent,
            outline=frame,
            width=1,
        )
        canvas.create_text(cx, cy + 22, text="CAPTAIN", fill=dim, font=hp.FONT_SMALL)
        if campaign.weapon_track is not None:
            from gravity_ho_matey.gameplay.weapon_kinds import WEAPON_TRACK_ADV_SHORT, WEAPON_TRACK_SHORT

            label = WEAPON_TRACK_SHORT[campaign.weapon_track]
            if campaign.weapon_advanced:
                label = WEAPON_TRACK_ADV_SHORT[campaign.weapon_track]
            canvas.create_text(
                cx,
                cy + max(18.0, r * 0.55),
                text=label,
                fill=self._powerup_color_for_track(campaign),
                font=hp.FONT_SMALL,
            )

    @staticmethod
    def _powerup_color_for_track(campaign: CampaignState) -> str:
        track = campaign.weapon_track
        if track is None:
            return palette.HUD_DIM
        from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack

        if track is WeaponTrack.LASER:
            return palette.WEAPON_LASER_MID
        if track is WeaponTrack.SHOTGUN:
            return palette.WEAPON_SHOTGUN_MID
        return palette.WEAPON_EXPLOSIVE_MID

    def _draw_skill_node(
        self,
        canvas: tk.Canvas,
        node: SkillTreeNode,
        *,
        viewport: SkillTreeViewport,
        campaign: CampaignState,
        hits: MenuHitMap,
        hover_id: str | None,
        accent: str,
        dim: str,
        frame: str,
    ) -> None:
        item = item_for_node(node)
        if item is None:
            return
        x, y, w, h = node_bounds(viewport, node)
        scale = viewport.scale
        color = self._powerup_color(node.kind)
        can_buy = campaign.can_purchase(node.kind)
        price = campaign.upgrade_price(node.kind)
        active = self._node_active(campaign, node.kind)
        hit = shop_hit_id(node.kind)
        hits.add(hit, x, y, w, h)

        fill = "#101820" if can_buy else "#0a1018"
        border = color if can_buy or active else dim
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=border, fill=fill)
        if active:
            canvas.create_rectangle(x + 2, y + 2, x + w - 2, y + h - 2, outline=color, width=max(1, int(2 * scale)))

        pad = max(6.0, 7.0 * scale)
        footer_h = max(18.0, 20.0 * scale)
        inner_w = w - pad * 2.0
        tag_font: tuple[str, int, str] = ("Courier New", max(9, int(11 * scale)), "bold")
        body_font: tuple[str, int] = ("Courier New", max(8, int(10 * scale)))
        hint_font: tuple[str, int] = ("Courier New", max(7, int(8 * scale)))
        action_font: tuple[str, int, str] = ("Courier New", max(8, int(9 * scale)), "bold")

        draw_fitted_text(canvas, x + pad, y + pad, item.tag, max_width=inner_w * 0.62, color=color, font=tag_font)
        if price is not None and can_buy:
            draw_fitted_text(
                canvas,
                x + w - pad,
                y + pad,
                f"{price}★",
                max_width=inner_w * 0.38,
                color=palette.JEWEL_CORE,
                font=hint_font,
                anchor="ne",
            )

        short = item.label.split(" — ")[0]
        line_h = max(11.0, 12.0 * scale)
        body_top = y + pad + line_h + 2.0
        draw_wrapped_text(
            canvas,
            x + pad,
            body_top,
            short,
            max_width=inner_w,
            line_height=line_h,
            color=accent if can_buy else dim,
            font=body_font,
            max_lines=2,
        )

        hint = shop_card_hint(campaign, node.kind)
        if hint:
            draw_fitted_text(
                canvas,
                x + pad,
                y + h - footer_h - pad - 2.0,
                hint,
                max_width=inner_w,
                color=dim,
                font=hint_font,
            )

        footer_y = y + h - footer_h
        canvas.create_line(x + pad, footer_y, x + w - pad, footer_y, fill=frame)

        label = shop_button_label(campaign, node.kind)
        btn_color = color if can_buy or active else dim
        draw_fitted_text(
            canvas,
            x + w / 2,
            footer_y + footer_h * 0.5,
            label,
            max_width=inner_w,
            color=btn_color,
            font=action_font,
            anchor="center",
        )

        if hover_id == hit and can_buy:
            canvas.create_rectangle(x - 1, y - 1, x + w + 1, y + h + 1, outline=palette.JEWEL_CORE, width=2)

    def _draw_zoom_controls(
        self,
        canvas: tk.Canvas,
        *,
        px: float,
        py: float,
        pw: float,
        ph: float,
        hits: MenuHitMap,
        hover_id: str | None,
        accent: str,
        dim: str,
        frame: str,
        zoom: float,
    ) -> None:
        btn_w = 34.0
        btn_h = 24.0
        gap = 4.0
        row_y = py + ph - btn_h - 12.0
        row_x = px + 14.0
        for hit_id, label in (
            ("shop_zoom_out", "−"),
            ("shop_zoom_in", "+"),
            ("shop_zoom_fit", "FIT"),
        ):
            w = 44.0 if label == "FIT" else btn_w
            draw_menu_button(
                canvas,
                row_x,
                row_y,
                w,
                btn_h,
                label,
                accent=accent,
                dim=dim,
                frame=frame,
                hover=hover_id == hit_id,
            )
            hits.add(hit_id, row_x, row_y, w, btn_h)
            row_x += w + gap
        canvas.create_text(
            row_x + 6,
            row_y + btn_h / 2,
            anchor="w",
            text=f"{int(zoom * 100):3d}%",
            fill=dim,
            font=hp.FONT_BODY,
        )

    def _draw_node_inspector(
        self,
        canvas: tk.Canvas,
        *,
        px: float,
        py: float,
        pw: float,
        ph: float,
        hits: MenuHitMap,
        campaign: CampaignState,
        shop_ui: ShopUiState | None,
        accent: str,
        dim: str,
        frame: str,
    ) -> None:
        from gravity_ho_matey.gameplay.shop_catalog import shop_kind_from_hit
        from gravity_ho_matey.render.menu_ui import wrap_text_lines

        if shop_ui is None:
            return
        selected = shop_ui.inspector_hit
        if not selected or shop_kind_from_hit(selected) is None:
            return

        panel_x, panel_y, panel_w, panel_h = self.inspector_default_rect(
            px,
            py,
            pw,
            ph,
            offset_x=shop_ui.inspector_offset_x,
            offset_y=shop_ui.inspector_offset_y,
        )
        drag_h = self._INSPECTOR_DRAG_H
        hp.draw_panel(canvas, panel_x, panel_y, panel_w, panel_h, frame=frame, accent=accent, fill="#0a1420")
        canvas.create_rectangle(
            panel_x,
            panel_y,
            panel_x + panel_w,
            panel_y + drag_h,
            fill="#0e1828",
            outline=accent,
            width=1,
        )
        canvas.create_line(panel_x, panel_y + drag_h, panel_x + panel_w, panel_y + drag_h, fill=frame)
        hp.draw_panel_title(canvas, panel_x + 10, panel_y + 5, "NODE INSPECTOR", color=accent)
        canvas.create_text(
            panel_x + panel_w - 10,
            panel_y + drag_h * 0.5,
            anchor="e",
            text="drag",
            fill=dim,
            font=hp.FONT_SMALL,
        )
        hits.add("shop_inspector_drag", panel_x, panel_y, panel_w, drag_h)
        hits.add("shop_inspector_panel", panel_x, panel_y + drag_h, panel_w, panel_h - drag_h)

        kind = shop_kind_from_hit(selected)
        if kind is None:
            return
        nodes = skill_tree_nodes(campaign)
        node = next((n for n in nodes if n.kind is kind), None)
        if node is None:
            return
        item = item_for_node(node)
        if item is None:
            return
        color = self._powerup_color(kind)
        status = shop_owned_status(campaign, kind)
        price = campaign.upgrade_price(kind)
        action = shop_button_label(campaign, kind)
        inner_w = panel_w - 24.0
        y = panel_y + drag_h + 10.0
        canvas.create_text(panel_x + 12, y, anchor="w", text=item.tag, fill=color, font=("Courier New", 12, "bold"))
        y += 16.0
        for line in wrap_text_lines(item.label, inner_w * 0.58, hp.FONT_BODY, max_lines=2):
            canvas.create_text(panel_x + 12, y, anchor="w", text=line, fill=accent, font=hp.FONT_BODY)
            y += 13.0
        status_x = panel_x + panel_w * 0.52
        status_w = inner_w * 0.46
        sy = panel_y + drag_h + 10.0
        for line in wrap_text_lines(status, status_w, hp.FONT_BODY, max_lines=3):
            canvas.create_text(status_x, sy, anchor="w", text=line, fill=dim, font=hp.FONT_BODY)
            sy += 13.0
        price_txt = f"Cost {price} ★" if price is not None else "No jewel cost"
        canvas.create_text(panel_x + 12, panel_y + panel_h - 22, anchor="w", text=price_txt, fill=palette.JEWEL_CORE, font=hp.FONT_BODY_BOLD)
        draw_fitted_text(
            canvas,
            panel_x + panel_w - 12,
            panel_y + panel_h - 22,
            action,
            max_width=inner_w * 0.42,
            color=color,
            font=hp.FONT_BODY_BOLD,
            anchor="e",
        )

    @staticmethod
    def _node_active(campaign: CampaignState, kind: PowerUpKind) -> bool:
        from gravity_ho_matey.gameplay.weapon_kinds import (
            is_weapon_advanced_powerup,
            is_weapon_powerup,
            weapon_track_from_kind,
        )

        if is_weapon_advanced_powerup(kind):
            track = weapon_track_from_kind(kind)
            return campaign.weapon_advanced and campaign.weapon_track is track
        if is_weapon_powerup(kind):
            track = weapon_track_from_kind(kind)
            return campaign.weapon_track is track
        if kind is PowerUpKind.RAPID_FIRE:
            return campaign.powerup_stacks.get(kind, 0) > 0
        if kind is PowerUpKind.DRONE_WINGMAN:
            return campaign.has_drone_contract
        if kind is PowerUpKind.NIFFLERP:
            return campaign.has_nifflerp_contract
        if kind is PowerUpKind.DRONE_ARMOR:
            return campaign.drone_armored
        if kind is PowerUpKind.RUBBER_HULL:
            return campaign.rubber_hull_charges > 0
        if kind is PowerUpKind.HULL_REINFORCE:
            return campaign.hull_reinforce_purchases > 0
        return campaign.powerup_stacks.get(kind, 0) > 0
