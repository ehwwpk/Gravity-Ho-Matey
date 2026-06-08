"""Shared parallax starfield — tactical, chase, title, chart."""

from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GravityWell
from gravity_ho_matey.render import palette

_THEME_STAR_TONES: dict[str, tuple[str, str, str]] = {
    "cove": ("#1e3348", "#324f68", "#4a6a88"),
    "drift": ("#1a2840", "#3a5070", "#5878a0"),
    "solar": ("#2a2010", "#4a3820", "#806030"),
    "rift": ("#201028", "#3a2850", "#604878"),
    "siege": ("#281008", "#402018", "#704028"),
    "brood_moon": ("#180820", "#302040", "#584868"),
}


def star_tones_for_theme(theme: str) -> tuple[str, str, str]:
    return _THEME_STAR_TONES.get(theme, _THEME_STAR_TONES["cove"])


def draw_layered_starfield(
    canvas: tk.Canvas,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    elapsed: float = 0.0,
    theme: str = "cove",
    vel_parallax: Vec2 | None = None,
    layers: tuple[tuple[int, float, int], ...] = (
        (48, 4.0, 2),
        (72, 12.0, 3),
        (36, 22.0, 4),
    ),
) -> None:
    """Three-band parallax drift — title hangar quality everywhere."""
    if width <= 0 or height <= 0:
        return
    drift_base = vel_parallax or Vec2()
    tones = star_tones_for_theme(theme)
    for layer, (count, speed, base_size) in enumerate(layers):
        drift = elapsed * speed
        tone = tones[min(layer, 2)]
        for i in range(count):
            sx = (i * 97 + 13 + layer * 41 + int(drift) + int(drift_base.x * (0.4 + layer * 0.2))) % max(1, int(width))
            sy = y + (i * 53 + 29 + layer * 17 + int(drift_base.y * (0.2 + layer * 0.15))) % max(1, int(height))
            twinkle = 0.85 + 0.15 * math.sin(elapsed * (2.8 + layer * 0.6) + i * 0.73)
            size = max(1, int((base_size if i % 4 else base_size + 1) * twinkle))
            canvas.create_rectangle(x + sx, sy, x + sx + size, sy + size, fill=tone, outline="")


def draw_tactical_starfield(
    canvas: tk.Canvas,
    *,
    width: int,
    height: int,
    y_offset: int,
    theme: str,
    elapsed: float = 0.0,
    dense: bool = True,
) -> None:
    if not dense:
        return
    draw_layered_starfield(
        canvas,
        x=0.0,
        y=float(y_offset),
        width=float(width),
        height=max(1.0, float(height - y_offset)),
        elapsed=elapsed,
        theme=theme,
    )


def draw_chase_parallax_stars(
    canvas: tk.Canvas,
    *,
    camera,
    world,
    horizon: float,
    wells: tuple[GravityWell, ...] | list[GravityWell] | None = None,
) -> None:
    """Velocity-linked chase stars with optional gravitational lens nudges."""
    width = camera.viewport_width
    top = camera.play_hud_top
    theme = world.config.level_theme
    vel = world.ship.vel
    parallax = vel * (-0.018)
    parallax = Vec2(
        parallax.x + camera.velocity_lag_x * 0.12,
        parallax.y + camera.velocity_lag_y * 0.06,
    )
    tones = star_tones_for_theme(theme)
    elapsed = world.elapsed
    well_list = list(wells or world.wells)

    for i in range(72):
        hx = (i * 7919 + 1237) % 10000
        hy = (i * 6271 + 4111) % 10000
        x = ((hx / 10000.0) * width + parallax.x) % max(1.0, width)
        y = top + (hy / 10000.0) * max(1.0, horizon - top - 8) + parallax.y * 0.5
        x, y = _lens_offset(x, y, well_list, camera, world.ship.pos, world.ship.angle)
        twinkle = 0.7 + 0.3 * math.sin(elapsed * 3.1 + i * 0.61)
        size = 2 if i % 4 else 3
        if twinkle < 0.82 and i % 5:
            continue
        tone = tones[2] if i % 3 == 0 else tones[1] if i % 3 == 1 else palette.CHASE_STAR_NEAR
        canvas.create_rectangle(x, y, x + size, y + size, fill=tone, outline="")


def _lens_offset(
    x: float,
    y: float,
    wells: list[GravityWell],
    camera,
    ship_pos: Vec2,
    ship_angle: float,
) -> tuple[float, float]:
    ox, oy = 0.0, 0.0
    for well in wells:
        if well.kind != "black_hole":
            continue
        wp = camera.world_to_chase_screen(
            well.pos,
            ship_pos,
            ship_angle,
            min_ahead=camera.min_depth * 0.35,
            screen_margin=200.0,
        )
        if not wp.visible or wp.y < camera.play_hud_top:
            continue
        dx = x - wp.x
        dy = y - wp.y
        dist_sq = dx * dx + dy * dy
        if dist_sq > 180.0 * 180.0 or dist_sq < 4.0:
            continue
        pull = min(14.0, 4200.0 / dist_sq)
        ox += dx * pull * 0.08
        oy += dy * pull * 0.06
    return x + ox, y + oy
