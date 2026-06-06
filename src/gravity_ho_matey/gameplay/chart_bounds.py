from __future__ import annotations

import math
from enum import Enum, auto

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import WorldConfig

CHART_RADIATION_EXPOSURE_LIMIT = 5.0
CHART_BOUNDS_TOAST_SECONDS = 1.6

# Chase view: dotted chart rim only when the ship is near an edge (world units).
CHART_EDGE_HINT_START_FRAC = 0.14
CHART_EDGE_HINT_FULL_FRAC = 0.045
CHART_EDGE_HINT_START_MIN = 85.0
CHART_EDGE_HINT_FULL_MIN = 28.0


class ChartBoundsToast(Enum):
    LEFT_CHART = auto()
    ENTERED_CHART = auto()


def ship_in_chart(pos: Vec2, config: WorldConfig, *, margin: float = 0.0) -> bool:
    return (
        -margin <= pos.x <= config.width + margin
        and -margin <= pos.y <= config.height + margin
    )


def chart_oob_distance(pos: Vec2, config: WorldConfig) -> float:
    """World units outside the chart rectangle (0 when inside)."""
    dx = 0.0
    if pos.x < 0.0:
        dx = -pos.x
    elif pos.x > config.width:
        dx = pos.x - config.width
    dy = 0.0
    if pos.y < 0.0:
        dy = -pos.y
    elif pos.y > config.height:
        dy = pos.y - config.height
    return math.hypot(dx, dy)


def chart_radiation_reason(*, level_theme: str) -> str:
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
    start = max(CHART_EDGE_HINT_START_MIN, span * CHART_EDGE_HINT_START_FRAC)
    full = max(CHART_EDGE_HINT_FULL_MIN, span * CHART_EDGE_HINT_FULL_FRAC)
    return start, full


def chart_edge_inset_distances(pos: Vec2, config: WorldConfig) -> tuple[float, float, float, float]:
    """Inside-chart distances to left, right, top, bottom edges."""
    return (pos.x, config.width - pos.x, pos.y, config.height - pos.y)


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
    x = max(inset, min(config.width - inset, pos.x))
    y = max(inset, min(config.height - inset, pos.y))
    return Vec2(x, y)


def chart_bounds_edge_badge(*, level_theme: str, exposure: float) -> str:
    remaining = max(0.0, CHART_RADIATION_EXPOSURE_LIMIT - exposure)
    if level_theme == "solar":
        return f"OFF STRIP · {remaining:0.1f}s to damage"
    return f"OFF CHART · {remaining:0.1f}s to damage"
