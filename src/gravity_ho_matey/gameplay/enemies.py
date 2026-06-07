from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemy_aim import lead_aim_direction
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.entities import GravityWell, Projectile
from gravity_ho_matey.gameplay.friendly_fighter_config import PATROL_ENGAGE_RANGE
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at, hazard_escape_acceleration_at

# Armed patrol baseline — 10% slower bolts, 10% wider aim spread, 10% less velocity lead.
PATROL_SHOT_SPEED = 228.0 * 0.90
PATROL_AIM_LEAD_FACTOR = 0.68 * 0.90
PATROL_AIM_SPREAD_RAD = 0.055 * 1.10


@dataclass(slots=True)
class PatrolEnemy:
    waypoints: tuple[Vec2, ...]
    thrust: float = 235.0
    max_speed: float = 105.0
    radius: float = 14.0
    pos: Vec2 = field(default_factory=Vec2)
    vel: Vec2 = field(default_factory=Vec2)
    waypoint_index: int = 0
    facing_angle: float = 0.0
    alive: bool = True
    can_shoot: bool = False
    fire_cooldown: float = 0.0
    fire_interval: float = 2.85
    shot_speed: float = PATROL_SHOT_SPEED
    engage_range: float = PATROL_ENGAGE_RANGE
    min_range: float = 70.0
    aim_lead_factor: float = PATROL_AIM_LEAD_FACTOR
    aim_spread_rad: float = PATROL_AIM_SPREAD_RAD
    skirmish_roster_id: int | None = None

    @property
    def kind(self) -> EnemyKind:
        return EnemyKind.PATROL

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
        well_maw_radius: float = 10.0,
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
        accel += hazard_escape_acceleration_at(
            self.pos,
            wells,
            gravity_scale=gravity_scale,
            default_maw_radius=well_maw_radius,
        )
        if to_target.length_sq() > 1e-9:
            accel += to_target.normalized() * self.thrust

        self.vel = (self.vel + accel * dt) * drag
        self.vel = self.vel.clamped_length(self.max_speed)
        self.pos = self.pos + self.vel * dt

        if self.vel.length_sq() > 1e-9:
            self.facing_angle = math.atan2(self.vel.y, self.vel.x)

    def tick_combat(self, dt: float) -> None:
        if self.fire_cooldown > 0.0:
            self.fire_cooldown = max(0.0, self.fire_cooldown - dt)

    def try_fire(self, ship_pos: Vec2, ship_vel: Vec2) -> Projectile | None:
        return self.try_fire_at_threats([(ship_pos, ship_vel)])

    def try_fire_at_threats(self, threats: list[tuple[Vec2, Vec2]]) -> Projectile | None:
        if not self.can_shoot or not self.alive or self.fire_cooldown > 0.0 or not threats:
            return None

        best_pos: Vec2 | None = None
        best_vel = Vec2()
        best_dist = self.engage_range + 1.0
        for pos, vel in threats:
            dist = (pos - self.pos).length()
            if dist < self.min_range or dist > self.engage_range:
                continue
            if dist < best_dist:
                best_pos = pos
                best_vel = vel
                best_dist = dist
        if best_pos is None:
            return None

        aim_dir = lead_aim_direction(
            self.pos,
            best_pos,
            best_vel * self.aim_lead_factor,
            self.shot_speed,
            refine_passes=1,
        )
        if aim_dir is None:
            return None

        spread = (random.random() * 2.0 - 1.0) * self.aim_spread_rad
        aim_dir = aim_dir.rotated(spread)

        self.fire_cooldown = self.fire_interval
        self.facing_angle = math.atan2(aim_dir.y, aim_dir.x)
        muzzle = self.pos + aim_dir * (self.radius + 7.0)
        inherit = self.vel * 0.12 if self.vel.length_sq() > 1.0 else Vec2()
        return Projectile(
            pos=muzzle,
            vel=aim_dir * self.shot_speed + inherit,
            ttl=2.1,
            radius=3.5,
            hostile=True,
        )
