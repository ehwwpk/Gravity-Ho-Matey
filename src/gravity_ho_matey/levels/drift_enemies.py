from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.levels.drift_belt_layout import RING_SPECS, DriftLayout


def drift_squid_enemies(layout: DriftLayout) -> list[SquidEnemy]:
    """Void squids — outer patrol nest plus one lurker embedded in each belt past ring two."""
    squids: list[SquidEnemy] = []
    for i, angle_deg in enumerate(layout.squid_angles_deg):
        angle = math.radians(angle_deg)
        pos = layout.center + Vec2(math.cos(angle), math.sin(angle)) * layout.squid_ring_radius
        squids.append(
            SquidEnemy(
                pos=pos,
                orbit_sign=-1.0 if i % 2 else 1.0,
                facing_angle=angle + math.pi,
            )
        )

    for ring_index, angle_deg in layout.ring_lurker_specs:
        radius = RING_SPECS[ring_index][0]
        angle = math.radians(angle_deg)
        pos = layout.center + Vec2(math.cos(angle), math.sin(angle)) * radius
        squids.append(
            SquidEnemy(
                pos=pos,
                orbit_sign=-1.0 if ring_index % 2 else 1.0,
                facing_angle=angle + math.pi,
            )
        )
    return squids
