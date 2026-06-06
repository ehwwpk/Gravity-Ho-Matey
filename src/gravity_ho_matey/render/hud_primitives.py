from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.render import palette

FONT_SMALL = ("Courier New", 8)
FONT_BODY = ("Courier New", 10)
FONT_BODY_BOLD = ("Courier New", 10, "bold")
FONT_SECTION = ("Courier New", 11, "bold")
FONT_DISPLAY = ("Courier New", 14, "bold")


def draw_scanlines(canvas: tk.Canvas, x: float, y: float, width: float, height: float) -> None:
    y_end = y + height
    for row in range(int(y), int(y_end), 4):
        canvas.create_line(x, row, x + width, row, fill=palette.HUD_SCANLINE)


def draw_panel(
    canvas: tk.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    frame: str = palette.HUD_FRAME,
    accent: str = palette.HUD_ACCENT,
    fill: str = "",
) -> None:
    canvas.create_rectangle(x, y, x + width, y + height, outline=frame, width=1, fill=fill)
    canvas.create_line(x + 4, y + 2, x + 18, y + 2, fill=accent)
    canvas.create_line(x + width - 18, y + height - 2, x + width - 4, y + height - 2, fill=accent)


def draw_panel_title(canvas: tk.Canvas, x: float, y: float, text: str, *, color: str = palette.HUD_DIM) -> None:
    canvas.create_text(x, y, anchor="w", text=text, fill=color, font=FONT_SMALL)


def draw_body_line(
    canvas: tk.Canvas,
    x: float,
    y: float,
    text: str,
    *,
    color: str = palette.TEXT,
    bold: bool = False,
) -> None:
    font = FONT_BODY_BOLD if bold else FONT_BODY
    canvas.create_text(x, y, anchor="w", text=text, fill=color, font=font)


def draw_key_value_row(
    canvas: tk.Canvas,
    x: float,
    y: float,
    key: str,
    action: str,
    *,
    accent: str = palette.HUD_ACCENT,
    dim: str = palette.HUD_DIM,
    key_width: float = 108.0,
) -> None:
    canvas.create_text(x, y, anchor="w", text=key, fill=accent, font=FONT_BODY_BOLD)
    canvas.create_text(x + key_width, y, anchor="w", text=action, fill=dim, font=FONT_BODY)
