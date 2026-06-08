from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid, make_ring_cluster, make_shower_cluster
from gravity_ho_matey.gameplay.asteroid_tiers import AsteroidTier
from gravity_ho_matey.gameplay.chart_bounds import (
    chart_limits,
    chart_outer_radius_from_center,
    oob_ring_radius,
)
from gravity_ho_matey.gameplay.entities import Asteroid, WorldConfig
from gravity_ho_matey.settings import CANVAS_WIDTH, SOLAR_STRIP_HEIGHT

_COVE_OOB_RING_COUNT = 12
_COVE_OOB_RING_SEED = 901
_COVE_OOB_SCATTER_COUNT = 4
_COVE_OOB_SCATTER_SEED = 911
_COVE_RIM_MEDIUM_SEED = 921
_COVE_RIM_OUTSET = 16.0


def _cove_void_anchor(config: WorldConfig) -> Vec2:
    return Vec2(config.width * 0.5, config.height * 0.5)


def build_cove_oob_chart_ring(config: WorldConfig) -> list[Asteroid]:
    """Pebbles orbiting ~1.5s beyond the chart rim — only simulates when the ship leaves chart."""
    anchor = _cove_void_anchor(config)
    ring = make_ring_cluster(
        anchor,
        radius=oob_ring_radius(config),
        count=_COVE_OOB_RING_COUNT,
        base_seed=_COVE_OOB_RING_SEED,
        size_class="pebble",
        clockwise=True,
    )
    for asteroid in ring:
        asteroid.free_bounds = True
    return ring


def build_cove_oob_void_scatter(config: WorldConfig) -> list[Asteroid]:
    """Mid-band void pebbles between chart rim and main ring."""
    anchor = _cove_void_anchor(config)
    outer = chart_outer_radius_from_center(config)
    full = oob_ring_radius(config)
    mid_radius = outer + (full - outer) * 0.55
    scatter = make_ring_cluster(
        anchor,
        radius=mid_radius,
        count=_COVE_OOB_SCATTER_COUNT,
        base_seed=_COVE_OOB_SCATTER_SEED,
        size_class="pebble",
        clockwise=False,
    )
    for asteroid in scatter:
        asteroid.free_bounds = True
    return scatter


def build_cove_chart_rim_mediums(config: WorldConfig) -> list[Asteroid]:
    """Medium rocks perched just past the chart rim — first void hazards when leaving chart."""
    x0, y0, x1, y1 = chart_limits(config)
    cx = config.width * 0.5
    cy = config.height * 0.5
    o = _COVE_RIM_OUTSET
    spots = (
        Vec2(x0 - o, cy + 80.0),
        Vec2(x1 + o, cy - 90.0),
        Vec2(cx - 120.0, y0 - o),
        Vec2(cx + 140.0, y1 + o),
    )
    rocks: list[Asteroid] = []
    for i, pos in enumerate(spots):
        asteroid = make_asteroid(
            pos,
            seed=_COVE_RIM_MEDIUM_SEED + i,
            size_class="rock",
            drift_kind="slow",
            tier_override=AsteroidTier.MEDIUM,
        )
        asteroid.free_bounds = True
        rocks.append(asteroid)
    return rocks


def build_cove_asteroids(config: WorldConfig) -> list[Asteroid]:
    """Intro field — a few hazards to teach drift; heavier belts come later."""
    rocks: list[Asteroid] = []

    rocks.extend(
        make_ring_cluster(
            Vec2(270, 505),
            radius=72.0,
            count=2,
            base_seed=101,
            size_class="rock",
            clockwise=True,
        )
    )
    rocks.append(
        make_asteroid(
            Vec2(355, 488),
            seed=102,
            size_class="rock",
            drift_kind="slow",
            tier_override=AsteroidTier.MEDIUM,
        )
    )
    rocks.append(make_asteroid(Vec2(520, 180), seed=301, size_class="pebble", drift_kind="medium"))
    rocks.extend(build_cove_chart_rim_mediums(config))
    rocks.extend(build_cove_oob_chart_ring(config))
    rocks.extend(build_cove_oob_void_scatter(config))
    return rocks


def build_solar_asteroids() -> list[Asteroid]:
    strip_h = SOLAR_STRIP_HEIGHT
    cx = CANVAS_WIDTH / 2
    field: list[Asteroid] = []

    field.extend(
        make_ring_cluster(
            Vec2(205, strip_h * 0.38),
            radius=105.0,
            count=4,
            base_seed=401,
            size_class="rock",
            clockwise=True,
        )
    )
    field.extend(
        make_ring_cluster(
            Vec2(755, strip_h * 0.64),
            radius=118.0,
            count=4,
            base_seed=402,
            size_class="rock",
            clockwise=False,
        )
    )

    field.extend(
        make_shower_cluster(
            Vec2(cx - 120, strip_h * 0.52),
            count=4,
            base_seed=501,
            direction=Vec2(0.92, 0.18),
            size_class="pebble",
            spread=85.0,
        )
    )

    field.append(make_asteroid(Vec2(880, strip_h * 0.3), seed=601, size_class="boulder", drift_kind="medium"))
    field.append(make_asteroid(Vec2(95, strip_h * 0.72), seed=602, size_class="rock", drift_kind="slow"))

    return field
