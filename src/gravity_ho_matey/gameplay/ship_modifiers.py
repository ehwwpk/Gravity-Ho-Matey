from __future__ import annotations

from gravity_ho_matey.gameplay.entities import Ship
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind


def apply_powerups_to_ship(ship: Ship, kinds: set[PowerUpKind]) -> None:
    ship.thrust_multiplier = 1.0
    ship.fire_cooldown_multiplier = 1.0
    ship.turn_rate_multiplier = 1.0
    for kind in kinds:
        if kind is PowerUpKind.THRUST_BOOST:
            ship.thrust_multiplier *= 1.28
        elif kind is PowerUpKind.RAPID_FIRE:
            ship.fire_cooldown_multiplier *= 0.55
        elif kind is PowerUpKind.STABILIZER:
            ship.turn_rate_multiplier *= 1.35
