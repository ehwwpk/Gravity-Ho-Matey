from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid
from gravity_ho_matey.gameplay.entities import Asteroid, WorldConfig
from gravity_ho_matey.levels.membrane_layout import MembraneLayout


def build_membrane_props(layout: MembraneLayout, config: WorldConfig) -> list[Asteroid]:
    """Sparse lane-edge pebbles — decoration only."""
    _ = config
    field: list[Asteroid] = []
    seed_base = 8800
    for i, sample in enumerate(layout.samples[::28]):
        lateral = sample.tangent.normalized()
        normal = Vec2(-lateral.y, lateral.x)
        side = 1 if i % 2 else -1
        offset = sample.half_width * 0.92 * side
        pos = sample.pos + normal * offset
        if pos.x < 80 or pos.x > layout.width - 80:
            continue
        if pos.y < 80 or pos.y > layout.height - 80:
            continue
        field.append(
            make_asteroid(
                pos,
                seed=seed_base + i * 7 + side,
                size_class="pebble" if i % 3 else "rock",
                drift_kind="slow",
                velocity=Vec2(normal.x * 8.0 * side, normal.y * 8.0 * side),
            )
        )
        if len(field) >= 13:
            return field
    return field
