from __future__ import annotations

from dataclasses import replace

from gravity_ho_matey.gameplay.entities import WorldConfig
from gravity_ho_matey.settings import CANVAS_HEIGHT, CANVAS_WIDTH

# Belt spacing / timing — ~1s cruise between rings at typical thrust.
BELT_CRUISE_SPEED = 220.0


def chart_sector_config(
    *,
    theme: str,
    name: str,
    width: int = CANVAS_WIDTH,
    height: int = CANVAS_HEIGHT,
    **overrides: float | int | str | bool,
) -> WorldConfig:
    """Compact chart sectors (Cove, Solar) — radiation on, beacons typical."""
    base = WorldConfig(
        width=width,
        height=height,
        viewport_width=CANVAS_WIDTH,
        viewport_height=CANVAS_HEIGHT,
        level_theme=theme,
        level_name=name,
        open_bounds=True,
        radiation_enabled=True,
        chart_margin_frac=0.05,
        max_asteroids=48,
    )
    return replace(base, **overrides) if overrides else base


def open_sector_config(
    *,
    theme: str,
    name: str,
    arena_size: int,
    **overrides: float | int | str | bool,
) -> WorldConfig:
    """Large open arena (Drift) — no radiation, high asteroid cap."""
    base = WorldConfig(
        width=arena_size,
        height=arena_size,
        viewport_width=CANVAS_WIDTH,
        viewport_height=CANVAS_HEIGHT,
        level_theme=theme,
        level_name=name,
        open_bounds=True,
        radiation_enabled=False,
        chart_margin_frac=0.48,
        max_asteroids=140,
        gravity_scale=0.48,
        turn_rate=5.1,
        thrust=252.0,
    )
    return replace(base, **overrides) if overrides else base
