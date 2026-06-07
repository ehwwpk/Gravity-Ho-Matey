"""Shared planetside flight profile for toroidal surface mini-levels (L6+).

Design lock: planetside phases use tactical side-scroll only — no chase camera.
Flight is faster than orbital with a stronger Shift boost (burst, overspeed, FX).
"""

from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import WorldConfig

# --- Standard planetside flight tuning (applied when WorldConfig.surface_wrap) ---

PLANETSIDE_FLIGHT_DEFAULTS: dict[str, float] = {
    "max_ship_speed": 312.0,
    "thrust": 310.0,
    "drag": 0.986,
    "boost_burst_fraction": 0.42,
    "boost_overspeed_cap": 1.38,
    "boost_flash_seconds": 0.55,
    "boost_energy_cost": 0.20,
    "boost_regen_rate": 0.16,
}

PLANETSIDE_DRAG_WHILE_BOOST = 0.994
PLANETSIDE_BURST_FORWARD_DOT = 0.18
PLANETSIDE_JOLT_SECONDS = 0.14
PLANETSIDE_BOOST_FX_SCALE = 1.15
PLANETSIDE_MAX_EDGE_HINTS = 4


def is_planetside(config: WorldConfig) -> bool:
    return config.surface_wrap


def planetside_overrides(**overrides: float | int | str | bool) -> dict[str, float | int | str | bool]:
    """Merge standard planetside flight values with level-specific overrides."""
    base: dict[str, float | int | str | bool] = dict(PLANETSIDE_FLIGHT_DEFAULTS)
    base.update(overrides)
    return base


def wrap_shortest_delta(from_pos: Vec2, to_pos: Vec2, wrap_width: float) -> Vec2:
    """Toroidal X delta — shortest path on a wrapping surface strip."""
    dx = to_pos.x - from_pos.x
    if wrap_width > 0.0:
        half = wrap_width * 0.5
        while dx > half:
            dx -= wrap_width
        while dx < -half:
            dx += wrap_width
    return Vec2(dx, to_pos.y - from_pos.y)


def hint_world_pos(from_pos: Vec2, target: Vec2, wrap_width: float) -> Vec2:
    """Unwrapped hint anchor so rim arrows aim along the shortest wrap path."""
    delta = wrap_shortest_delta(from_pos, target, wrap_width)
    return Vec2(from_pos.x + delta.x, from_pos.y + delta.y)


def ship_draw_jolt_angle(boost_jolt: float, elapsed: float) -> float:
    if boost_jolt <= 0.0:
        return 0.0
    t = boost_jolt / PLANETSIDE_JOLT_SECONDS
    return math.sin(elapsed * 95.0) * 0.055 * t + math.sin(elapsed * 141.0) * 0.028 * t
