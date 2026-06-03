from __future__ import annotations

from dataclasses import dataclass, field
import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import (
    Beacon,
    FinishGate,
    GameStatus,
    GravityWell,
    Projectile,
    Ship,
    Wall,
    WorldConfig,
)
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at


@dataclass(slots=True)
class ControlIntent:
    rotate_left: bool = False
    rotate_right: bool = False
    thrust: bool = False
    boost: bool = False
    fire: bool = False


@dataclass(slots=True)
class GameWorld:
    config: WorldConfig
    ship: Ship
    walls: list[Wall]
    wells: list[GravityWell]
    beacons: list[Beacon]
    finish_gate: FinishGate
    projectiles: list[Projectile] = field(default_factory=list)
    status: GameStatus = GameStatus.RUNNING
    elapsed: float = 0.0
    loss_reason: str = ""

    @property
    def beacons_remaining(self) -> int:
        return sum(1 for beacon in self.beacons if not beacon.collected)

    @property
    def finish_unlocked(self) -> bool:
        return self.beacons_remaining == 0

    def update(self, dt: float, intent: ControlIntent) -> None:
        if self.status is not GameStatus.RUNNING:
            return

        dt = max(0.0, min(dt, 1.0 / 20.0))
        self.elapsed += dt
        self._update_ship(dt, intent)
        self._update_projectiles(dt)
        self._collect_beacons()
        self._check_finish()
        self._check_loss()

    def _update_ship(self, dt: float, intent: ControlIntent) -> None:
        if intent.rotate_left:
            self.ship.angle -= self.config.turn_rate * dt
        if intent.rotate_right:
            self.ship.angle += self.config.turn_rate * dt

        accel = gravity_acceleration_at(self.ship.pos, self.wells)
        if intent.thrust:
            multiplier = self.config.boost_multiplier if intent.boost and self.ship.boost_energy > 0.05 else 1.0
            accel += Vec2.from_angle(self.ship.angle) * (self.config.thrust * multiplier)
            if multiplier > 1.0:
                self.ship.boost_energy = max(0.0, self.ship.boost_energy - 0.45 * dt)
        else:
            self.ship.boost_energy = min(1.0, self.ship.boost_energy + 0.18 * dt)

        self.ship.vel = (self.ship.vel + accel * dt) * self.config.drag
        self.ship.vel = self.ship.vel.clamped_length(self.config.max_ship_speed)
        self.ship.pos = self.ship.pos + self.ship.vel * dt
        self.ship.cooldown = max(0.0, self.ship.cooldown - dt)

        if intent.fire and self.ship.cooldown <= 0.0:
            self.fire_projectile()

    def fire_projectile(self) -> None:
        direction = Vec2.from_angle(self.ship.angle)
        muzzle = self.ship.pos + direction * (self.ship.radius + 8.0)
        velocity = self.ship.vel * 0.35 + direction * self.config.projectile_speed
        self.projectiles.append(Projectile(pos=muzzle, vel=velocity))
        self.ship.cooldown = self.config.ship_fire_cooldown

    def _update_projectiles(self, dt: float) -> None:
        kept: list[Projectile] = []
        for projectile in self.projectiles:
            accel = gravity_acceleration_at(projectile.pos, self.wells)
            projectile.vel = projectile.vel + accel * dt
            projectile.pos = projectile.pos + projectile.vel * dt
            projectile.ttl -= dt
            if projectile.ttl <= 0:
                continue
            if not self._point_in_bounds(projectile.pos, margin=32):
                continue
            if any(wall.rect.intersects_circle(projectile.pos, projectile.radius) for wall in self.walls):
                continue
            kept.append(projectile)
        self.projectiles = kept

    def _collect_beacons(self) -> None:
        for beacon in self.beacons:
            if beacon.collected:
                continue
            if (beacon.pos - self.ship.pos).length() <= beacon.radius + self.ship.radius:
                beacon.collected = True

    def _check_finish(self) -> None:
        if self.finish_unlocked and self.finish_gate.rect.intersects_circle(self.ship.pos, self.ship.radius):
            self.status = GameStatus.WON

    def _check_loss(self) -> None:
        if not self._point_in_bounds(self.ship.pos, margin=0):
            self.status = GameStatus.LOST
            self.loss_reason = "Lost beyond the reef."
            return
        if any(wall.rect.intersects_circle(self.ship.pos, self.ship.radius) for wall in self.walls):
            self.status = GameStatus.LOST
            self.loss_reason = "Hull smashed on the rocks."
            return
        for well in self.wells:
            if (well.pos - self.ship.pos).length() <= 16.0:
                self.status = GameStatus.LOST
                self.loss_reason = "Dragged into the gravity maw."
                return

    def _point_in_bounds(self, p: Vec2, margin: float) -> bool:
        return -margin <= p.x <= self.config.width + margin and -margin <= p.y <= self.config.height + margin
