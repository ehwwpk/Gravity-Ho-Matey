from __future__ import annotations

import math
from enum import Enum, auto

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import WorldConfig

CHART_RADIATION_EXPOSURE_LIMIT = 5.0
CHART_BOUNDS_TOAST_SECONDS = 1.6
CHART_BOUNDS_MARGIN_FRAC = 0.05
# Levels 1–2 (Cove, Solar): +10% outward breathing room beyond base margin.
_CHART_SECTOR_BASE_FRAC = CHART_BOUNDS_MARGIN_FRAC * 1.10
# Playtest widen L1/L2 — chart rim expanded vs pre-playtest base (wells/rocks/beacons stay put).
# Stacked: sector base +10%, then +12.5%, then +10% playtest follow-up ≈ +37% total vs first L1/L2 margins.
CHART_RIM_EXPAND_L12 = 1.2375
CHART_SECTOR_MARGIN_FRAC = _CHART_SECTOR_BASE_FRAC * CHART_RIM_EXPAND_L12
# Level 1 Cove — sector base + another 5% per side, then L12 expand (void hazards follow same margin).
COVE_CHART_MARGIN_FRAC = (_CHART_SECTOR_BASE_FRAC + CHART_BOUNDS_MARGIN_FRAC) * CHART_RIM_EXPAND_L12

# Camera: ramp free-follow over this distance past the chart rim (world units).
OOB_CAMERA_BLEND_FULL_DIST = 90.0

# Cove void ring: ~1.5s cruise beyond the chart rim at typical thrust speed.
OOB_RING_TRAVEL_SECONDS = 1.5
OOB_RING_CRUISE_SPEED = 220.0

# Chase view: dotted chart rim only when the ship is near an edge (world units).
CHART_EDGE_HINT_START_FRAC = 0.14
CHART_EDGE_HINT_FULL_FRAC = 0.045
CHART_EDGE_HINT_START_MIN = 85.0
CHART_EDGE_HINT_FULL_MIN = 28.0
# L1/L2 — chase dotted rim only when hugging the true boundary (not mid-chart drift).
CHART_EDGE_HINT_START_FRAC_L12 = 0.085
CHART_EDGE_HINT_FULL_FRAC_L12 = 0.032
CHART_EDGE_HINT_START_MIN_L12 = 58.0
CHART_EDGE_HINT_FULL_MIN_L12 = 20.0


class ChartBoundsToast(Enum):
    LEFT_CHART = auto()
    ENTERED_CHART = auto()


def chart_margin_xy(config: WorldConfig) -> tuple[float, float]:
    frac = config.chart_margin_frac
    return config.width * frac, config.height * frac


def chart_limits(config: WorldConfig) -> tuple[float, float, float, float]:
    """Inclusive playable chart rect — expanded outward from level width/height."""
    mx, my = chart_margin_xy(config)
    return (-mx, -my, config.width + mx, config.height + my)


def chart_limits_for_margin_frac(
    config: WorldConfig,
    margin_frac: float,
) -> tuple[float, float, float, float]:
    """Chart rect for an explicit margin — tests and historical margin comparisons."""
    mx = config.width * margin_frac
    my = config.height * margin_frac
    return (-mx, -my, config.width + mx, config.height + my)


def chart_outer_radius_for_margin_frac(config: WorldConfig, margin_frac: float) -> float:
    cx = config.width * 0.5
    cy = config.height * 0.5
    x0, y0, x1, y1 = chart_limits_for_margin_frac(config, margin_frac)
    return max(
        math.hypot(x0 - cx, y0 - cy),
        math.hypot(x1 - cx, y0 - cy),
        math.hypot(x1 - cx, y1 - cy),
        math.hypot(x0 - cx, y1 - cy),
    )


def oob_ring_radius_for_margin_frac(config: WorldConfig, margin_frac: float) -> float:
    return chart_outer_radius_for_margin_frac(config, margin_frac) + OOB_RING_TRAVEL_SECONDS * OOB_RING_CRUISE_SPEED


def chart_outer_radius_from_center(config: WorldConfig) -> float:
    """Distance from level center to the farthest chart corner."""
    cx = config.width * 0.5
    cy = config.height * 0.5
    x0, y0, x1, y1 = chart_limits(config)
    return max(
        math.hypot(x0 - cx, y0 - cy),
        math.hypot(x1 - cx, y0 - cy),
        math.hypot(x1 - cx, y1 - cy),
        math.hypot(x0 - cx, y1 - cy),
    )


def oob_ring_radius(config: WorldConfig) -> float:
    """Orbital radius for the void hazard ring just outside the chart."""
    return chart_outer_radius_from_center(config) + OOB_RING_TRAVEL_SECONDS * OOB_RING_CRUISE_SPEED


def ship_in_chart(pos: Vec2, config: WorldConfig, *, margin: float = 0.0) -> bool:
    x0, y0, x1, y1 = chart_limits(config)
    return (
        x0 - margin <= pos.x <= x1 + margin
        and y0 - margin <= pos.y <= y1 + margin
    )


def chart_oob_distance(pos: Vec2, config: WorldConfig) -> float:
    """World units outside the chart rectangle (0 when inside)."""
    x0, y0, x1, y1 = chart_limits(config)
    dx = 0.0
    if pos.x < x0:
        dx = x0 - pos.x
    elif pos.x > x1:
        dx = pos.x - x1
    dy = 0.0
    if pos.y < y0:
        dy = y0 - pos.y
    elif pos.y > y1:
        dy = pos.y - y1
    return math.hypot(dx, dy)


def oob_camera_blend(pos: Vec2, config: WorldConfig) -> float:
    """0 = clamped chart cam; 1 = free ship-centered follow — smooth past the rim."""
    if not config.open_bounds:
        return 0.0
    dist = chart_oob_distance(pos, config)
    if dist <= 0.0:
        return 0.0
    full = OOB_CAMERA_BLEND_FULL_DIST
    if dist >= full:
        return 1.0
    t = dist / full
    return t * t * (3.0 - 2.0 * t)


def chart_radiation_reason(*, level_theme: str) -> str:
    if level_theme == "drift":
        return "Deep void exposure exceeded safe limits."
    if level_theme == "solar":
        return "Chart radiation exceeded safe exposure beyond the star strip."
    return "Void radiation breached the hull outside the reef chart."


def radiation_exposure_fraction(exposure: float) -> float:
    if CHART_RADIATION_EXPOSURE_LIMIT <= 0.0:
        return 0.0
    return max(0.0, min(1.0, exposure / CHART_RADIATION_EXPOSURE_LIMIT))


def chart_bounds_toast_copy(
    kind: ChartBoundsToast,
    *,
    level_theme: str,
    exposure: float,
) -> tuple[str, str]:
    """Headline + subline for chart boundary transitions."""
    limit = CHART_RADIATION_EXPOSURE_LIMIT
    if kind is ChartBoundsToast.LEFT_CHART:
        if level_theme == "solar":
            return ("Off strip", f"{limit:0.0f}s exposure banked toward hull damage")
        return ("Off chart", f"{limit:0.0f}s exposure banked toward hull damage")

    if exposure <= 0.0:
        sub = "Exposure timer paused"
    else:
        sub = f"Banked {exposure:0.1f}s / {limit:0.0f}s"
    if level_theme == "solar":
        return ("Back on strip", sub)
    return ("Back on chart", sub)


def chart_edge_hint_distances(config: WorldConfig) -> tuple[float, float]:
    """Return (fade_in_start, full_strength) distances from a chart edge."""
    span = min(config.width, config.height)
    if config.level_theme in ("cove", "solar"):
        start_frac = CHART_EDGE_HINT_START_FRAC_L12
        full_frac = CHART_EDGE_HINT_FULL_FRAC_L12
        start_min = CHART_EDGE_HINT_START_MIN_L12
        full_min = CHART_EDGE_HINT_FULL_MIN_L12
    else:
        start_frac = CHART_EDGE_HINT_START_FRAC
        full_frac = CHART_EDGE_HINT_FULL_FRAC
        start_min = CHART_EDGE_HINT_START_MIN
        full_min = CHART_EDGE_HINT_FULL_MIN
    start = max(start_min, span * start_frac)
    full = max(full_min, span * full_frac)
    return start, full


def chart_edge_inset_distances(pos: Vec2, config: WorldConfig) -> tuple[float, float, float, float]:
    """Inside-chart distances to left, right, top, bottom edges."""
    x0, y0, x1, y1 = chart_limits(config)
    return (pos.x - x0, x1 - pos.x, pos.y - y0, y1 - pos.y)


def chart_edge_hint_strength(inset: float, *, start: float, full: float) -> float:
    """0 = too far to show; 1 = at the edge."""
    if inset >= start:
        return 0.0
    if inset <= full:
        return 1.0
    t = 1.0 - (inset - full) / (start - full)
    return t * t


def chart_edge_hints_for_ship(pos: Vec2, config: WorldConfig) -> tuple[tuple[str, float], ...]:
    """Near-edge chart sides with hint strength — empty unless open bounds and in-chart."""
    if not config.open_bounds or not ship_in_chart(pos, config):
        return ()
    start, full = chart_edge_hint_distances(config)
    left, right, top, bottom = chart_edge_inset_distances(pos, config)
    hints: list[tuple[str, float]] = []
    for tag, inset in (("left", left), ("right", right), ("top", top), ("bottom", bottom)):
        strength = chart_edge_hint_strength(inset, start=start, full=full)
        if strength > 0.02:
            hints.append((tag, strength))
    return tuple(hints)


def nudge_ship_into_chart(pos: Vec2, config: WorldConfig, *, inset: float = 6.0) -> Vec2:
    """Clamp to the inset chart rectangle — pulls OOB positions back inside."""
    x0, y0, x1, y1 = chart_limits(config)
    x = max(x0 + inset, min(x1 - inset, pos.x))
    y = max(y0 + inset, min(y1 - inset, pos.y))
    return Vec2(x, y)


def chart_bounds_edge_badge(*, level_theme: str, exposure: float) -> str:
    remaining = max(0.0, CHART_RADIATION_EXPOSURE_LIMIT - exposure)
    if level_theme == "solar":
        return f"OFF STRIP · {remaining:0.1f}s to damage"
    return f"OFF CHART · {remaining:0.1f}s to damage"
