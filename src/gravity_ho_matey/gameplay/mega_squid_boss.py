from __future__ import annotations

import math
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemy_aim import lead_aim_direction
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.entities import GravityWell, Projectile
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at
from gravity_ho_matey.gameplay.spawn_director import SpawnDirector
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.gameplay.squid_pod import SquidPod


MEGA_SQUID_HITS = 32
PHASE_INVULN_SECONDS = 0.25
PHASE_SHIFT_FX_SECONDS = 0.55
PHASE_2_HP_THRESHOLD = 21
PHASE_3_HP_THRESHOLD = 10
SQUID_SPAWN_INTERVALS = (5.0, 4.0, 3.0)
POD_SPAWN_INTERVALS = (999.0, 4.0, 3.0)
ENERGY_ORB_COOLDOWN = 6.0
# Matches brood liftoff lock zone (BOSS_COMBAT_RADIUS) so orbs reach players in the combat bubble.
ENERGY_ORB_RANGE = 920.0
ENERGY_ORB_SPEED = 340.0
ENERGY_ORB_RADIUS = 7.0


def combat_phase_for_hp(hp: int) -> int:
    if hp > PHASE_2_HP_THRESHOLD:
        return 1
    if hp > PHASE_3_HP_THRESHOLD:
        return 2
    return 3


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
    phase_invuln_remaining: float = 0.0
    phase_shift_fx: float = 0.0
    phase_shift_pending: bool = False
    energy_cooldown: float = 0.0

    @property
    def kind(self) -> EnemyKind:
        return EnemyKind.MEGA_SQUID

    @property
    def combat_phase(self) -> int:
        return combat_phase_for_hp(self.hits_remaining)

    def is_damage_immune(self) -> bool:
        return self.phase_invuln_remaining > 0.0

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

    def _sync_spawn_director(self, phase: int) -> None:
        interval = SQUID_SPAWN_INTERVALS[phase - 1]
        self.director.archetype_cooldown = interval
        self.director.global_cooldown = min(2.5, interval * 0.5)

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
        phase = self.combat_phase
        hp = self.hits_remaining
        self._sync_spawn_director(phase)
        self.spawn_timer += dt
        self.pod_timer += dt
        squid_interval = SQUID_SPAWN_INTERVALS[phase - 1]
        pod_interval = POD_SPAWN_INTERVALS[phase - 1]
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
        if self.pod_timer >= pod_interval and phase >= 2:
            self.pod_timer = 0.0
            aim = prey_pos + (prey_pos - self.pos).normalized() * 40.0
            direction = (aim - self.pos).normalized()
            speed = 400.0 if hp > PHASE_3_HP_THRESHOLD else 460.0
            pod_out = SquidPod(pos=Vec2(self.pos.x, self.pos.y), vel=direction * speed, target=aim)
        return squid_out, pod_out

    def body_hit_by_projectile(self, pos: Vec2, radius: float) -> bool:
        return (self.pos - pos).length() <= self.radius + radius

    def apply_shot(self) -> bool:
        if self.is_damage_immune():
            return False
        prev_phase = self.combat_phase
        self.hits_remaining = max(0, self.hits_remaining - 1)
        if self.hits_remaining <= 0:
            self.alive = False
            return True
        new_phase = self.combat_phase
        if new_phase > prev_phase:
            self._begin_phase_transition(new_phase)
        return False

    def _begin_phase_transition(self, phase: int) -> None:
        self.phase_invuln_remaining = PHASE_INVULN_SECONDS
        self.phase_shift_fx = PHASE_SHIFT_FX_SECONDS
        self.phase_shift_pending = True
        self.spawn_timer = 0.0
        self.pod_timer = 0.0
        self._sync_spawn_director(phase)

    def tick_combat(self, dt: float) -> None:
        if self.phase_invuln_remaining > 0.0:
            self.phase_invuln_remaining = max(0.0, self.phase_invuln_remaining - dt)
        if self.phase_shift_fx > 0.0:
            self.phase_shift_fx = max(0.0, self.phase_shift_fx - dt)
        self.energy_cooldown += dt

    def try_fire(self, ship_pos: Vec2, ship_vel: Vec2) -> Projectile | None:
        if not self.alive or self.is_damage_immune():
            return None
        dist = (ship_pos - self.pos).length()
        if dist > ENERGY_ORB_RANGE or dist < 80.0:
            return None
        if self.energy_cooldown < ENERGY_ORB_COOLDOWN:
            return None
        aim_dir = lead_aim_direction(
            self.pos,
            ship_pos,
            ship_vel * 0.32,
            ENERGY_ORB_SPEED,
            refine_passes=1,
        )
        if aim_dir is None:
            aim_dir = (ship_pos - self.pos).normalized()
        self.energy_cooldown = 0.0
        self.facing_angle = math.atan2(aim_dir.y, aim_dir.x)
        muzzle = self.pos + aim_dir * (self.radius + 12.0)
        inherit = self.vel * 0.08 if self.vel.length_sq() > 1.0 else Vec2()
        return Projectile(
            pos=muzzle,
            vel=aim_dir * ENERGY_ORB_SPEED + inherit,
            ttl=2.8,
            radius=ENERGY_ORB_RADIUS,
            hostile=True,
            boss_energy_orb=True,
        )
