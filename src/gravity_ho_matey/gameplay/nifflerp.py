from __future__ import annotations

import math
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.entities import Asteroid, GravityWell, Projectile
from gravity_ho_matey.gameplay.friendly_fighter import _angle_delta
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at, hazard_escape_acceleration_at
from gravity_ho_matey.gameplay.jewel_pickup import JewelPickup
from gravity_ho_matey.gameplay.nifflerp_config import (
    NIFFLERP_ASTEROID_AVOID_RADIUS,
    NIFFLERP_ASTEROID_AVOID_THRUST,
    NIFFLERP_ASTEROID_PANIC_GAP,
    NIFFLERP_BOOST_ENERGY_COST,
    NIFFLERP_BOOST_FLASH_SECONDS,
    NIFFLERP_BOOST_REGEN,
    NIFFLERP_BOOST_SPEED,
    NIFFLERP_BOOST_TRIGGER_URGENCY,
    NIFFLERP_ENEMY_AVOID_RADIUS,
    NIFFLERP_ENEMY_AVOID_THRUST,
    NIFFLERP_ENEMY_BOOST_TRIGGER,
    NIFFLERP_FLEE_ENEMY_URGENCY,
    NIFFLERP_HIT_INVULN,
    NIFFLERP_HITS_MAX,
    NIFFLERP_JEWEL_ABORT_ENEMY_URGENCY,
    NIFFLERP_MAX_SPEED,
    NIFFLERP_PLAY_ORBIT,
    NIFFLERP_PROJECTILE_DODGE_RADIUS,
    NIFFLERP_PROJECTILE_DODGE_THRUST,
    NIFFLERP_RADIUS,
    NIFFLERP_SEEK_RADIUS,
    NIFFLERP_SPAWN_LATERAL,
    NIFFLERP_SPAWN_TRAIL,
    NIFFLERP_SQUID_AVOID_RADIUS,
    NIFFLERP_SQUID_AVOID_THRUST,
    NIFFLERP_SQUID_PANIC_RADIUS,
    NIFFLERP_THRUST,
    NIFFLERP_TURN_RATE,
    NIFFLERP_WELL_ESCAPE_SCALE,
)
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy


def _closing_speed(pos_a: Vec2, vel_a: Vec2, pos_b: Vec2, vel_b: Vec2) -> float:
    offset = pos_b - pos_a
    dist = offset.length()
    if dist < 1e-6:
        return 0.0
    return max(0.0, (vel_b - vel_a).dot(offset.normalized()))


@dataclass(slots=True)
class Nifflerp:
    """Tiny jewel-retriever — no guns, extreme agility, plays when idle."""

    pos: Vec2
    vel: Vec2 = field(default_factory=Vec2)
    angle: float = 0.0
    facing_angle: float = 0.0
    alive: bool = True
    radius: float = NIFFLERP_RADIUS
    hits_remaining: int = NIFFLERP_HITS_MAX
    hits_max: int = NIFFLERP_HITS_MAX
    hit_invuln: float = 0.0
    boost_energy: float = 1.0
    boost_flash: float = 0.0
    play_phase: float = 0.0

    @classmethod
    def spawn_beside_player(
        cls,
        ship: object,
        *,
        hits_remaining: int | None = None,
        hits_max: int | None = None,
    ) -> Nifflerp:
        angle = getattr(ship, "angle", 0.0)
        pos = getattr(ship, "pos", Vec2())
        forward = Vec2.from_angle(angle)
        right = forward.rotated(math.pi / 2.0)
        spawn = pos - forward * NIFFLERP_SPAWN_TRAIL + right * NIFFLERP_SPAWN_LATERAL
        hp_cap = NIFFLERP_HITS_MAX if hits_max is None else hits_max
        hp = hp_cap if hits_remaining is None else max(0, min(hp_cap, hits_remaining))
        return cls(
            pos=Vec2(spawn.x, spawn.y),
            angle=angle + 0.35,
            facing_angle=angle + 0.35,
            hits_remaining=hp,
            hits_max=hp_cap,
            alive=hp > 0,
        )

    def tick(self, dt: float) -> None:
        if self.hit_invuln > 0.0:
            self.hit_invuln = max(0.0, self.hit_invuln - dt)
        if self.boost_flash > 0.0:
            self.boost_flash = max(0.0, self.boost_flash - dt)
        if self.boost_energy < 1.0:
            self.boost_energy = min(1.0, self.boost_energy + NIFFLERP_BOOST_REGEN * dt)
        self.play_phase += dt

    def nearest_jewel_target(
        self,
        jewels: list[JewelPickup],
        player_pos: Vec2,
    ) -> Vec2 | None:
        best: Vec2 | None = None
        best_dist = float("inf")
        for jewel in jewels:
            if (jewel.pos - player_pos).length() > NIFFLERP_SEEK_RADIUS:
                continue
            dist = (jewel.pos - self.pos).length()
            if dist < best_dist:
                best_dist = dist
                best = jewel.pos
        return best

    def play_target(self, player_pos: Vec2, player_angle: float) -> Vec2:
        t = self.play_phase * 1.45
        orbit = NIFFLERP_PLAY_ORBIT + 16.0 * math.sin(t * 0.85)
        forward = Vec2.from_angle(player_angle)
        right = forward.rotated(math.pi / 2.0)
        figure_x = math.sin(t) * orbit
        figure_y = math.sin(t * 2.0) * orbit * 0.38
        loop_lift = max(0.0, math.sin(t * 0.62)) ** 2 * 34.0 * math.sin(t * 3.1)
        base_orbit = forward * 36.0 + right * 28.0 * math.cos(t * 0.75)
        return (
            player_pos
            + base_orbit
            + right * figure_x
            + forward * (figure_y + loop_lift)
        )

    def integrate(
        self,
        dt: float,
        *,
        player_pos: Vec2,
        player_vel: Vec2,
        player_angle: float,
        elapsed: float,
        wells: list[GravityWell],
        gravity_scale: float,
        drag: float,
        well_maw_radius: float,
        jewels: list[JewelPickup],
        asteroids: list[Asteroid],
        enemies: list,
        hostile_projectiles: list[Projectile],
    ) -> None:
        if not self.alive:
            return

        avoid_rock, rock_urgency = self._asteroid_avoidance(asteroids)
        avoid_enemy, enemy_urgency, squid_urgency = self._enemy_avoidance(enemies)
        dodge_bolt, bolt_urgency = self._projectile_dodge(hostile_projectiles)
        dodge_urgency = max(rock_urgency, enemy_urgency * 1.12, bolt_urgency)
        if squid_urgency > 0.0:
            dodge_urgency = max(dodge_urgency, squid_urgency * 1.18)
        avoid_accel = avoid_rock + avoid_enemy + dodge_bolt

        boost_threshold = NIFFLERP_BOOST_TRIGGER_URGENCY
        if enemy_urgency > 0.08 or squid_urgency > 0.05:
            boost_threshold = min(boost_threshold, NIFFLERP_ENEMY_BOOST_TRIGGER)
        if dodge_urgency >= boost_threshold and self.boost_energy >= NIFFLERP_BOOST_ENERGY_COST:
            self.boost_flash = NIFFLERP_BOOST_FLASH_SECONDS
            self.boost_energy = max(0.0, self.boost_energy - NIFFLERP_BOOST_ENERGY_COST)

        jewel_target = self.nearest_jewel_target(jewels, player_pos)
        if jewel_target is not None and enemy_urgency >= NIFFLERP_JEWEL_ABORT_ENEMY_URGENCY:
            jewel_target = None

        fleeing = enemy_urgency >= NIFFLERP_FLEE_ENEMY_URGENCY or squid_urgency >= 0.35
        if fleeing and jewel_target is not None:
            jewel_target = None

        if jewel_target is not None and not fleeing:
            move_target = jewel_target
            seek_weight = max(0.18, 0.92 - enemy_urgency * 0.75)
        else:
            move_target = self.play_target(player_pos, player_angle)
            seek_weight = 0.55 + 0.12 * math.sin(elapsed * 2.4)

        to_target = move_target - self.pos
        target_dist = to_target.length()
        seek_dir = to_target.normalized() if target_dist > 1e-6 else Vec2.from_angle(self.angle)

        to_player = player_pos - self.pos
        player_dir = to_player.normalized() if to_player.length_sq() > 64.0 else Vec2.from_angle(player_angle)

        if fleeing and avoid_enemy.length_sq() > 1.0:
            flee_dir = avoid_enemy.normalized()
            move_dir = (flee_dir * 0.82 + player_dir * 0.18).normalized()
        elif dodge_urgency > 0.08 and avoid_accel.length_sq() > 1.0:
            dodge_dir = avoid_accel.normalized()
            blend = min(0.99, 0.58 + dodge_urgency * 0.42)
            if enemy_urgency > 0.2:
                blend = min(0.99, blend + 0.12)
            move_dir = (seek_dir * (1.0 - blend) * seek_weight + dodge_dir * blend).normalized()
        else:
            move_dir = seek_dir

        desired_heading = math.atan2(move_dir.y, move_dir.x)
        heading_delta = _angle_delta(desired_heading - self.angle)
        max_turn = NIFFLERP_TURN_RATE * dt
        if heading_delta > max_turn:
            self.angle += max_turn
        elif heading_delta < -max_turn:
            self.angle -= max_turn
        else:
            self.angle = desired_heading
        self.facing_angle = self.angle

        accel = gravity_acceleration_at(self.pos, wells) * gravity_scale
        accel += hazard_escape_acceleration_at(
            self.pos,
            wells,
            gravity_scale=gravity_scale,
            default_maw_radius=well_maw_radius,
        ) * NIFFLERP_WELL_ESCAPE_SCALE
        accel += avoid_accel

        boosting = self.boost_flash > 0.0
        speed_cap = NIFFLERP_BOOST_SPEED if boosting else NIFFLERP_MAX_SPEED
        if fleeing or squid_urgency > 0.25:
            speed_cap = max(speed_cap, NIFFLERP_BOOST_SPEED * (0.92 + max(enemy_urgency, squid_urgency) * 0.22))
        elif dodge_urgency > 0.18:
            speed_cap = max(speed_cap, NIFFLERP_BOOST_SPEED * (0.90 + dodge_urgency * 0.20))
        if jewel_target is not None and target_dist > 80.0 and enemy_urgency < 0.15:
            speed_cap = max(speed_cap, NIFFLERP_MAX_SPEED * 1.06)

        thrust_scale = 1.42 if boosting else 1.12
        if fleeing:
            thrust_scale = max(thrust_scale, 1.55 + max(enemy_urgency, squid_urgency) * 0.65)
        elif dodge_urgency > 0.15:
            thrust_scale = max(thrust_scale, 1.28 + dodge_urgency * 0.62)
        if squid_urgency > 0.2:
            thrust_scale = max(thrust_scale, 1.48 + squid_urgency * 0.55)
        player_match = min(1.35, 0.55 + player_vel.length() / max(1.0, speed_cap))
        accel += Vec2.from_angle(self.angle) * (NIFFLERP_THRUST * thrust_scale * player_match)

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
            if gap > NIFFLERP_ASTEROID_AVOID_RADIUS:
                continue
            t = 1.0 - max(0.0, gap / NIFFLERP_ASTEROID_AVOID_RADIUS)
            strength = t * t * (3.0 - 2.0 * t)
            closing = _closing_speed(self.pos, self.vel, asteroid.pos, asteroid.vel)
            if closing > 0.0:
                strength *= 1.0 + min(3.2, closing / 58.0)
            if gap < NIFFLERP_ASTEROID_PANIC_GAP:
                strength = min(1.0, strength + 0.68)
            push += offset.normalized() * (NIFFLERP_ASTEROID_AVOID_THRUST * strength)
            urgency = max(urgency, strength)
        return push, urgency

    def _enemy_avoidance(self, enemies: list) -> tuple[Vec2, float, float]:
        push = Vec2()
        urgency = 0.0
        squid_urgency = 0.0
        for enemy in enemies:
            if not enemy.alive:
                continue
            offset = self.pos - enemy.pos
            dist = offset.length()
            if dist < 1e-6:
                continue
            is_squid = getattr(enemy, "kind", None) is EnemyKind.SQUID and isinstance(enemy, SquidEnemy)
            if is_squid:
                assert isinstance(enemy, SquidEnemy)
                reach = enemy.tentacle_span() + self.radius + 38.0
                avoid_radius = NIFFLERP_SQUID_AVOID_RADIUS
                panic = NIFFLERP_SQUID_PANIC_RADIUS
                thrust = NIFFLERP_SQUID_AVOID_THRUST
            else:
                reach = enemy.radius + self.radius + 48.0
                avoid_radius = NIFFLERP_ENEMY_AVOID_RADIUS
                panic = NIFFLERP_ENEMY_AVOID_RADIUS * 0.52
                thrust = NIFFLERP_ENEMY_AVOID_THRUST
            gap = dist - reach
            if gap > avoid_radius:
                continue
            t = 1.0 - max(0.0, gap / avoid_radius)
            strength = t * t * (3.0 - 2.0 * t)
            closing = _closing_speed(self.pos, self.vel, enemy.pos, getattr(enemy, "vel", Vec2()))
            if closing > 0.0:
                close_mul = 4.2 if is_squid else 3.6
                strength *= 1.0 + min(close_mul, closing / (42.0 if is_squid else 48.0))
            if gap < panic:
                strength = min(1.0, strength + (0.88 if is_squid else 0.78))
            if is_squid:
                strength = min(1.0, strength * 1.22)
            push += offset.normalized() * (thrust * strength)
            urgency = max(urgency, strength)
            if is_squid:
                squid_urgency = max(squid_urgency, strength)
        return push, urgency, squid_urgency

    def _projectile_dodge(self, projectiles: list[Projectile]) -> tuple[Vec2, float]:
        push = Vec2()
        urgency = 0.0
        for bolt in projectiles:
            if not bolt.hostile:
                continue
            offset = self.pos - bolt.pos
            dist = offset.length()
            if dist < 1e-6:
                continue
            combined = bolt.radius + self.radius + 8.0
            gap = dist - combined
            if gap > NIFFLERP_PROJECTILE_DODGE_RADIUS:
                continue
            if bolt.vel.length_sq() < 1.0:
                continue
            bolt_dir = bolt.vel.normalized()
            toward = offset.normalized() * -1.0
            if toward.dot(bolt_dir) < 0.08:
                continue
            t = 1.0 - max(0.0, gap / NIFFLERP_PROJECTILE_DODGE_RADIUS)
            strength = t * t * (3.0 - 2.0 * t)
            lateral = bolt_dir.rotated(math.pi / 2.0)
            if lateral.dot(offset) < 0.0:
                lateral = lateral * -1.0
            dodge = (offset.normalized() * 0.72 + lateral * 0.28).normalized()
            push += dodge * (NIFFLERP_PROJECTILE_DODGE_THRUST * strength)
            urgency = max(urgency, strength)
        return push, urgency

    def apply_shot(self) -> bool:
        if self.hit_invuln > 0.0:
            return False
        self.hit_invuln = NIFFLERP_HIT_INVULN
        self.hits_remaining = max(0, self.hits_remaining - 1)
        if self.hits_remaining <= 0:
            self.alive = False
            return True
        return False

    def body_hit_by_projectile(self, projectile_pos: Vec2, projectile_radius: float) -> bool:
        return (projectile_pos - self.pos).length() <= self.radius + projectile_radius
