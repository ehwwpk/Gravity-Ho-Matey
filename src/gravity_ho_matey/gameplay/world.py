from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.damage import DamageEvent, DamageSource, default_reason
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.entities import (
    Beacon,
    FinishGate,
    GameStatus,
    GravityWell,
    PowerUpPickup,
    Projectile,
    Ship,
    Wall,
    WorldConfig,
)
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind


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
    enemies: list[PatrolEnemy] = field(default_factory=list)
    pickups: list[PowerUpPickup] = field(default_factory=list)
    on_powerup_collected: Callable[[PowerUpKind], None] | None = None
    status: GameStatus = GameStatus.RUNNING
    elapsed: float = 0.0
    last_damage: DamageEvent | None = None
    spawn_pos: Vec2 = field(default_factory=Vec2)
    spawn_angle: float = 0.0
    invuln_remaining: float = 0.0

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
        self._tick_invuln(dt)
        self._update_ship(dt, intent)
        self._update_projectiles(dt)
        self._update_enemies(dt)
        self._collect_beacons()
        self._collect_pickups()
        self._check_enemy_collisions()
        self._check_finish()
        self._check_loss()

    def _tick_invuln(self, dt: float) -> None:
        if self.invuln_remaining > 0.0:
            self.invuln_remaining = max(0.0, self.invuln_remaining - dt)

    def _register_ship_hit(self, source: DamageSource, reason: str = "") -> None:
        if self.invuln_remaining > 0.0:
            return
        theme = self.config.level_theme
        self.last_damage = DamageEvent(
            source=source,
            reason=reason or default_reason(source, theme),
        )
        self.status = GameStatus.SHIP_HIT

    def _update_ship(self, dt: float, intent: ControlIntent) -> None:
        turn_rate = self.config.turn_rate * self.ship.turn_rate_multiplier
        if intent.rotate_left:
            self.ship.angle -= turn_rate * dt
        if intent.rotate_right:
            self.ship.angle += turn_rate * dt

        accel = gravity_acceleration_at(self.ship.pos, self.wells) * self.config.gravity_scale
        if intent.thrust:
            multiplier = self.config.boost_multiplier if intent.boost and self.ship.boost_energy > 0.05 else 1.0
            thrust = self.config.thrust * self.ship.thrust_multiplier
            accel += Vec2.from_angle(self.ship.angle) * (thrust * multiplier)
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
        self.ship.cooldown = self.config.ship_fire_cooldown * self.ship.fire_cooldown_multiplier

    def _update_projectiles(self, dt: float) -> None:
        kept: list[Projectile] = []
        for projectile in self.projectiles:
            accel = gravity_acceleration_at(projectile.pos, self.wells) * self.config.gravity_scale
            projectile.vel = projectile.vel + accel * dt
            projectile.pos = projectile.pos + projectile.vel * dt
            projectile.ttl -= dt
            if projectile.ttl <= 0:
                continue
            if not self._point_in_bounds(projectile.pos, margin=32):
                continue
            if any(wall.rect.intersects_circle(projectile.pos, projectile.radius) for wall in self.walls):
                continue
            if self._projectile_hits_enemy(projectile):
                continue
            kept.append(projectile)
        self.projectiles = kept

    def _projectile_hits_enemy(self, projectile: Projectile) -> bool:
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if (enemy.pos - projectile.pos).length() <= enemy.radius + projectile.radius:
                enemy.alive = False
                self.pickups.append(PowerUpPickup(pos=Vec2(enemy.pos.x, enemy.pos.y), kind=enemy.drop_kind))
                self._prune_dead_enemies()
                return True
        return False

    def _update_enemies(self, dt: float) -> None:
        for enemy in self.enemies:
            if enemy.alive:
                enemy.integrate(
                    dt,
                    self.wells,
                    gravity_scale=self.config.gravity_scale,
                    drag=self.config.drag,
                )

    def _prune_dead_enemies(self) -> None:
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]

    def _collect_beacons(self) -> None:
        for beacon in self.beacons:
            if beacon.collected:
                continue
            if (beacon.pos - self.ship.pos).length() <= beacon.radius + self.ship.radius:
                beacon.collected = True

    def _collect_pickups(self) -> None:
        if self.on_powerup_collected is None:
            return
        remaining: list[PowerUpPickup] = []
        handler = self.on_powerup_collected
        for pickup in self.pickups:
            if (pickup.pos - self.ship.pos).length() <= pickup.radius + self.ship.radius:
                handler(pickup.kind)
            else:
                remaining.append(pickup)
        self.pickups = remaining

    def _check_enemy_collisions(self) -> None:
        if self.status is not GameStatus.RUNNING:
            return
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if (enemy.pos - self.ship.pos).length() <= enemy.radius + self.ship.radius:
                self._register_ship_hit(DamageSource.ENEMY)
                return

    def _check_finish(self) -> None:
        if self.status is not GameStatus.RUNNING:
            return
        if self.finish_unlocked and self.finish_gate.rect.intersects_circle(self.ship.pos, self.ship.radius):
            self.status = GameStatus.WON

    def _check_loss(self) -> None:
        if self.status is not GameStatus.RUNNING:
            return
        if not self._point_in_bounds(self.ship.pos, margin=0):
            self._register_ship_hit(DamageSource.OUT_OF_BOUNDS)
            return
        if any(wall.rect.intersects_circle(self.ship.pos, self.ship.radius) for wall in self.walls):
            self._register_ship_hit(DamageSource.WALL)
            return
        for well in self.wells:
            maw = well.maw_radius if well.maw_radius is not None else self.config.well_maw_radius
            if (well.pos - self.ship.pos).length() <= maw:
                reason = self._gravity_maw_reason(well)
                self._register_ship_hit(DamageSource.GRAVITY_MAW, reason=reason)
                return

    def _gravity_maw_reason(self, well: GravityWell) -> str:
        if well.kind == "black_hole":
            return "Spaghettified by the singularity."
        if well.kind == "planet":
            return f"Swallowed by {well.label or 'the planet'}."
        return "Dragged into the gravity maw."

    def _point_in_bounds(self, p: Vec2, margin: float) -> bool:
        return -margin <= p.x <= self.config.width + margin and -margin <= p.y <= self.config.height + margin
