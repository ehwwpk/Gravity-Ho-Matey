from __future__ import annotations

from enum import Enum, auto


class PowerUpKind(Enum):
    THRUST_BOOST = auto()
    RAPID_FIRE = auto()
    STABILIZER = auto()


POWERUP_LABELS: dict[PowerUpKind, str] = {
    PowerUpKind.THRUST_BOOST: "Plunder Thrusters",
    PowerUpKind.RAPID_FIRE: "Gatling Rigging",
    PowerUpKind.STABILIZER: "Steady Helm",
}
