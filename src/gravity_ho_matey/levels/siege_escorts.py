from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.friendly_fighter import FriendlyFighter
from gravity_ho_matey.levels.siege_layout import ALLY_WING_COUNT, SiegeLayout


def siege_friendly_fighters(layout: SiegeLayout) -> list[FriendlyFighter]:
    """Twelve wing escorts on the west half near player spawn."""
    spawn = layout.spawn_ship
    forward = Vec2.from_angle(spawn.angle)
    right = forward.rotated(math.pi / 2.0)
    allies: list[FriendlyFighter] = []
    for wing_id in range(ALLY_WING_COUNT):
        row = wing_id // 4
        col = wing_id % 4
        lateral = (col - 1.5) * 78.0
        trail = 55.0 + row * 62.0
        jitter_x = (wing_id % 5) * 6.0 - 12.0
        jitter_y = (wing_id % 3) * 8.0 - 8.0
        pos = (
            spawn.pos
            + right * (lateral + jitter_x)
            - forward * (trail + jitter_y)
        )
        allies.append(
            FriendlyFighter(
                wing_id=wing_id,
                pos=Vec2(pos.x, pos.y),
                angle=spawn.angle,
                fire_cooldown=0.35 * wing_id,
            )
        )
    return allies
