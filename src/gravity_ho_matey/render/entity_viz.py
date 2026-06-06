from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Beacon
from gravity_ho_matey.render import palette


def gate_label(*, unlocked: bool, solar: bool) -> str:
    if solar:
        return "WORMHOLE" if unlocked else "SEALED"
    return "OPEN" if unlocked else "LOCK"


def draw_gate_glyph(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    size: float,
    unlocked: bool,
    solar: bool,
    scale: float = 1.0,
) -> None:
    color = palette.GATE_OPEN if unlocked else palette.GATE_LOCKED
    r = max(14.0, size * 0.45) * scale
    canvas.create_arc(x - r, y - r, x + r, y + r, start=200, extent=140, style="arc", outline=color, width=3)
    canvas.create_line(x - r * 0.85, y + r * 0.35, x + r * 0.85, y + r * 0.35, fill=color, width=2)
    font_size = max(7, min(8, int(8 * scale)))
    canvas.create_text(x, y - 2, text=gate_label(unlocked=unlocked, solar=solar), fill=color, font=("Courier New", font_size, "bold"))


def draw_beacon_glyph(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    collected: bool,
    scale: float = 1.0,
    show_ring: bool = True,
) -> None:
    color = palette.BEACON_COLLECTED if collected else palette.BEACON
    ring = 12.0 * scale
    body = 6.0 * scale
    if show_ring and not collected:
        canvas.create_oval(x - ring, y - ring, x + ring, y + ring, outline=color, width=1)
    canvas.create_rectangle(x - body, y - body, x + body, y + body, fill=color, outline="#dff", width=1)
    canvas.create_polygon(
        x,
        y - 10 * scale,
        x + 5 * scale,
        y - 4 * scale,
        x,
        y + 2 * scale,
        x - 5 * scale,
        y - 4 * scale,
        fill=color,
        outline="",
    )


def draw_gate_portal(
    canvas: tk.Canvas,
    center: Vec2,
    *,
    size: float,
    unlocked: bool,
    solar: bool,
    hud_top: float = 0.0,
) -> None:
    draw_gate_glyph(
        canvas,
        center.x,
        center.y + hud_top,
        size=size,
        unlocked=unlocked,
        solar=solar,
        scale=1.0,
    )


def draw_beacon_marker(canvas: tk.Canvas, pos: Vec2, beacon: Beacon, *, hud_top: float) -> None:
    draw_beacon_glyph(
        canvas,
        pos.x,
        pos.y + hud_top,
        collected=beacon.collected,
        scale=1.0,
        show_ring=True,
    )
