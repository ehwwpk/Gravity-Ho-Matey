from __future__ import annotations

import math
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.entities import GravityWell, Projectile
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at, hazard_escape_acceleration_at

SQUID_HITS_MAX = 3
SQUID_TENTACLE_COUNT = 8
SQUID_CLING_DAMAGE_INTERVAL = 2.0


@dataclass(slots=True)
class SquidEnemy:
    """Void kraken — tentacles latch the hull; 1 chunk / 2s while clinging, 3 body shots to kill."""

    pos: Vec2
    orbit_sign: float = 1.0
    radius: float = 18.0
    tentacle_reach: float = 88.0
    vel: Vec2 = field(default_factory=Vec2)
    facing_angle: float = 0.0
    alive: bool = True
    hits_max: int = SQUID_HITS_MAX
    hits_remaining: int = SQUID_HITS_MAX
    approach_thrust: float = 480.0
    max_speed: float = 208.0
    detect_range: float = 1380.0
    engage_range: float = 1200.0
    orbit_radius: float = 62.0
    orbit_speed: float = 168.0
    wrap_spring: float = 4.6
    cling_damage_interval: float = SQUID_CLING_DAMAGE_INTERVAL
    clinging: bool = False
    tentacle_wobble: float = 0.0
    tip_pos: list[Vec2] = field(default_factory=list)
    tip_vel: list[Vec2] = field(default_factory=list)
    tentacle_mid: list[Vec2] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._ensure_tentacles()

    @property
    def kind(self) -> EnemyKind:
        return EnemyKind.SQUID

    def tick_combat(self, dt: float) -> None:
        _ = dt

    def any_tentacle_on_hull(self, ship_pos: Vec2, ship_radius: float) -> bool:
        touch = ship_radius + 10.0
        touch_sq = touch * touch
        for tip in self.tip_pos:
            if (tip - ship_pos).length_sq() <= touch_sq:
                return True
        return False

    def is_clinging(self, ship_pos: Vec2, ship_radius: float) -> bool:
        """Latched only when tentacle tips reach the hull."""
        if not self.coils_ship(ship_pos, ship_radius):
            return False
        return self.any_tentacle_on_hull(ship_pos, ship_radius)

    def try_fire(self, ship_pos: Vec2, ship_vel: Vec2) -> Projectile | None:
        _ = ship_pos, ship_vel
        return None

    def tentacle_span(self) -> float:
        return self.radius + self.tentacle_reach

    def _ensure_tentacles(self) -> None:
        while len(self.tip_pos) < SQUID_TENTACLE_COUNT:
            i = len(self.tip_pos)
            angle = self.facing_angle + math.tau * i / SQUID_TENTACLE_COUNT
            self.tip_pos.append(self.pos + Vec2.from_angle(angle) * self.tentacle_reach * 0.72)
            self.tip_vel.append(Vec2())
        while len(self.tentacle_mid) < SQUID_TENTACLE_COUNT:
            i = len(self.tentacle_mid)
            tip = self.tip_pos[i]
            self.tentacle_mid.append(self.pos + (tip - self.pos) * 0.5)

    def tentacle_tips(self) -> tuple[Vec2, ...]:
        return tuple(self.tip_pos)

    def coils_ship(self, ship_pos: Vec2, ship_radius: float) -> bool:
        return (ship_pos - self.pos).length() <= self.tentacle_span() + ship_radius + 8.0

    def body_hit_by_projectile(self, projectile_pos: Vec2, projectile_radius: float) -> bool:
        return (projectile_pos - self.pos).length() <= self.radius + projectile_radius

    def apply_shot(self) -> bool:
        self.hits_remaining = max(0, self.hits_remaining - 1)
        return self.hits_remaining <= 0

    def update_tentacles(self, dt: float, ship_pos: Vec2, ship_radius: float) -> None:
        self._ensure_tentacles()
        self.tentacle_wobble += dt * (7.5 if self.coils_ship(ship_pos, ship_radius) else 4.8)
        coiling = self.coils_ship(ship_pos, ship_radius)
        clinging = self.is_clinging(ship_pos, ship_radius)
        for i in range(SQUID_TENTACLE_COUNT):
            spread = self.facing_angle + math.tau * i / SQUID_TENTACLE_COUNT
            if clinging or coiling:
                lash = math.sin(self.tentacle_wobble * 8.0 + i * 1.05) * 4.0
                target = ship_pos + Vec2.from_angle(spread + lash * 0.012) * (ship_radius + 5.0)
                spring = 68.0
                drag = 0.76
                max_len = self.tentacle_reach * 1.05
            else:
                wave_a = math.sin(self.tentacle_wobble * 5.5 + i * 0.85) * 18.0
                wave_b = math.cos(self.tentacle_wobble * 4.0 + i * 1.1) * 12.0
                dir_v = Vec2.from_angle(spread + math.sin(self.tentacle_wobble * 3.2 + i) * 0.08)
                target = self.pos + dir_v * self.tentacle_reach + Vec2(wave_a, wave_b)
                spring = 28.0
                drag = 0.86
                max_len = self.tentacle_reach * 1.24

            tip = self.tip_pos[i]
            vel = self.tip_vel[i]
            vel = vel + (target - tip) * spring * dt
            vel = vel * drag
            tip = tip + vel * dt
            offset = tip - self.pos
            dist = offset.length()
            if dist > max_len and dist > 1e-6:
                tip = self.pos + offset * (max_len / dist)
                vel = vel * 0.42
            self.tip_pos[i] = tip
            self.tip_vel[i] = vel

            perp = offset.rotated(math.pi / 2.0).normalized() if dist > 1e-6 else Vec2.from_angle(spread + math.pi / 2.0)
            mid_sway = math.sin(self.tentacle_wobble * 6.0 + i * 0.95) * (5.0 if coiling else 11.0)
            mid_target = self.pos + offset * 0.52 + perp * mid_sway
            mid = self.tentacle_mid[i]
            mid = mid + (mid_target - mid) * min(1.0, dt * 24.0)
            self.tentacle_mid[i] = mid

    def integrate(
        self,
        dt: float,
        prey_pos: Vec2,
        prey_vel: Vec2,
        wells: list[GravityWell],
        *,
        gravity_scale: float,
        drag: float,
        well_maw_radius: float = 10.0,
        prey_radius: float = 12.0,
        homeward_target: Vec2 | None = None,
        homeward_thrust: float = 0.0,
    ) -> None:
        if not self.alive:
            return

        to_prey = prey_pos - self.pos
        dist = to_prey.length()
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
                home_scale = min(1.0, max(0.4, (home_dist - 100.0) / 820.0))
                accel += (to_home / home_dist) * homeward_thrust * home_scale

        if dist > 1e-6:
            radial = to_prey / dist
            tangent = radial.rotated(math.pi / 2.0 * self.orbit_sign)
        else:
            radial = Vec2(1.0, 0.0)
            tangent = Vec2(0.0, 1.0)

        self.update_tentacles(dt, prey_pos, prey_radius)
        self.clinging = self.is_clinging(prey_pos, prey_radius)

        surface_gap = dist - self.orbit_radius

        if self.clinging:
            latch_dist = prey_radius + self.radius * 0.52
            desired = prey_pos - radial * latch_dist
            latch_blend = min(1.0, dt * 12.0)
            self.pos = Vec2(
                self.pos.x + (desired.x - self.pos.x) * latch_blend,
                self.pos.y + (desired.y - self.pos.y) * latch_blend,
            )
            self.vel = prey_vel * 0.96 + tangent * (34.0 * self.orbit_sign)
            self.facing_angle = math.atan2(radial.y, radial.x)
            return

        if dist > self.engage_range:
            if dist <= self.detect_range:
                accel += radial * (self.approach_thrust * 0.24)
            else:
                drift = Vec2(math.cos(self.facing_angle), math.sin(self.facing_angle)) * 34.0
                accel += drift * 0.28
        elif dist > self.orbit_radius + 28.0:
            accel += radial * (self.approach_thrust * (1.2 if dist > self.engage_range * 0.5 else 1.0))
        else:
            target_orbit = tangent * self.orbit_speed + prey_vel * 0.42
            radial_fix = radial * surface_gap * self.wrap_spring
            blend = min(1.0, dt * 7.0)
            self.vel = self.vel + (target_orbit + radial_fix - self.vel) * blend
            self.vel = self.vel + accel * dt
            self.vel = self.vel * drag
            self.vel = self.vel.clamped_length(self.max_speed)
            self.pos = self.pos + self.vel * dt
            self.facing_angle = math.atan2(radial.y, radial.x)
            return

        self.vel = (self.vel + accel * dt) * drag
        self.vel = self.vel.clamped_length(self.max_speed)
        self.pos = self.pos + self.vel * dt
        if self.vel.length_sq() > 1e-9:
            self.facing_angle = math.atan2(self.vel.y, self.vel.x)

    @staticmethod
    def cling_interval() -> float:
        return SQUID_CLING_DAMAGE_INTERVAL
