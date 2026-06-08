from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemy_aim import lead_aim_direction
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.entities import GravityWell, Projectile
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at, hazard_escape_acceleration_at

HOSTILE_FIGHTER_SHOT_SPEED = 232.0
HOSTILE_FIGHTER_AIM_LEAD = 0.62
HOSTILE_FIGHTER_AIM_SPREAD = 0.048


@dataclass(slots=True)
class HostileFighter:
    """Corsair strike craft — converges on relay and engages player or station."""

    pos: Vec2
    vel: Vec2 = field(default_factory=Vec2)
    facing_angle: float = 0.0
    alive: bool = True
    radius: float = 11.0
    thrust: float = 278.0
    max_speed: float = 125.0
    can_shoot: bool = True
    fire_cooldown: float = 0.0
    fire_interval: float = 1.9
    shot_speed: float = HOSTILE_FIGHTER_SHOT_SPEED
    engage_range: float = 540.0
    min_range: float = 68.0
    aim_lead_factor: float = HOSTILE_FIGHTER_AIM_LEAD
    aim_spread_rad: float = HOSTILE_FIGHTER_AIM_SPREAD

    @property
    def kind(self) -> EnemyKind:
        return EnemyKind.HOSTILE_FIGHTER

    def integrate(
        self,
        dt: float,
        wells: list[GravityWell],
        *,
        gravity_scale: float,
        drag: float,
        well_maw_radius: float,
        homeward_target: Vec2 | None,
        homeward_thrust: float,
        pursue_target: Vec2 | None,
        pursue_thrust: float,
    ) -> None:
        if not self.alive:
            return

        accel = gravity_acceleration_at(self.pos, wells) * gravity_scale
        accel += hazard_escape_acceleration_at(
            self.pos,
            wells,
            gravity_scale=gravity_scale,
            default_maw_radius=well_maw_radius,
        )

        if homeward_target is not None and homeward_thrust > 0.0:
            to_home = homeward_target - self.pos
            home_dist = to_home.length()
            if home_dist > 1e-6:
                home_scale = min(1.0, max(0.35, (home_dist - 80.0) / 720.0))
                accel += (to_home / home_dist) * homeward_thrust * home_scale * 0.55

        if pursue_target is not None and pursue_thrust > 0.0:
            to_prey = pursue_target - self.pos
            prey_dist = to_prey.length()
            if prey_dist > 1e-6:
                prey_scale = min(1.0, max(0.45, prey_dist / 620.0))
                accel += (to_prey / prey_dist) * pursue_thrust * prey_scale

        self.vel = (self.vel + accel * dt) * drag
        self.vel = self.vel.clamped_length(self.max_speed)
        self.pos = self.pos + self.vel * dt

        if self.vel.length_sq() > 1e-9:
            self.facing_angle = math.atan2(self.vel.y, self.vel.x)

    def tick_combat(self, dt: float) -> None:
        if self.fire_cooldown > 0.0:
            self.fire_cooldown = max(0.0, self.fire_cooldown - dt)

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
        muzzle = self.pos + aim_dir * (self.radius + 6.0)
        inherit = self.vel * 0.14 if self.vel.length_sq() > 1.0 else Vec2()
        return Projectile(
            pos=muzzle,
            vel=aim_dir * self.shot_speed + inherit,
            ttl=2.2,
            radius=3.5,
            hostile=True,
        )

    def pick_pursue_target(self, threats: list[tuple[Vec2, Vec2]]) -> Vec2 | None:
        """Nearest threat within engage range — player, allies, or relay."""
        best: Vec2 | None = None
        best_dist = self.engage_range + 1.0
        for pos, _vel in threats:
            dist = (pos - self.pos).length()
            if dist > self.engage_range or dist >= best_dist:
                continue
            best = pos
            best_dist = dist
        return best
