from __future__ import annotations

import math

from collections.abc import Callable
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.chart_radiation import advance_chart_radiation_exposure
from gravity_ho_matey.gameplay.chart_bounds import chart_radiation_reason, ship_in_chart
from gravity_ho_matey.gameplay.damage import DamageEvent, DamageSeverity, DamageSource, damage_spec_for, default_reason
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.explosions import ExplosionKind, ExplosionSystem
from gravity_ho_matey.gameplay.asteroid_combat import (
    AsteroidCombatResult,
    apply_projectile_hit,
)
from gravity_ho_matey.gameplay.asteroid_motion import integrate_asteroid, integrate_ring_asteroid_kinematic
from gravity_ho_matey.gameplay.entities import (
    Asteroid,
    Beacon,
    FinishGate,
    GameStatus,
    GravityWell,
    PowerUpPickup,
    Projectile,
    Ship,
    WorldConfig,
)
from gravity_ho_matey.core.geometry import circle_intersects_convex_polygon
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.squid_enemy import SQUID_CLING_DAMAGE_INTERVAL, SquidEnemy
from gravity_ho_matey.gameplay.asteroid_spatial import AsteroidSpatialGrid
from gravity_ho_matey.gameplay.threat_snapshot import AsteroidThreatSnapshot, build_asteroid_threat_snapshots

EnemyUnit = PatrolEnemy | SquidEnemy


@dataclass(slots=True)
class ControlIntent:
    rotate_left: bool = False
    rotate_right: bool = False
    thrust: bool = False
    boost_tap: bool = False
    fire: bool = False


@dataclass(slots=True)
class GameWorld:
    config: WorldConfig
    ship: Ship
    asteroids: list[Asteroid]
    wells: list[GravityWell]
    beacons: list[Beacon]
    finish_gate: FinishGate
    projectiles: list[Projectile] = field(default_factory=list)
    enemies: list[EnemyUnit] = field(default_factory=list)
    pickups: list[PowerUpPickup] = field(default_factory=list)
    on_powerup_collected: Callable[[PowerUpKind], None] | None = None
    status: GameStatus = GameStatus.RUNNING
    elapsed: float = 0.0
    last_damage: DamageEvent | None = None
    spawn_pos: Vec2 = field(default_factory=Vec2)
    spawn_angle: float = 0.0
    invuln_remaining: float = 0.0
    explosions: ExplosionSystem = field(default_factory=ExplosionSystem)
    asteroid_threat_snapshots: tuple[AsteroidThreatSnapshot, ...] = ()
    asteroid_spatial: AsteroidSpatialGrid = field(default_factory=AsteroidSpatialGrid)
    chart_radiation_exposure: float = 0.0
    squid_cling_timer: float = 0.0

    def refresh_threat_snapshots(self) -> None:
        """Narrow-phase meshes for interaction zone only — far belt rocks stay motion-only."""
        if not self.asteroid_spatial.populated:
            self.asteroid_spatial.rebuild(self.asteroids)
        active = self.asteroid_spatial.query_interaction_zones(
            self.ship.pos,
            projectile_points=tuple(Vec2(p.pos.x, p.pos.y) for p in self.projectiles),
        )
        self.asteroid_threat_snapshots = build_asteroid_threat_snapshots(active)

    @property
    def beacons_remaining(self) -> int:
        return sum(1 for beacon in self.beacons if not beacon.collected)

    @property
    def finish_unlocked(self) -> bool:
        return self.beacons_remaining == 0

    def update(self, dt: float, intent: ControlIntent, *, beacon_capture_slack: float = 0.0) -> None:
        dt = max(0.0, min(dt, 1.0 / 20.0))
        self.elapsed += dt
        self.explosions.update(dt)
        if self.status is not GameStatus.RUNNING:
            return

        self._tick_invuln(dt)
        self._update_asteroids(dt)
        self.asteroid_spatial.rebuild(self.asteroids)
        self._update_ship(dt, intent)
        self._update_enemies(dt)
        self._update_projectiles(dt)
        self.refresh_threat_snapshots()
        self._collect_beacons(beacon_capture_slack)
        self._collect_pickups()
        self._check_squid_cling_damage(dt)
        if self.status is GameStatus.RUNNING:
            self._check_patrol_enemy_collisions()
        self._check_finish()
        self._tick_chart_radiation(dt)
        self._check_loss()

    def _update_asteroids(self, dt: float) -> None:
        cfg = self.config
        ship_in_playfield = not cfg.open_bounds or ship_in_chart(self.ship.pos, cfg)
        for asteroid in self.asteroids:
            if asteroid.free_bounds and ship_in_playfield:
                continue
            if asteroid.drift_kind == "ring" and asteroid.ring_anchor is not None:
                integrate_ring_asteroid_kinematic(asteroid, dt)
                continue
            integrate_asteroid(
                asteroid,
                dt,
                self.wells,
                gravity_scale=cfg.gravity_scale,
                world_width=float(cfg.width),
                world_height=float(cfg.height),
            )

    def _asteroid_hit_at(self, pos: Vec2, radius: float, *, use_spatial: bool = False) -> Asteroid | None:
        if use_spatial and self.asteroid_spatial.populated:
            return self._asteroid_hit_among(
                self.asteroid_spatial.query_circle(pos, radius + 72.0),
                pos,
                radius,
            )
        snapshots = self.asteroid_threat_snapshots
        if not snapshots:
            self.refresh_threat_snapshots()
            snapshots = self.asteroid_threat_snapshots
        for snap in snapshots:
            if not snap.aabb.intersects_circle(pos, radius):
                continue
            if circle_intersects_convex_polygon(pos, radius, list(snap.verts)):
                return snap.asteroid
        return None

    def _asteroid_hit_among(self, candidates: list[Asteroid], pos: Vec2, radius: float) -> Asteroid | None:
        for asteroid in candidates:
            reach = asteroid.approximate_radius() + radius
            if (asteroid.pos - pos).length_sq() > reach * reach:
                continue
            if circle_intersects_convex_polygon(pos, radius, asteroid.world_vertices()):
                return asteroid
        return None

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
        spec = damage_spec_for(source)
        if spec.severity is DamageSeverity.LETHAL:
            self.explosions.spawn(ExplosionKind.SHIP_DESTROYED, Vec2(self.ship.pos.x, self.ship.pos.y))
        else:
            self.explosions.spawn(ExplosionKind.SHIP_STRUCK, Vec2(self.ship.pos.x, self.ship.pos.y))
        self.status = GameStatus.SHIP_HIT

    def _update_ship(self, dt: float, intent: ControlIntent) -> None:
        turn_rate = self.config.turn_rate * self.ship.turn_rate_multiplier
        if intent.rotate_left:
            self.ship.angle -= turn_rate * dt
        if intent.rotate_right:
            self.ship.angle += turn_rate * dt

        if self.ship.boost_flash > 0.0:
            self.ship.boost_flash = max(0.0, self.ship.boost_flash - dt)
        self.ship.boost_energy = min(
            1.0,
            self.ship.boost_energy + self.config.boost_regen_rate * dt,
        )

        accel = gravity_acceleration_at(self.ship.pos, self.wells) * self.config.gravity_scale
        if intent.thrust:
            thrust = self.config.thrust * self.ship.thrust_multiplier
            accel += Vec2.from_angle(self.ship.angle) * thrust

        self.ship.vel = (self.ship.vel + accel * dt) * self.config.drag

        if intent.boost_tap and self.ship.boost_energy >= self.config.boost_energy_cost:
            forward = Vec2.from_angle(self.ship.angle)
            burst = (
                self.config.max_ship_speed
                * self.config.boost_burst_fraction
                * self.ship.thrust_multiplier
            )
            burst += max(0.0, self.ship.vel.dot(forward)) * 0.12
            self.ship.vel = self.ship.vel + forward * burst
            self.ship.boost_energy = max(0.0, self.ship.boost_energy - self.config.boost_energy_cost)
            self.ship.boost_flash = self.config.boost_flash_seconds

        speed_cap = self.config.max_ship_speed * (
            self.config.boost_overspeed_cap if self.ship.boost_flash > 0.0 else 1.0
        )
        self.ship.vel = self.ship.vel.clamped_length(speed_cap)
        self.ship.pos = self.ship.pos + self.ship.vel * dt
        self.ship.cooldown = max(0.0, self.ship.cooldown - dt)

        if intent.fire and self.ship.cooldown <= 0.0:
            self.fire_projectile()

    def fire_projectile(self) -> None:
        direction = Vec2.from_angle(self.ship.angle)
        muzzle = self.ship.pos + direction * (self.ship.radius + 8.0)
        velocity = self.ship.vel * 0.35 + direction * self.config.projectile_speed
        self.projectiles.append(Projectile(pos=muzzle, vel=velocity, hostile=False))
        self.ship.cooldown = self.config.ship_fire_cooldown * self.ship.fire_cooldown_multiplier

    def _apply_asteroid_combat_result(self, result: AsteroidCombatResult) -> None:
        for fx in result.fx:
            self.explosions.spawn(fx.kind, fx.pos, scale=fx.scale)
        for asteroid in result.asteroids_removed:
            if asteroid in self.asteroids:
                self.asteroids.remove(asteroid)
        if result.asteroids_added:
            self.asteroids.extend(result.asteroids_added)
        if result.snapshots_dirty:
            self.asteroid_spatial.rebuild(self.asteroids)
            self.refresh_threat_snapshots()

    def _update_projectiles(self, dt: float) -> None:
        kept: list[Projectile] = []
        for projectile in self.projectiles:
            accel = gravity_acceleration_at(projectile.pos, self.wells) * self.config.gravity_scale
            projectile.vel = projectile.vel + accel * dt
            projectile.pos = projectile.pos + projectile.vel * dt
            projectile.ttl -= dt
            if projectile.ttl <= 0:
                continue
            if not self.config.open_bounds and not self._point_in_bounds(projectile.pos, margin=32):
                self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, Vec2(projectile.pos.x, projectile.pos.y))
                continue
            hit = self._asteroid_hit_at(projectile.pos, projectile.radius, use_spatial=True)
            if hit is not None:
                impact = Vec2(projectile.pos.x, projectile.pos.y)
                self._apply_asteroid_combat_result(
                    apply_projectile_hit(
                        hit,
                        impact,
                        projectile.vel,
                        world_asteroid_count=len(self.asteroids),
                        max_asteroids=self.config.max_asteroids,
                    )
                )
                continue
            if projectile.hostile:
                if self._projectile_hits_ship(projectile):
                    continue
            elif self._projectile_hits_enemy(projectile):
                continue
            kept.append(projectile)
        self.projectiles = kept

    def _projectile_hits_enemy(self, projectile: Projectile) -> bool:
        if projectile.hostile:
            return False
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if enemy.kind is EnemyKind.SQUID:
                assert isinstance(enemy, SquidEnemy)
                if not enemy.body_hit_by_projectile(projectile.pos, projectile.radius):
                    continue
                hit_pos = Vec2(projectile.pos.x, projectile.pos.y)
                self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, hit_pos)
                if enemy.apply_shot():
                    enemy_pos = Vec2(enemy.pos.x, enemy.pos.y)
                    enemy.alive = False
                    self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, enemy_pos)
                    self.pickups.append(PowerUpPickup(pos=enemy_pos, kind=enemy.drop_kind))
                    self._prune_dead_enemies()
                return True
            if (enemy.pos - projectile.pos).length() <= enemy.radius + projectile.radius:
                hit_pos = Vec2(projectile.pos.x, projectile.pos.y)
                enemy_pos = Vec2(enemy.pos.x, enemy.pos.y)
                enemy.alive = False
                self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, hit_pos)
                self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, enemy_pos)
                self.pickups.append(PowerUpPickup(pos=enemy_pos, kind=enemy.drop_kind))
                self._prune_dead_enemies()
                return True
        return False

    def _projectile_hits_ship(self, projectile: Projectile) -> bool:
        if not projectile.hostile or self.status is not GameStatus.RUNNING:
            return False
        if (self.ship.pos - projectile.pos).length() > self.ship.radius + projectile.radius:
            return False
        self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, Vec2(projectile.pos.x, projectile.pos.y))
        self._register_ship_hit(DamageSource.ENEMY_PROJECTILE)
        return True

    def _update_enemies(self, dt: float) -> None:
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            enemy.tick_combat(dt)
            if enemy.kind is EnemyKind.SQUID:
                assert isinstance(enemy, SquidEnemy)
                enemy.integrate(
                    dt,
                    self.ship.pos,
                    self.ship.vel,
                    self.wells,
                    gravity_scale=self.config.gravity_scale,
                    drag=self.config.drag,
                    well_maw_radius=self.config.well_maw_radius,
                    ship_radius=self.ship.radius,
                )
            else:
                enemy.integrate(
                    dt,
                    self.wells,
                    gravity_scale=self.config.gravity_scale,
                    drag=self.config.drag,
                    well_maw_radius=self.config.well_maw_radius,
                )
            shot = enemy.try_fire(self.ship.pos, self.ship.vel)
            if shot is not None:
                self.projectiles.append(shot)

    def _prune_dead_enemies(self) -> None:
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]

    def _collect_beacons(self, capture_slack: float = 0.0) -> None:
        slack = max(0.0, capture_slack)
        for beacon in self.beacons:
            if beacon.collected:
                continue
            if (beacon.pos - self.ship.pos).length() <= beacon.radius + self.ship.radius + slack:
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

    def _squid_is_clinging(self) -> bool:
        for enemy in self.enemies:
            if not enemy.alive or enemy.kind is not EnemyKind.SQUID:
                continue
            assert isinstance(enemy, SquidEnemy)
            if enemy.is_clinging(self.ship.pos, self.ship.radius):
                return True
        return False

    def _check_squid_cling_damage(self, dt: float) -> None:
        if self.status is not GameStatus.RUNNING:
            return
        if not self._squid_is_clinging():
            self.squid_cling_timer = 0.0
            return
        self.squid_cling_timer += dt
        if self.squid_cling_timer < SQUID_CLING_DAMAGE_INTERVAL:
            return
        if self.invuln_remaining > 0.0:
            return
        self.squid_cling_timer = 0.0
        self._register_ship_hit(
            DamageSource.SQUID_CLING,
            reason="Void squid tentacles cling and squeeze — hull chunk lost.",
        )

    def _check_patrol_enemy_collisions(self) -> None:
        for enemy in self.enemies:
            if not enemy.alive or enemy.kind is EnemyKind.SQUID:
                continue
            if (enemy.pos - self.ship.pos).length() <= enemy.radius + self.ship.radius:
                if self.invuln_remaining > 0.0:
                    continue
                self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, Vec2(enemy.pos.x, enemy.pos.y))
                enemy.alive = False
                self._prune_dead_enemies()
                self._register_ship_hit(DamageSource.ENEMY)
                return

    def _check_enemy_collisions(self, dt: float) -> None:
        self._check_squid_cling_damage(dt)
        if self.status is GameStatus.RUNNING:
            self._check_patrol_enemy_collisions()

    def _check_finish(self) -> None:
        if self.status is not GameStatus.RUNNING:
            return
        if self.finish_unlocked and self.finish_gate.rect.intersects_circle(self.ship.pos, self.ship.radius):
            self.status = GameStatus.WON

    def _tick_chart_radiation(self, dt: float) -> None:
        if advance_chart_radiation_exposure(self, dt):
            self._register_ship_hit(
                DamageSource.CHART_RADIATION,
                reason=chart_radiation_reason(level_theme=self.config.level_theme),
            )

    def _check_loss(self) -> None:
        if self.status is not GameStatus.RUNNING:
            return
        if not self.config.open_bounds and not self._point_in_bounds(self.ship.pos, margin=0):
            self._register_ship_hit(DamageSource.OUT_OF_BOUNDS)
            return
        if self._asteroid_hit_at(self.ship.pos, self.ship.radius) is not None:
            self._register_ship_hit(DamageSource.ASTEROID)
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
