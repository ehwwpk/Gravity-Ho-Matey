from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.render import palette


def hp_fraction(entity: object) -> float | None:
    """Return 0–1 HP fraction when entity tracks multi-hit health."""
    hits_max = getattr(entity, "hits_max", 0)
    hits_remaining = getattr(entity, "hits_remaining", 0)
    if not isinstance(hits_max, int) or not isinstance(hits_remaining, int):
        return None
    if hits_max <= 1:
        return None
    return hits_remaining / max(1, hits_max)


def draw_health_bar(
    canvas: tk.Canvas,
    cx: float,
    top_y: float,
    half_width: float,
    fraction: float,
    *,
    outline: str = "#8a7090",
    fill: str = "#40c0a0",
    low_fill: str | None = None,
    bar_height: float = 5.0,
    low_threshold: float = 0.35,
) -> None:
    frac = max(0.0, min(1.0, fraction))
    warn = low_fill or palette.HUD_WARN
    bar_fill = warn if frac < low_threshold else fill
    bottom = top_y + bar_height
    canvas.create_rectangle(cx - half_width, top_y, cx + half_width, bottom, fill="#180818", outline=outline)
    canvas.create_rectangle(
        cx - half_width,
        top_y,
        cx - half_width + 2 * half_width * frac,
        bottom,
        fill=bar_fill,
        outline="",
    )
