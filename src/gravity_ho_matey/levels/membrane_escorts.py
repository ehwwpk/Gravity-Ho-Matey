from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.friendly_fighter import FriendlyFighter
from gravity_ho_matey.levels.membrane_layout import MembraneLayout


def membrane_friendly_fighters(layout: MembraneLayout) -> list[FriendlyFighter]:
    """Two wing escorts flanking the southern ribbon spawn."""
    spawn = layout.spawn_ship
    forward = Vec2.from_angle(spawn.angle)
    right = forward.rotated(math.pi / 2.0)
    return [
        FriendlyFighter(
            wing_id=0,
            pos=Vec2(
                spawn.pos.x + right.x * 90.0 - forward.x * 40.0,
                spawn.pos.y + right.y * 90.0 - forward.y * 40.0,
            ),
            angle=spawn.angle,
            fire_cooldown=2.0,
        ),
        FriendlyFighter(
            wing_id=1,
            pos=Vec2(
                spawn.pos.x - right.x * 110.0 - forward.x * 65.0,
                spawn.pos.y - right.y * 110.0 - forward.y * 65.0,
            ),
            angle=spawn.angle,
            fire_cooldown=2.8,
        ),
    ]
