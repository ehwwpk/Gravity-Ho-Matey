from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid, make_ring_cluster, make_shower_cluster
from gravity_ho_matey.gameplay.entities import Asteroid
from gravity_ho_matey.settings import CANVAS_WIDTH, SOLAR_STRIP_HEIGHT


def build_cove_asteroids() -> list[Asteroid]:
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
    rocks.append(make_asteroid(Vec2(355, 488), seed=102, size_class="rock", drift_kind="slow"))
    rocks.append(make_asteroid(Vec2(520, 180), seed=301, size_class="pebble", drift_kind="medium"))

    return rocks


def build_solar_asteroids() -> list[Asteroid]:
    strip_h = SOLAR_STRIP_HEIGHT
    cx = CANVAS_WIDTH / 2
    field: list[Asteroid] = []

    field.extend(
        make_ring_cluster(
            Vec2(205, strip_h * 0.38),
            radius=105.0,
            count=5,
            base_seed=401,
            size_class="rock",
            clockwise=True,
        )
    )
    field.extend(
        make_ring_cluster(
            Vec2(755, strip_h * 0.64),
            radius=118.0,
            count=5,
            base_seed=402,
            size_class="rock",
            clockwise=False,
        )
    )

    field.extend(
        make_shower_cluster(
            Vec2(cx - 120, strip_h * 0.52),
            count=6,
            base_seed=501,
            direction=Vec2(0.92, 0.18),
            size_class="pebble",
            spread=85.0,
        )
    )

    field.append(make_asteroid(Vec2(880, strip_h * 0.3), seed=601, size_class="boulder", drift_kind="medium"))
    field.append(make_asteroid(Vec2(95, strip_h * 0.72), seed=602, size_class="rock", drift_kind="slow"))
    field.append(make_asteroid(Vec2(cx + 180, strip_h * 0.18), seed=603, size_class="pebble", drift_kind="fast"))

    return field
