from __future__ import annotations

import math
import random

from gravity_ho_matey.core.vector import Vec2

_SIZE_TABLE: dict[str, tuple[int, int, float, float]] = {
    "pebble": (6, 8, 16.0, 28.0),
    "rock": (8, 12, 30.0, 52.0),
    "boulder": (10, 14, 52.0, 82.0),
}


def generate_asteroid_verts(seed: int, size_class: str = "rock") -> tuple[Vec2, ...]:
    """Classic radial Asteroids-style convex polygon (CCW, centered on origin)."""
    n_min, n_max, r_min, r_max = _SIZE_TABLE.get(size_class, _SIZE_TABLE["rock"])
    rng = random.Random(seed)
    count = rng.randint(n_min, n_max)
    step = math.tau / count
    verts: list[Vec2] = []
    for i in range(count):
        target = step * i
        angle = target + (rng.random() - 0.5) * step * 0.42
        radius = r_min + rng.random() * (r_max - r_min)
        verts.append(Vec2(math.cos(angle) * radius, math.sin(angle) * radius))
    return tuple(verts)


def crater_offsets(seed: int, count: int, radius_hint: float) -> list[tuple[float, float, float]]:
    """Local-space crater centers as (x, y, r) for drawing."""
    rng = random.Random(seed ^ 0xA57E001)
    craters: list[tuple[float, float, float]] = []
    for _ in range(count):
        ang = rng.random() * math.tau
        dist = radius_hint * (0.25 + rng.random() * 0.45)
        craters.append(
            (
                math.cos(ang) * dist,
                math.sin(ang) * dist,
                radius_hint * (0.08 + rng.random() * 0.12),
            )
        )
    return craters
