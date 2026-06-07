from __future__ import annotations

import math
import tkinter as tk
from dataclasses import dataclass, field

from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette


@dataclass(frozen=True, slots=True)
class HitRegion:
    """Screen-space click target registered during menu draw."""

    id: str
    x0: float
    y0: float
    x1: float
    y1: float

    def contains(self, x: float, y: float) -> bool:
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1


@dataclass
class MenuHitMap:
    regions: list[HitRegion] = field(default_factory=list)

    def clear(self) -> None:
        self.regions.clear()

    def add(self, region_id: str, x: float, y: float, w: float, h: float) -> None:
        self.regions.append(HitRegion(region_id, x, y, x + w, y + h))

    def hit(self, x: float, y: float) -> str | None:
        for region in reversed(self.regions):
            if region.contains(x, y):
                return region.id
        return None


def truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return text[:max_len]
    return text[: max_len - 1] + "…"


def draw_fitted_text(
    canvas: tk.Canvas,
    x: float,
    y: float,
    text: str,
    *,
    max_width: float,
    color: str,
    font: tuple[str, int] | tuple[str, int, str],
    anchor: str = "w",
    bold: bool = False,
) -> None:
    """Single-line label clipped to pixel width via character estimate."""
    if max_width <= 0:
        return
    size = font[1] if len(font) > 1 else 10
    char_w = max(5.5, size * 0.58)
    max_chars = max(4, int(max_width / char_w))
    canvas.create_text(x, y, anchor=anchor, text=truncate(text, max_chars), fill=color, font=font)


def draw_menu_button(
    canvas: tk.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    *,
    accent: str,
    dim: str,
    frame: str,
    active: bool = True,
    selected: bool = False,
    hover: bool = False,
) -> None:
    fill = "#0a1420" if active else "#060810"
    if selected:
        fill = "#0e2030"
    if hover and active:
        fill = "#122838"
    border = accent if selected or hover else (accent if active else frame)
    hp.draw_panel(canvas, x, y, w, h, frame=border, accent=accent, fill=fill)
    text_color = accent if active else dim
    font = hp.FONT_BODY_BOLD if selected or hover else hp.FONT_BODY
    canvas.create_text(x + w / 2, y + h / 2, text=label, fill=text_color, font=font)


def draw_level_row(
    canvas: tk.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    index: int,
    title: str,
    detail: str,
    accent: str,
    dim: str,
    frame: str,
    unlocked: bool,
    lock_reason: str,
    selected: bool = False,
    hover: bool = False,
) -> None:
    active = unlocked
    draw_menu_button(
        canvas,
        x,
        y,
        w,
        h,
        "",
        accent=accent,
        dim=dim,
        frame=frame,
        active=active,
        selected=selected,
        hover=hover,
    )
    num_color = accent if active else dim
    canvas.create_text(x + 18, y + h / 2, text=str(index), fill=num_color, font=hp.FONT_DISPLAY)
    title_x = x + 44
    title_w = w - 130
    draw_fitted_text(
        canvas,
        title_x,
        y + 22,
        title,
        max_width=title_w,
        color=palette.TEXT if active else dim,
        font=hp.FONT_BODY_BOLD,
    )
    draw_fitted_text(
        canvas,
        title_x,
        y + 40,
        detail,
        max_width=title_w,
        color=dim,
        font=hp.FONT_BODY,
    )
    if unlocked:
        action = "SELECT →"
        action_color = palette.HUD_LOOT_NEW if selected or hover else accent
    else:
        action = lock_reason
        action_color = dim
    canvas.create_text(x + w - 14, y + h / 2, anchor="e", text=action, fill=action_color, font=hp.FONT_BODY)


def draw_holo_corners(
    canvas: tk.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    accent: str,
    elapsed: float = 0.0,
) -> None:
    pulse = 0.65 + 0.35 * math.sin(elapsed * 2.8)
    arm = 14.0
    width = 2 if pulse > 0.85 else 1
    color = accent if pulse > 0.75 else palette.HUD_DIM
    corners = (
        (x, y, x + arm, y, x, y + arm),
        (x + w, y, x + w - arm, y, x + w, y + arm),
        (x, y + h, x + arm, y + h, x, y + h - arm),
        (x + w, y + h, x + w - arm, y + h, x + w, y + h - arm),
    )
    for lx, ly, mx, my, ex, ey in corners:
        canvas.create_line(lx, ly, mx, my, fill=color, width=width)
        canvas.create_line(lx, ly, ex, ey, fill=color, width=width)
