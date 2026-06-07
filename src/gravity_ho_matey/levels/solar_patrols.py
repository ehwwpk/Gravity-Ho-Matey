from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemies import PatrolEnemy


def solar_patrol_enemies(strip_height: float) -> list[PatrolEnemy]:
    """Patrol skiffs for Singularity Crossing — armed with predictive battery fire."""
    mid = strip_height * 0.5
    return [
        PatrolEnemy(
            waypoints=(Vec2(360, 140), Vec2(600, 140), Vec2(600, 220), Vec2(360, 220)),
            thrust=245.0,
            max_speed=108.0,
            can_shoot=True,
            fire_interval=3.2,
            fire_cooldown=0.6,
            engage_range=460.0,
        ),
        PatrolEnemy(
            waypoints=(Vec2(845, mid - 120), Vec2(845, mid + 80), Vec2(770, mid + 80), Vec2(770, mid - 120)),
            thrust=235.0,
            max_speed=102.0,
            can_shoot=True,
            fire_interval=3.55,
            fire_cooldown=1.1,
        ),
    ]
