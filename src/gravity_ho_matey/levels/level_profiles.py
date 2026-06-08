from __future__ import annotations

from dataclasses import replace

from gravity_ho_matey.gameplay.chart_bounds import CHART_L12_EXTRA_MARGIN_WU, CHART_SECTOR_MARGIN_FRAC
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
        chart_extra_margin_wu=CHART_L12_EXTRA_MARGIN_WU,
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
        max_asteroids=200,
        gravity_scale=0.48,
        turn_rate=5.1,
        thrust=252.0,
    )
    return replace(base, **overrides) if overrides else base


def protection_arena_config(
    *,
    theme: str,
    name: str,
    width: int,
    height: int,
    **overrides: float | int | str | bool,
) -> WorldConfig:
    """Relay defense arena — timed waves, friendly station must survive."""
    base = WorldConfig(
        width=width,
        height=height,
        viewport_width=CANVAS_WIDTH,
        viewport_height=CANVAS_HEIGHT,
        level_theme=theme,
        level_name=name,
        open_bounds=True,
        radiation_enabled=False,
        chart_margin_frac=0.44,
        max_asteroids=24,
        gravity_scale=0.48,
        turn_rate=5.1,
        thrust=252.0,
        protection_mission=True,
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


def brood_moon_orbital_config(
    *,
    width: int,
    height: int,
    **overrides: float | int | str | bool,
) -> WorldConfig:
    """Approach the Brood Moon — orbital shell before surface descent."""
    base = WorldConfig(
        width=width,
        height=height,
        viewport_width=CANVAS_WIDTH,
        viewport_height=CANVAS_HEIGHT,
        level_theme="brood_moon",
        level_name="The Brood Moon",
        open_bounds=True,
        radiation_enabled=False,
        chart_margin_frac=0.44,
        max_asteroids=36,
        gravity_scale=0.46,
        turn_rate=5.1,
        thrust=252.0,
        brood_moon_mission=True,
    )
    return replace(base, **overrides) if overrides else base


def brood_moon_surface_config(
    *,
    width: int,
    height: int,
    **overrides: float | int | str | bool,
) -> WorldConfig:
    """Low-altitude nursery skim — thick air, soft down-pull, toroidal wrap."""
    from gravity_ho_matey.gameplay.planetside_flight import planetside_overrides

    flight = planetside_overrides()
    base = WorldConfig(
        width=width,
        height=height,
        viewport_width=CANVAS_WIDTH,
        viewport_height=CANVAS_HEIGHT,
        level_theme="brood_moon",
        level_name="The Brood Moon · Surface",
        open_bounds=True,
        radiation_enabled=False,
        chart_margin_frac=0.42,
        max_asteroids=48,
        gravity_scale=0.34,
        turn_rate=5.55,
        thrust=float(flight["thrust"]),
        drag=float(flight["drag"]),
        max_ship_speed=float(flight["max_ship_speed"]),
        boost_burst_fraction=float(flight["boost_burst_fraction"]),
        boost_overspeed_cap=float(flight["boost_overspeed_cap"]),
        boost_flash_seconds=float(flight["boost_flash_seconds"]),
        boost_energy_cost=float(flight["boost_energy_cost"]),
        boost_regen_rate=float(flight["boost_regen_rate"]),
        brood_moon_mission=True,
        surface_wrap=True,
    )
    return replace(base, **overrides) if overrides else base
