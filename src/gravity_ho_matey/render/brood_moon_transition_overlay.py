from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.gameplay.brood_moon_mission import BroodMoonState
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.menu_ui import draw_fitted_text, draw_holo_corners


class BroodMoonTransitionOverlay:
    """In-play landing / ascent cinematic — brood GIFs when present, else cove (L1) placeholder."""

    def draw(
        self,
        canvas: tk.Canvas,
        *,
        bm: BroodMoonState,
        frame_image: tk.PhotoImage | None,
        vw: int = 960,
        vh: int = 640,
    ) -> None:
        accent = palette.BROOD_MOON_HUD_ACCENT
        dim = palette.HUD_DIM
        frame = palette.HUD_FRAME
        bg = palette.HUD_BG
        progress = min(1.0, bm.cinematic_elapsed / max(0.01, bm.cinematic_seconds))

        canvas.create_rectangle(0, 0, vw, vh, fill=palette.BROOD_MOON_BG, outline="")
        for i in range(80):
            sx = (i * 83 + 17) % vw
            sy = (i * 47 + 31) % vh
            canvas.create_rectangle(sx, sy, sx + 2, sy + 2, fill="#3a2850", outline="")

        header = "DESCENT" if bm.cinematic_kind == "landing" else "ASCENT"
        hp.draw_panel(canvas, 12, 10, vw - 24, 48, frame=frame, accent=accent, fill=bg)
        canvas.create_text(24, 28, anchor="w", text=f"BROOD MOON · {header}", fill=accent, font=hp.FONT_SECTION)

        body_top = 68
        body_h = vh - body_top - 78
        hp.draw_panel(canvas, 14, body_top, vw - 28, body_h, frame=frame, accent=accent, fill=bg)
        draw_holo_corners(canvas, 14, body_top, vw - 28, body_h, accent=accent, elapsed=bm.cinematic_elapsed)

        vx, vy = 26.0, body_top + 12
        vw_inner, vh_inner = vw - 52.0, body_h - 24.0
        canvas.create_rectangle(vx, vy, vx + vw_inner, vy + vh_inner, fill="#120818", outline=frame)
        if frame_image is not None:
            canvas.create_image(vx + vw_inner / 2, vy + vh_inner / 2, image=frame_image, anchor="center")
        else:
            draw_fitted_text(
                canvas,
                vx + vw_inner / 2,
                vy + vh_inner / 2 - 12,
                "ATMOSPHERIC TRANSIT",
                max_width=vw_inner - 40,
                color=accent,
                font=("Courier New", 16, "bold"),
                anchor="center",
            )
            draw_fitted_text(
                canvas,
                vx + vw_inner / 2,
                vy + vh_inner / 2 + 18,
                "Drop brood_moon_landing.gif / brood_moon_ascent.gif in assets/narrative/",
                max_width=vw_inner - 40,
                color=dim,
                font=hp.FONT_SMALL,
                anchor="center",
            )

        bar_y = vh - 58
        hp.draw_panel(canvas, 14, bar_y, vw - 28, 42, frame=frame, accent=accent, fill=bg)
        bar_w = (vw - 56) * progress
        canvas.create_rectangle(28, bar_y + 18, 28 + bar_w, bar_y + 28, fill=accent, outline="")
        canvas.create_text(vw // 2, bar_y + 10, text="Space · skip", fill=dim, font=hp.FONT_SMALL)

        shimmer = 0.5 + 0.5 * math.sin(bm.cinematic_elapsed * 4.0)
        canvas.create_rectangle(0, 0, vw, vh, outline=palette.BROOD_MOON_HUD_ACCENT if shimmer > 0.65 else "", width=1)
