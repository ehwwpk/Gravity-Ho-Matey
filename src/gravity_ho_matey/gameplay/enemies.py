from __future__ import annotations

import math
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind


@dataclass(slots=True)
class PatrolEnemy:
    waypoints: tuple[Vec2, ...]
    speed: float = 88.0
    radius: float = 14.0
    drop_kind: PowerUpKind = PowerUpKind.THRUST_BOOST
    pos: Vec2 = field(default_factory=Vec2)
    waypoint_index: int = 0
    facing_angle: float = 0.0
    alive: bool = True

    def __post_init__(self) -> None:
        if not self.waypoints:
            return
        self.pos = Vec2(self.waypoints[0].x, self.waypoints[0].y)
        if len(self.waypoints) > 1:
            self.waypoint_index = 1

    def advance(self, dt: float, arrive_radius: float = 10.0) -> None:
        if not self.alive or not self.waypoints:
            return
        target = self.waypoints[self.waypoint_index]
        delta = target - self.pos
        distance = delta.length()
        if distance <= arrive_radius:
            self.waypoint_index = (self.waypoint_index + 1) % len(self.waypoints)
            return
        step = min(distance, self.speed * dt)
        move = delta.normalized() * step
        self.pos = self.pos + move
        if move.length_sq() > 1e-9:
            self.facing_angle = math.atan2(move.y, move.x)
