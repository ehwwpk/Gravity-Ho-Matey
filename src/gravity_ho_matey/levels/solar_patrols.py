from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind


def solar_patrol_enemies() -> list[PatrolEnemy]:
    """Patrol skiffs for Singularity Crossing — each drops a persistent power-up."""
    return [
        PatrolEnemy(
            waypoints=(Vec2(360, 88), Vec2(600, 88), Vec2(600, 150), Vec2(360, 150)),
            thrust=245.0,
            max_speed=108.0,
            drop_kind=PowerUpKind.RAPID_FIRE,
        ),
        PatrolEnemy(
            waypoints=(Vec2(845, 210), Vec2(845, 430), Vec2(770, 430), Vec2(770, 210)),
            thrust=235.0,
            max_speed=102.0,
            drop_kind=PowerUpKind.THRUST_BOOST,
        ),
        PatrolEnemy(
            waypoints=(Vec2(110, 430), Vec2(240, 520), Vec2(360, 440), Vec2(240, 360)),
            thrust=230.0,
            max_speed=100.0,
            drop_kind=PowerUpKind.STABILIZER,
        ),
        PatrolEnemy(
            waypoints=(Vec2(620, 250), Vec2(700, 320), Vec2(620, 390), Vec2(540, 320)),
            thrust=228.0,
            max_speed=98.0,
            drop_kind=PowerUpKind.THRUST_BOOST,
        ),
    ]
