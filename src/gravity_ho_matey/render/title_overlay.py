from __future__ import annotations

import math
import tkinter as tk
from collections.abc import Callable
from enum import Enum, auto

from gravity_ho_matey.gameplay.progress import is_level_selectable
from gravity_ho_matey.levels.level_registry import LEVEL_LABELS, LEVEL_ORDER
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.menu_ui import MenuHitMap, draw_fitted_text, draw_holo_corners, draw_level_row, draw_menu_button
from gravity_ho_matey.settings import DEV_UNLOCK_ALL_LEVELS

_LEVEL_DETAILS: dict[str, str] = {
    "cove": "Beacon run · gravity wells · training chart",
    "solar": "Vertical strip · patrol skiffs · singularity",
    "drift": "Open belts · void squids · north exit",
    "rift": "Boost braids · void pockets · Brood-Mother",
}

_LEVEL_LOCK: dict[str, str] = {
    "cove": "",
    "solar": "Clear Cove first",
    "drift": "Clear Solar first",
    "rift": "Clear Drift first",
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
    FOOTER_H = 58
    FONT_TITLE = ("Courier New", 32, "bold")
    FONT_SUBTITLE = ("Courier New", 11)

    def __init__(self) -> None:
        self.hits = MenuHitMap()

    def draw(
        self,
        canvas: tk.Canvas,
        *,
        page: TitlePage,
        solar_unlocked: bool,
        drift_unlocked: bool = False,
        rift_unlocked: bool = False,
        draw_ship: Callable[[float, float], None] | None = None,
        deploy_focus: int = 0,
        hover_id: str | None = None,
        elapsed: float = 0.0,
    ) -> None:
        self.hits.clear()
        accent = palette.HUD_ACCENT
        dim = palette.HUD_DIM
        frame = palette.HUD_FRAME

        canvas.create_rectangle(0, 0, self.WIDTH, self.HEIGHT, fill=palette.SOLAR_BG, outline="")
        self._draw_background_stars(canvas)
        self._draw_top_bar(canvas, page, accent, dim)

        body_top = self.TOP_BAR_H + 14
        body_bottom = self.HEIGHT - self.FOOTER_H - 14
        body_h = body_bottom - body_top

        if page is TitlePage.WELCOME:
            self._draw_welcome_page(canvas, body_top, body_h, accent, dim, frame, draw_ship, hover_id)
        elif page is TitlePage.MISSION:
            self._draw_mission_page(canvas, body_top, body_h, accent, dim, frame)
        elif page is TitlePage.HELM:
            self._draw_helm_page(canvas, body_top, body_h, accent, dim, frame)
        elif page is TitlePage.COMBAT:
            self._draw_combat_page(canvas, body_top, body_h, accent, dim, frame)
        else:
            self._draw_deploy_page(
                canvas,
                body_top,
                body_h,
                accent,
                dim,
                frame,
                deploy_focus=deploy_focus,
                hover_id=hover_id,
            )

        self._draw_footer(canvas, page, solar_unlocked, drift_unlocked, rift_unlocked, accent, dim, frame, hover_id)
        self._draw_page_rail(canvas, page, accent, dim, hover_id, elapsed)

    def _draw_top_bar(self, canvas: tk.Canvas, page: TitlePage, accent: str, dim: str) -> None:
        canvas.create_rectangle(0, 0, self.WIDTH, self.TOP_BAR_H, fill=palette.HUD_BG, outline="")
        canvas.create_line(0, self.TOP_BAR_H, self.WIDTH, self.TOP_BAR_H, fill=accent, width=1)
        hp.draw_scanlines(canvas, 0, 0, self.WIDTH, self.TOP_BAR_H)
        idx = TITLE_PAGE_ORDER.index(page) + 1
        canvas.create_text(self.MARGIN, 18, anchor="w", text=f"TAB {idx}/{len(TITLE_PAGE_ORDER)}", fill=dim, font=hp.FONT_SMALL)
        canvas.create_text(self.WIDTH // 2, 18, text="BRIGAND NAV STATION", fill=dim, font=hp.FONT_SMALL)
        canvas.create_text(self.WIDTH // 2, 36, text=_PAGE_LABELS[page], fill=accent, font=hp.FONT_SECTION)
        canvas.create_text(self.WIDTH - self.MARGIN, 26, anchor="e", text="GRAVITY HO, MATEY!", fill=accent, font=hp.FONT_SMALL)
        if DEV_UNLOCK_ALL_LEVELS:
            canvas.create_text(
                self.WIDTH - self.MARGIN,
                42,
                anchor="e",
                text="DEV — ALL CHARTS",
                fill=palette.HUD_WARN,
                font=hp.FONT_SMALL,
            )

    def _center_panel(self, height: float, *, width: float = 760.0) -> tuple[float, float, float, float]:
        x = (self.WIDTH - width) / 2
        y = self.TOP_BAR_H + 14 + max(0.0, (self.HEIGHT - self.TOP_BAR_H - self.FOOTER_H - 28 - height) / 2)
        return x, y, width, height

    def _draw_welcome_page(
        self,
        canvas: tk.Canvas,
        body_top: float,
        body_h: float,
        accent: str,
        dim: str,
        frame: str,
        draw_ship: Callable[[float, float], None] | None,
        hover_id: str | None,
    ) -> None:
        panel_h = min(body_h, 400.0)
        x, y, w, h = self._center_panel(panel_h, width=900.0)
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        draw_holo_corners(canvas, x, y, w, h, accent=accent)

        left_w = w * 0.52
        canvas.create_text(x + 24, y + 36, anchor="w", text="GRAVITY HO, MATEY!", fill=palette.TEXT, font=self.FONT_TITLE)
        draw_fitted_text(
            canvas,
            x + 24,
            y + 82,
            "Chart cursed sectors, loot patrol skiffs, and escape the maw.",
            max_width=left_w - 40,
            color=dim,
            font=self.FONT_SUBTITLE,
        )

        btn_w = 220.0
        btn_h = 40.0
        btn_x = x + 24
        btn_y = y + 118
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

        canvas.create_text(x + 24, y + 178, anchor="w", text="Click a chart or use ↑ ↓ on Select Chart tab.", fill=accent, font=hp.FONT_BODY)
        canvas.create_text(x + 24, y + 200, anchor="w", text="← → switches briefing tabs · mouse supported.", fill=dim, font=hp.FONT_BODY)

        vessel_x = x + left_w + 8
        vessel_w = w - left_w - 16
        hp.draw_panel(canvas, vessel_x, y + 16, vessel_w, h - 32, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, vessel_x + 12, y + 28, "BRIGAND SKIFF", color=dim)
        if draw_ship is not None:
            draw_ship(vessel_x + vessel_w / 2, y + h / 2 + 8)

    def _draw_mission_page(self, canvas: tk.Canvas, body_top: float, body_h: float, accent: str, dim: str, frame: str) -> None:
        x, y, w, h = self._center_panel(min(body_h, 340.0))
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        hp.draw_panel_title(canvas, x + 16, y + 14, "MISSION DIRECTIVE", color=dim)
        lines = [
            ("Objective", "Collect every nav beacon on the chart."),
            ("Exit", "All beacons logged unlocks the finish gate."),
            ("Loot", "Destroy patrol skiffs — fittings carry across charts."),
            ("Briefing", "Review the holo map before each launch."),
        ]
        ry = y + 42
        for heading, body in lines:
            hp.draw_body_line(canvas, x + 20, ry, heading, color=accent, bold=True)
            draw_fitted_text(canvas, x + 20, ry + 18, body, max_width=w - 40, color=palette.TEXT, font=hp.FONT_BODY)
            ry += 46

    def _draw_helm_page(self, canvas: tk.Canvas, body_top: float, body_h: float, accent: str, dim: str, frame: str) -> None:
        x, y, w, h = self._center_panel(min(body_h, 360.0))
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        hp.draw_panel_title(canvas, x + 16, y + 14, "HELM & WEAPONS", color=dim)
        rows = [
            ("A / D  ·  ← / →", "Rotate sail"),
            ("W  ·  ↑", "Main thrusters"),
            ("Shift", "Reactor burst"),
            ("Space", "Fire cannon"),
            ("V", "Tactical / chase camera"),
            ("R", "Restart chart"),
            ("Esc", "Return to nav station"),
        ]
        for i, (key, action) in enumerate(rows):
            hp.draw_key_value_row(
                canvas,
                x + 24,
                y + 42 + i * 28,
                key,
                action,
                accent=accent,
                dim=palette.TEXT,
                key_width=132.0,
            )

    def _draw_combat_page(self, canvas: tk.Canvas, body_top: float, body_h: float, accent: str, dim: str, frame: str) -> None:
        x, y, w, h = self._center_panel(min(body_h, 380.0))
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
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
        for i, (heading, body, color) in enumerate(left_blocks):
            rx = x + 20
            ry = y + 42 + i * 52
            hp.draw_body_line(canvas, rx, ry, heading, color=accent, bold=True)
            draw_fitted_text(canvas, rx, ry + 18, body, max_width=col_w - 8, color=color, font=hp.FONT_BODY)
        for i, (heading, body, color) in enumerate(right_blocks):
            rx = x + 24 + col_w
            ry = y + 42 + i * 52
            hp.draw_body_line(canvas, rx, ry, heading, color=accent, bold=True)
            draw_fitted_text(canvas, rx, ry + 18, body, max_width=col_w - 8, color=color, font=hp.FONT_BODY)

    def _draw_deploy_page(
        self,
        canvas: tk.Canvas,
        body_top: float,
        body_h: float,
        accent: str,
        dim: str,
        frame: str,
        *,
        deploy_focus: int,
        hover_id: str | None,
    ) -> None:
        panel_h = min(body_h, 380.0)
        x, y, w, h = self._center_panel(panel_h, width=820.0)
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        draw_holo_corners(canvas, x, y, w, h, accent=accent)
        hp.draw_panel_title(canvas, x + 16, y + 14, "CHART MANIFEST", color=dim)
        canvas.create_text(x + w - 16, y + 14, anchor="e", text="Click row or ↑ ↓ + Enter", fill=dim, font=hp.FONT_SMALL)

        row_h = 68.0
        row_gap = 10.0
        list_y = y + 38
        list_h = len(LEVEL_ORDER) * row_h + (len(LEVEL_ORDER) - 1) * row_gap
        for i, level_id in enumerate(LEVEL_ORDER):
            unlocked = is_level_selectable(level_id)
            ry = list_y + i * (row_h + row_gap)
            region_id = f"level:{level_id}"
            self.hits.add(region_id, x + 12, ry, w - 24, row_h)
            label = LEVEL_LABELS.get(level_id, level_id)
            title = label.split(" — ", 1)[-1] if " — " in label else label
            draw_level_row(
                canvas,
                x + 12,
                ry,
                w - 24,
                row_h,
                index=i + 1,
                title=title,
                detail=_LEVEL_DETAILS.get(level_id, ""),
                accent=accent,
                dim=dim,
                frame=frame,
                unlocked=unlocked,
                lock_reason=_LEVEL_LOCK.get(level_id, "Locked"),
                selected=i == deploy_focus,
                hover=hover_id == region_id,
            )

        canvas.create_text(
            x + 16,
            list_y + list_h + 14,
            anchor="w",
            text="Power-up stacks persist for the whole campaign run.",
            fill=dim,
            font=hp.FONT_BODY,
        )

    def _draw_footer(
        self,
        canvas: tk.Canvas,
        page: TitlePage,
        solar_unlocked: bool,
        drift_unlocked: bool,
        rift_unlocked: bool,
        accent: str,
        dim: str,
        frame: str,
        hover_id: str | None,
    ) -> None:
        y = self.HEIGHT - self.FOOTER_H - 6
        hp.draw_panel(canvas, self.MARGIN, y, self.WIDTH - self.MARGIN * 2, self.FOOTER_H, frame=frame, accent=accent, fill=palette.HUD_BG)

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
            center = "Select a chart · Enter confirms · click row to open holo briefing"
        elif page is TitlePage.WELCOME:
            center = "Open Select Chart tab or click SELECT CHART"
        else:
            center = "Use PREV / NEXT tabs · Select Chart to launch"
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
        accent: str,
        dim: str,
        hover_id: str | None,
        elapsed: float,
    ) -> None:
        rail_y = self.HEIGHT - self.FOOTER_H - 22
        count = len(TITLE_PAGE_ORDER)
        idx = TITLE_PAGE_ORDER.index(page)
        spacing = 72.0
        start_x = self.WIDTH / 2 - (count - 1) * spacing / 2
        for i, terminal in enumerate(TITLE_PAGE_ORDER):
            tab_x = start_x + i * spacing - 28
            tab_w = 56.0
            tab_h = 18.0
            tab_y = rail_y - 8
            region_id = f"tab:{terminal.name.lower()}"
            self.hits.add(region_id, tab_x, tab_y, tab_w, tab_h)
            selected = terminal is page
            hover = hover_id == region_id
            label = _PAGE_LABELS[terminal][:8]
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
        pulse = 0.5 + 0.5 * math.sin(elapsed * 3.0)
        canvas.create_text(
            self.WIDTH // 2,
            rail_y - 18,
            text=TITLE_PAGE_ORDER[idx].name.replace("_", " ").title(),
            fill=accent if pulse > 0.5 else dim,
            font=hp.FONT_SMALL,
        )

    def _draw_background_stars(self, canvas: tk.Canvas) -> None:
        for i in range(100):
            sx = (i * 83 + 17) % self.WIDTH
            sy = (i * 47 + 31) % self.HEIGHT
            size = 3 if i % 5 == 0 else 2
            tone = "#3a5570" if i % 7 == 0 else "#294764"
            canvas.create_rectangle(sx, sy, sx + size, sy + size, fill=tone, outline="")
