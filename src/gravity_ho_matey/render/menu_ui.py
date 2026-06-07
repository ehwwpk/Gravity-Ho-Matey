from __future__ import annotations

import math
import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass, field

from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette

_FONT_CACHE: dict[tuple[str, int, str], tkfont.Font] = {}
_HIDDEN_ROOT: tk.Misc | None = None


def _hidden_root() -> tk.Misc | None:
    global _HIDDEN_ROOT
    if _HIDDEN_ROOT is not None:
        try:
            if _HIDDEN_ROOT.winfo_exists():
                return _HIDDEN_ROOT
        except tk.TclError:
            pass
        _HIDDEN_ROOT = None
        _FONT_CACHE.clear()
    try:
        _HIDDEN_ROOT = tk.Tk()
        _HIDDEN_ROOT.withdraw()
    except tk.TclError:
        return None
    return _HIDDEN_ROOT


def _estimate_char_width(font: tuple[str, int] | tuple[str, int, str]) -> float:
    size = font[1] if len(font) > 1 else 10
    return max(5.5, size * 0.58)


def _font_for(spec: tuple[str, int] | tuple[str, int, str]) -> tkfont.Font | None:
    family = spec[0]
    size = spec[1]
    weight = "bold" if len(spec) > 2 and spec[2] == "bold" else "normal"
    key = (family, size, weight)
    cached = _FONT_CACHE.get(key)
    if cached is not None:
        return cached
    root = _hidden_root()
    if root is None:
        return None
    cached = tkfont.Font(root=root, family=family, size=size, weight=weight)
    _FONT_CACHE[key] = cached
    return cached


def measure_text(text: str, font: tuple[str, int] | tuple[str, int, str]) -> float:
    f = _font_for(font)
    if f is not None:
        try:
            return float(f.measure(text))
        except tk.TclError:
            _FONT_CACHE.clear()
    return len(text) * _estimate_char_width(font)


def fit_text_to_width(text: str, max_width: float, font: tuple[str, int] | tuple[str, int, str]) -> str:
    """Trim with ellipsis using real font metrics when Tk is available."""
    if max_width <= 0 or not text:
        return text
    f = _font_for(font)
    if f is None:
        max_chars = max(4, int(max_width / _estimate_char_width(font)))
        return truncate(text, max_chars)
    try:
        if f.measure(text) <= max_width:
            return text
        ell = "…"
        if f.measure(ell) > max_width:
            return ell
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            candidate = text[:mid] + (ell if mid < len(text) else "")
            if f.measure(candidate) <= max_width:
                lo = mid
            else:
                hi = mid - 1
        if lo >= len(text):
            return text[:lo]
        return text[:lo] + ell
    except tk.TclError:
        _FONT_CACHE.clear()
        max_chars = max(4, int(max_width / _estimate_char_width(font)))
        return truncate(text, max_chars)


def wrap_text_lines(
    text: str,
    max_width: float,
    font: tuple[str, int] | tuple[str, int, str],
    *,
    max_lines: int = 4,
) -> list[str]:
    """Word-wrap to pixel width."""
    if max_width <= 0 or not text.strip():
        return [""]
    words = text.split()
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if measure_text(candidate, font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) >= max_lines:
                break
    if len(lines) < max_lines:
        lines.append(fit_text_to_width(current, max_width, font))
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    if len(lines) == max_lines and len(words) > sum(len(line.split()) for line in lines):
        lines[-1] = fit_text_to_width(lines[-1], max_width, font)
    return lines


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
    """Single-line label clipped to pixel width via font metrics."""
    if max_width <= 0:
        return
    if bold and len(font) == 2:
        font = (font[0], font[1], "bold")
    fitted = fit_text_to_width(text, max_width, font)
    canvas.create_text(x, y, anchor=anchor, text=fitted, fill=color, font=font)


def draw_wrapped_text(
    canvas: tk.Canvas,
    x: float,
    y: float,
    text: str,
    *,
    max_width: float,
    line_height: float,
    color: str,
    font: tuple[str, int] | tuple[str, int, str],
    max_lines: int = 3,
    anchor: str = "nw",
) -> float:
    """Draw wrapped lines; return total height used."""
    lines = wrap_text_lines(text, max_width, font, max_lines=max_lines)
    cy = y
    for line in lines:
        canvas.create_text(x, cy, anchor=anchor, text=line, fill=color, font=font)
        cy += line_height
    return cy - y


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
    draw_fitted_text(
        canvas,
        x + w / 2,
        y + h / 2,
        label,
        max_width=w - 8,
        color=text_color,
        font=font,
        anchor="center",
    )


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
