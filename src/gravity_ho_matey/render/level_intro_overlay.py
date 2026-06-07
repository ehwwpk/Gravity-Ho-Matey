from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.levels.level_registry import LEVEL_LABELS
from gravity_ho_matey.narrative.level_intros import LevelIntroSpec
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.launch_countdown_overlay import accent_for_theme
from gravity_ho_matey.render.menu_ui import MenuHitMap, draw_fitted_text, draw_holo_corners, draw_menu_button

_HEADER_H = 54
_FOOTER_H = 72
_MARGIN = 14
_INNER_PAD = 10


class LevelIntroOverlay:
    """Holo command-deck frame for pre-level narrative GIFs — matches chart / play HUD."""

    def __init__(self) -> None:
        self.hits = MenuHitMap()

    def draw(
        self,
        canvas: tk.Canvas,
        *,
        level_id: str,
        spec: LevelIntroSpec,
        frame_image: tk.PhotoImage,
        elapsed: float,
        playback_seconds: float,
        progress: float,
        hover_id: str | None = None,
    ) -> None:
        self.hits.clear()
        vw = 960
        vh = 640
        accent = accent_for_theme(level_id)
        dim = palette.HUD_DIM
        frame = palette.HUD_FRAME
        bg = palette.HUD_BG

        canvas.create_rectangle(0, 0, vw, vh, fill=palette.BACKGROUND, outline="")
        self._starfield(canvas, vw, vh)
        self._draw_header(canvas, vw, level_id, spec, accent, dim, frame, bg, elapsed)
        body_top = _HEADER_H + 8
        footer_top = vh - _FOOTER_H - 6
        body_h = footer_top - body_top - 8
        panel_x = _MARGIN
        panel_w = vw - 2 * _MARGIN
        hp.draw_panel(canvas, panel_x, body_top, panel_w, body_h, frame=frame, accent=accent, fill=bg)
        draw_holo_corners(canvas, panel_x, body_top, panel_w, body_h, accent=accent, elapsed=elapsed)

        viewport_x = panel_x + _INNER_PAD
        viewport_y = body_top + _INNER_PAD
        viewport_w = panel_w - 2 * _INNER_PAD
        viewport_h = body_h - 2 * _INNER_PAD
        canvas.create_rectangle(
            viewport_x,
            viewport_y,
            viewport_x + viewport_w,
            viewport_y + viewport_h,
            outline=frame,
            fill="#040810",
            width=1,
        )
        draw_holo_corners(
            canvas,
            viewport_x,
            viewport_y,
            viewport_w,
            viewport_h,
            accent=accent,
            elapsed=elapsed + 0.4,
        )

        cx = viewport_x + viewport_w / 2
        cy = viewport_y + viewport_h / 2
        canvas.create_image(cx, cy, image=frame_image, anchor="center")
        hp.draw_scanlines(canvas, viewport_x, viewport_y, viewport_w, viewport_h)

        pulse = 0.55 + 0.45 * math.sin(elapsed * 3.2)
        rail_color = accent if pulse > 0.7 else dim
        for offset in (6.0, viewport_w - 6.0):
            canvas.create_line(
                viewport_x + offset,
                viewport_y + 8,
                viewport_x + offset,
                viewport_y + viewport_h - 8,
                fill=rail_color,
                width=1,
                dash=(3, 5),
            )

        self._draw_footer(
            canvas,
            vw,
            vh,
            footer_top,
            spec,
            accent,
            dim,
            frame,
            bg,
            elapsed,
            playback_seconds,
            progress,
            hover_id,
        )

    def _draw_header(
        self,
        canvas: tk.Canvas,
        vw: int,
        level_id: str,
        spec: LevelIntroSpec,
        accent: str,
        dim: str,
        frame: str,
        bg: str,
        elapsed: float,
    ) -> None:
        hp.draw_panel(canvas, 0, 0, vw, _HEADER_H, frame=frame, accent=accent, fill=bg)
        hp.draw_panel_title(canvas, 14, 10, "SECTOR BRIEFING", color=dim)
        draw_fitted_text(
            canvas,
            14,
            30,
            LEVEL_LABELS.get(level_id, level_id),
            max_width=vw * 0.45,
            color=palette.TEXT,
            font=hp.FONT_SECTION,
        )
        draw_fitted_text(
            canvas,
            vw - 14,
            18,
            spec.header_tag,
            max_width=vw * 0.42,
            color=accent,
            font=hp.FONT_BODY_BOLD,
            anchor="e",
        )
        tick = "▮" if int(elapsed * 4) % 2 == 0 else "▯"
        canvas.create_text(
            vw - 14,
            36,
            anchor="e",
            text=f"RELAY {tick} LIVE",
            fill=dim,
            font=hp.FONT_SMALL,
        )

    def _draw_footer(
        self,
        canvas: tk.Canvas,
        vw: int,
        vh: int,
        footer_top: float,
        spec: LevelIntroSpec,
        accent: str,
        dim: str,
        frame: str,
        bg: str,
        elapsed: float,
        playback_seconds: float,
        progress: float,
        hover_id: str | None,
    ) -> None:
        hp.draw_panel(canvas, 0, footer_top, vw, vh - footer_top, frame=frame, accent=accent, fill=bg)
        bar_x = _MARGIN
        bar_w = vw - 2 * _MARGIN - 220
        bar_y = footer_top + 18
        bar_h = 8.0
        canvas.create_rectangle(bar_x, bar_y, bar_x + bar_w, bar_y + bar_h, outline=frame, fill="#0a1420")
        fill_w = max(0.0, min(bar_w, bar_w * progress))
        if fill_w > 0.0:
            canvas.create_rectangle(bar_x, bar_y, bar_x + fill_w, bar_y + bar_h, outline="", fill=accent)
        remaining = max(0.0, playback_seconds - elapsed)
        canvas.create_text(
            bar_x + bar_w,
            bar_y + bar_h / 2,
            anchor="e",
            text=f"{elapsed:0.1f} / {playback_seconds:0.1f}s",
            fill=accent if progress < 1.0 else palette.GATE_OPEN,
            font=hp.FONT_SMALL,
        )
        canvas.create_text(
            bar_x,
            bar_y + 20,
            anchor="w",
            text=f"{spec.footer_hint} · {remaining:0.1f}s",
            fill=dim,
            font=hp.FONT_SMALL,
        )

        btn_w = 200.0
        btn_h = 36.0
        btn_x = vw - _MARGIN - btn_w
        btn_y = footer_top + 14
        self.hits.add("skip_intro", btn_x, btn_y, btn_w, btn_h)
        draw_menu_button(
            canvas,
            btn_x,
            btn_y,
            btn_w,
            btn_h,
            "LAUNCH SECTOR →",
            accent=accent,
            dim=dim,
            frame=frame,
            selected=True,
            hover=hover_id == "skip_intro",
        )

    def _starfield(self, canvas: tk.Canvas, vw: int, vh: int) -> None:
        for i in range(120):
            x = (i * 83 + 17) % vw
            y = (i * 47 + 31) % vh
            tone = "#3a5570" if i % 7 == 0 else "#1a3048"
            canvas.create_rectangle(x, y, x + 2, y + 2, fill=tone, outline="")
