from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.ally_kinds import AllyKind
from gravity_ho_matey.gameplay.enemy_aim import lead_aim_direction
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.entities import Asteroid, GravityWell, Projectile
from gravity_ho_matey.gameplay.friendly_fighter_config import (
    ALLY_ASTEROID_AVOID_RADIUS,
    ALLY_ASTEROID_AVOID_THRUST,
    ALLY_ASTEROID_PANIC_GAP,
    ALLY_BOSS_ENGAGE_BONUS,
    ALLY_COMBAT_ENTER_RATIO,
    ALLY_ENGAGE_RANGE,
)
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at, hazard_escape_acceleration_at
from gravity_ho_matey.gameplay.mega_squid_boss import MegaSquidBoss

# Escort baseline — faster than prior pass, still below player top-end.
_DEFAULT_THRUST = 252.0
_DEFAULT_MAX_SPEED = 106.0
_CATCH_UP_SPEED = 128.0
_DEFAULT_TURN_RATE = 4.95
_DEFAULT_FIRE_INTERVAL = 4.4
_DEFAULT_SHOT_SPEED = 214.0
_SQUID_TARGET_BIAS = 48.0
_PLAYER_THREAT_BIAS = 36.0

ALLY_HIGHWAY_CRUISE_RATIO = 0.90
ALLY_HIGHWAY_CATCHUP_RATIO = 0.96
_DEFAULT_MIN_RANGE = 85.0
_DEFAULT_AIM_LEAD = 0.58
_DEFAULT_AIM_SPREAD = 0.068


@dataclass(frozen=True, slots=True)
class ThreatTarget:
    pos: Vec2
    vel: Vec2
    radius: float
    is_boss: bool = False
    is_asteroid: bool = False
    is_squid: bool = False
    danger_radius: float = 0.0


@dataclass(slots=True)
class FriendlyFighter:
    """Allied escort — follows the player and engages nearby hostiles."""

    wing_id: int
    pos: Vec2
    vel: Vec2 = field(default_factory=Vec2)
    angle: float = 0.0
    facing_angle: float = 0.0
    alive: bool = True
    radius: float = 10.0
    hits_remaining: int = 2
    hits_max: int = 2
    fire_cooldown: float = 0.0
    boost_flash: float = 0.0
    thrust: float = _DEFAULT_THRUST
    max_speed: float = _DEFAULT_MAX_SPEED
    catch_up_speed: float = _CATCH_UP_SPEED
    turn_rate: float = _DEFAULT_TURN_RATE
    fire_interval: float = _DEFAULT_FIRE_INTERVAL
    shot_speed: float = _DEFAULT_SHOT_SPEED
    engage_range: float = ALLY_ENGAGE_RANGE
    min_range: float = _DEFAULT_MIN_RANGE
    aim_lead_factor: float = _DEFAULT_AIM_LEAD
    aim_spread_rad: float = _DEFAULT_AIM_SPREAD
    formation_lateral: float = 88.0
    formation_trail: float = 58.0
    catch_up_radius: float = 400.0

    @property
    def kind(self) -> AllyKind:
        return AllyKind.FRIENDLY_FIGHTER

    def formation_offset(self, player_angle: float) -> Vec2:
        forward = Vec2.from_angle(player_angle)
        right = forward.rotated(math.pi / 2.0)
        lateral = self.formation_lateral if self.wing_id == 0 else -self.formation_lateral * 1.12
        trail = self.formation_trail + (18.0 if self.wing_id == 1 else 0.0)
        return right * lateral - forward * trail

    def formation_target(self, player_pos: Vec2, player_angle: float) -> Vec2:
        return player_pos + self.formation_offset(player_angle)

    def pick_threat(
        self,
        enemies: list,
        boss: MegaSquidBoss | None,
        *,
        player_pos: Vec2 | None = None,
        allow_boss: bool = True,
    ) -> ThreatTarget | None:
        anchor = player_pos if player_pos is not None else self.pos

        if allow_boss and boss is not None and boss.alive:
            boss_dist_player = (boss.pos - anchor).length() - boss.radius * 0.35
            boss_dist_ally = (boss.pos - self.pos).length() - boss.radius * 0.35
            if (
                boss_dist_ally <= self.engage_range + ALLY_BOSS_ENGAGE_BONUS
                or boss_dist_player <= self.engage_range + ALLY_BOSS_ENGAGE_BONUS * 0.85
            ):
                return ThreatTarget(
                    pos=Vec2(boss.pos.x, boss.pos.y),
                    vel=Vec2(boss.vel.x, boss.vel.y),
                    radius=boss.radius,
                    is_boss=True,
                )

        best: ThreatTarget | None = None
        best_score = self.engage_range + 1.0
        for enemy in enemies:
            if not enemy.alive:
                continue
            to_ally = (enemy.pos - self.pos).length()
            to_player = (enemy.pos - anchor).length()
            if to_ally > self.engage_range and to_player > self.engage_range:
                continue
            kind = getattr(enemy, "kind", None)
            bias = _SQUID_TARGET_BIAS if kind is EnemyKind.SQUID else 0.0
            if to_player <= self.engage_range * 0.72:
                bias += _PLAYER_THREAT_BIAS
            score = min(to_ally, to_player * 0.92) - bias
            if score >= best_score:
                continue
            vel = getattr(enemy, "vel", Vec2())
            is_squid = kind is EnemyKind.SQUID
            danger = getattr(enemy, "tentacle_span", lambda: enemy.radius)() if is_squid else enemy.radius
            best = ThreatTarget(
                pos=Vec2(enemy.pos.x, enemy.pos.y),
                vel=vel,
                radius=enemy.radius,
                is_squid=is_squid,
                danger_radius=danger,
            )
            best_score = score
        return best

    def integrate(
        self,
        dt: float,
        *,
        player_pos: Vec2,
        player_vel: Vec2,
        player_angle: float,
        wells: list[GravityWell],
        gravity_scale: float,
        drag: float,
        well_maw_radius: float,
        threat: ThreatTarget | None,
        asteroids: list[Asteroid] | None = None,
    ) -> None:
        if not self.alive:
            return

        avoid_accel, dodge_urgency = self._asteroid_avoidance(asteroids or ())

        form_target = self.formation_target(player_pos, player_angle)
        to_form = form_target - self.pos
        form_dist = to_form.length()
        form_dir = to_form.normalized() if form_dist > 1e-6 else Vec2.from_angle(player_angle)

        combat_range = self.engage_range * ALLY_COMBAT_ENTER_RATIO
        in_combat = threat is not None and (threat.pos - self.pos).length() <= combat_range

        if dodge_urgency > 0.16 and avoid_accel.length_sq() > 1.0:
            dodge_dir = avoid_accel.normalized()
            form_weight = max(0.08, 1.0 - dodge_urgency * 0.92)
            if in_combat:
                form_weight *= 0.42
            blend = min(0.94, 0.38 + dodge_urgency * 0.56)
            move_dir = (form_dir * (1.0 - blend) + dodge_dir * blend).normalized()
            to_move = move_dir * max(72.0, form_dist)
            desired_heading = math.atan2(move_dir.y, move_dir.x)
        elif in_combat:
            move_goal = form_target * 0.35 + threat.pos * 0.65  # type: ignore[union-attr]
            to_move = move_goal - self.pos
            desired_heading = math.atan2(to_move.y, to_move.x)
        else:
            desired_heading = math.atan2(to_form.y, to_form.x) if form_dist > 1e-6 else self.angle
            to_move = to_form

        heading_delta = _angle_delta(desired_heading - self.angle)
        max_turn = self.turn_rate * dt
        if heading_delta > max_turn:
            self.angle += max_turn
        elif heading_delta < -max_turn:
            self.angle -= max_turn
        else:
            self.angle = desired_heading
        if not in_combat or dodge_urgency < 0.38:
            self.facing_angle = self.angle
        elif threat is not None:
            to_target = threat.pos - self.pos
            if to_target.length_sq() > 64.0:
                self.facing_angle = math.atan2(to_target.y, to_target.x)

        accel = gravity_acceleration_at(self.pos, wells) * gravity_scale
        accel += hazard_escape_acceleration_at(
            self.pos,
            wells,
            gravity_scale=gravity_scale,
            default_maw_radius=well_maw_radius,
        )
        accel += avoid_accel

        cruise_cap = self.max_speed
        catch_cap = self.catch_up_speed

        speed_cap = catch_cap if form_dist > self.catch_up_radius else cruise_cap
        if dodge_urgency > 0.28:
            speed_cap = max(speed_cap, self.catch_up_speed * (0.92 + dodge_urgency * 0.18))

        catch_thrust = 1.26 if form_dist > self.catch_up_radius else 1.0
        if dodge_urgency > 0.18:
            catch_thrust = max(catch_thrust, 1.18 + dodge_urgency * 0.34)
        if to_move.length_sq() > 64.0:
            player_match = min(1.12, 0.35 + player_vel.length() / max(1.0, speed_cap))
            accel += Vec2.from_angle(self.angle) * (self.thrust * catch_thrust * player_match)

        self.vel = (self.vel + accel * dt) * drag
        self.vel = self.vel.clamped_length(speed_cap)
        self.pos = self.pos + self.vel * dt

    def _asteroid_avoidance(self, asteroids: list[Asteroid]) -> tuple[Vec2, float]:
        push = Vec2()
        urgency = 0.0
        for asteroid in asteroids:
            offset = self.pos - asteroid.pos
            dist = offset.length()
            if dist < 1e-6:
                continue
            combined = asteroid.approximate_radius() + self.radius
            gap = dist - combined
            if gap > ALLY_ASTEROID_AVOID_RADIUS:
                continue
            t = 1.0 - max(0.0, gap / ALLY_ASTEROID_AVOID_RADIUS)
            strength = t * t * (3.0 - 2.0 * t)
            closing = _closing_speed(self.pos, self.vel, asteroid.pos, asteroid.vel)
            if closing > 0.0:
                strength *= 1.0 + min(2.2, closing / 68.0)
            if gap < ALLY_ASTEROID_PANIC_GAP:
                strength = min(1.0, strength + 0.48)
            push += offset.normalized() * (ALLY_ASTEROID_AVOID_THRUST * strength)
            urgency = max(urgency, strength)
        return push, urgency

    def tick_combat(self, dt: float) -> None:
        if self.fire_cooldown > 0.0:
            self.fire_cooldown = max(0.0, self.fire_cooldown - dt)

    def try_fire(self, threat: ThreatTarget | None) -> Projectile | None:
        if not self.alive or self.fire_cooldown > 0.0 or threat is None:
            return None
        to_target = threat.pos - self.pos
        dist = to_target.length()
        if dist < self.min_range or dist > self.engage_range:
            return None

        aim_dir = lead_aim_direction(
            self.pos,
            threat.pos,
            threat.vel * self.aim_lead_factor,
            self.shot_speed,
            refine_passes=2,
        )
        if aim_dir is None:
            return None

        spread = (random.random() * 2.0 - 1.0) * self.aim_spread_rad
        aim_dir = aim_dir.rotated(spread)
        self.fire_cooldown = self.fire_interval
        self.facing_angle = math.atan2(aim_dir.y, aim_dir.x)
        muzzle = self.pos + aim_dir * (self.radius + 6.0)
        inherit = self.vel * 0.10 if self.vel.length_sq() > 1.0 else Vec2()
        return Projectile(
            pos=muzzle,
            vel=aim_dir * self.shot_speed + inherit,
            ttl=2.0,
            radius=3.5,
            hostile=False,
            from_ally=True,
        )

    def apply_shot(self) -> bool:
        self.hits_remaining = max(0, self.hits_remaining - 1)
        if self.hits_remaining <= 0:
            self.alive = False
            return True
        return False

    def body_hit_by_projectile(self, projectile_pos: Vec2, projectile_radius: float) -> bool:
        return (projectile_pos - self.pos).length() <= self.radius + projectile_radius


def _angle_delta(angle: float) -> float:
    while angle > math.pi:
        angle -= math.tau
    while angle < -math.pi:
        angle += math.tau
    return angle


def _closing_speed(
    pos_a: Vec2,
    vel_a: Vec2,
    pos_b: Vec2,
    vel_b: Vec2,
) -> float:
    offset = pos_b - pos_a
    dist = offset.length()
    if dist < 1e-6:
        return 0.0
    rel_vel = vel_b - vel_a
    return max(0.0, rel_vel.dot(offset.normalized()))
