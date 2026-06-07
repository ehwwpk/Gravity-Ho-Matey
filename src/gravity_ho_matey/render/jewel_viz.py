from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.render import palette


def draw_jewel_orb(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    radius: float = 5.0,
    elapsed: float = 0.0,
    depth_scale: float = 1.0,
) -> None:
    """Bright orange loot orb — tactical and chase share this glyph."""
    r = max(2.5, radius * depth_scale)
    pulse = 0.85 + 0.15 * math.sin(elapsed * 9.0 + x * 0.03)
    glow_r = r * (2.2 + pulse * 0.25)
    canvas.create_oval(
        x - glow_r,
        y - glow_r,
        x + glow_r,
        y + glow_r,
        fill="",
        outline=palette.JEWEL_GLOW,
        width=1,
    )
    canvas.create_oval(
        x - r,
        y - r,
        x + r,
        y + r,
        fill=palette.JEWEL_CORE,
        outline=palette.JEWEL_EDGE,
        width=1,
    )
    highlight = r * 0.35
    canvas.create_oval(
        x - highlight,
        y - highlight * 1.2,
        x - highlight * 0.1,
        y - highlight * 0.35,
        fill=palette.JEWEL_HIGHLIGHT,
        outline="",
    )


def draw_jewel_world(
    canvas: tk.Canvas,
    pos: Vec2,
    *,
    hud_top: float = 0.0,
    elapsed: float = 0.0,
    depth_scale: float = 1.0,
) -> None:
    draw_jewel_orb(canvas, pos.x, pos.y + hud_top, elapsed=elapsed, depth_scale=depth_scale)
