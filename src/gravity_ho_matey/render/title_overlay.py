from __future__ import annotations

import tkinter as tk
from enum import Enum, auto

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.progress import is_level_selectable
from gravity_ho_matey.levels.level_registry import LEVEL_LABELS, LEVEL_ORDER
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.holo_shop_overlay import HoloShopOverlay
from gravity_ho_matey.render.menu_ui import MenuHitMap, draw_fitted_text, draw_holo_corners, draw_level_row, draw_menu_button, draw_wrapped_text
from gravity_ho_matey.render.shop_tree_view import ShopTreeView
from gravity_ho_matey.render.title_home_layout import (
    compute_codex_layout,
    compute_welcome_home_layout,
    compute_welcome_left_layout,
)
from gravity_ho_matey.render.title_home_viz import (
    draw_hangar_bay,
    draw_title_starfield,
)
from gravity_ho_matey.render.title_codex import TitleCodexState
from gravity_ho_matey.render.title_codex_viz import draw_codex_pedestal
from gravity_ho_matey.render.title_deploy_list import (
    DeployListLayout,
    TitleChromeLayout,
    clamp_scroll,
    compute_deploy_split_layout,
    row_screen_y,
    row_visible,
    title_chrome_layout,
    viewport_contains,
    visible_row_hit_rect,
)
from gravity_ho_matey.render.title_info_pages import (
    draw_combat_page,
    draw_helm_page,
    draw_mission_page,
    draw_sector_dossier,
)

_LEVEL_DETAILS: dict[str, str] = {
    "cove": "Tag 3/4 beacons · unlock exit · learn wells",
    "solar": "All 3 beacons · cross singularity strip · south exit",
    "drift": "No beacons · push north · open gate · shake squids",
    "rift": "Hold relay · 3 waves · extract south",
    "siege": "Clear 12-hostile roster · escorts · optional station",
    "brood_moon": "Land · tag · rupture pods · seal lap · dock RTB",
}

_LEVEL_LOCK: dict[str, str] = {
    "cove": "",
    "solar": "Clear Cove first",
    "drift": "Clear Solar first",
    "rift": "Clear Drift first",
    "siege": "Clear Rift first",
    "brood_moon": "Clear Siege first",
}


class TitlePage(Enum):
    WELCOME = auto()
    MISSION = auto()
    HELM = auto()
    COMBAT = auto()
    DEPLOY = auto()


TITLE_PAGE_ORDER: tuple[TitlePage, ...] = (
    TitlePage.WELCOME,
    TitlePage.MISSION,
    TitlePage.HELM,
    TitlePage.COMBAT,
    TitlePage.DEPLOY,
)
from gravity_ho_matey.settings import DEV_UNLOCK_ALL_LEVELS

_PAGE_RAIL_H = 36.0
_PAGE_RAIL_GAP = 6.0
_BODY_SHOP_GAP = 8.0
_SHOP_STRIP_H = 34.0

_PAGE_LABELS: dict[TitlePage, str] = {
    TitlePage.WELCOME: "WELCOME",
    TitlePage.MISSION: "MISSION",
    TitlePage.HELM: "CONTROLS",
    TitlePage.COMBAT: "COMBAT",
    TitlePage.DEPLOY: "SELECT LEVEL",
}


class TitleScreenOverlay:
    """Paginated nav station — click or keyboard to browse and launch charts."""

    WIDTH = 960
    HEIGHT = 640
    MARGIN = 20
    TOP_BAR_H = 54
    FOOTER_H = 52
    SHOP_CTA_H = 36  # legacy alias for chart briefing parity
    SHOP_STRIP_H = _SHOP_STRIP_H
    PAGE_RAIL_H = _PAGE_RAIL_H
    FONT_TITLE = ("Courier New", 32, "bold")
    FONT_SUBTITLE = ("Courier New", 11)

    def __init__(self) -> None:
        self.hits = MenuHitMap()
        self._shop = HoloShopOverlay()
        self.deploy_layout: DeployListLayout | None = None

    @classmethod
    def chrome_layout(cls) -> TitleChromeLayout:
        """Shared vertical zones for draw + title-scene hit testing."""
        return title_chrome_layout(
            screen_h=float(cls.HEIGHT),
            top_bar_h=float(cls.TOP_BAR_H),
            footer_h=float(cls.FOOTER_H),
            rail_h=float(cls.PAGE_RAIL_H),
            shop_h=float(cls.SHOP_STRIP_H),
            margin_gap=_PAGE_RAIL_GAP,
            body_pad=_BODY_SHOP_GAP,
        )

    def draw(
        self,
        canvas: tk.Canvas,
        *,
        page: TitlePage,
        campaign: CampaignState,
        solar_unlocked: bool,
        drift_unlocked: bool = False,
        rift_unlocked: bool = False,
        siege_unlocked: bool = False,
        brood_unlocked: bool = False,
        deploy_focus: int = 0,
        deploy_scroll: float = 0.0,
        hover_id: str | None = None,
        elapsed: float = 0.0,
        shop_open: bool = False,
        shop_open_anim: float = 1.0,
        shop_view: ShopTreeView | None = None,
        shop_ui: object | None = None,
        codex: TitleCodexState | None = None,
    ) -> None:
        self.hits.clear()
        self.deploy_layout = None
        accent = palette.HUD_ACCENT
        dim = palette.HUD_DIM
        frame = palette.HUD_FRAME
        shop_strip = float(_SHOP_STRIP_H)
        chrome = self.chrome_layout()
        body_top = chrome.body_top

        canvas.create_rectangle(0, 0, self.WIDTH, self.HEIGHT, fill=palette.SOLAR_BG, outline="")
        self._draw_background_stars(canvas, body_top=body_top, body_bottom=chrome.body_bottom, elapsed=elapsed)
        self._draw_top_bar(canvas, page, accent, dim, campaign)

        if page is TitlePage.WELCOME:
            self._draw_welcome_page(
                canvas, chrome, accent, dim, frame, campaign, hover_id, elapsed, codex,
            )
        elif page is TitlePage.MISSION:
            draw_mission_page(
                canvas, chrome, screen_w=float(self.WIDTH), accent=accent, dim=dim, frame=frame, elapsed=elapsed,
            )
        elif page is TitlePage.HELM:
            draw_helm_page(
                canvas, chrome, screen_w=float(self.WIDTH), accent=accent, dim=dim, frame=frame, elapsed=elapsed,
            )
        elif page is TitlePage.COMBAT:
            draw_combat_page(
                canvas, chrome, screen_w=float(self.WIDTH), accent=accent, dim=dim, frame=frame, elapsed=elapsed,
            )
        else:
            split = compute_deploy_split_layout(chrome, screen_w=float(self.WIDTH))
            scroll = clamp_scroll(deploy_scroll, split.list)
            self._draw_deploy_page(
                canvas,
                chrome,
                split,
                accent,
                dim,
                frame,
                deploy_focus=deploy_focus,
                deploy_scroll=scroll,
                hover_id=hover_id,
                elapsed=elapsed,
            )

        if shop_strip > 0.0:
            self._shop.draw_compact_bazaar_strip(
                canvas,
                x=self.MARGIN,
                y=chrome.shop_y,
                w=self.WIDTH - 2 * self.MARGIN,
                h=chrome.shop_h,
                campaign=campaign,
                hits=self.hits,
                accent=accent,
                hover_id=hover_id,
                elapsed=elapsed,
            )
        self._draw_footer(
            canvas,
            page,
            chrome,
            solar_unlocked,
            drift_unlocked,
            rift_unlocked,
            siege_unlocked,
            brood_unlocked,
            accent,
            dim,
            frame,
            hover_id,
        )
        self._draw_page_rail(canvas, page, chrome, accent, dim, hover_id, elapsed)
        if shop_open:
            self._shop.draw(
                canvas,
                vw=self.WIDTH,
                vh=self.HEIGHT,
                campaign=campaign,
                hits=self.hits,
                hover_id=hover_id,
                elapsed=elapsed,
                shop_open_anim=shop_open_anim,
                shop_view=shop_view,
                shop_ui=shop_ui,
            )

    def _draw_top_bar(
        self,
        canvas: tk.Canvas,
        page: TitlePage,
        accent: str,
        dim: str,
        campaign: CampaignState,
    ) -> None:
        canvas.create_rectangle(0, 0, self.WIDTH, self.TOP_BAR_H, fill=palette.HUD_BG, outline="")
        canvas.create_line(0, self.TOP_BAR_H, self.WIDTH, self.TOP_BAR_H, fill=accent, width=1)
        hp.draw_scanlines(canvas, 0, 0, self.WIDTH, self.TOP_BAR_H)
        idx = TITLE_PAGE_ORDER.index(page) + 1
        canvas.create_text(self.MARGIN, 18, anchor="w", text=f"TAB {idx}/{len(TITLE_PAGE_ORDER)}", fill=dim, font=hp.FONT_SMALL)
        canvas.create_text(self.WIDTH // 2, 18, text="BRIGAND NAV STATION", fill=dim, font=hp.FONT_SMALL)
        canvas.create_text(self.WIDTH // 2, 36, text=_PAGE_LABELS[page], fill=accent, font=hp.FONT_SECTION)
        canvas.create_text(
            self.WIDTH - self.MARGIN,
            20,
            anchor="e",
            text=f"TREASURY {campaign.jewels}",
            fill=palette.HUD_LOOT_NEW,
            font=hp.FONT_SMALL,
        )
        canvas.create_text(
            self.WIDTH - self.MARGIN,
            38,
            anchor="e",
            text="GRAVITY HO, MATEY!",
            fill=accent,
            font=hp.FONT_SMALL,
        )
        if DEV_UNLOCK_ALL_LEVELS:
            canvas.create_text(
                self.WIDTH - self.MARGIN,
                42,
                anchor="e",
                text="DEV — ALL CHARTS",
                fill=palette.HUD_WARN,
                font=hp.FONT_SMALL,
            )

    def _draw_deploy_scrollbar(
        self,
        canvas: tk.Canvas,
        layout: DeployListLayout,
        scroll: float,
        *,
        accent: str,
        dim: str,
    ) -> None:
        if layout.max_scroll <= 0.0:
            return
        track_x = layout.panel_x + layout.panel_w - 18.0
        track_y = layout.viewport_y + 4.0
        track_h = layout.viewport_h - 8.0
        canvas.create_rectangle(track_x, track_y, track_x + 8.0, track_y + track_h, fill=palette.HUD_BG, outline=dim)
        thumb_h = max(24.0, track_h * (layout.viewport_h / layout.content_h))
        travel = max(1.0, track_h - thumb_h)
        thumb_y = track_y + (scroll / layout.max_scroll) * travel
        canvas.create_rectangle(track_x + 1.0, thumb_y, track_x + 7.0, thumb_y + thumb_h, fill=accent, outline="")

    def _draw_deploy_page(
        self,
        canvas: tk.Canvas,
        chrome: TitleChromeLayout,
        split,
        accent: str,
        dim: str,
        frame: str,
        *,
        deploy_focus: int,
        deploy_scroll: float,
        hover_id: str | None,
        elapsed: float,
    ) -> None:
        layout = split.list
        scroll = clamp_scroll(deploy_scroll, layout)
        self.deploy_layout = layout
        level_id = LEVEL_ORDER[deploy_focus]

        x, y, w, h = layout.panel_x, layout.panel_y, layout.panel_w, layout.panel_h
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        draw_holo_corners(canvas, x, y, w, h, accent=accent, elapsed=elapsed)
        hp.draw_panel_title(canvas, x + 16, y + 14, "CHART MANIFEST", color=dim)
        hint = "↑ ↓ · wheel · Enter" if layout.max_scroll > 0.0 else "↑ ↓ · Enter"
        canvas.create_text(x + w - 16, y + 14, anchor="e", text=hint, fill=dim, font=hp.FONT_SMALL)

        vy0 = layout.viewport_y
        vy1 = layout.viewport_y + layout.viewport_h
        canvas.create_line(x + 12, vy0, x + w - 12, vy0, fill=frame, width=1)
        canvas.create_line(x + 12, vy1, x + w - 12, vy1, fill=frame, width=1)

        list_w = layout.viewport_w - (24.0 if layout.max_scroll > 0.0 else 0.0)
        for i, lid in enumerate(LEVEL_ORDER):
            hit = visible_row_hit_rect(layout, i, scroll)
            if hit is None:
                continue
            hx, hy, hw, hh = hit
            region_id = f"level:{lid}"
            self.hits.add(region_id, hx, hy, hw, hh)
            ry = row_screen_y(layout, i, scroll)
            label = LEVEL_LABELS.get(lid, lid)
            title = label.split(" — ", 1)[-1] if " — " in label else label
            draw_level_row(
                canvas,
                layout.viewport_x,
                ry,
                list_w,
                layout.row_h,
                index=i + 1,
                title=title,
                detail=_LEVEL_DETAILS.get(lid, ""),
                accent=accent,
                dim=dim,
                frame=frame,
                unlocked=is_level_selectable(lid),
                lock_reason=_LEVEL_LOCK.get(lid, "Locked"),
                selected=i == deploy_focus,
                hover=hover_id == region_id,
            )

        canvas.create_rectangle(x, y, x + w, vy0, fill=palette.HUD_BG, outline="")
        canvas.create_rectangle(
            layout.viewport_x,
            vy1,
            layout.viewport_x + layout.viewport_w,
            y + h,
            fill=palette.HUD_BG,
            outline="",
        )
        hp.draw_panel_title(canvas, x + 16, y + 14, "CHART MANIFEST", color=dim)
        canvas.create_text(x + w - 16, y + 14, anchor="e", text=hint, fill=dim, font=hp.FONT_SMALL)
        canvas.create_line(x + 12, vy0, x + w - 12, vy0, fill=frame, width=1)
        canvas.create_line(x + 12, vy1, x + w - 12, vy1, fill=frame, width=1)
        draw_holo_corners(canvas, x, y, w, h, accent=accent, elapsed=elapsed)

        self._draw_deploy_scrollbar(canvas, layout, scroll, accent=accent, dim=dim)

        canvas.create_text(
            x + 16,
            vy1 + 8,
            anchor="w",
            text="Fittings persist for the whole campaign run.",
            fill=dim,
            font=hp.FONT_BODY,
        )

        prev = split.preview
        draw_sector_dossier(
            canvas,
            prev.x,
            prev.y,
            prev.w,
            prev.h,
            level_id,
            accent=accent,
            dim=dim,
            frame=frame,
            elapsed=elapsed,
        )

    def _draw_welcome_page(
        self,
        canvas: tk.Canvas,
        chrome: TitleChromeLayout,
        accent: str,
        dim: str,
        frame: str,
        campaign: CampaignState,
        hover_id: str | None,
        elapsed: float,
        codex: TitleCodexState | None,
    ) -> None:
        layout = compute_welcome_home_layout(chrome, screen_w=float(self.WIDTH))
        codex_state = codex or TitleCodexState()
        entry = codex_state.entry()
        codex_layout = compute_codex_layout(layout, entry)
        left = compute_welcome_left_layout(layout.panel, layout.left_x, layout.left_w)
        p = layout.panel
        hp.draw_panel(canvas, p.x, p.y, p.w, p.h, frame=frame, accent=accent, fill=palette.HUD_BG)
        draw_holo_corners(canvas, p.x, p.y, p.w, p.h, accent=accent, elapsed=elapsed)

        canvas.create_line(left.x - 4, p.y + 16, left.x - 4, p.y + p.h - 16, fill=frame, width=1)

        draw_wrapped_text(
            canvas,
            left.x,
            left.pitch_y,
            "Chart cursed sectors, loot patrol skiffs, and sling-shot past the maw.",
            max_width=left.w - 8,
            line_height=14.0,
            color=dim,
            font=self.FONT_SUBTITLE,
            max_lines=2,
        )

        self.hits.add("goto_deploy", left.btn_x, left.btn_y, left.btn_w, left.btn_h)
        draw_menu_button(
            canvas,
            left.btn_x,
            left.btn_y,
            left.btn_w,
            left.btn_h,
            "SELECT LEVEL →",
            accent=accent,
            dim=dim,
            frame=frame,
            hover=hover_id == "goto_deploy",
            selected=True,
        )

        draw_hangar_bay(
            canvas,
            layout,
            accent=accent,
            dim=dim,
            frame=frame,
            elapsed=elapsed,
            codex_index=codex_state.index,
        )
        draw_codex_pedestal(
            canvas,
            codex_layout,
            entry,
            index=codex_state.index,
            accent=accent,
            dim=dim,
            frame=frame,
            elapsed=elapsed,
            yaw=codex_state.yaw,
            hover_id=hover_id,
            hits=self.hits,
        )

    def _draw_footer(
        self,
        canvas: tk.Canvas,
        page: TitlePage,
        chrome: TitleChromeLayout,
        solar_unlocked: bool,
        drift_unlocked: bool,
        rift_unlocked: bool,
        siege_unlocked: bool,
        brood_unlocked: bool,
        accent: str,
        dim: str,
        frame: str,
        hover_id: str | None,
    ) -> None:
        y = chrome.footer_y
        hp.draw_panel(canvas, self.MARGIN, y, self.WIDTH - self.MARGIN * 2, chrome.footer_h, frame=frame, accent=accent, fill=palette.HUD_BG)

        prev_x = self.MARGIN + 12
        prev_w = 88.0
        next_x = prev_x + prev_w + 8
        next_w = 88.0
        self.hits.add("page_prev", prev_x, y + 10, prev_w, 36)
        self.hits.add("page_next", next_x, y + 10, next_w, 36)
        draw_menu_button(
            canvas,
            prev_x,
            y + 10,
            prev_w,
            36,
            "← PREV",
            accent=accent,
            dim=dim,
            frame=frame,
            hover=hover_id == "page_prev",
        )
        draw_menu_button(
            canvas,
            next_x,
            y + 10,
            next_w,
            36,
            "NEXT →",
            accent=accent,
            dim=dim,
            frame=frame,
            hover=hover_id == "page_next",
        )

        if page is TitlePage.DEPLOY:
            center = "Pick a chart · dossier updates on focus · Enter launches · B = Bazaar"
        elif page is TitlePage.WELCOME:
            center = "↑ ↓ field codex · ← → briefing tabs · Enter deploys · B bazaar"
        else:
            center = "Briefing tabs below · B opens Holo Bazaar on any page"
        draw_fitted_text(
            canvas,
            self.WIDTH // 2,
            y + 22,
            center,
            max_width=self.WIDTH - 280,
            color=palette.HUD_LOOT_NEW,
            font=hp.FONT_BODY_BOLD,
            anchor="center",
        )

        if DEV_UNLOCK_ALL_LEVELS:
            hint = "All charts unlocked (dev)"
        else:
            bits = ["Cove open"]
            if solar_unlocked:
                bits.append("Solar open")
            if drift_unlocked:
                bits.append("Drift open")
            if rift_unlocked:
                bits.append("Rift open")
            if siege_unlocked:
                bits.append("Siege open")
            if brood_unlocked:
                bits.append("Brood open")
            hint = " · ".join(bits)
        draw_fitted_text(
            canvas,
            self.WIDTH - self.MARGIN - 12,
            y + 40,
            hint,
            max_width=220,
            color=dim,
            font=hp.FONT_SMALL,
            anchor="e",
        )

    def _draw_page_rail(
        self,
        canvas: tk.Canvas,
        page: TitlePage,
        chrome: TitleChromeLayout,
        accent: str,
        dim: str,
        hover_id: str | None,
        elapsed: float,
    ) -> None:
        _ = elapsed
        bar_x = float(self.MARGIN)
        bar_y = chrome.rail_y
        bar_w = float(self.WIDTH - 2 * self.MARGIN)
        bar_h = chrome.rail_h
        tab_gap = 4.0
        count = len(TITLE_PAGE_ORDER)
        seg_w = (bar_w - tab_gap * (count - 1)) / count

        hp.draw_panel(canvas, bar_x, bar_y, bar_w, bar_h, frame=dim, accent=accent, fill="#060810")
        canvas.create_line(bar_x, bar_y, bar_x + bar_w, bar_y, fill=accent, width=1)

        for index, terminal in enumerate(TITLE_PAGE_ORDER):
            label = _PAGE_LABELS[terminal]
            sx = bar_x + index * (seg_w + tab_gap)
            region_id = f"tab:{terminal.name.lower()}"
            self.hits.add(region_id, sx, bar_y, seg_w, bar_h)
            selected = terminal is page
            hover = hover_id == region_id
            draw_menu_button(
                canvas,
                sx,
                bar_y + 2.0,
                seg_w,
                bar_h - 4.0,
                label,
                accent=accent,
                dim=dim,
                frame=dim,
                active=True,
                selected=selected,
                hover=hover,
            )
            if selected:
                canvas.create_line(sx + 6, bar_y + bar_h - 3, sx + seg_w - 6, bar_y + bar_h - 3, fill=accent, width=2)

    def _draw_background_stars(
        self,
        canvas: tk.Canvas,
        *,
        body_top: float,
        body_bottom: float,
        elapsed: float,
    ) -> None:
        draw_title_starfield(
            canvas,
            float(self.WIDTH),
            float(self.HEIGHT),
            elapsed=elapsed,
            body_top=body_top,
            body_bottom=body_bottom,
        )
