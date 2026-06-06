from __future__ import annotations

from gravity_ho_matey.gameplay.entities import Ship
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.powerup_stacks import PowerUpStacks

_THRUST_PER_STACK = 1.28
_RAPID_FIRE_PER_STACK = 0.55
_STABILIZER_PER_STACK = 1.35


def apply_powerups_to_ship(ship: Ship, stacks: PowerUpStacks) -> None:
    ship.thrust_multiplier = 1.0
    ship.fire_cooldown_multiplier = 1.0
    ship.turn_rate_multiplier = 1.0

    thrust = stacks.get(PowerUpKind.THRUST_BOOST, 0)
    if thrust:
        ship.thrust_multiplier *= _THRUST_PER_STACK**thrust

    rapid = stacks.get(PowerUpKind.RAPID_FIRE, 0)
    if rapid:
        ship.fire_cooldown_multiplier *= _RAPID_FIRE_PER_STACK**rapid

    stabilizer = stacks.get(PowerUpKind.STABILIZER, 0)
    if stabilizer:
        ship.turn_rate_multiplier *= _STABILIZER_PER_STACK**stabilizer
