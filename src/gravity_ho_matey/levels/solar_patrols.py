from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind

# Level 2 combat feel — slightly slower volleys, a touch less predictive aim.
_SOLAR_AIM_LEAD = 0.60
_SOLAR_AIM_SPREAD = 0.068


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
            fire_interval=3.2,
            fire_cooldown=0.6,
            engage_range=460.0,
            aim_lead_factor=_SOLAR_AIM_LEAD,
            aim_spread_rad=_SOLAR_AIM_SPREAD,
        ),
        PatrolEnemy(
            waypoints=(Vec2(845, mid - 120), Vec2(845, mid + 80), Vec2(770, mid + 80), Vec2(770, mid - 120)),
            thrust=235.0,
            max_speed=102.0,
            drop_kind=PowerUpKind.THRUST_BOOST,
            can_shoot=True,
            fire_interval=3.55,
            fire_cooldown=1.1,
            shot_speed=232.0,
            aim_lead_factor=_SOLAR_AIM_LEAD,
            aim_spread_rad=_SOLAR_AIM_SPREAD,
        ),
        PatrolEnemy(
            waypoints=(Vec2(620, mid - 40), Vec2(700, mid + 20), Vec2(620, mid + 80), Vec2(540, mid + 20)),
            thrust=228.0,
            max_speed=98.0,
            drop_kind=PowerUpKind.THRUST_BOOST,
            can_shoot=True,
            fire_interval=3.8,
            fire_cooldown=2.0,
            shot_speed=224.0,
            aim_lead_factor=_SOLAR_AIM_LEAD,
            aim_spread_rad=_SOLAR_AIM_SPREAD,
        ),
    ]
