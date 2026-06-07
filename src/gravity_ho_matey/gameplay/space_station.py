from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.enemy_aim import lead_aim_direction
from gravity_ho_matey.gameplay.entities import Asteroid, GravityWell, Projectile
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at
from gravity_ho_matey.gameplay.spawn_director import SpawnDirector
from gravity_ho_matey.gameplay.station_kinds import StationFaction
from gravity_ho_matey.gameplay.tractor_beam import (
    TractorBeamState,
    pick_tractor_asteroid,
    pick_toss_target,
)

STATION_HITS_MAX = 24
STATION_RADIUS = 88.0
STATION_GUN_INTERVAL = 2.2
STATION_GUN_RANGE = 520.0
STATION_GUN_SHOT_SPEED = 245.0
STATION_SPAWN_INTERVAL = 17.5
STATION_SPAWN_JITTER = 2.5
STATION_EXCLUSION = 280.0


@dataclass(slots=True)
class SpaceStation:
    """Orbital platform — turret, tractor, optional spawn bay. Faction drives targeting."""

    pos: Vec2
    anchor: Vec2
    faction: StationFaction = StationFaction.HOSTILE
    hits_max: int = STATION_HITS_MAX
    hits_remaining: int = STATION_HITS_MAX
    radius: float = STATION_RADIUS
    alive: bool = True
    facing_angle: float = math.pi
    ring_angle: float = 0.0
    gun_cooldown: float = 0.0
    gun_interval: float = STATION_GUN_INTERVAL
    gun_range: float = STATION_GUN_RANGE
    gun_shot_speed: float = STATION_GUN_SHOT_SPEED
    spawn_timer: float = 0.0
    spawn_interval: float = STATION_SPAWN_INTERVAL
    spawn_jitter: float = STATION_SPAWN_JITTER
    can_spawn: bool = True
    spawn_bay_open: float = 0.0
    wobble: float = 0.0
    _pending_spawn_interval: float = STATION_SPAWN_INTERVAL
    director: SpawnDirector = field(default_factory=lambda: SpawnDirector(max_alive=3, global_cooldown=4.0))

    def integrate(self, dt: float, wells: list[GravityWell], *, gravity_scale: float, drag: float) -> None:
        if not self.alive:
            return
        self.wobble += dt * 0.85
        orbit = Vec2(math.cos(self.wobble * 0.22) * 6.0, math.sin(self.wobble * 0.19) * 5.0)
        target = self.anchor + orbit
        pull = (target - self.pos) * 2.4
        accel = gravity_acceleration_at(self.pos, wells) * gravity_scale * 0.12 + pull
        vel = (self.pos - self.anchor) * 0.5
        self.pos = self.anchor + (vel + accel * dt) * 0.92
        self.ring_angle += dt * 0.35
        if self.spawn_bay_open > 0.0:
            self.spawn_bay_open = max(0.0, self.spawn_bay_open - dt)

    def tick_combat(self, dt: float) -> None:
        if self.gun_cooldown > 0.0:
            self.gun_cooldown = max(0.0, self.gun_cooldown - dt)

    def apply_shot(self) -> bool:
        self.hits_remaining = max(0, self.hits_remaining - 1)
        if self.hits_remaining <= 0:
            self.alive = False
            return True
        return False

    def body_hit_by_projectile(self, projectile_pos: Vec2, projectile_radius: float) -> bool:
        return (projectile_pos - self.pos).length() <= self.radius + projectile_radius

    def _pick_gun_target(
        self,
        player_pos: Vec2,
        player_vel: Vec2,
        allies: list,
        drone_pos: Vec2 | None,
    ) -> tuple[Vec2, Vec2] | None:
        if self.faction is not StationFaction.HOSTILE:
            return None
        best_pos = player_pos
        best_vel = player_vel
        best_dist = (player_pos - self.pos).length() * 0.82
        for ally in allies:
            if not getattr(ally, "alive", True):
                continue
            pos = getattr(ally, "pos", None)
            if pos is None:
                continue
            dist = (pos - self.pos).length()
            if dist < best_dist:
                best_pos = pos
                best_vel = getattr(ally, "vel", Vec2())
                best_dist = dist
        if drone_pos is not None:
            dist = (drone_pos - self.pos).length()
            if dist < best_dist * 0.95:
                best_pos = drone_pos
                best_vel = Vec2()
        if best_dist > self.gun_range:
            return None
        return best_pos, best_vel

    def try_fire(
        self,
        player_pos: Vec2,
        player_vel: Vec2,
        allies: list,
        *,
        drone_pos: Vec2 | None = None,
    ) -> Projectile | None:
        if not self.alive or self.gun_cooldown > 0.0:
            return None
        picked = self._pick_gun_target(player_pos, player_vel, allies, drone_pos)
        if picked is None:
            return None
        target_pos, target_vel = picked
        aim_dir = lead_aim_direction(
            self.pos,
            target_pos,
            target_vel * 0.72,
            self.gun_shot_speed,
            refine_passes=2,
        )
        if aim_dir is None:
            return None
        spread = (random.random() * 2.0 - 1.0) * 0.018
        aim_dir = aim_dir.rotated(spread)
        self.gun_cooldown = self.gun_interval
        self.facing_angle = math.atan2(aim_dir.y, aim_dir.x)
        muzzle = self.pos + aim_dir * (self.radius + 14.0)
        return Projectile(
            pos=muzzle,
            vel=aim_dir * self.gun_shot_speed,
            ttl=2.4,
            radius=3.8,
            hostile=True,
        )

    def tick_tractor(
        self,
        dt: float,
        tractor: TractorBeamState,
        asteroids: list[Asteroid],
        player_pos: Vec2,
        allies: list,
    ) -> bool:
        if not self.alive or self.faction is not StationFaction.HOSTILE:
            return False
        from gravity_ho_matey.gameplay.tractor_beam import TractorPhase

        tractor.tick_cooldown(dt)
        tossed = tractor.advance(dt, self.pos, asteroids)
        if tractor.phase is TractorPhase.IDLE and tractor.cooldown_remaining <= 0.0:
            rock = pick_tractor_asteroid(self.pos, asteroids, exclusion_radius=STATION_EXCLUSION)
            if rock is not None:
                aim = pick_toss_target(self.pos, player_pos, allies)
                tractor.begin_acquire(rock, aim)
        return tossed

    def tick_spawns(self, dt: float, station_spawned_patrols: int) -> PatrolEnemy | None:
        if not self.alive or not self.can_spawn or self.faction is not StationFaction.HOSTILE:
            return None
        self.director.tick(dt)
        self.spawn_timer += dt
        if self.spawn_timer < self._pending_spawn_interval:
            return None
        if not self.director.can_spawn(station_spawned_patrols):
            return None
        self.spawn_timer = 0.0
        self._pending_spawn_interval = self.spawn_interval + (random.random() * 2.0 - 1.0) * self.spawn_jitter
        self.director.record_spawn()
        self.spawn_bay_open = 0.55
        launch = Vec2.from_angle(self.facing_angle) * (self.radius + 36.0)
        spawn_pos = self.pos + launch
        right = Vec2.from_angle(self.facing_angle + math.pi / 2.0)
        wp_a = spawn_pos - Vec2.from_angle(self.facing_angle) * 90.0 + right * 55.0
        wp_b = spawn_pos - Vec2.from_angle(self.facing_angle) * 90.0 - right * 55.0
        wp_c = spawn_pos - Vec2.from_angle(self.facing_angle) * 160.0
        return PatrolEnemy(
            waypoints=(wp_a, wp_b, wp_c),
            pos=Vec2(spawn_pos.x, spawn_pos.y),
            thrust=248.0,
            max_speed=108.0,
            can_shoot=True,
            fire_interval=2.65,
            fire_cooldown=0.8,
            engage_range=480.0,
            skirmish_roster_id=None,
        )
