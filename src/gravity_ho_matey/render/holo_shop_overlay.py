from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.shop_catalog import shop_hit_id, shop_visible_catalog, shop_weapon_doctrine_catalog
from gravity_ho_matey.gameplay.shop_display import shop_button_label, shop_owned_status
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.menu_ui import MenuHitMap, draw_fitted_text, draw_holo_corners, draw_menu_button


class HoloShopOverlay:
    """Modal holo bazaar — overlays the chart briefing table."""

    _PANEL_W = 580.0
    _PANEL_H = 640.0

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
            PowerUpKind.WEAPON_EXPLOSIVE: palette.WEAPON_EXPLOSIVE_MID,
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
    ) -> None:
        accent = palette.HUD_ACCENT
        dim = palette.HUD_DIM
        frame = palette.HUD_FRAME

        canvas.create_rectangle(0, 0, vw, vh, fill="#040810", outline="", stipple="gray50")
        canvas.create_rectangle(0, 0, vw, vh, fill="#060a14", outline="")

        px = (vw - self._PANEL_W) * 0.5
        py = (vh - self._PANEL_H) * 0.5
        pw = self._PANEL_W
        ph = self._PANEL_H

        hp.draw_panel(canvas, px, py, pw, ph, frame=accent, accent=accent, fill=palette.HUD_BG)
        draw_holo_corners(canvas, px, py, pw, ph, accent=accent, elapsed=elapsed)
        hp.draw_scanlines(canvas, px, py, pw, ph)

        header_h = 52.0
        canvas.create_rectangle(px, py, px + pw, py + header_h, fill="#0a1420", outline="")
        canvas.create_line(px, py + header_h, px + pw, py + header_h, fill=accent, width=1)

        hp.draw_panel_title(canvas, px + 16, py + 12, "TRADE DECK", color=dim)
        canvas.create_text(
            px + 16,
            py + 30,
            anchor="w",
            text="HOLO BAZAAR",
            fill=accent,
            font=hp.FONT_SECTION,
        )
        canvas.create_text(
            px + pw - 16,
            py + 22,
            anchor="e",
            text=f"TREASURY  ★ {campaign.jewels}",
            fill=palette.JEWEL_CORE,
            font=hp.FONT_BODY_BOLD,
        )

        close_w = 88.0
        close_h = 28.0
        close_x = px + pw - close_w - 12
        close_y = py + ph - close_h - 14
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

        inner_x = px + 16
        inner_w = pw - 32
        cursor_y = py + header_h + 10

        cursor_y = self._draw_weapon_doctrine_row(
            canvas,
            inner_x,
            cursor_y,
            inner_w,
            campaign=campaign,
            hits=hits,
            hover_id=hover_id,
            accent=accent,
            dim=dim,
            frame=frame,
        )

        catalog = shop_visible_catalog(campaign)
        item_h = 68.0 if len(catalog) > 5 else 76.0
        item_gap = 6.0

        hp.draw_panel_title(canvas, inner_x + 4, cursor_y + 4, "FITTINGS & SUPPORT", color=dim)
        cursor_y += 22.0

        for index, item in enumerate(catalog):
            iy = cursor_y + index * (item_h + item_gap)
            self._draw_shop_item(
                canvas,
                inner_x,
                iy,
                inner_w,
                item_h,
                item=item,
                campaign=campaign,
                hits=hits,
                hover_id=hover_id,
                accent=accent,
                dim=dim,
                frame=frame,
            )

        canvas.create_text(
            px + pw / 2,
            py + ph - 14,
            text="Weapon doctrine: one path per campaign · Esc closes",
            fill=dim,
            font=hp.FONT_SMALL,
        )

    def _draw_weapon_doctrine_row(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        w: float,
        *,
        campaign: CampaignState,
        hits: MenuHitMap,
        hover_id: str | None,
        accent: str,
        dim: str,
        frame: str,
    ) -> float:
        section_h = 132.0
        hp.draw_panel(canvas, x, y, w, section_h, frame=frame, accent=accent, fill="#0a1018")
        hp.draw_panel_title(canvas, x + 10, y + 8, "WEAPON DOCTRINE — CHOOSE ONE", color=dim)
        canvas.create_text(
            x + w - 12,
            y + 10,
            anchor="e",
            text="mutually exclusive",
            fill=dim,
            font=hp.FONT_SMALL,
        )

        doctrine = shop_weapon_doctrine_catalog()
        gap = 8.0
        card_w = (w - gap * (len(doctrine) + 1)) / len(doctrine)
        card_h = 88.0
        card_y = y + 32.0

        for index, item in enumerate(doctrine):
            cx = x + gap + index * (card_w + gap)
            if index > 0:
                prev_cx = x + gap + (index - 1) * (card_w + gap)
                line_x0 = prev_cx + card_w
                line_x1 = cx
                line_y = card_y + card_h * 0.5
                canvas.create_line(line_x0, line_y, line_x1, line_y, fill=dim, dash=(4, 4))

            self._draw_doctrine_card(
                canvas,
                cx,
                card_y,
                card_w,
                card_h,
                item=item,
                campaign=campaign,
                hits=hits,
                hover_id=hover_id,
                accent=accent,
                dim=dim,
                frame=frame,
            )

        return y + section_h + 10.0

    def _draw_doctrine_card(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        item,
        campaign: CampaignState,
        hits: MenuHitMap,
        hover_id: str | None,
        accent: str,
        dim: str,
        frame: str,
    ) -> None:
        color = self._powerup_color(item.kind)
        can_buy = campaign.can_purchase(item.kind)
        price = campaign.upgrade_price(item.kind)
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=color if can_buy else dim, fill="#0c141c")
        draw_fitted_text(canvas, x + 8, y + 8, item.tag, max_width=w - 16, color=color, font=hp.FONT_BODY_BOLD)
        draw_fitted_text(
            canvas,
            x + 8,
            y + 24,
            item.label.split(" — ")[0],
            max_width=w - 16,
            color=accent,
            font=hp.FONT_SMALL,
        )
        draw_fitted_text(
            canvas,
            x + 8,
            y + 40,
            shop_owned_status(campaign, item.kind),
            max_width=w - 16,
            color=dim,
            font=hp.FONT_SMALL,
        )

        btn_w = min(92.0, w - 16.0)
        btn_h = 24.0
        btn_x = x + (w - btn_w) * 0.5
        btn_y = y + h - btn_h - 8
        hit = shop_hit_id(item.kind)
        hits.add(hit, btn_x, btn_y, btn_w, btn_h)
        draw_menu_button(
            canvas,
            btn_x,
            btn_y,
            btn_w,
            btn_h,
            shop_button_label(campaign, item.kind),
            accent=color if can_buy else dim,
            dim=dim,
            frame=frame,
            active=can_buy,
            selected=can_buy,
            hover=hover_id == hit,
        )
        if price is not None and can_buy:
            canvas.create_text(
                x + w - 8,
                y + 8,
                anchor="ne",
                text=f"{price}★",
                fill=palette.JEWEL_CORE,
                font=hp.FONT_SMALL,
            )

    def _draw_shop_item(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        item,
        campaign: CampaignState,
        hits: MenuHitMap,
        hover_id: str | None,
        accent: str,
        dim: str,
        frame: str,
    ) -> None:
        color = self._powerup_color(item.kind)
        can_buy = campaign.can_purchase(item.kind)
        price = campaign.upgrade_price(item.kind)

        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=color if can_buy else dim, fill="#0a1018")
        canvas.create_rectangle(x + 4, y + 4, x + 8, y + h - 4, fill=color, outline="")

        tag_x = x + 18
        draw_fitted_text(
            canvas,
            tag_x,
            y + 12,
            item.tag,
            max_width=100,
            color=color,
            font=hp.FONT_BODY_BOLD,
        )
        draw_fitted_text(
            canvas,
            tag_x,
            y + 28,
            item.label,
            max_width=w - 130,
            color=accent,
            font=hp.FONT_SMALL,
        )
        draw_fitted_text(
            canvas,
            tag_x,
            y + 44,
            shop_owned_status(campaign, item.kind),
            max_width=w - 130,
            color=dim,
            font=hp.FONT_SMALL,
        )
        price_text = f"{price} ★" if price is not None else "—"
        canvas.create_text(
            tag_x,
            y + h - 14,
            anchor="w",
            text=price_text,
            fill=palette.JEWEL_CORE if can_buy else dim,
            font=hp.FONT_BODY_BOLD,
        )

        btn_w = 108.0
        btn_h = 32.0
        btn_x = x + w - btn_w - 12
        btn_y = y + (h - btn_h) * 0.5
        hit = shop_hit_id(item.kind)
        hits.add(hit, btn_x, btn_y, btn_w, btn_h)
        buy_label = shop_button_label(campaign, item.kind)
        draw_menu_button(
            canvas,
            btn_x,
            btn_y,
            btn_w,
            btn_h,
            buy_label,
            accent=color if can_buy else dim,
            dim=dim,
            frame=frame,
            active=can_buy,
            selected=can_buy,
            hover=hover_id == hit,
        )
