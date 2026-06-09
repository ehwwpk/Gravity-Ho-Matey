from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from gravity_ho_matey.core.vector import Vec2


class SquidBehaviorMode(Enum):
    HUNT = auto()
    FEEDING = auto()
    ALERT = auto()
    ENGAGE = auto()


@dataclass(frozen=True, slots=True)
class SquidFeedPoint:
    id: str
    pos: Vec2
    line_id: str
    feed_target: Vec2
    facing_angle: float = 0.0
    feed_radius: float = 28.0


@dataclass(frozen=True, slots=True)
class FuelFeedLine:
    id: str
    start: Vec2
    end: Vec2
    burst_width: float = 18.0
    flow_rate: float = 1.0
    alive: bool = True
