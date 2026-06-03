from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GravityWell


def gravity_acceleration_at(point: Vec2, wells: list[GravityWell]) -> Vec2:
    total = Vec2()
    for well in wells:
        delta = well.pos - point
        dist_sq = max(delta.length_sq(), 100.0)
        dist = dist_sq ** 0.5
        if dist > well.radius:
            continue
        falloff = 1.0 - (dist / well.radius)
        # Tuned for arcade readability rather than physical realism.
        magnitude = well.strength * falloff / max(dist, 10.0)
        total += delta.normalized() * magnitude
    return total
