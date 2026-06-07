from __future__ import annotations


from collections.abc import Callable
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.chart_radiation import advance_chart_radiation_exposure
from gravity_ho_matey.gameplay.chart_bounds import chart_radiation_reason, ship_in_chart
from gravity_ho_matey.gameplay.damage import DamageEvent, DamageSeverity, DamageSource, damage_spec_for, default_reason
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.explosions import ExplosionKind, ExplosionSystem
from gravity_ho_matey.gameplay.asteroid_bounce import resolve_rubber_hull_bounce
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
    Projectile,
    Ship,
    WorldConfig,
)
from gravity_ho_matey.core.geometry import Rect, circle_intersects_convex_polygon
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at
from gravity_ho_matey.gameplay.jewel_drops import (
    jewel_count_for_asteroid,
    jewel_count_for_beacon,
    jewel_count_for_boss,
    jewel_count_for_enemy,
)
from gravity_ho_matey.gameplay.jewel_pickup import JewelPickup, spawn_scattered_jewels, tick_jewels
from gravity_ho_matey.gameplay.boost_lane import LaneProbe, LaneState, probe_lane
from gravity_ho_matey.gameplay.boost_pad import BoostPad, tick_boost_pads, try_trigger_pad
from gravity_ho_matey.gameplay.squid_enemy import SQUID_CLING_DAMAGE_INTERVAL, SquidEnemy
from gravity_ho_matey.gameplay.lane_physics import (
    apply_lane_centering,
    lane_modifiers,
)
from gravity_ho_matey.gameplay.friendly_fighter import FriendlyFighter
from gravity_ho_matey.gameplay.drone_config import DRONE_ASTEROID_QUERY_RADIUS
from gravity_ho_matey.gameplay.drone_wingman import DroneWingman
from gravity_ho_matey.gameplay.mega_squid_boss import MegaSquidBoss
from gravity_ho_matey.gameplay.squid_pod import SquidPod
from gravity_ho_matey.levels.membrane_layout import MembraneLayout
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
    jewels: list[JewelPickup] = field(default_factory=list)
    on_jewels_collected: Callable[[int], None] | None = None
    consume_rubber_hull_bounce: Callable[[], bool] | None = None
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
    membrane_layout: MembraneLayout | None = None
    boost_pads: list[BoostPad] = field(default_factory=list)
    mega_squid: MegaSquidBoss | None = None
    squid_pods: list[SquidPod] = field(default_factory=list)
    boss_cleared: bool = False
    lane_probe: LaneProbe | None = None
    pad_flash: float = 0.0
    boss_scrape_flash: float = 0.0
    allies: list[FriendlyFighter] = field(default_factory=list)
    drone_wingman: DroneWingman | None = None

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
    def beacons_required_for_exit(self) -> int:
        """Beacon-gated chart sectors (Cove, Solar): total beacons minus one may be skipped."""
        if not self.beacons:
            return 0
        if self.config.level_theme in ("cove", "solar"):
            return max(1, len(self.beacons) - 1)
        return len(self.beacons)

    @property
    def finish_unlocked(self) -> bool:
        if self.config.exit_requires_boss:
            return self.boss_cleared
        required = self.beacons_required_for_exit
        if required == 0:
            return True
        collected = len(self.beacons) - self.beacons_remaining
        return collected >= required

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
        self._update_allies(dt)
        self._update_drone_wingman(dt)
        self._update_boss_and_pods(dt)
        self._update_projectiles(dt)
        self.refresh_threat_snapshots()
        self._collect_beacons(beacon_capture_slack)
        self._update_jewels(dt)
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

        if self.pad_flash > 0.0:
            self.pad_flash = max(0.0, self.pad_flash - dt)
        if self.boss_scrape_flash > 0.0:
            self.boss_scrape_flash = max(0.0, self.boss_scrape_flash - dt)

        lane_probe: LaneProbe | None = None
        lane_mods = None
        gravity_scale = self.config.gravity_scale
        drag = self.config.drag
        thrust_mult = self.ship.thrust_multiplier
        max_speed = self.config.max_ship_speed

        if self.membrane_layout is not None:
            lane_probe = probe_lane(self.ship.pos, self.membrane_layout)
            self.lane_probe = lane_probe
            if lane_probe.state is LaneState.ON_RIBBON:
                lane_mods = lane_modifiers(
                    lane_probe,
                    base_drag=self.config.drag,
                    base_max_speed=self.config.max_ship_speed,
                )
                drag = lane_mods.drag
                thrust_mult *= lane_mods.thrust_mult
                max_speed = lane_mods.max_speed

        accel = gravity_acceleration_at(self.ship.pos, self.wells) * gravity_scale
        if intent.thrust:
            accel += Vec2.from_angle(self.ship.angle) * (self.config.thrust * thrust_mult)

        if lane_probe is not None and lane_mods is not None:
            accel = apply_lane_centering(accel, lane_probe, lane_mods)

        self.ship.vel = (self.ship.vel + accel * dt) * drag

        if self.membrane_layout is not None and self.boost_pads:
            tick_boost_pads(self.boost_pads, dt)
            if try_trigger_pad(
                self.boost_pads,
                self.ship,
                self.membrane_layout,
                pad_flash_seconds=self.config.pad_flash_seconds,
            ):
                self.pad_flash = self.config.pad_flash_seconds

        if intent.boost_tap and self.ship.boost_energy >= self.config.boost_energy_cost:
            forward = Vec2.from_angle(self.ship.angle)
            burst = max_speed * self.config.boost_burst_fraction * thrust_mult * self.ship.boost_tap_multiplier
            burst += max(0.0, self.ship.vel.dot(forward)) * 0.12
            self.ship.vel = self.ship.vel + forward * burst
            self.ship.boost_energy = max(0.0, self.ship.boost_energy - self.config.boost_energy_cost)
            self.ship.boost_flash = self.config.boost_flash_seconds

        overspeed = self.config.boost_overspeed_cap
        if self.pad_flash > 0.0:
            overspeed = max(overspeed, self.config.pad_overspeed_cap)
        speed_cap = max_speed * (overspeed if self.ship.boost_flash > 0.0 or self.pad_flash > 0.0 else 1.0)
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
            drop_count = jewel_count_for_asteroid(asteroid)
            if drop_count > 0:
                self._spawn_jewels_at(asteroid.pos, drop_count)
        if result.asteroids_added:
            self.asteroids.extend(result.asteroids_added)
        if result.snapshots_dirty:
            self.asteroid_spatial.rebuild(self.asteroids)
            self.refresh_threat_snapshots()

    def _spawn_jewels_at(self, pos: Vec2, count: int) -> None:
        self.jewels.extend(spawn_scattered_jewels(pos, count))

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
                if self._projectile_hits_drone(projectile):
                    continue
            elif self._projectile_hits_ally(projectile):
                continue
            elif self._projectile_hits_boss(projectile):
                continue
            elif self._projectile_hits_enemy(projectile, drop_loot=not projectile.from_ally):
                continue
            kept.append(projectile)
        self.projectiles = kept

    def _projectile_hits_enemy(self, projectile: Projectile, *, drop_loot: bool = True) -> bool:
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
                    if drop_loot:
                        drop_count = jewel_count_for_enemy(enemy)
                        if drop_count > 0:
                            self._spawn_jewels_at(enemy_pos, drop_count)
                    self._prune_dead_enemies()
                return True
            if (enemy.pos - projectile.pos).length() <= enemy.radius + projectile.radius:
                hit_pos = Vec2(projectile.pos.x, projectile.pos.y)
                enemy_pos = Vec2(enemy.pos.x, enemy.pos.y)
                enemy.alive = False
                self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, hit_pos)
                self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, enemy_pos)
                if drop_loot:
                    drop_count = jewel_count_for_enemy(enemy)
                    if drop_count > 0:
                        self._spawn_jewels_at(enemy_pos, drop_count)
                self._prune_dead_enemies()
                return True
        return False

    def _projectile_hits_boss(self, projectile: Projectile) -> bool:
        boss = self.mega_squid
        if boss is None or not boss.alive or projectile.hostile:
            return False
        if not boss.body_hit_by_projectile(projectile.pos, projectile.radius):
            return False
        hit_pos = Vec2(projectile.pos.x, projectile.pos.y)
        self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, hit_pos)
        if boss.apply_shot():
            self._on_boss_defeated()
        return True

    def _on_boss_defeated(self) -> None:
        boss = self.mega_squid
        if boss is None:
            return
        boss_pos = Vec2(boss.pos.x, boss.pos.y)
        self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, boss_pos, scale=2.4)
        drop_count = jewel_count_for_boss(boss.anchor)
        if drop_count > 0:
            self._spawn_jewels_at(boss_pos, drop_count)
        self.boss_cleared = True
        gate_half = 34.0
        portal_y = boss.anchor.y - 90.0
        self.finish_gate = FinishGate(
            Rect(
                boss.anchor.x - gate_half,
                portal_y - gate_half,
                gate_half * 2.0,
                gate_half * 2.0,
            )
        )

    def _update_boss_and_pods(self, dt: float) -> None:
        boss = self.mega_squid
        if boss is not None and boss.alive:
            boss.integrate(
                dt,
                self.wells,
                gravity_scale=self.config.gravity_scale,
                drag=self.config.drag,
            )
            alive_squids = sum(1 for e in self.enemies if e.alive and e.kind is EnemyKind.SQUID)
            squid, pod = boss.tick_spawns(dt, self.ship.pos, alive_squids)
            if squid is not None:
                self.enemies.append(squid)
            if pod is not None:
                self.squid_pods.append(pod)
            if (
                self.status is GameStatus.RUNNING
                and (boss.pos - self.ship.pos).length() <= boss.radius + self.ship.radius
                and self.invuln_remaining <= 0.0
            ):
                self.boss_scrape_flash = 0.45
                self._register_ship_hit(DamageSource.ENEMY, reason="Brood-Mother hull scrape — chunk lost.")

        kept_pods: list[SquidPod] = []
        for pod in self.squid_pods:
            if not pod.alive:
                continue
            if pod.tick(dt):
                self.enemies.append(
                    SquidEnemy(
                        pos=Vec2(pod.pos.x, pod.pos.y),
                        tentacle_reach=62.0,
                        max_speed=185.0,
                        detect_range=760.0,
                        engage_range=620.0,
                    )
                )
            else:
                kept_pods.append(pod)
        self.squid_pods = kept_pods

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

    def _update_allies(self, dt: float) -> None:
        if not self.allies:
            return
        for ally in self.allies:
            if not ally.alive:
                continue
            ally.tick_combat(dt)
            if ally.boost_flash > 0.0:
                ally.boost_flash = max(0.0, ally.boost_flash - dt)
            threat = ally.pick_threat(self.enemies, self.mega_squid)
            gravity_scale = self.config.gravity_scale
            drag = self.config.drag
            thrust_mult = 1.0
            lane_probe: LaneProbe | None = None
            lane_mods = None
            pad_overspeed = self.config.boost_overspeed_cap
            if self.membrane_layout is not None:
                lane_probe = probe_lane(ally.pos, self.membrane_layout)
                if lane_probe.state is LaneState.ON_RIBBON:
                    lane_mods = lane_modifiers(
                        lane_probe,
                        base_drag=self.config.drag,
                        base_max_speed=self.config.max_ship_speed,
                    )
                    drag = lane_mods.drag
                    thrust_mult = lane_mods.thrust_mult
                if self.boost_pads:
                    try_trigger_pad(
                        self.boost_pads,
                        ally,
                        self.membrane_layout,
                        pad_flash_seconds=self.config.pad_flash_seconds,
                    )
                if ally.boost_flash > 0.0:
                    pad_overspeed = max(pad_overspeed, self.config.pad_overspeed_cap)
            ally.integrate(
                dt,
                player_pos=self.ship.pos,
                player_vel=self.ship.vel,
                player_angle=self.ship.angle,
                wells=self.wells,
                gravity_scale=gravity_scale,
                drag=drag,
                well_maw_radius=self.config.well_maw_radius,
                threat=threat,
                lane_probe=lane_probe,
                lane_mods=lane_mods,
                thrust_mult=thrust_mult,
                pad_overspeed_cap=pad_overspeed,
            )
            shot = ally.try_fire(threat)
            if shot is not None:
                self.projectiles.append(shot)
        self._check_ally_hazards()
        self._prune_dead_allies()

    def _nearby_asteroids_for_drone(self, pos: Vec2) -> list[Asteroid]:
        if self.asteroid_spatial.populated:
            return self.asteroid_spatial.query_circle(pos, DRONE_ASTEROID_QUERY_RADIUS)
        out: list[Asteroid] = []
        reach_sq = (DRONE_ASTEROID_QUERY_RADIUS + 48.0) ** 2
        for asteroid in self.asteroids:
            if (asteroid.pos - pos).length_sq() <= reach_sq:
                out.append(asteroid)
        return out

    def _update_drone_wingman(self, dt: float) -> None:
        drone = self.drone_wingman
        if drone is None or not drone.alive:
            return
        drone.tick_combat(dt)
        nearby_asteroids = self._nearby_asteroids_for_drone(drone.pos)
        threat = drone.pick_threat(
            self.enemies,
            self.mega_squid,
            player_pos=self.ship.pos,
            asteroids=nearby_asteroids,
        )
        drone.integrate(
            dt,
            player_pos=self.ship.pos,
            player_vel=self.ship.vel,
            player_angle=self.ship.angle,
            wells=self.wells,
            gravity_scale=self.config.gravity_scale,
            drag=self.config.drag,
            well_maw_radius=self.config.well_maw_radius,
            threat=threat,
            asteroids=nearby_asteroids,
            enemies=self.enemies,
            hostile_projectiles=[p for p in self.projectiles if p.hostile],
        )
        shot = drone.try_fire(threat)
        if shot is not None:
            self.projectiles.append(shot)
        self._check_drone_hazards()
        if not drone.alive:
            self.drone_wingman = None

    def _projectile_hits_drone(self, projectile: Projectile) -> bool:
        drone = self.drone_wingman
        if drone is None or not drone.alive:
            return False
        if not drone.body_hit_by_projectile(projectile.pos, projectile.radius):
            return False
        self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, Vec2(projectile.pos.x, projectile.pos.y))
        if drone.apply_shot():
            self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, Vec2(drone.pos.x, drone.pos.y), scale=0.75)
            self.drone_wingman = None
        return True

    def _check_drone_hazards(self) -> None:
        if self.status is not GameStatus.RUNNING:
            return
        drone = self.drone_wingman
        if drone is None or not drone.alive or drone.hit_invuln > 0.0:
            return
        if self._asteroid_hit_at(drone.pos, drone.radius) is not None:
            self.explosions.spawn(ExplosionKind.SHIP_STRUCK, Vec2(drone.pos.x, drone.pos.y), scale=0.7)
            if drone.apply_shot():
                self.drone_wingman = None
            return
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if enemy.kind is EnemyKind.SQUID:
                assert isinstance(enemy, SquidEnemy)
                gap = (enemy.pos - drone.pos).length() - enemy.tentacle_span() - drone.radius
                if gap > 6.0:
                    continue
            elif (enemy.pos - drone.pos).length() > enemy.radius + drone.radius + 4.0:
                continue
            self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, Vec2(drone.pos.x, drone.pos.y), scale=0.65)
            if drone.apply_shot():
                self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, Vec2(drone.pos.x, drone.pos.y), scale=0.75)
                self.drone_wingman = None
            return

    def _projectile_hits_ally(self, projectile: Projectile) -> bool:
        """Player bolts dissipate on allies — no friendly fire damage."""
        if projectile.hostile or projectile.from_ally:
            return False
        for ally in self.allies:
            if not ally.alive:
                continue
            if not ally.body_hit_by_projectile(projectile.pos, projectile.radius):
                continue
            self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, Vec2(projectile.pos.x, projectile.pos.y))
            return True
        drone = self.drone_wingman
        if drone is not None and drone.alive and drone.body_hit_by_projectile(projectile.pos, projectile.radius):
            self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, Vec2(projectile.pos.x, projectile.pos.y))
            return True
        return False

    def _check_ally_hazards(self) -> None:
        if self.status is not GameStatus.RUNNING:
            return
        for ally in self.allies:
            if not ally.alive:
                continue
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if (enemy.pos - ally.pos).length() > enemy.radius + ally.radius:
                    continue
                self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, Vec2(ally.pos.x, ally.pos.y), scale=0.85)
                ally.alive = False
                if enemy.kind is EnemyKind.SQUID:
                    assert isinstance(enemy, SquidEnemy)
                    enemy.alive = False
                    self._prune_dead_enemies()
                break

    def _prune_dead_allies(self) -> None:
        self.allies = [ally for ally in self.allies if ally.alive]

    def _prune_dead_enemies(self) -> None:
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]

    def _collect_beacons(self, capture_slack: float = 0.0) -> None:
        slack = max(0.0, capture_slack)
        for beacon in self.beacons:
            if beacon.collected:
                continue
            if (beacon.pos - self.ship.pos).length() <= beacon.radius + self.ship.radius + slack:
                beacon.collected = True
                drop_count = jewel_count_for_beacon(beacon.pos)
                self._spawn_jewels_at(beacon.pos, drop_count)

    def _update_jewels(self, dt: float) -> None:
        if not self.jewels:
            return
        allow_collect = self.on_jewels_collected is not None
        self.jewels, collected = tick_jewels(
            self.jewels,
            self.ship.pos,
            self.ship.radius,
            dt,
            allow_collect=allow_collect,
        )
        if collected > 0 and allow_collect:
            self.on_jewels_collected(collected)
            fx_scale = 0.55 + min(collected, 6) * 0.1
            self.explosions.spawn(
                ExplosionKind.JEWEL_COLLECT,
                Vec2(self.ship.pos.x, self.ship.pos.y),
                scale=fx_scale,
            )

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
        asteroid = self._asteroid_hit_at(self.ship.pos, self.ship.radius)
        if asteroid is not None:
            if self.consume_rubber_hull_bounce and self.consume_rubber_hull_bounce():
                resolve_rubber_hull_bounce(self.ship, asteroid)
                return
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
