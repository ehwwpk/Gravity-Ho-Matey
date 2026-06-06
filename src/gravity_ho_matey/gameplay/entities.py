from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind


class GameStatus(Enum):
    RUNNING = auto()
    WON = auto()
    LOST = auto()


@dataclass(slots=True)
class Ship:
    pos: Vec2
    vel: Vec2 = field(default_factory=Vec2)
    angle: float = 0.0
    radius: float = 12.0
    cooldown: float = 0.0
    boost_energy: float = 1.0
    thrust_multiplier: float = 1.0
    fire_cooldown_multiplier: float = 1.0
    turn_rate_multiplier: float = 1.0


@dataclass(slots=True)
class Projectile:
    pos: Vec2
    vel: Vec2
    ttl: float = 2.3
    radius: float = 4.0


@dataclass(slots=True)
class PowerUpPickup:
    pos: Vec2
    kind: PowerUpKind
    radius: float = 11.0


@dataclass(frozen=True, slots=True)
class GravityWell:
    pos: Vec2
    strength: float
    radius: float
    label: str = ""
    kind: str = "well"
    maw_radius: float | None = None


@dataclass(frozen=True, slots=True)
class Wall:
    rect: Rect


@dataclass(slots=True)
class Beacon:
    pos: Vec2
    radius: float = 9.0
    collected: bool = False


@dataclass(frozen=True, slots=True)
class FinishGate:
    rect: Rect


@dataclass(frozen=True, slots=True)
class WorldConfig:
    width: int
    height: int
    gravity_scale: float = 0.5
    turn_rate: float = 5.0
    thrust: float = 250.0
    boost_multiplier: float = 1.85
    drag: float = 0.988
    max_ship_speed: float = 330.0
    projectile_speed: float = 315.0
    ship_fire_cooldown: float = 0.18
    well_maw_radius: float = 10.0
    level_theme: str = "cove"
    level_name: str = "Level"
