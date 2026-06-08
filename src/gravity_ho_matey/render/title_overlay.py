from __future__ import annotations

import math
import tkinter as tk
from enum import Enum, auto

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.progress import is_level_selectable
from gravity_ho_matey.levels.level_registry import LEVEL_LABELS, LEVEL_ORDER
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.holo_shop_overlay import HoloShopOverlay
from gravity_ho_matey.render.menu_ui import MenuHitMap, draw_fitted_text, draw_holo_corners, draw_level_row, draw_menu_button, measure_text
from gravity_ho_matey.render.shop_tree_view import ShopTreeView
from gravity_ho_matey.render.title_home_layout import compute_body_panel, compute_codex_layout, compute_welcome_home_layout
from gravity_ho_matey.render.title_home_viz import (
    draw_campaign_status_chip,
    draw_hangar_bay,
    draw_title_starfield,
)
from gravity_ho_matey.render.title_codex import TitleCodexState
from gravity_ho_matey.render.title_codex_viz import draw_codex_pedestal
from gravity_ho_matey.render.title_deploy_list import (
    DeployListLayout,
    TitleChromeLayout,
    clamp_scroll,
    compute_deploy_list_layout,
    row_screen_y,
    row_visible,
    title_chrome_layout,
    viewport_contains,
    visible_row_hit_rect,
)

_LEVEL_DETAILS: dict[str, str] = {
    "cove": "Beacon run · gravity wells · training chart",
    "solar": "Vertical strip · patrol skiffs · singularity",
    "drift": "Open belts · void squids · north exit",
    "rift": "Relay hold · 3 waves · Brood-Mother · RTB extract",
    "siege": "12v12 skirmish · spiral belt · hostile station",
    "brood_moon": "Land on nursery moon · tag · rupture · RTB",
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

_PAGE_RAIL_H = 24.0
_PAGE_RAIL_GAP = 6.0
_BODY_SHOP_GAP = 8.0

_PAGE_LABELS: dict[TitlePage, str] = {
    TitlePage.WELCOME: "WELCOME",
    TitlePage.MISSION: "MISSION",
    TitlePage.HELM: "CONTROLS",
    TitlePage.COMBAT: "COMBAT",
    TitlePage.DEPLOY: "SELECT CHART",
}


class TitleScreenOverlay:
    """Paginated nav station — click or keyboard to browse and launch charts."""

    WIDTH = 960
    HEIGHT = 640
    MARGIN = 20
    TOP_BAR_H = 54
    FOOTER_H = 52
    SHOP_CTA_H = 36
    FONT_TITLE = ("Courier New", 32, "bold")
    FONT_SUBTITLE = ("Courier New", 11)

    def __init__(self) -> None:
        self.hits = MenuHitMap()
        self._shop = HoloShopOverlay()
        self.deploy_layout: DeployListLayout | None = None

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
        chrome = title_chrome_layout(
            screen_h=float(self.HEIGHT),
            top_bar_h=float(self.TOP_BAR_H),
            footer_h=float(self.FOOTER_H),
            rail_h=_PAGE_RAIL_H,
            shop_h=float(self.SHOP_CTA_H),
            margin_gap=_PAGE_RAIL_GAP,
            body_pad=_BODY_SHOP_GAP,
        )
        body_top = chrome.body_top

        canvas.create_rectangle(0, 0, self.WIDTH, self.HEIGHT, fill=palette.SOLAR_BG, outline="")
        self._draw_background_stars(canvas, body_top=body_top, body_bottom=chrome.body_bottom, elapsed=elapsed)
        self._draw_top_bar(canvas, page, accent, dim, campaign)

        if page is TitlePage.WELCOME:
            self._draw_welcome_page(
                canvas, chrome, accent, dim, frame, campaign, hover_id, elapsed, codex,
            )
        elif page is TitlePage.MISSION:
            self._draw_mission_page(canvas, chrome, accent, dim, frame)
        elif page is TitlePage.HELM:
            self._draw_helm_page(canvas, chrome, accent, dim, frame)
        elif page is TitlePage.COMBAT:
            self._draw_combat_page(canvas, chrome, accent, dim, frame)
        else:
            scroll = clamp_scroll(deploy_scroll, compute_deploy_list_layout(chrome, screen_w=float(self.WIDTH)))
            self._draw_deploy_page(
                canvas,
                chrome,
                accent,
                dim,
                frame,
                deploy_focus=deploy_focus,
                deploy_scroll=scroll,
                hover_id=hover_id,
            )

        self._shop.draw_bazaar_cta(
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

    def _body_panel(self, chrome: TitleChromeLayout) -> tuple[float, float, float, float]:
        panel = compute_body_panel(chrome, screen_w=float(self.WIDTH))
        return panel.x, panel.y, panel.w, panel.h

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
        accent: str,
        dim: str,
        frame: str,
        *,
        deploy_focus: int,
        deploy_scroll: float,
        hover_id: str | None,
    ) -> None:
        layout = compute_deploy_list_layout(chrome, screen_w=float(self.WIDTH))
        scroll = clamp_scroll(deploy_scroll, layout)
        self.deploy_layout = layout

        x, y, w, h = layout.panel_x, layout.panel_y, layout.panel_w, layout.panel_h
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        draw_holo_corners(canvas, x, y, w, h, accent=accent)
        hp.draw_panel_title(canvas, x + 16, y + 14, "CHART MANIFEST", color=dim)
        hint = "↑ ↓ · wheel scroll · Enter" if layout.max_scroll > 0.0 else "Click row or ↑ ↓ + Enter"
        canvas.create_text(x + w - 16, y + 14, anchor="e", text=hint, fill=dim, font=hp.FONT_SMALL)

        vy0 = layout.viewport_y
        vy1 = layout.viewport_y + layout.viewport_h
        canvas.create_line(x + 12, vy0, x + w - 12, vy0, fill=frame, width=1)
        canvas.create_line(x + 12, vy1, x + w - 12, vy1, fill=frame, width=1)

        list_w = layout.viewport_w - (24.0 if layout.max_scroll > 0.0 else 0.0)
        for i, level_id in enumerate(LEVEL_ORDER):
            hit = visible_row_hit_rect(layout, i, scroll)
            if hit is None:
                continue
            hx, hy, hw, hh = hit
            region_id = f"level:{level_id}"
            self.hits.add(region_id, hx, hy, hw, hh)
            ry = row_screen_y(layout, i, scroll)
            label = LEVEL_LABELS.get(level_id, level_id)
            title = label.split(" — ", 1)[-1] if " — " in label else label
            draw_level_row(
                canvas,
                layout.viewport_x,
                ry,
                list_w,
                layout.row_h,
                index=i + 1,
                title=title,
                detail=_LEVEL_DETAILS.get(level_id, ""),
                accent=accent,
                dim=dim,
                frame=frame,
                unlocked=is_level_selectable(level_id),
                lock_reason=_LEVEL_LOCK.get(level_id, "Locked"),
                selected=i == deploy_focus,
                hover=hover_id == region_id,
            )

        # Rows can extend past the viewport; mask bleed then restore chrome.
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
        draw_holo_corners(canvas, x, y, w, h, accent=accent)

        self._draw_deploy_scrollbar(canvas, layout, scroll, accent=accent, dim=dim)

        canvas.create_text(
            x + 16,
            vy1 + 8,
            anchor="w",
            text="Power-up stacks persist for the whole campaign run.",
            fill=dim,
            font=hp.FONT_BODY,
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
        codex_layout = compute_codex_layout(layout)
        entry = codex_state.entry()
        p = layout.panel
        hp.draw_panel(canvas, p.x, p.y, p.w, p.h, frame=frame, accent=accent, fill=palette.HUD_BG)
        draw_holo_corners(canvas, p.x, p.y, p.w, p.h, accent=accent)
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

        lx = layout.left_x
        ly = p.y + 20.0
        canvas.create_text(lx, ly, anchor="w", text="GRAVITY HO,", fill=palette.TEXT, font=("Courier New", 28, "bold"))
        canvas.create_text(lx, ly + 34, anchor="w", text="MATEY!", fill=accent, font=("Courier New", 28, "bold"))
        draw_fitted_text(
            canvas,
            lx,
            ly + 78,
            "Chart cursed sectors, loot patrol skiffs, and escape the maw.",
            max_width=layout.left_w - 8,
            color=dim,
            font=self.FONT_SUBTITLE,
        )

        btn_w = min(240.0, layout.left_w - 4.0)
        btn_h = 44.0
        btn_x = lx
        btn_y = ly + 108
        self.hits.add("goto_deploy", btn_x, btn_y, btn_w, btn_h)
        draw_menu_button(
            canvas,
            btn_x,
            btn_y,
            btn_w,
            btn_h,
            "SELECT CHART →",
            accent=accent,
            dim=dim,
            frame=frame,
            hover=hover_id == "goto_deploy",
            selected=True,
        )

        draw_campaign_status_chip(
            canvas, lx, btn_y + btn_h + 14, campaign=campaign, accent=accent, dim=dim, frame=frame,
        )

        tips_y = btn_y + btn_h + 58
        canvas.create_text(
            lx,
            tips_y,
            anchor="w",
            text="Holo Bazaar below · B to trade",
            fill=accent,
            font=hp.FONT_BODY,
        )
        canvas.create_text(
            lx,
            tips_y + 20,
            anchor="w",
            text="↑ ↓ codex · ← → tabs · last tab = charts",
            fill=dim,
            font=hp.FONT_SMALL,
        )

    def _draw_mission_page(
        self, canvas: tk.Canvas, chrome: TitleChromeLayout, accent: str, dim: str, frame: str,
    ) -> None:
        x, y, w, h = self._body_panel(chrome)
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        draw_holo_corners(canvas, x, y, w, h, accent=accent)
        hp.draw_panel_title(canvas, x + 16, y + 14, "MISSION DIRECTIVE", color=dim)
        lines = [
            ("Objective", "Collect every nav beacon on the chart."),
            ("Exit", "All beacons logged unlocks the finish gate."),
            ("Loot", "Destroy patrol skiffs — fittings carry across charts."),
            ("Briefing", "Review the holo map before each launch."),
            ("Holo Bazaar", "Trade deck on nav station and between sectors."),
        ]
        ry = y + 42
        row_pitch = max(42.0, (h - 56) / max(1, len(lines)))
        for heading, body in lines:
            hp.draw_body_line(canvas, x + 20, ry, heading, color=accent, bold=True)
            draw_fitted_text(canvas, x + 20, ry + 18, body, max_width=w - 40, color=palette.TEXT, font=hp.FONT_BODY)
            ry += row_pitch

    def _draw_helm_page(self, canvas: tk.Canvas, chrome: TitleChromeLayout, accent: str, dim: str, frame: str) -> None:
        x, y, w, h = self._body_panel(chrome)
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        draw_holo_corners(canvas, x, y, w, h, accent=accent)
        hp.draw_panel_title(canvas, x + 16, y + 14, "HELM & WEAPONS", color=dim)
        rows = [
            ("A / D  ·  ← / →", "Rotate sail"),
            ("W  ·  ↑", "Main thrusters"),
            ("Shift", "Reactor burst"),
            ("Space", "Fire cannon"),
            ("V", "Tactical / chase camera"),
            ("E (hold)", "Land / ascend (Brood Moon)"),
            ("R", "Restart chart"),
            ("Esc", "Return to nav station"),
        ]
        row_pitch = max(28.0, (h - 52) / max(1, len(rows)))
        for i, (key, action) in enumerate(rows):
            hp.draw_key_value_row(
                canvas,
                x + 24,
                y + 42 + i * row_pitch,
                key,
                action,
                accent=accent,
                dim=palette.TEXT,
                key_width=132.0,
            )

    def _draw_combat_page(self, canvas: tk.Canvas, chrome: TitleChromeLayout, accent: str, dim: str, frame: str) -> None:
        x, y, w, h = self._body_panel(chrome)
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        draw_holo_corners(canvas, x, y, w, h, accent=accent)
        hp.draw_panel_title(canvas, x + 16, y + 14, "COMBAT & SURVIVAL", color=dim)
        col_w = (w - 48) / 2
        left_blocks = [
            ("Lives", "3 lives for the full campaign.", palette.TEXT),
            ("Hull", "3 chunks per life — chips respawn you.", palette.TEXT),
            ("Maw", "Singularity contact = life lost.", palette.HUD_WARN),
            ("Skiff scrape", "Patrol ram costs 1 hull chunk.", accent),
        ]
        right_blocks = [
            ("Void squid", "Tentacles cling — 1 chunk / 2s.", palette.SQUID_CORE),
            ("Asteroids", "Impact costs 1 hull chunk.", accent),
            ("Open drift", "5s off-chart = 1 chunk, no respawn.", palette.HUD_WARN),
        ]
        block_pitch = max(48.0, (h - 56) / max(4, len(left_blocks)))
        for i, (heading, body, color) in enumerate(left_blocks):
            rx = x + 20
            ry = y + 42 + i * block_pitch
            hp.draw_body_line(canvas, rx, ry, heading, color=accent, bold=True)
            draw_fitted_text(canvas, rx, ry + 18, body, max_width=col_w - 8, color=color, font=hp.FONT_BODY)
        for i, (heading, body, color) in enumerate(right_blocks):
            rx = x + 24 + col_w
            ry = y + 42 + i * block_pitch
            hp.draw_body_line(canvas, rx, ry, heading, color=accent, bold=True)
            draw_fitted_text(canvas, rx, ry + 18, body, max_width=col_w - 8, color=color, font=hp.FONT_BODY)

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
            center = "Select a chart · Enter confirms · wheel scrolls list · B opens Holo Bazaar"
        elif page is TitlePage.WELCOME:
            center = "Open Holo Bazaar to trade · Select Chart to launch"
        else:
            center = "Use PREV / NEXT tabs · B opens Holo Bazaar"
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
        tab_h = 22.0
        tab_y = chrome.rail_y + (chrome.rail_h - tab_h) * 0.5
        idx = TITLE_PAGE_ORDER.index(page)
        inner_w = self.WIDTH - self.MARGIN * 2
        tab_font = hp.FONT_BODY
        tab_pad = 12.0
        tab_gap = 6.0
        labels = [_PAGE_LABELS[terminal] for terminal in TITLE_PAGE_ORDER]
        tab_widths = [measure_text(label, tab_font) + tab_pad * 2 for label in labels]
        total_w = sum(tab_widths) + tab_gap * (len(tab_widths) - 1)
        start_x = self.MARGIN + max(0.0, (inner_w - total_w) * 0.5)
        tab_x = start_x
        for terminal, label, tab_w in zip(TITLE_PAGE_ORDER, labels, tab_widths):
            region_id = f"tab:{terminal.name.lower()}"
            self.hits.add(region_id, tab_x, tab_y, tab_w, tab_h)
            selected = terminal is page
            hover = hover_id == region_id
            draw_menu_button(
                canvas,
                tab_x,
                tab_y,
                tab_w,
                tab_h,
                label,
                accent=accent,
                dim=dim,
                frame=dim,
                active=True,
                selected=selected,
                hover=hover,
            )
            tab_x += tab_w + tab_gap
        pulse = 0.5 + 0.5 * math.sin(elapsed * 3.0)
        canvas.create_text(
            self.WIDTH / 2,
            chrome.rail_y - 6,
            text=TITLE_PAGE_ORDER[idx].name.replace("_", " ").title(),
            fill=accent if pulse > 0.5 else dim,
            font=hp.FONT_SMALL,
        )

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
