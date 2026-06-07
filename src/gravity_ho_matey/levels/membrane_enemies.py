from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.levels.membrane_layout import MembraneLayout


def membrane_road_squids(layout: MembraneLayout) -> list[SquidEnemy]:
    squids: list[SquidEnemy] = []
    for i, pos in enumerate(layout.road_squid_spawns):
        squids.append(
            SquidEnemy(
                pos=Vec2(pos.x, pos.y),
                orbit_sign=1.0 if i % 2 == 0 else -1.0,
                tentacle_reach=64.0,
                max_speed=178.0,
                detect_range=720.0,
                engage_range=580.0,
                approach_thrust=420.0,
            )
        )
    return squids
