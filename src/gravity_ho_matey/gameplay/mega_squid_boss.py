from __future__ import annotations

import math
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.entities import GravityWell, Projectile
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at
from gravity_ho_matey.gameplay.spawn_director import SpawnDirector
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.gameplay.squid_pod import SquidPod


MEGA_SQUID_HITS = 18


@dataclass(slots=True)
class MegaSquidBoss:
    pos: Vec2
    anchor: Vec2
    vel: Vec2 = field(default_factory=Vec2)
    radius: float = 42.0
    alive: bool = True
    hits_max: int = MEGA_SQUID_HITS
    hits_remaining: int = MEGA_SQUID_HITS
    facing_angle: float = 0.0
    wobble: float = 0.0
    spawn_timer: float = 0.0
    pod_timer: float = 0.0
    approach_gain: float = 1.8
    max_cruise: float = 62.0
    director: SpawnDirector = field(default_factory=SpawnDirector)

    @property
    def kind(self) -> EnemyKind:
        return EnemyKind.MEGA_SQUID

    def integrate(
        self,
        dt: float,
        wells: list[GravityWell],
        *,
        gravity_scale: float,
        drag: float,
        well_gravity_scale: float = 0.35,
    ) -> None:
        if not self.alive:
            return
        self.wobble += dt * 2.2
        orbit = Vec2(
            math.cos(self.wobble * 0.35) * 48.0,
            math.sin(self.wobble * 0.28) * 36.0,
        )
        target = self.anchor + orbit
        pull = (target - self.pos) * self.approach_gain
        accel = gravity_acceleration_at(self.pos, wells) * gravity_scale * well_gravity_scale + pull
        self.vel = (self.vel + accel * dt) * drag
        self.vel = self.vel.clamped_length(self.max_cruise)
        self.pos = self.pos + self.vel * dt
        if self.vel.length_sq() > 4.0:
            self.facing_angle = math.atan2(self.vel.y, self.vel.x)

    def tick_spawns(
        self,
        dt: float,
        prey_pos: Vec2,
        alive_squids: int,
    ) -> tuple[SquidEnemy | None, SquidPod | None]:
        if not self.alive:
            return None, None
        self.director.tick(dt)
        squid_out: SquidEnemy | None = None
        pod_out: SquidPod | None = None
        hp = self.hits_remaining
        self.spawn_timer += dt
        self.pod_timer += dt
        squid_interval = 7.5 if hp > 11 else 6.0 if hp > 5 else 4.8
        pod_interval = 999.0 if hp > 11 else 6.3 if hp > 5 else 4.5
        if self.spawn_timer >= squid_interval and self.director.can_spawn(alive_squids):
            self.spawn_timer = 0.0
            self.director.record_spawn()
            offset = Vec2.from_angle(self.facing_angle + 0.6) * 120.0
            squid_out = SquidEnemy(
                pos=self.pos + offset,
                tentacle_reach=68.0,
                max_speed=192.0,
                detect_range=980.0,
                engage_range=820.0,
            )
        if self.pod_timer >= pod_interval and hp <= 11:
            self.pod_timer = 0.0
            aim = prey_pos + (prey_pos - self.pos).normalized() * 40.0
            direction = (aim - self.pos).normalized()
            speed = 400.0 if hp > 5 else 460.0
            pod_out = SquidPod(pos=Vec2(self.pos.x, self.pos.y), vel=direction * speed, target=aim)
        return squid_out, pod_out

    def body_hit_by_projectile(self, pos: Vec2, radius: float) -> bool:
        return (self.pos - pos).length() <= self.radius + radius

    def apply_shot(self) -> bool:
        self.hits_remaining = max(0, self.hits_remaining - 1)
        if self.hits_remaining <= 0:
            self.alive = False
            return True
        return False

    def tick_combat(self, dt: float) -> None:
        _ = dt

    def try_fire(self, ship_pos: Vec2, ship_vel: Vec2) -> Projectile | None:
        _ = ship_pos, ship_vel
        return None
