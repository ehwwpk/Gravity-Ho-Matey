from __future__ import annotations

from enum import Enum, auto


class PowerUpKind(Enum):
    THRUST_BOOST = auto()
    RAPID_FIRE = auto()
    BOOST_TAP = auto()
    RUBBER_HULL = auto()
    DRONE_WINGMAN = auto()


POWERUP_LABELS: dict[PowerUpKind, str] = {
    PowerUpKind.THRUST_BOOST: "Plunder Thrusters — +6% acceleration per tier",
    PowerUpKind.RAPID_FIRE: "Gatling Rigging — faster bolt cycle",
    PowerUpKind.BOOST_TAP: "Shift Boost Coil — +8% shift-burst per tier",
    PowerUpKind.RUBBER_HULL: "Rubber Hull — 10 asteroid bounces, no chip damage",
    PowerUpKind.DRONE_WINGMAN: "Guardian Drone — escorts next sector, 5 HP, overheats",
}

POWERUP_HUD_TAGS: dict[PowerUpKind, str] = {
    PowerUpKind.THRUST_BOOST: "THRUST",
    PowerUpKind.RAPID_FIRE: "GATLING",
    PowerUpKind.BOOST_TAP: "SHIFT",
    PowerUpKind.RUBBER_HULL: "RUBBER",
    PowerUpKind.DRONE_WINGMAN: "DRONE",
}
