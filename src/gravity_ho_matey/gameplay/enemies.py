from __future__ import annotations

import math
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GravityWell
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind


@dataclass(slots=True)
class PatrolEnemy:
    waypoints: tuple[Vec2, ...]
    thrust: float = 235.0
    max_speed: float = 105.0
    radius: float = 14.0
    drop_kind: PowerUpKind = PowerUpKind.THRUST_BOOST
    pos: Vec2 = field(default_factory=Vec2)
    vel: Vec2 = field(default_factory=Vec2)
    waypoint_index: int = 0
    facing_angle: float = 0.0
    alive: bool = True

    def __post_init__(self) -> None:
        if not self.waypoints:
            return
        self.pos = Vec2(self.waypoints[0].x, self.waypoints[0].y)
        if len(self.waypoints) > 1:
            self.waypoint_index = 1

    def integrate(
        self,
        dt: float,
        wells: list[GravityWell],
        *,
        gravity_scale: float,
        drag: float,
        arrive_radius: float = 22.0,
    ) -> None:
        if not self.alive or not self.waypoints:
            return

        target = self.waypoints[self.waypoint_index]
        to_target = target - self.pos
        if to_target.length() <= arrive_radius:
            self.waypoint_index = (self.waypoint_index + 1) % len(self.waypoints)
            target = self.waypoints[self.waypoint_index]
            to_target = target - self.pos

        accel = gravity_acceleration_at(self.pos, wells) * gravity_scale
        if to_target.length_sq() > 1e-9:
            accel += to_target.normalized() * self.thrust

        self.vel = (self.vel + accel * dt) * drag
        self.vel = self.vel.clamped_length(self.max_speed)
        self.pos = self.pos + self.vel * dt

        if self.vel.length_sq() > 1e-9:
            self.facing_angle = math.atan2(self.vel.y, self.vel.x)
