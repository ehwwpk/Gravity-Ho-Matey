from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.levels.siege_layout import ROSTER_ENEMY_COUNT, SiegeLayout

_ENEMY_ORIGIN_X = 3600.0
_ENEMY_ORIGIN_Y = 1320.0
_COLS = 4
_ROWS = 3
_COL_SPACING = 120.0
_ROW_SPACING = 110.0


def _defensive_loop(center: Vec2, *, seed: int) -> tuple[Vec2, ...]:
    angle = seed * 0.71
    r = 72.0 + (seed % 3) * 8.0
    pts: list[Vec2] = []
    for i in range(3):
        a = angle + i * (math.tau / 3.0)
        pts.append(center + Vec2(math.cos(a) * r, math.sin(a) * r * 0.82))
    return tuple(pts)


def siege_roster_patrols(layout: SiegeLayout) -> list[PatrolEnemy]:
    """Twelve armed patrol skiffs on the east half — each counts toward exit quota."""
    del layout
    enemies: list[PatrolEnemy] = []
    roster_id = 0
    for row in range(_ROWS):
        for col in range(_COLS):
            cx = _ENEMY_ORIGIN_X + col * _COL_SPACING + (row % 2) * 18.0
            cy = _ENEMY_ORIGIN_Y + row * _ROW_SPACING
            center = Vec2(cx, cy)
            enemies.append(
                PatrolEnemy(
                    waypoints=_defensive_loop(center, seed=roster_id),
                    pos=Vec2(center.x, center.y),
                    thrust=238.0,
                    max_speed=95.0,
                    can_shoot=True,
                    fire_interval=2.95,
                    fire_cooldown=0.4 + roster_id * 0.12,
                    skirmish_roster_id=roster_id,
                )
            )
            roster_id += 1
    assert roster_id == ROSTER_ENEMY_COUNT
    return enemies
