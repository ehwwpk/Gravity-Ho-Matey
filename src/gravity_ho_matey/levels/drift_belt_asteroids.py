from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import make_mixed_belt_ring
from gravity_ho_matey.gameplay.entities import Asteroid, WorldConfig
from gravity_ho_matey.levels.drift_belt_layout import CENTER, RING_SPECS, SPAWN_CLEAR_RADIUS


def build_drift_belt_asteroids(config: WorldConfig) -> list[Asteroid]:
    """Every spawned rock is real — kinematic rings + spatial collision keep Drift fast."""
    anchor = Vec2(CENTER.x, CENTER.y)
    field: list[Asteroid] = []
    for ring_index, (radius, count, size_mix) in enumerate(RING_SPECS):
        clockwise = ring_index % 2 == 0
        field.extend(
            make_mixed_belt_ring(
                anchor,
                radius=radius,
                count=count,
                base_seed=3000 + ring_index * 17,
                size_mix=size_mix,
                clockwise=clockwise,
                radial_jitter=5.0 if ring_index < len(RING_SPECS) - 1 else 4.0,
            )
        )
    if config.width > 0 and config.height > 0:
        field = [a for a in field if (a.pos - anchor).length() >= SPAWN_CLEAR_RADIUS]
    return field
