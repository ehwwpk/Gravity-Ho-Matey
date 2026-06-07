from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.friendly_fighter import FriendlyFighter
from gravity_ho_matey.levels.siege_layout import ALLY_WING_COUNT, SiegeLayout


def siege_friendly_fighters(layout: SiegeLayout) -> list[FriendlyFighter]:
    """Twelve wing escorts — wide stagger east of spawn, closer to the skirmish line."""
    spawn = layout.spawn_ship
    forward = Vec2.from_angle(spawn.angle)
    right = forward.rotated(math.pi / 2.0)
    allies: list[FriendlyFighter] = []
    for wing_id in range(ALLY_WING_COUNT):
        row = wing_id // 4
        col = wing_id % 4
        lateral = (col - 1.5) * 118.0
        advance = 310.0 + row * 98.0
        jitter_x = (wing_id % 5) * 7.0 - 14.0
        jitter_y = (wing_id % 3) * 10.0 - 10.0
        pos = (
            spawn.pos
            + right * (lateral + jitter_x)
            + forward * (advance + jitter_y)
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
