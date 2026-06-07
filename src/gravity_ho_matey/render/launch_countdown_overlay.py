from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.levels.level_registry import LEVEL_LABELS
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.menu_ui import draw_fitted_text, draw_holo_corners

_STRIP_H = 56.0
_MARGIN = 12.0


def accent_for_theme(theme: str) -> str:
    if theme == "solar":
        return palette.HUD_ACCENT_SOLAR
    if theme == "rift":
        return palette.RIFT_HUD_ACCENT
    if theme == "siege":
        return palette.SIEGE_HUD_ACCENT
    if theme == "brood_moon":
        return palette.BROOD_MOON_HUD_ACCENT
    return palette.HUD_ACCENT


def draw_playfield_reveal(
    canvas: tk.Canvas,
    *,
    hud_top: float,
    vw: int,
    vh: int,
    reveal: float,
    theme: str,
) -> None:
    """Viewport materializes — command deck stays lit; playfield clears in."""
    if reveal >= 0.995:
        return
    pf_x = 0.0
    pf_y = hud_top
    pf_w = float(vw)
    pf_h = float(vh) - hud_top - _STRIP_H - 4.0
    if pf_h <= 0.0:
        return

    accent = accent_for_theme(theme)
    darkness = 1.0 - max(0.0, min(1.0, reveal))
    if darkness > 0.55:
        fill, stipple = "#010206", "gray75"
    elif darkness > 0.28:
        fill, stipple = "#020408", "gray50"
    else:
        fill, stipple = "#040810", "gray25"
    canvas.create_rectangle(pf_x, pf_y, pf_x + pf_w, pf_y + pf_h, fill=fill, outline="", stipple=stipple)
    hp.draw_scanlines(canvas, pf_x, pf_y, pf_w, pf_h * min(1.0, 0.35 + reveal * 0.65))

    arm = 16.0
    corner_color = palette.HUD_FRAME if darkness > 0.35 else accent
    corners = (
        (pf_x + 8, pf_y + 6, pf_x + 8 + arm, pf_y + 6, pf_x + 8, pf_y + 6 + arm),
        (pf_x + pf_w - 8, pf_y + 6, pf_x + pf_w - 8 - arm, pf_y + 6, pf_x + pf_w - 8, pf_y + 6 + arm),
        (pf_x + 8, pf_y + pf_h - 6, pf_x + 8 + arm, pf_y + pf_h - 6, pf_x + 8, pf_y + pf_h - 6 - arm),
        (pf_x + pf_w - 8, pf_y + pf_h - 6, pf_x + pf_w - 8 - arm, pf_y + pf_h - 6, pf_x + pf_w - 8, pf_y + pf_h - 6 - arm),
    )
    for lx, ly, mx, my, ex, ey in corners:
        canvas.create_line(lx, ly, mx, my, fill=corner_color, width=1)
        canvas.create_line(lx, ly, ex, ey, fill=corner_color, width=1)


def draw_launch_countdown_strip(
    canvas: tk.Canvas,
    *,
    vw: int,
    vh: int,
    level_id: str,
    theme: str,
    digits: tuple[int, ...],
    step_index: int,
    current_digit: int,
    step_elapsed: float,
    step_seconds: float,
    reveal: float,
    total_elapsed: float,
    total_seconds: float,
) -> None:
    """Bottom command-deck strip — matches chart briefing / play HUD panels."""
    accent = accent_for_theme(theme)
    dim = palette.HUD_DIM
    frame = palette.HUD_FRAME
    bg = palette.HUD_BG

    strip_y = vh - _STRIP_H - 4.0
    strip_w = vw - 2 * _MARGIN
    hp.draw_panel(canvas, _MARGIN, strip_y, strip_w, _STRIP_H, frame=frame, accent=accent, fill=bg)
    draw_holo_corners(canvas, _MARGIN, strip_y, strip_w, _STRIP_H, accent=accent, elapsed=total_elapsed)

    hp.draw_panel_title(canvas, _MARGIN + 12, strip_y + 8, "DRIVE SPIN-UP", color=dim)

    tick_x = _MARGIN + 12
    tick_y = strip_y + 30
    for i, value in enumerate(digits):
        slot_x = tick_x + i * 26
        if i < step_index:
            fill, outline = accent, accent
        elif i == step_index:
            pulse = 0.65 + 0.35 * math.sin(step_elapsed * 6.0)
            fill = accent if pulse > 0.72 else palette.HUD_LOOT_NEW
            outline = accent
        else:
            fill, outline = palette.HUD_HULL_EMPTY, frame
        canvas.create_rectangle(slot_x, tick_y, slot_x + 18, tick_y + 14, fill=fill, outline=outline, width=1)
        label_color = palette.TEXT if i <= step_index else dim
        canvas.create_text(
            slot_x + 9,
            tick_y + 7,
            text=str(value),
            fill=label_color,
            font=("Courier New", 9, "bold"),
        )

    readout_x = _MARGIN + 118
    hp.draw_panel(canvas, readout_x, strip_y + 10, 118, 36, frame=frame, accent=accent, fill="#0a1420")
    hp.draw_panel_title(canvas, readout_x + 8, strip_y + 14, "T-MIN", color=dim)
    canvas.create_text(
        readout_x + 8,
        strip_y + 32,
        anchor="w",
        text=f"{current_digit:02d}",
        fill=accent,
        font=("Courier New", 16, "bold"),
    )

    level_label = LEVEL_LABELS.get(level_id, level_id).split(" — ", 1)[-1].upper()
    draw_fitted_text(
        canvas,
        readout_x + 62,
        strip_y + 32,
        level_label,
        max_width=52,
        color=dim,
        font=hp.FONT_SMALL,
        anchor="w",
    )

    bar_x = readout_x + 132
    bar_w = strip_w - (bar_x - _MARGIN) - 14
    bar_y = strip_y + 22
    bar_h = 8.0
    overall = min(1.0, total_elapsed / max(0.01, total_seconds))
    step_prog = min(1.0, step_elapsed / max(0.01, step_seconds))
    canvas.create_rectangle(bar_x, bar_y, bar_x + bar_w, bar_y + bar_h, outline=frame, fill="#0a1420")
    canvas.create_rectangle(
        bar_x,
        bar_y,
        bar_x + bar_w * overall,
        bar_y + bar_h,
        outline="",
        fill=accent,
    )
    canvas.create_rectangle(
        bar_x,
        bar_y + bar_h + 4,
        bar_x + bar_w * step_prog,
        bar_y + bar_h + 9,
        outline="",
        fill=dim,
    )
    canvas.create_text(
        bar_x,
        bar_y + 18,
        anchor="w",
        text=f"LINK {int(reveal * 100):3d}% · Enter commits",
        fill=dim,
        font=hp.FONT_SMALL,
    )

    canvas.create_line(_MARGIN, strip_y - 1, _MARGIN + strip_w, strip_y - 1, fill=accent, width=1)
