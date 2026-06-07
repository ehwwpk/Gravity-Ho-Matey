from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow


def draw_rift_extract_pad(
    canvas: tk.Canvas,
    sx: float,
    sy: float,
    *,
    unlocked: bool,
    elapsed: float,
) -> None:
    pulse = 0.5 + 0.5 * math.sin(elapsed * 4.5)
    colors = palette.RIFT_PAD_GLOW if unlocked else (palette.RIFT_PAD_COOLDOWN, palette.HUD_DIM)
    draw_ground_fog_glow(canvas, sx, sy + 6.0, 52.0 + pulse * 10.0, colors, pulse=elapsed * 3.0)
    w = 46.0
    h = 28.0
    fill = palette.RIFT_PAD_READY if unlocked else palette.RIFT_PAD_COOLDOWN
    outline = palette.RIFT_PAD_STRIPE if unlocked else palette.HUD_DIM
    canvas.create_rectangle(sx - w, sy - h * 0.35, sx + w, sy + h * 0.65, fill=fill, outline=outline, width=2)
    stripe_y = sy + h * 0.15
    canvas.create_line(sx - w * 0.85, stripe_y, sx + w * 0.85, stripe_y, fill=palette.RIFT_PAD_ZIGZAG, width=2)
    for i, color in enumerate(
        (
            palette.RIFT_PAD_MK_RED,
            palette.RIFT_PAD_MK_YELLOW,
            palette.RIFT_PAD_MK_ORANGE,
            palette.RIFT_PAD_MK_PINK,
        )
    ):
        mx = sx - w * 0.55 + i * w * 0.37
        canvas.create_rectangle(mx - 5, sy - h * 0.2, mx + 5, sy + h * 0.35, fill=color, outline="")
    if unlocked:
        canvas.create_text(
            sx,
            sy - h * 0.55,
            text="EXTRACT",
            fill=palette.RIFT_PAD_FLASH if pulse > 0.55 else palette.RIFT_PAD_STRIPE,
            font=("Courier New", 9, "bold"),
        )


def draw_rift_extract_pad_at(
    canvas: tk.Canvas,
    center: Vec2,
    *,
    unlocked: bool,
    elapsed: float,
    hud_top: float = 0.0,
) -> None:
    draw_rift_extract_pad(canvas, center.x, center.y + hud_top, unlocked=unlocked, elapsed=elapsed)
