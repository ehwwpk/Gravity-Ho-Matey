from __future__ import annotations

from gravity_ho_matey.gameplay.entities import Ship
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.powerup_stacks import PowerUpStacks
from gravity_ho_matey.gameplay.upgrade_config import (
    ACCEL_BONUS_PER_STACK,
    BOOST_TAP_BONUS_PER_STACK,
    RAPID_FIRE_COOLDOWN_MULT,
)


def apply_powerups_to_ship(ship: Ship, stacks: PowerUpStacks) -> None:
    ship.thrust_multiplier = 1.0
    ship.fire_cooldown_multiplier = 1.0
    ship.turn_rate_multiplier = 1.0
    ship.boost_tap_multiplier = 1.0

    thrust = stacks.get(PowerUpKind.THRUST_BOOST, 0)
    if thrust:
        ship.thrust_multiplier *= 1.0 + ACCEL_BONUS_PER_STACK * thrust

    boost_tap = stacks.get(PowerUpKind.BOOST_TAP, 0)
    if boost_tap:
        ship.boost_tap_multiplier *= 1.0 + BOOST_TAP_BONUS_PER_STACK * boost_tap

    rapid = stacks.get(PowerUpKind.RAPID_FIRE, 0)
    if rapid:
        ship.fire_cooldown_multiplier *= RAPID_FIRE_COOLDOWN_MULT
