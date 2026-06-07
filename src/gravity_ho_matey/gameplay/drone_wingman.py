from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.drone_config import (
    DRONE_ASTEROID_AVOID_RADIUS,
    DRONE_ASTEROID_AVOID_THRUST,
    DRONE_ASTEROID_ENGAGE_RANGE,
    DRONE_ASTEROID_MIN_FIRE_RANGE,
    DRONE_ASTEROID_PANIC_GAP,
    DRONE_ASTEROID_PLAYER_GUARD_RANGE,
    DRONE_CATCH_UP_RADIUS,
    DRONE_CATCH_UP_SPEED,
    DRONE_ENGAGE_RANGE,
    DRONE_FIRE_INTERVAL,
    DRONE_FORMATION_LATERAL,
    DRONE_FORMATION_TRAIL,
    DRONE_HEAT_DECAY,
    DRONE_HEAT_PER_SHOT,
    DRONE_HITS_MAX,
    DRONE_MAX_SPEED,
    DRONE_MIN_RANGE,
    DRONE_OVERHEAT_COOLDOWN,
    DRONE_THRUST,
    DRONE_TURN_RATE,
)
from gravity_ho_matey.gameplay.enemy_aim import lead_aim_direction
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.entities import Asteroid, GravityWell, Projectile
from gravity_ho_matey.gameplay.friendly_fighter import ThreatTarget, _angle_delta
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at, hazard_escape_acceleration_at
from gravity_ho_matey.gameplay.mega_squid_boss import MegaSquidBoss

_ASTEROID_SELF_BIAS = 140.0
_ASTEROID_PLAYER_BIAS = 48.0
_ASTEROID_IMMINENT_BIAS = 95.0


@dataclass(slots=True)
class DroneWingman:
    """Advanced escort drone — hugs the player's six, rapid fire with overheat."""

    pos: Vec2
    vel: Vec2 = field(default_factory=Vec2)
    angle: float = 0.0
    facing_angle: float = 0.0
    alive: bool = True
    radius: float = 9.0
    hits_remaining: int = DRONE_HITS_MAX
    hits_max: int = DRONE_HITS_MAX
    fire_cooldown: float = 0.0
    heat: float = 0.0
    overheat_timer: float = 0.0
    shot_speed: float = 248.0
    engage_range: float = DRONE_ENGAGE_RANGE

    @classmethod
    def spawn_behind_player(cls, ship: object, *, hits_remaining: int | None = None) -> DroneWingman:
        angle = getattr(ship, "angle", 0.0)
        pos = getattr(ship, "pos", Vec2())
        forward = Vec2.from_angle(angle)
        right = forward.rotated(math.pi / 2.0)
        spawn = pos - forward * (DRONE_FORMATION_TRAIL + 8.0) + right * DRONE_FORMATION_LATERAL
        hp = DRONE_HITS_MAX if hits_remaining is None else max(0, min(DRONE_HITS_MAX, hits_remaining))
        return cls(
            pos=Vec2(spawn.x, spawn.y),
            angle=angle,
            facing_angle=angle,
            hits_remaining=hp,
            hits_max=DRONE_HITS_MAX,
            alive=hp > 0,
        )

    def formation_target(self, player_pos: Vec2, player_angle: float) -> Vec2:
        forward = Vec2.from_angle(player_angle)
        right = forward.rotated(math.pi / 2.0)
        return player_pos - forward * DRONE_FORMATION_TRAIL + right * DRONE_FORMATION_LATERAL

    def pick_threat(
        self,
        enemies: list,
        boss: MegaSquidBoss | None,
        *,
        player_pos: Vec2,
        asteroids: list[Asteroid] | None = None,
    ) -> ThreatTarget | None:
        """Prioritize imminent rocks, then hostiles threatening the player."""
        best: ThreatTarget | None = None
        best_score = self.engage_range + 1.0

        if asteroids:
            for asteroid in asteroids:
                threat = self._score_asteroid_threat(asteroid, player_pos=player_pos)
                if threat is None:
                    continue
                _, score, target = threat
                if score < best_score:
                    best = target
                    best_score = score

        if boss is not None and boss.alive:
            player_dist = (boss.pos - player_pos).length() - boss.radius * 0.35
            if player_dist <= self.engage_range + 120.0:
                score = player_dist * 0.68 - 80.0
                if score < best_score:
                    best = ThreatTarget(
                        pos=Vec2(boss.pos.x, boss.pos.y),
                        vel=Vec2(boss.vel.x, boss.vel.y),
                        radius=boss.radius,
                        is_boss=True,
                    )
                    best_score = score

        for enemy in enemies:
            if not enemy.alive:
                continue
            to_player = (enemy.pos - player_pos).length()
            to_drone = (enemy.pos - self.pos).length()
            if to_player > self.engage_range and to_drone > self.engage_range:
                continue
            kind = getattr(enemy, "kind", None)
            bias = 36.0 if kind is EnemyKind.SQUID else 0.0
            score = to_player * 0.72 + to_drone * 0.28 - bias
            if score >= best_score:
                continue
            vel = getattr(enemy, "vel", Vec2())
            best = ThreatTarget(pos=Vec2(enemy.pos.x, enemy.pos.y), vel=vel, radius=enemy.radius)
            best_score = score
        return best

    def _score_asteroid_threat(
        self,
        asteroid: Asteroid,
        *,
        player_pos: Vec2,
    ) -> tuple[float, float, ThreatTarget] | None:
        rock_r = asteroid.approximate_radius()
        to_drone = asteroid.pos - self.pos
        to_player = asteroid.pos - player_pos
        gap_drone = to_drone.length() - rock_r - self.radius
        gap_player = to_player.length() - rock_r - 12.0
        if gap_drone > DRONE_ASTEROID_ENGAGE_RANGE and gap_player > DRONE_ASTEROID_PLAYER_GUARD_RANGE:
            return None

        closing_drone = _closing_speed(self.pos, self.vel, asteroid.pos, asteroid.vel)
        score = gap_drone * 0.58 + gap_player * 0.42
        if gap_drone < DRONE_ASTEROID_PANIC_GAP:
            score -= _ASTEROID_IMMINENT_BIAS
        elif gap_drone < DRONE_ASTEROID_AVOID_RADIUS * 0.55:
            score -= _ASTEROID_SELF_BIAS * 0.72
        if gap_drone < DRONE_ASTEROID_ENGAGE_RANGE * 0.45:
            score -= _ASTEROID_SELF_BIAS
        if gap_player < DRONE_ASTEROID_PLAYER_GUARD_RANGE * 0.55:
            score -= _ASTEROID_PLAYER_BIAS
        if closing_drone > 40.0 and gap_drone < DRONE_ASTEROID_AVOID_RADIUS:
            score -= min(60.0, closing_drone * 0.45)

        target = ThreatTarget(
            pos=Vec2(asteroid.pos.x, asteroid.pos.y),
            vel=Vec2(asteroid.vel.x, asteroid.vel.y),
            radius=rock_r,
            is_asteroid=True,
        )
        return gap_drone, score, target

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

        form_weight = max(0.22, 1.0 - dodge_urgency * 0.82)
        if threat is not None and threat.is_asteroid and dodge_urgency > 0.35:
            form_weight *= 0.45

        if threat is not None and not threat.is_asteroid:
            threat_dist = (threat.pos - self.pos).length()
            if threat_dist <= self.engage_range * 0.95:
                cover = player_pos - Vec2.from_angle(player_angle) * 28.0
                move_goal = (
                    form_target * (0.55 * form_weight)
                    + cover * 0.25
                    + threat.pos * 0.20
                )
                to_move = move_goal - self.pos
                desired_heading = math.atan2(to_move.y, to_move.x) if to_move.length_sq() > 1.0 else self.angle
            else:
                desired_heading = math.atan2(to_form.y, to_form.x) if form_dist > 1e-6 else self.angle
                to_move = to_form
        elif dodge_urgency > 0.12 and avoid_accel.length_sq() > 1.0:
            dodge_dir = avoid_accel.normalized()
            blend = min(0.92, 0.35 + dodge_urgency * 0.65)
            form_dir = to_form.normalized() if form_dist > 1e-6 else dodge_dir
            move_dir = form_dir * (1.0 - blend) + dodge_dir * blend
            to_move = move_dir * max(48.0, form_dist)
            desired_heading = math.atan2(move_dir.y, move_dir.x)
        else:
            desired_heading = math.atan2(to_form.y, to_form.x) if form_dist > 1e-6 else player_angle
            to_move = to_form

        heading_delta = _angle_delta(desired_heading - self.angle)
        max_turn = DRONE_TURN_RATE * dt
        if heading_delta > max_turn:
            self.angle += max_turn
        elif heading_delta < -max_turn:
            self.angle -= max_turn
        else:
            self.angle = desired_heading
        if threat is None or dodge_urgency < 0.55:
            self.facing_angle = self.angle

        accel = gravity_acceleration_at(self.pos, wells) * gravity_scale
        accel += hazard_escape_acceleration_at(
            self.pos,
            wells,
            gravity_scale=gravity_scale,
            default_maw_radius=well_maw_radius,
        )
        accel += avoid_accel

        speed_cap = DRONE_CATCH_UP_SPEED if form_dist > DRONE_CATCH_UP_RADIUS else DRONE_MAX_SPEED
        if dodge_urgency > 0.45:
            speed_cap = max(speed_cap, DRONE_CATCH_UP_SPEED * (0.92 + dodge_urgency * 0.18))
        catch_thrust = 1.34 if form_dist > DRONE_CATCH_UP_RADIUS else 1.08
        if dodge_urgency > 0.25:
            catch_thrust = max(catch_thrust, 1.22 + dodge_urgency * 0.35)
        if to_move.length_sq() > 36.0:
            player_match = min(1.18, 0.42 + player_vel.length() / max(1.0, speed_cap))
            accel += Vec2.from_angle(self.angle) * (DRONE_THRUST * catch_thrust * player_match)

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
            if gap > DRONE_ASTEROID_AVOID_RADIUS:
                continue
            t = 1.0 - max(0.0, gap / DRONE_ASTEROID_AVOID_RADIUS)
            strength = t * t * (3.0 - 2.0 * t)
            closing = _closing_speed(self.pos, self.vel, asteroid.pos, asteroid.vel)
            if closing > 0.0:
                strength *= 1.0 + min(2.4, closing / 70.0)
            if gap < DRONE_ASTEROID_PANIC_GAP:
                strength = min(1.0, strength + 0.55)
            push += offset.normalized() * (DRONE_ASTEROID_AVOID_THRUST * strength)
            urgency = max(urgency, strength)
        return push, urgency

    def tick_combat(self, dt: float) -> None:
        if self.fire_cooldown > 0.0:
            self.fire_cooldown = max(0.0, self.fire_cooldown - dt)
        if self.overheat_timer > 0.0:
            self.overheat_timer = max(0.0, self.overheat_timer - dt)
            if self.overheat_timer <= 0.0:
                self.heat = 0.0
            return
        if self.heat > 0.0:
            self.heat = max(0.0, self.heat - DRONE_HEAT_DECAY * dt)

    @property
    def is_overheated(self) -> bool:
        return self.overheat_timer > 0.0

    def try_fire(self, threat: ThreatTarget | None) -> Projectile | None:
        if not self.alive or self.is_overheated or self.fire_cooldown > 0.0 or threat is None:
            return None
        dist = (threat.pos - self.pos).length()
        min_range = DRONE_ASTEROID_MIN_FIRE_RANGE if threat.is_asteroid else DRONE_MIN_RANGE
        max_range = self.engage_range if not threat.is_asteroid else DRONE_ASTEROID_ENGAGE_RANGE
        if dist < min_range or dist > max_range:
            return None

        lead_factor = 0.85 if threat.is_asteroid else 0.72
        aim_dir = lead_aim_direction(
            self.pos,
            threat.pos,
            threat.vel * lead_factor,
            self.shot_speed,
            refine_passes=3,
        )
        if aim_dir is None:
            return None

        spread = (random.random() * 2.0 - 1.0) * (0.018 if threat.is_asteroid else 0.028)
        aim_dir = aim_dir.rotated(spread)
        self.fire_cooldown = DRONE_FIRE_INTERVAL
        self.heat = min(1.0, self.heat + DRONE_HEAT_PER_SHOT)
        if self.heat >= 1.0:
            self.overheat_timer = DRONE_OVERHEAT_COOLDOWN
        self.facing_angle = math.atan2(aim_dir.y, aim_dir.x)
        muzzle = self.pos + aim_dir * (self.radius + 5.0)
        inherit = self.vel * 0.14 if self.vel.length_sq() > 1.0 else Vec2()
        return Projectile(
            pos=muzzle,
            vel=aim_dir * self.shot_speed + inherit,
            ttl=2.1,
            radius=3.2,
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


def _closing_speed(
    pos_a: Vec2,
    vel_a: Vec2,
    pos_b: Vec2,
    vel_b: Vec2,
) -> float:
    """Positive when A moves toward B."""
    offset = pos_b - pos_a
    dist = offset.length()
    if dist < 1e-6:
        return 0.0
    rel_vel = vel_b - vel_a
    return max(0.0, rel_vel.dot(offset.normalized()))
