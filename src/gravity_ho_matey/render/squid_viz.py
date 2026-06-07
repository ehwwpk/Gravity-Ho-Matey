from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.render import palette


def draw_squid_tentacles(
    canvas: tk.Canvas,
    body: tuple[float, float],
    tips: tuple[tuple[float, float], ...],
    *,
    coiled: bool,
) -> None:
    bx, by = body
    width = 3 if coiled else 2
    for tip in tips:
        tx, ty = tip
        mx = bx + (tx - bx) * 0.48
        my = by + (ty - by) * 0.48
        canvas.create_line(bx, by, mx, my, tx, ty, fill=palette.SQUID_TENTACLE, width=width, smooth=True)


def draw_squid_body(canvas: tk.Canvas, x: float, y: float, *, radius: float, scale: float = 1.0) -> None:
    r = radius * scale
    canvas.create_oval(x - r, y - r * 0.65, x + r, y + r * 0.55, fill=palette.SQUID_BODY, outline=palette.SQUID_CORE, width=2)
    canvas.create_oval(
        x - r * 0.35,
        y - r * 0.25,
        x + r * 0.35,
        y + r * 0.2,
        fill=palette.SQUID_CORE,
        outline="",
    )


def project_tips_to_screen(
    tips: tuple[Vec2, ...],
    project,
) -> tuple[tuple[float, float], ...]:
    out: list[tuple[float, float]] = []
    for tip in tips:
        p = project(tip)
        if p is None:
            continue
        out.append(p)
    return tuple(out)
