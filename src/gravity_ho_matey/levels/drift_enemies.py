from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.levels.drift_belt_layout import DriftLayout


def drift_squid_enemies(layout: DriftLayout) -> list[SquidEnemy]:
    """Void squids prowling the outer dense belt — physical wrap, no gunfire."""
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
    return squids
