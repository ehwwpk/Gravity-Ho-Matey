from __future__ import annotations

from dataclasses import replace

from gravity_ho_matey.gameplay.chart_bounds import CHART_SECTOR_MARGIN_FRAC
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
        chart_margin_frac=CHART_SECTOR_MARGIN_FRAC,
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


def membrane_strip_config(
    *,
    theme: str,
    name: str,
    width: int,
    height: int,
    **overrides: float | int | str | bool,
) -> WorldConfig:
    """Tall membrane highway — boost ribbons, void pockets, boss-gated exit."""
    base = WorldConfig(
        width=width,
        height=height,
        viewport_width=CANVAS_WIDTH,
        viewport_height=CANVAS_HEIGHT,
        level_theme=theme,
        level_name=name,
        open_bounds=True,
        radiation_enabled=False,
        chart_margin_frac=0.42,
        max_asteroids=16,
        gravity_scale=0.48,
        turn_rate=5.1,
        thrust=250.0,
        exit_requires_boss=True,
        pad_overspeed_cap=1.18,
    )
    return replace(base, **overrides) if overrides else base


def skirmish_arena_config(
    *,
    theme: str,
    name: str,
    width: int,
    height: int,
    roster_kill_quota: int,
    **overrides: float | int | str | bool,
) -> WorldConfig:
    """Wide force-vs-force arena — roster kill quota unlocks exit."""
    base = WorldConfig(
        width=width,
        height=height,
        viewport_width=CANVAS_WIDTH,
        viewport_height=CANVAS_HEIGHT,
        level_theme=theme,
        level_name=name,
        open_bounds=True,
        radiation_enabled=False,
        chart_margin_frac=0.46,
        max_asteroids=80,
        gravity_scale=0.47,
        turn_rate=5.15,
        thrust=254.0,
        exit_requires_roster_clear=True,
        roster_kill_quota=roster_kill_quota,
    )
    return replace(base, **overrides) if overrides else base
