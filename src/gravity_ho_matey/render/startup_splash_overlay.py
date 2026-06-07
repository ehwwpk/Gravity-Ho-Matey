from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette


class StartupSplashOverlay:
    """Full-bleed opening GIF — logo is baked into the art, no briefing chrome."""

    def draw(
        self,
        canvas: tk.Canvas,
        *,
        frame_image: tk.PhotoImage,
        elapsed: float,
        playback_seconds: float,
        progress: float,
        show_skip_hint: bool,
    ) -> None:
        vw = 960
        vh = 640
        canvas.create_rectangle(0, 0, vw, vh, fill=palette.BACKGROUND, outline="")
        canvas.create_image(vw / 2, vh / 2, image=frame_image, anchor="center")
        hp.draw_scanlines(canvas, 0, 0, vw, vh)

        if show_skip_hint:
            pulse = 0.55 + 0.45 * math.sin(elapsed * 4.0)
            hint = palette.HUD_ACCENT if pulse > 0.72 else palette.HUD_DIM
            canvas.create_text(
                vw / 2,
                vh - 22,
                text="Enter · click to continue",
                fill=hint,
                font=hp.FONT_SMALL,
            )

        if progress < 1.0:
            bar_w = 120.0
            bar_x = vw - 24.0 - bar_w
            bar_y = vh - 18.0
            canvas.create_rectangle(bar_x, bar_y, bar_x + bar_w, bar_y + 4, outline=palette.HUD_FRAME, fill="#0a1420")
            fill_w = bar_w * progress
            if fill_w > 0.0:
                canvas.create_rectangle(bar_x, bar_y, bar_x + fill_w, bar_y + 4, outline="", fill=palette.HUD_ACCENT)
