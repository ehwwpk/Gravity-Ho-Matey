from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from enum import Enum, auto

from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette


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
    TitlePage.MISSION: "MISSION DIRECTIVE",
    TitlePage.HELM: "HELM CONTROLS",
    TitlePage.COMBAT: "COMBAT DOCTRINE",
    TitlePage.DEPLOY: "CHART SELECTION",
}


class TitleScreenOverlay:
    """Paginated pre-flight terminals — one focused briefing per screen."""

    WIDTH = 960
    HEIGHT = 640
    MARGIN = 20
    TOP_BAR_H = 54
    FOOTER_H = 52
    FONT_TITLE = ("Courier New", 34, "bold")
    FONT_HERO = ("Courier New", 15, "bold")
    FONT_SUBTITLE = ("Courier New", 11)
    FONT_LAUNCH = ("Courier New", 13, "bold")

    def draw(
        self,
        canvas: tk.Canvas,
        *,
        page: TitlePage,
        solar_unlocked: bool,
        draw_ship: Callable[[float, float], None] | None = None,
    ) -> None:
        accent = palette.HUD_ACCENT
        dim = palette.HUD_DIM
        frame = palette.HUD_FRAME

        canvas.create_rectangle(0, 0, self.WIDTH, self.HEIGHT, fill=palette.SOLAR_BG, outline="")
        self._draw_background_stars(canvas)
        self._draw_top_bar(canvas, page, accent, dim)

        body_top = self.TOP_BAR_H + 16
        body_bottom = self.HEIGHT - self.FOOTER_H - 18
        body_h = body_bottom - body_top

        if page is TitlePage.WELCOME:
            self._draw_welcome_page(canvas, body_top, body_h, accent, dim, frame, draw_ship)
        elif page is TitlePage.MISSION:
            self._draw_mission_page(canvas, body_top, body_h, accent, dim, frame)
        elif page is TitlePage.HELM:
            self._draw_helm_page(canvas, body_top, body_h, accent, dim, frame)
        elif page is TitlePage.COMBAT:
            self._draw_combat_page(canvas, body_top, body_h, accent, dim, frame)
        else:
            self._draw_deploy_page(canvas, body_top, body_h, solar_unlocked, accent, dim, frame)

        self._draw_footer(canvas, page, solar_unlocked, accent, dim, frame)
        self._draw_page_rail(canvas, page, accent, dim)

    def _draw_top_bar(self, canvas: tk.Canvas, page: TitlePage, accent: str, dim: str) -> None:
        canvas.create_rectangle(0, 0, self.WIDTH, self.TOP_BAR_H, fill=palette.HUD_BG, outline="")
        canvas.create_line(0, self.TOP_BAR_H, self.WIDTH, self.TOP_BAR_H, fill=accent, width=1)
        hp.draw_scanlines(canvas, 0, 0, self.WIDTH, self.TOP_BAR_H)
        idx = TITLE_PAGE_ORDER.index(page) + 1
        canvas.create_text(
            self.MARGIN,
            18,
            anchor="w",
            text=f"TERMINAL {idx}/{len(TITLE_PAGE_ORDER)}",
            fill=dim,
            font=hp.FONT_SMALL,
        )
        canvas.create_text(
            self.WIDTH // 2,
            16,
            text="BRIGAND NAV STATION // PRE-FLIGHT",
            fill=dim,
            font=hp.FONT_SMALL,
        )
        canvas.create_text(
            self.WIDTH // 2,
            36,
            text=f"◈ {_PAGE_LABELS[page]} ◈",
            fill=accent,
            font=("Courier New", 12, "bold"),
        )
        canvas.create_text(
            self.WIDTH - self.MARGIN,
            18,
            anchor="e",
            text="GRAVITY HO, MATEY!",
            fill=accent,
            font=hp.FONT_SMALL,
        )

    def _center_panel(self, height: float, *, width: float = 720.0) -> tuple[float, float, float, float]:
        x = (self.WIDTH - width) / 2
        y = self.TOP_BAR_H + 16 + max(0.0, (self.HEIGHT - self.TOP_BAR_H - self.FOOTER_H - 34 - height) / 2)
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
    ) -> None:
        panel_h = min(body_h, 420.0)
        x, y, w, h = self._center_panel(panel_h, width=880.0)
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)

        left_w = w * 0.56
        canvas.create_text(
            x + 28,
            y + 42,
            anchor="w",
            text="GRAVITY HO, MATEY!",
            fill=palette.TEXT,
            font=self.FONT_TITLE,
        )
        canvas.create_text(
            x + 28,
            y + 88,
            anchor="w",
            text="Pirate gravity races through cursed coves and star charts.",
            fill=dim,
            font=self.FONT_SUBTITLE,
        )
        canvas.create_text(
            x + 28,
            y + 118,
            anchor="w",
            text="Chart the void. Loot patrol skiffs. Escape before the maw takes you.",
            fill=dim,
            font=self.FONT_SUBTITLE,
        )

        hp.draw_panel(canvas, x + 24, y + 150, left_w - 48, 88, frame=frame, accent=accent)
        canvas.create_text(
            x + 40,
            y + 168,
            anchor="w",
            text="READY TO DEPLOY",
            fill=dim,
            font=hp.FONT_SMALL,
        )
        canvas.create_text(
            x + 40,
            y + 192,
            anchor="w",
            text="Enter opens the holo chart for Smuggler's Cove.",
            fill=palette.TEXT,
            font=hp.FONT_BODY,
        )
        canvas.create_text(
            x + 40,
            y + 214,
            anchor="w",
            text="← → browse briefing terminals before launch.",
            fill=accent,
            font=hp.FONT_BODY,
        )

        vessel_x = x + left_w + 12
        vessel_w = w - left_w - 24
        hp.draw_panel(canvas, vessel_x, y + 24, vessel_w, h - 48, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, vessel_x + 12, y + 36, "BRIGAND SKIFF — PREVIEW", color=dim)
        if draw_ship is not None:
            draw_ship(vessel_x + vessel_w / 2, y + h / 2 + 12)

    def _draw_mission_page(self, canvas: tk.Canvas, body_top: float, body_h: float, accent: str, dim: str, frame: str) -> None:
        x, y, w, h = self._center_panel(min(body_h, 360.0))
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        hp.draw_panel_title(canvas, x + 16, y + 14, "MISSION DIRECTIVE", color=dim)
        lines = [
            ("Primary objective", "Collect every nav beacon marked on the sector chart."),
            ("Exit protocol", "Once all beacons are logged, the finish gate unlocks — reach it to clear the chart."),
            ("Campaign loot", "Destroy patrol skiffs to recover fittings. Stacks persist across charts."),
            ("Recon", "Review the holo map before each launch — wells, hazards, and spawn are plotted."),
        ]
        ry = y + 44
        for heading, body in lines:
            hp.draw_body_line(canvas, x + 20, ry, heading, color=accent, bold=True)
            hp.draw_body_line(canvas, x + 20, ry + 20, body, color=palette.TEXT)
            ry += 54

    def _draw_helm_page(self, canvas: tk.Canvas, body_top: float, body_h: float, accent: str, dim: str, frame: str) -> None:
        x, y, w, h = self._center_panel(min(body_h, 380.0))
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        hp.draw_panel_title(canvas, x + 16, y + 14, "HELM & WEAPONS", color=dim)

        rows = [
            ("A / D  ·  ← / →", "Rotate sail"),
            ("W  ·  ↑", "Main thrusters"),
            ("Shift (tap)", "Reactor burst — nose kick"),
            ("Space", "Fire curved cannon"),
            ("V", "Toggle tactical chart / follow-cam"),
            ("R", "Restart current chart"),
            ("Esc", "Return to nav station"),
        ]
        for i, (key, action) in enumerate(rows):
            hp.draw_key_value_row(
                canvas,
                x + 24,
                y + 44 + i * 30,
                key,
                action,
                accent=accent,
                dim=palette.TEXT,
                key_width=140.0,
            )

        hp.draw_panel(canvas, x + 24, y + h - 62, w - 48, 44, frame=frame, accent=accent)
        hp.draw_body_line(
            canvas,
            x + 36,
            y + h - 44,
            "Follow-cam is easier for beacons and dogfights; tactical chart shows the whole sector.",
            color=dim,
        )

    def _draw_combat_page(self, canvas: tk.Canvas, body_top: float, body_h: float, accent: str, dim: str, frame: str) -> None:
        x, y, w, h = self._center_panel(min(body_h, 360.0))
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        hp.draw_panel_title(canvas, x + 16, y + 14, "COMBAT & SURVIVAL", color=dim)

        blocks = [
            ("Campaign lives", "3 lives for the full run.", palette.TEXT),
            ("Hull integrity", "3 chunks per life — chip damage respawns you on-chart.", palette.TEXT),
            ("Singularity / maw", "Instant life loss — treat gravity wells as lethal hazards.", palette.HUD_WARN),
            ("Reef & skiff scrape", "1 hull chunk + brief respawn at last spawn.", accent),
            ("Drifting rock", "Asteroid impact costs 1 chunk — ring clusters drift on set paths.", accent),
            ("Off-chart drift", "Open sectors: 5s void exposure = 1 chunk, no respawn.", palette.HUD_WARN),
        ]
        ry = y + 44
        for heading, body, color in blocks:
            hp.draw_body_line(canvas, x + 20, ry, heading, color=accent, bold=True)
            hp.draw_body_line(canvas, x + 20, ry + 20, body, color=color)
            ry += 48

    def _draw_deploy_page(
        self,
        canvas: tk.Canvas,
        body_top: float,
        body_h: float,
        solar_unlocked: bool,
        accent: str,
        dim: str,
        frame: str,
    ) -> None:
        panel_h = min(body_h, 340.0)
        x, y, w, h = self._center_panel(panel_h)
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
        hp.draw_panel_title(canvas, x + 16, y + 14, "SELECT CHART", color=dim)

        card_w = (w - 56) / 2
        self._draw_chart_card(
            canvas,
            x + 20,
            y + 44,
            card_w,
            h - 68,
            chart_key="Enter  ·  1",
            title="Smuggler's Cove",
            subtitle="Sector 1 — intro chart",
            detail="Light asteroid field · gravity wells · nav beacons",
            accent=accent,
            dim=dim,
            frame=frame,
            active=True,
        )
        self._draw_chart_card(
            canvas,
            x + 32 + card_w,
            y + 44,
            card_w,
            h - 68,
            chart_key="2" if solar_unlocked else "2  ✕",
            title="Singularity Crossing",
            subtitle="Sector 2 — vertical star strip",
            detail="Patrol skiffs · black hole · stacked loot",
            accent=accent if solar_unlocked else dim,
            dim=dim if solar_unlocked else dim,
            frame=frame,
            active=solar_unlocked,
            locked=not solar_unlocked,
        )

        hp.draw_body_line(
            canvas,
            x + 20,
            y + h - 22,
            "Power-up stacks carry for the whole campaign.",
            color=dim,
        )

    def _draw_chart_card(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        chart_key: str,
        title: str,
        subtitle: str,
        detail: str,
        accent: str,
        dim: str,
        frame: str,
        active: bool,
        locked: bool = False,
    ) -> None:
        border = accent if active else frame
        hp.draw_panel(canvas, x, y, w, h, frame=border, accent=accent, fill="#060810")
        hp.draw_key_value_row(canvas, x + 14, y + 16, chart_key, title, accent=accent if active else dim, dim=accent if active else dim, key_width=72.0)
        hp.draw_body_line(canvas, x + 14, y + 46, subtitle, color=dim)
        hp.draw_body_line(canvas, x + 14, y + 72, detail, color=palette.TEXT if active else dim)
        if locked:
            canvas.create_text(
                x + w / 2,
                y + h - 28,
                text="Clear Cove to unlock",
                fill=dim,
                font=hp.FONT_BODY,
            )
        else:
            canvas.create_text(
                x + w / 2,
                y + h - 28,
                text="Opens holo chart briefing",
                fill=accent,
                font=hp.FONT_BODY,
            )

    def _draw_footer(self, canvas: tk.Canvas, page: TitlePage, solar_unlocked: bool, accent: str, dim: str, frame: str) -> None:
        y = self.HEIGHT - self.FOOTER_H - 10
        hp.draw_panel(canvas, self.MARGIN, y, self.WIDTH - self.MARGIN * 2, self.FOOTER_H, frame=frame, accent=accent, fill=palette.HUD_BG)

        hp.draw_key_value_row(canvas, self.MARGIN + 16, y + 16, "←  →", "Browse terminals", accent=accent, dim=dim, key_width=52.0)

        if page is TitlePage.DEPLOY:
            center = "Enter / 1 — Cove holo chart   ·   2 — Solar (if unlocked)"
        elif page is TitlePage.WELCOME:
            center = "Enter — Open holo chart & launch at Smuggler's Cove"
        else:
            center = "Enter — Launch campaign   ·   Continue browsing with ← →"
        canvas.create_text(self.WIDTH // 2, y + 26, text=center, fill=palette.HUD_LOOT_NEW, font=self.FONT_LAUNCH)

        hint = "Solar unlocked" if solar_unlocked else "Solar locked"
        canvas.create_text(self.WIDTH - self.MARGIN - 16, y + 26, anchor="e", text=hint, fill=dim, font=hp.FONT_SMALL)

    def _draw_page_rail(self, canvas: tk.Canvas, page: TitlePage, accent: str, dim: str) -> None:
        rail_y = self.HEIGHT - self.FOOTER_H - 28
        count = len(TITLE_PAGE_ORDER)
        idx = TITLE_PAGE_ORDER.index(page)
        spacing = 18
        start_x = self.WIDTH / 2 - (count - 1) * spacing / 2
        for i, terminal in enumerate(TITLE_PAGE_ORDER):
            cx = start_x + i * spacing
            fill = accent if terminal is page else dim
            r = 4 if terminal is page else 3
            canvas.create_oval(cx - r, rail_y - r, cx + r, rail_y + r, fill=fill, outline="")
        canvas.create_text(
            self.WIDTH // 2,
            rail_y - 14,
            text=_PAGE_LABELS[TITLE_PAGE_ORDER[idx]],
            fill=dim,
            font=hp.FONT_SMALL,
        )

    def _draw_background_stars(self, canvas: tk.Canvas) -> None:
        for i in range(120):
            x = (i * 83 + 17) % self.WIDTH
            y = (i * 47 + 31) % self.HEIGHT
            size = 3 if i % 5 == 0 else 2
            tone = "#3a5570" if i % 7 == 0 else "#294764"
            canvas.create_rectangle(x, y, x + size, y + size, fill=tone, outline="")
