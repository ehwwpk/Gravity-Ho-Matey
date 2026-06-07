from __future__ import annotations

import random

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid
from gravity_ho_matey.gameplay.entities import Asteroid, WorldConfig
from gravity_ho_matey.levels.guard_layout import CENTER, GuardLayout


def build_guard_asteroids(layout: GuardLayout, config: WorldConfig) -> list[Asteroid]:
    """Sparse mid-field clutter — no belt simulation."""
    del config
    rng = random.Random(4401)
    asteroids: list[Asteroid] = []
    specs = (
        (Vec2(1180.0, 1980.0), "pebble", 44011),
        (Vec2(1520.0, 1760.0), "rock", 44012),
        (Vec2(1880.0, 2100.0), "pebble", 44013),
        (Vec2(2140.0, 1720.0), "rock", 44014),
        (Vec2(2480.0, 2050.0), "pebble", 44015),
        (Vec2(2820.0, 1840.0), "rock", 44016),
        (Vec2(1360.0, 2280.0), "pebble", 44017),
        (Vec2(2640.0, 2220.0), "pebble", 44018),
        (Vec2(1680.0, 1420.0), "rock", 44019),
        (Vec2(2320.0, 1380.0), "rock", 44020),
        (Vec2(CENTER.x + 180.0, 1900.0), "pebble", 44021),
        (Vec2(CENTER.x - 220.0, 1860.0), "pebble", 44022),
        (Vec2(980.0, 1520.0), "rock", 44023),
        (Vec2(3020.0, 1480.0), "rock", 44024),
        (Vec2(CENTER.x, 2180.0), "pebble", 44025),
    )
    for pos, size_class, seed in specs:
        drift = Vec2.from_angle(rng.uniform(0.0, 6.28)) * rng.uniform(8.0, 22.0)
        asteroids.append(
            make_asteroid(
                pos,
                seed=seed,
                size_class=size_class,
                drift_kind="slow",
                velocity=drift,
            )
        )
    return asteroids
