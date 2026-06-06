from __future__ import annotations

import tkinter as tk

from collections.abc import Callable

from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette


class TitleScreenOverlay:
    """Pre-flight briefing layout — matches in-game command HUD chrome."""

    WIDTH = 960
    HEIGHT = 640
    MARGIN = 20
    GUTTER = 16
    CENTER_LANE = 128
    TOP_BAR_H = 54
    TITLE_BLOCK_H = 76
    LAUNCH_STRIP_H = 52

    FONT_TITLE = ("Courier New", 30, "bold")
    FONT_SUBTITLE = ("Courier New", 11)
    FONT_LAUNCH = ("Courier New", 13, "bold")

    def draw(
        self,
        canvas: tk.Canvas,
        *,
        solar_unlocked: bool,
        draw_ship: Callable[[float, float], None] | None = None,
    ) -> None:
        accent = palette.HUD_ACCENT
        dim = palette.HUD_DIM
        frame = palette.HUD_FRAME

        canvas.create_rectangle(0, 0, self.WIDTH, self.HEIGHT, fill=palette.SOLAR_BG, outline="")
        self._draw_background_stars(canvas)

        canvas.create_rectangle(0, 0, self.WIDTH, self.TOP_BAR_H, fill=palette.HUD_BG, outline="")
        canvas.create_line(0, self.TOP_BAR_H, self.WIDTH, self.TOP_BAR_H, fill=accent, width=1)
        hp.draw_scanlines(canvas, 0, 0, self.WIDTH, self.TOP_BAR_H)
        canvas.create_text(
            self.WIDTH // 2,
            14,
            text="BRIGAND NAV STATION // PRE-FLIGHT",
            fill=dim,
            font=hp.FONT_SMALL,
        )
        canvas.create_text(
            self.WIDTH // 2,
            36,
            text="◈ GRAVITY HO, MATEY! ◈",
            fill=accent,
            font=("Courier New", 12, "bold"),
        )

        title_y = self.TOP_BAR_H + 12
        hp.draw_panel(canvas, self.MARGIN, title_y, self.WIDTH - self.MARGIN * 2, self.TITLE_BLOCK_H, frame=frame, accent=accent)
        canvas.create_text(
            self.WIDTH // 2,
            title_y + 28,
            text="GRAVITY HO, MATEY!",
            fill=palette.TEXT,
            font=self.FONT_TITLE,
        )
        canvas.create_text(
            self.WIDTH // 2,
            title_y + 58,
            text="Pirate gravity races through cursed coves and cursed star charts",
            fill=dim,
            font=self.FONT_SUBTITLE,
        )

        col_y = title_y + self.TITLE_BLOCK_H + 14
        col_w = (self.WIDTH - self.MARGIN * 2 - self.CENTER_LANE) // 2
        left_x = self.MARGIN
        center_x = self.MARGIN + col_w
        right_x = self.MARGIN + col_w + self.CENTER_LANE
        row_h = 196

        self._draw_mission_panel(canvas, left_x, col_y, col_w, row_h, accent, dim, frame)
        self._draw_controls_panel(canvas, right_x, col_y, col_w, row_h, accent, dim, frame)
        self._draw_center_vessel_lane(canvas, center_x, col_y, self.CENTER_LANE, row_h, accent, dim, frame, draw_ship)

        row2_y = col_y + row_h + 14
        row2_h = 118
        row2_w = (self.WIDTH - self.MARGIN * 2 - self.GUTTER) // 2
        self._draw_survival_panel(canvas, self.MARGIN, row2_y, row2_w, row2_h, accent, dim, frame)
        self._draw_deploy_panel(
            canvas,
            self.MARGIN + row2_w + self.GUTTER,
            row2_y,
            row2_w,
            row2_h,
            solar_unlocked,
            accent,
            dim,
            frame,
        )

        launch_y = self.HEIGHT - self.LAUNCH_STRIP_H - 14
        hp.draw_panel(canvas, self.MARGIN, launch_y, self.WIDTH - self.MARGIN * 2, self.LAUNCH_STRIP_H, frame=frame, accent=accent)
        canvas.create_text(
            self.WIDTH // 2,
            launch_y + 26,
            text="◈  PRESS ENTER — LAUNCH CAMPAIGN AT SMUGGLER'S COVE  ◈",
            fill=palette.HUD_LOOT_NEW,
            font=self.FONT_LAUNCH,
        )

    def _draw_background_stars(self, canvas: tk.Canvas) -> None:
        for i in range(120):
            x = (i * 83 + 17) % self.WIDTH
            y = (i * 47 + 31) % self.HEIGHT
            size = 3 if i % 5 == 0 else 2
            tone = "#3a5570" if i % 7 == 0 else "#294764"
            canvas.create_rectangle(x, y, x + size, y + size, fill=tone, outline="")

    def _draw_center_vessel_lane(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        width: float,
        height: float,
        accent: str,
        dim: str,
        frame: str,
        draw_ship,
    ) -> None:
        hp.draw_panel(canvas, x, y, width, height, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, x + 8, y + 10, "VESSEL", color=dim)
        if draw_ship is not None:
            draw_ship(x + width / 2, y + height / 2 + 8)

    def _draw_mission_panel(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        w: float,
        h: float,
        accent: str,
        dim: str,
        frame: str,
    ) -> None:
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, x + 10, y + 10, "MISSION DIRECTIVE", color=dim)
        lines = [
            "Collect every nav beacon on the chart.",
            "Unlock the finish gate and escape.",
            "Sink patrol skiffs — loot carries across charts.",
        ]
        for i, line in enumerate(lines):
            hp.draw_body_line(canvas, x + 14, y + 34 + i * 22, f"▸ {line}", color=palette.TEXT)

    def _draw_controls_panel(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        w: float,
        h: float,
        accent: str,
        dim: str,
        frame: str,
    ) -> None:
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, x + 10, y + 10, "HELM CONTROLS", color=dim)
        rows = [
            ("A / D  ·  ← / →", "Rotate sail"),
            ("W  ·  ↑", "Thrust"),
            ("Shift (tap)", "Reactor burst — nose kick"),
            ("Space", "Fire curved cannon"),
            ("R", "Restart current chart"),
            ("Esc", "Return to station"),
        ]
        for i, (key, action) in enumerate(rows):
            hp.draw_key_value_row(canvas, x + 14, y + 32 + i * 22, key, action, accent=accent, dim=dim, key_width=118.0)

    def _draw_survival_panel(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        w: float,
        h: float,
        accent: str,
        dim: str,
        frame: str,
    ) -> None:
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, x + 10, y + 10, "COMBAT & SURVIVAL", color=dim)
        lines = [
            ("3 campaign lives  ·  3 hull chunks per life", palette.TEXT),
            ("Planet wells & singularity: LETHAL (whole life)", palette.HUD_WARN),
            ("Reef / wall / skiff scrape: 1 chunk + respawn", accent),
        ]
        for i, (line, color) in enumerate(lines):
            hp.draw_body_line(canvas, x + 14, y + 34 + i * 22, f"▸ {line}", color=color)

    def _draw_deploy_panel(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        w: float,
        h: float,
        solar_unlocked: bool,
        accent: str,
        dim: str,
        frame: str,
    ) -> None:
        hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent)
        hp.draw_panel_title(canvas, x + 10, y + 10, "CHART SELECTION", color=dim)

        hp.draw_key_value_row(
            canvas,
            x + 14,
            y + 36,
            "Enter  ·  1",
            "Full campaign — Smuggler's Cove",
            accent=accent,
            dim=palette.TEXT,
            key_width=88.0,
        )

        if solar_unlocked:
            level_line = "Singularity Crossing — unlocked"
            level_color = palette.HUD_LOOT_NEW
            key_text = "2"
        else:
            level_line = "Singularity Crossing — locked (clear Cove first)"
            level_color = dim
            key_text = "2  ✕"

        hp.draw_key_value_row(
            canvas,
            x + 14,
            y + 62,
            key_text,
            level_line,
            accent=accent if solar_unlocked else dim,
            dim=level_color,
            key_width=88.0,
        )

        hp.draw_body_line(
            canvas,
            x + 14,
            y + 90,
            "Power-ups persist for the whole campaign.",
            color=dim,
        )
