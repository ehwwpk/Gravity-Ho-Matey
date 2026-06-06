from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind


def solar_patrol_enemies(strip_height: float) -> list[PatrolEnemy]:
    """Patrol skiffs for Singularity Crossing — armed with predictive battery fire."""
    mid = strip_height * 0.5
    return [
        PatrolEnemy(
            waypoints=(Vec2(360, 140), Vec2(600, 140), Vec2(600, 220), Vec2(360, 220)),
            thrust=245.0,
            max_speed=108.0,
            drop_kind=PowerUpKind.RAPID_FIRE,
            can_shoot=True,
            fire_interval=2.85,
            fire_cooldown=0.6,
            engage_range=460.0,
        ),
        PatrolEnemy(
            waypoints=(Vec2(845, mid - 120), Vec2(845, mid + 80), Vec2(770, mid + 80), Vec2(770, mid - 120)),
            thrust=235.0,
            max_speed=102.0,
            drop_kind=PowerUpKind.THRUST_BOOST,
            can_shoot=True,
            fire_interval=3.15,
            fire_cooldown=1.1,
            shot_speed=232.0,
        ),
        PatrolEnemy(
            waypoints=(
                Vec2(110, strip_height * 0.68),
                Vec2(240, strip_height * 0.74),
                Vec2(360, strip_height * 0.68),
                Vec2(240, strip_height * 0.62),
            ),
            thrust=230.0,
            max_speed=100.0,
            drop_kind=PowerUpKind.STABILIZER,
            can_shoot=True,
            fire_interval=3.0,
            fire_cooldown=1.7,
            engage_range=420.0,
        ),
        PatrolEnemy(
            waypoints=(Vec2(620, mid - 40), Vec2(700, mid + 20), Vec2(620, mid + 80), Vec2(540, mid + 20)),
            thrust=228.0,
            max_speed=98.0,
            drop_kind=PowerUpKind.THRUST_BOOST,
            can_shoot=True,
            fire_interval=3.35,
            fire_cooldown=2.0,
            shot_speed=224.0,
        ),
    ]
