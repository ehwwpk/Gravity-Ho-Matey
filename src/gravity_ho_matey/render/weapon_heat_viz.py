"""Weapon heat readouts — shared across command HUD, tactical, and chase helm."""

from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Ship
from gravity_ho_matey.gameplay.weapon_heat import player_weapon_overheated, ship_weapon_heat_visible
from gravity_ho_matey.render import palette


def barrel_status(ship: Ship) -> tuple[str, str] | None:
    if not ship_weapon_heat_visible(ship):
        return None
    if player_weapon_overheated(ship):
        return ("BARREL COOLING", palette.HUD_WARN)
    heat_pct = int(ship.weapon_heat * 100)
    color = palette.DRONE_HEAT if ship.weapon_heat > 0.55 else palette.HUD_ACCENT
    return (f"BARREL {heat_pct:3d}%", color)


def draw_weapon_heat_on_ship(
    canvas: tk.Canvas,
    pos: Vec2,
    *,
    scale: float,
    weapon_heat: float,
    weapon_overheat_timer: float = 0.0,
) -> None:
    """Tactical / top-down ring — mirrors escort drone heat arc."""
    if weapon_heat <= 0.08 and weapon_overheat_timer <= 0.0:
        return
    cx, cy = pos.x, pos.y
    r = 19.0 * scale
    if weapon_overheat_timer > 0.0:
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=palette.HUD_WARN, width=2)
        return
    if weapon_heat > 0.15:
        heat_frac = min(1.0, weapon_heat)
        canvas.create_arc(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            start=90,
            extent=-360 * heat_frac,
            outline=palette.DRONE_HEAT,
            width=max(1, int(1 + scale * 0.5)),
            style=tk.ARC,
        )


def draw_weapon_heat_chase_reticle(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    ship: Ship,
) -> None:
    """Chase POV — reticle warning + micro heat bar under the nose pip."""
    status = barrel_status(ship)
    if status is None:
        return
    text, color = status
    bar_w = 36.0
    bar_h = 4.0
    bx = cx - bar_w * 0.5
    by = cy + 6.0
    heat_frac = 1.0 if player_weapon_overheated(ship) else min(1.0, ship.weapon_heat)
    canvas.create_rectangle(bx, by, bx + bar_w, by + bar_h, fill=palette.DRONE_HEAT_BG, outline=color, width=1)
    canvas.create_rectangle(bx + 1, by + 1, bx + 1 + (bar_w - 2) * heat_frac, by + bar_h - 1, fill=color, outline="")
    canvas.create_text(cx, by + bar_h + 8, text=text, fill=color, font=("Courier", 8, "bold"))
    if player_weapon_overheated(ship):
        canvas.create_oval(cx - 16, cy - 22, cx + 16, cy - 8, outline=palette.HUD_WARN, width=2)


def draw_weapon_heat_tactical_gauge(
    canvas: tk.Canvas,
    x: float,
    y: float,
    ship: Ship,
    *,
    accent: str,
    dim: str,
    compact: bool = True,
) -> None:
    """Tactical POV — compact BARREL strip beside flight instruments."""
    status = barrel_status(ship)
    if status is None:
        return
    text, color = status
    bar_w = 88.0 if compact else 108.0
    bar_h = 5.0 if compact else 6.0
    canvas.create_text(x, y, text="BARREL", anchor="sw", fill=dim, font=("Courier", 7 if compact else 8, "bold"))
    canvas.create_text(x + bar_w, y, text=text.replace("BARREL ", ""), anchor="se", fill=color, font=("Courier", 8, "bold"))
    by = y + (8 if compact else 10)
    canvas.create_rectangle(x, by, x + bar_w, by + bar_h, outline=accent if not player_weapon_overheated(ship) else palette.HUD_WARN, width=1)
    heat_frac = 1.0 if player_weapon_overheated(ship) else min(1.0, ship.weapon_heat)
    fill = color if heat_frac > 0.12 else accent
    canvas.create_rectangle(x + 1, by + 1, x + 1 + (bar_w - 2) * heat_frac, by + bar_h - 1, fill=fill, outline="")
