from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid, make_ring_cluster, make_shower_cluster
from gravity_ho_matey.gameplay.entities import Asteroid
from gravity_ho_matey.settings import CANVAS_WIDTH, SOLAR_STRIP_HEIGHT


def build_cove_asteroids() -> list[Asteroid]:
    rocks: list[Asteroid] = []

    rocks.extend(
        make_ring_cluster(
            Vec2(270, 505),
            radius=88.0,
            count=4,
            base_seed=101,
            size_class="rock",
            clockwise=True,
        )
    )
    rocks.append(make_asteroid(Vec2(355, 488), seed=102, size_class="boulder", drift_kind="slow"))
    rocks.append(make_asteroid(Vec2(210, 520), seed=103, size_class="rock", drift_kind="medium"))

    rocks.extend(
        make_ring_cluster(
            Vec2(667, 422),
            radius=62.0,
            count=3,
            base_seed=201,
            size_class="rock",
            clockwise=False,
        )
    )
    rocks.append(make_asteroid(Vec2(710, 455), seed=202, size_class="boulder", drift_kind="slow"))

    for i, pos in enumerate(
        (
            Vec2(160, 280),
            Vec2(520, 180),
            Vec2(780, 340),
            Vec2(430, 560),
        )
    ):
        rocks.append(make_asteroid(pos, seed=301 + i, size_class="pebble", drift_kind="medium"))

    rocks.append(make_asteroid(Vec2(600, 120), seed=310, size_class="rock", drift_kind="fast"))

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
