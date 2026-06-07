from __future__ import annotations

import math
import random

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid
from gravity_ho_matey.gameplay.entities import Asteroid, WorldConfig
from gravity_ho_matey.levels.siege_layout import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    SPAWN_CLEAR_RADIUS,
    SPIRAL_INNER,
    SPIRAL_OUTER,
    STATION_ANCHOR,
    STATION_EXCLUSION,
    SiegeLayout,
)

_SIZE_CLASSES = ("pebble", "pebble", "rock", "rock", "boulder")
_CORRIDOR_ANGLES = (0.0, math.pi * 0.34, -math.pi * 0.34)


def _too_close_to_spawns(pos: Vec2, layout: SiegeLayout) -> bool:
    if (pos - layout.spawn_ship.pos).length() < SPAWN_CLEAR_RADIUS:
        return True
    if (pos - layout.station_anchor).length() < STATION_EXCLUSION + 80.0:
        return True
    return False


def _in_corridor_gap(theta: float) -> bool:
    for center in _CORRIDOR_ANGLES:
        delta = abs((theta - center + math.pi) % math.tau - math.pi)
        if delta < math.radians(18.0):
            return True
    return False


def siege_spiral_asteroids(layout: SiegeLayout, config: WorldConfig) -> list[Asteroid]:
    """Archimedean spiral belt with semi-chaotic drift between the two forces."""
    del config
    rng = random.Random(5107)
    rocks: list[Asteroid] = []
    center = layout.spiral_center
    count = 72
    theta_max = 4.5 * math.pi

    for i in range(count):
        t = i / max(1, count - 1)
        theta = t * theta_max
        if _in_corridor_gap(theta) and 0.18 < t < 0.88:
            continue
        base_r = SPIRAL_INNER + (SPIRAL_OUTER - SPIRAL_INNER) * t
        jitter = rng.uniform(-18.0, 18.0)
        r = base_r + jitter
        pos = center + Vec2(math.cos(theta) * r, math.sin(theta) * r * 0.92)
        if pos.x < 80.0 or pos.x > ARENA_WIDTH - 80.0:
            continue
        if pos.y < 80.0 or pos.y > ARENA_HEIGHT - 80.0:
            continue
        if _too_close_to_spawns(pos, layout):
            continue
        if (pos - STATION_ANCHOR).length() < STATION_EXCLUSION:
            continue

        size_class = _SIZE_CLASSES[i % len(_SIZE_CLASSES)]
        if i % 9 == 0:
            size_class = "rock"
        drift_kind = "slow" if i % 4 else "medium"
        speed = rng.uniform(8.0, 28.0)
        drift_dir = Vec2.from_angle(theta + math.pi / 2.0 + rng.uniform(-0.4, 0.4))
        vel = drift_dir * speed
        if i % 11 == 0:
            rocks.append(
                make_asteroid(
                    pos,
                    seed=9000 + i,
                    size_class=size_class,
                    drift_kind="ring",
                    ring_anchor=Vec2(center.x, center.y),
                    ring_radius=r,
                    ring_orbit_radius=r * 0.04,
                    ring_phase=theta,
                )
            )
        else:
            rocks.append(
                make_asteroid(
                    pos,
                    seed=9000 + i,
                    size_class=size_class,
                    drift_kind=drift_kind,
                    velocity=vel,
                )
            )

    for extra in range(10):
        theta = rng.uniform(0.0, math.tau)
        r = rng.uniform(SPIRAL_INNER + 40.0, SPIRAL_OUTER - 30.0)
        pos = center + Vec2(math.cos(theta) * r, math.sin(theta) * r * 0.9)
        if _too_close_to_spawns(pos, layout):
            continue
        rocks.append(
            make_asteroid(
                pos,
                seed=12000 + extra,
                size_class="rock",
                drift_kind="medium",
                velocity=Vec2.from_angle(theta) * rng.uniform(12.0, 32.0),
            )
        )
    return rocks
