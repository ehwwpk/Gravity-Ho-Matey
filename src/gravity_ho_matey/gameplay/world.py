from __future__ import annotations


from collections.abc import Callable
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.chart_radiation import advance_chart_radiation_exposure
from gravity_ho_matey.gameplay.chart_bounds import chart_radiation_reason, ship_in_chart
from gravity_ho_matey.gameplay.damage import DamageEvent, DamageSeverity, DamageSource, damage_spec_for, default_reason
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.hostile_fighter import HostileFighter
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
from gravity_ho_matey.gameplay.squid_enemy import SQUID_CLING_DAMAGE_INTERVAL, SquidEnemy
from gravity_ho_matey.gameplay.friendly_fighter import FriendlyFighter
from gravity_ho_matey.gameplay.friendly_fighter_config import ALLY_ASTEROID_QUERY_RADIUS
from gravity_ho_matey.gameplay.drone_config import DRONE_ASTEROID_QUERY_RADIUS
from gravity_ho_matey.gameplay.drone_wingman import DroneWingman
from gravity_ho_matey.gameplay.nifflerp import Nifflerp
from gravity_ho_matey.gameplay.nifflerp_config import NIFFLERP_ASTEROID_QUERY_RADIUS
from gravity_ho_matey.gameplay.mega_squid_boss import MegaSquidBoss
from gravity_ho_matey.gameplay.space_station import SpaceStation
from gravity_ho_matey.gameplay.tractor_beam import TractorBeamState
from gravity_ho_matey.gameplay.squid_pod import SquidPod
from gravity_ho_matey.gameplay.wave_director import WaveDirector
from gravity_ho_matey.gameplay.egg_pod_objective import EggPodObjective
from gravity_ho_matey.gameplay.brood_moon_mission import BroodMoonState, BroodPhase
from gravity_ho_matey.gameplay.brood_moon_controller import (
    on_egg_pod_destroyed,
    surface_gravity_accel,
    tick_brood_moon,
)
from gravity_ho_matey.levels.guard_layout import GuardLayout
from gravity_ho_matey.levels.guard_waves import wave_spawn_for
from gravity_ho_matey.gameplay.asteroid_spatial import AsteroidSpatialGrid
from gravity_ho_matey.gameplay.threat_snapshot import AsteroidThreatSnapshot, build_asteroid_threat_snapshots
from gravity_ho_matey.gameplay.weapon_combat import HitDisposition, apply_explosive_burst, resolve_projectile_after_hit, spawn_weapon_hit_fx
from gravity_ho_matey.gameplay.weapon_fire import player_fire_cooldown, spawn_player_shots
from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack

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
    mega_squid: MegaSquidBoss | None = None
    squid_pods: list[SquidPod] = field(default_factory=list)
    boss_cleared: bool = False
    boss_tagged_by_player: bool = False
    protection_wave_alert_ttl: float = 0.0
    protection_hold_complete_ttl: float = 0.0
    relay_repair_hold: float = 0.0
    relay_repair_charges_used: int = 0
    _protection_was_cleared: bool = False
    boss_scrape_flash: float = 0.0
    allies: list[FriendlyFighter] = field(default_factory=list)
    drone_wingman: DroneWingman | None = None
    nifflerp: Nifflerp | None = None
    space_station: SpaceStation | None = None
    friendly_stations: list[SpaceStation] = field(default_factory=list)
    guard_layout: GuardLayout | None = None
    wave_director: WaveDirector | None = None
    station_cling_timers: dict[str, float] = field(default_factory=dict)
    tractor_beam: TractorBeamState | None = None
    station_cleared: bool = False
    roster_enemies_total: int = 0
    roster_enemies_remaining: int = 0
    egg_pods: list[EggPodObjective] = field(default_factory=list)
    brood_moon: BroodMoonState | None = None
    player_weapon_track: WeaponTrack | None = None
    player_weapon_advanced: bool = False

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
    def egg_pods_remaining(self) -> int:
        return sum(1 for pod in self.egg_pods if pod.alive)

    @property
    def finish_unlocked(self) -> bool:
        if self.config.brood_moon_mission and self.brood_moon is not None:
            bm = self.brood_moon
            if bm.phase is BroodPhase.ORBITAL_RETURN:
                return bm.dock_unlocked and bm.seal_complete
            return False
        if self.config.protection_mission:
            return self.protection_combat_cleared
        if self.config.exit_requires_roster_clear:
            return self.roster_enemies_remaining <= 0
        if self.config.exit_requires_boss:
            return self.boss_cleared
        required = self.beacons_required_for_exit
        if required == 0:
            return True
        collected = len(self.beacons) - self.beacons_remaining
        return collected >= required

    @property
    def protection_combat_cleared(self) -> bool:
        """All waves fired, relay alive, hostiles cleared — extract pad unlocks."""
        if not self.config.protection_mission:
            return False
        if self.wave_director is None or not self.wave_director.all_waves_fired:
            return False
        if not self.friendly_stations or not all(station.alive for station in self.friendly_stations):
            return False
        if any(enemy.alive for enemy in self.enemies):
            return False
        if any(pod.alive for pod in self.squid_pods):
            return False
        return True

    def protection_hostiles_alive(self) -> int:
        return sum(1 for enemy in self.enemies if enemy.alive)

    def _boss_alive(self) -> bool:
        boss = self.mega_squid
        return boss is not None and boss.alive

    @property
    def protection_mission_won(self) -> bool:
        return self.protection_combat_cleared

    @property
    def roster_enemies_defeated(self) -> int:
        return max(0, self.roster_enemies_total - self.roster_enemies_remaining)

    def update(self, dt: float, intent: ControlIntent, *, beacon_capture_slack: float = 0.0, interaction_hold: bool = False) -> bool:
        """Advance simulation. Returns True when gravity field should be rebaked (brood moon phase swap)."""
        dt = max(0.0, min(dt, 1.0 / 20.0))
        self.elapsed += dt
        self.explosions.update(dt)
        if self.status is not GameStatus.RUNNING:
            return False

        rebake_gravity = False
        if self.brood_moon is not None:
            if self.brood_moon.in_cinematic:
                rebake_gravity = tick_brood_moon(self, dt, interaction_hold=interaction_hold)
                return rebake_gravity
            rebake_gravity = tick_brood_moon(self, dt, interaction_hold=interaction_hold)

        self._tick_invuln(dt)
        self._update_tractor_beam(dt)
        self._update_asteroids(dt)
        self.asteroid_spatial.rebuild(self.asteroids)
        self._update_ship(dt, intent)
        self._tick_wave_director(dt)
        self._tick_protection_relay_repair(interaction_hold, dt)
        self._update_enemies(dt)
        self._update_allies(dt)
        self._update_drone_wingman(dt)
        self._update_nifflerp(dt)
        self._update_boss_and_pods(dt)
        self._update_space_station(dt)
        self._update_friendly_stations(dt)
        self._update_projectiles(dt)
        self.refresh_threat_snapshots()
        self._collect_beacons(beacon_capture_slack)
        self._update_jewels(dt)
        self._check_squid_cling_damage(dt)
        self._check_station_squid_cling_damage(dt)
        if self.status is GameStatus.RUNNING:
            self._check_patrol_enemy_collisions()
        self._check_finish()
        if self.protection_wave_alert_ttl > 0.0:
            self.protection_wave_alert_ttl = max(0.0, self.protection_wave_alert_ttl - dt)
        if self.protection_hold_complete_ttl > 0.0:
            self.protection_hold_complete_ttl = max(0.0, self.protection_hold_complete_ttl - dt)
        cleared = self.protection_combat_cleared
        if self.config.protection_mission:
            if cleared and not self._protection_was_cleared:
                self.protection_hold_complete_ttl = 2.5
            self._protection_was_cleared = cleared
        self._tick_chart_radiation(dt)
        self._check_loss()
        for pod in self.egg_pods:
            if pod.alive:
                pod.tick(dt)
        return rebake_gravity

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
        if self.ship.boost_jolt > 0.0:
            self.ship.boost_jolt = max(0.0, self.ship.boost_jolt - dt)
        self.ship.boost_energy = min(
            1.0,
            self.ship.boost_energy + self.config.boost_regen_rate * dt,
        )

        if self.boss_scrape_flash > 0.0:
            self.boss_scrape_flash = max(0.0, self.boss_scrape_flash - dt)

        from gravity_ho_matey.gameplay.planetside_flight import (
            PLANETSIDE_BOOST_FX_SCALE,
            PLANETSIDE_BURST_FORWARD_DOT,
            PLANETSIDE_DRAG_WHILE_BOOST,
            PLANETSIDE_JOLT_SECONDS,
            is_planetside,
        )

        planetside = is_planetside(self.config)
        gravity_scale = self.config.gravity_scale
        drag = self.config.drag
        if planetside and self.ship.boost_flash > 0.0:
            drag = PLANETSIDE_DRAG_WHILE_BOOST
        thrust_mult = self.ship.thrust_multiplier
        max_speed = self.config.max_ship_speed

        accel = gravity_acceleration_at(self.ship.pos, self.wells) * gravity_scale
        surface_pull = surface_gravity_accel(self)
        if surface_pull is not None:
            accel += surface_pull
        if intent.thrust:
            accel += Vec2.from_angle(self.ship.angle) * (self.config.thrust * thrust_mult)

        self.ship.vel = (self.ship.vel + accel * dt) * drag

        if intent.boost_tap and self.ship.boost_energy >= self.config.boost_energy_cost:
            forward = Vec2.from_angle(self.ship.angle)
            burst = max_speed * self.config.boost_burst_fraction * thrust_mult * self.ship.boost_tap_multiplier
            forward_dot = PLANETSIDE_BURST_FORWARD_DOT if planetside else 0.12
            burst += max(0.0, self.ship.vel.dot(forward)) * forward_dot
            self.ship.vel = self.ship.vel + forward * burst
            self.ship.boost_energy = max(0.0, self.ship.boost_energy - self.config.boost_energy_cost)
            self.ship.boost_flash = self.config.boost_flash_seconds
            if planetside:
                self.ship.boost_jolt = PLANETSIDE_JOLT_SECONDS
                tail = self.ship.pos - forward * (self.ship.radius + 5.0)
                self.explosions.spawn(
                    ExplosionKind.REACTOR_BURST,
                    tail,
                    scale=PLANETSIDE_BOOST_FX_SCALE,
                )

        overspeed = self.config.boost_overspeed_cap
        speed_cap = max_speed * (overspeed if self.ship.boost_flash > 0.0 else 1.0)
        self.ship.vel = self.ship.vel.clamped_length(speed_cap)
        self.ship.pos = self.ship.pos + self.ship.vel * dt
        self.ship.cooldown = max(0.0, self.ship.cooldown - dt)

        if intent.fire and self.ship.cooldown <= 0.0:
            self.fire_projectile()

    def fire_projectile(self) -> None:
        shots = spawn_player_shots(
            ship_pos=self.ship.pos,
            ship_vel=self.ship.vel,
            ship_angle=self.ship.angle,
            ship_radius=self.ship.radius,
            projectile_speed=self.config.projectile_speed,
            track=self.player_weapon_track,
            advanced=self.player_weapon_advanced,
        )
        self.projectiles.extend(shots)
        self.ship.cooldown = player_fire_cooldown(
            self.config.ship_fire_cooldown,
            self.ship.fire_cooldown_multiplier,
            self.player_weapon_track,
            advanced=self.player_weapon_advanced,
        )

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
                if projectile.explosive_radius > 0.0:
                    apply_explosive_burst(
                        self,
                        impact,
                        projectile.explosive_radius,
                        drop_loot=not projectile.from_ally,
                    )
                else:
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
                if self._projectile_hits_friendly_stations(projectile):
                    continue
                if self._projectile_hits_ship(projectile):
                    continue
                if self._projectile_hits_ally_hostile(projectile):
                    continue
                if self._projectile_hits_drone(projectile):
                    continue
                if self._projectile_hits_nifflerp(projectile):
                    continue
            elif self._projectile_hits_ally(projectile):
                continue
            else:
                disposition = self._projectile_hits_boss(projectile)
                if disposition != "none":
                    if disposition == "pierce":
                        kept.append(projectile)
                    continue
                disposition = self._projectile_hits_station(projectile)
                if disposition != "none":
                    if disposition == "pierce":
                        kept.append(projectile)
                    continue
                disposition = self._projectile_hits_enemy(projectile, drop_loot=not projectile.from_ally)
                if disposition != "none":
                    if disposition == "pierce":
                        kept.append(projectile)
                    continue
                disposition = self._projectile_hits_egg_pods(projectile)
                if disposition != "none":
                    if disposition == "pierce":
                        kept.append(projectile)
                    continue
                disposition = self._projectile_hits_squid_pods(projectile)
                if disposition != "none":
                    if disposition == "pierce":
                        kept.append(projectile)
                    continue
            kept.append(projectile)
        self.projectiles = kept

    def _projectile_hits_enemy(self, projectile: Projectile, *, drop_loot: bool = True) -> HitDisposition:
        if projectile.hostile:
            return "none"
        if projectile.explosive_radius > 0.0:
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if (enemy.pos - projectile.pos).length() <= enemy.radius + projectile.radius:
                    apply_explosive_burst(
                        self,
                        Vec2(projectile.pos.x, projectile.pos.y),
                        projectile.explosive_radius,
                        drop_loot=drop_loot,
                    )
                    return "consume"
            return "none"
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if enemy.kind is EnemyKind.SQUID:
                assert isinstance(enemy, SquidEnemy)
                if not enemy.body_hit_by_projectile(projectile.pos, projectile.radius):
                    continue
                hit_pos = Vec2(projectile.pos.x, projectile.pos.y)
                piercing = projectile.pierce_remaining > 0 and projectile.explosive_radius <= 0.0
                spawn_weapon_hit_fx(self, hit_pos, projectile, piercing=piercing)
                if enemy.apply_shot():
                    enemy_pos = Vec2(enemy.pos.x, enemy.pos.y)
                    enemy.alive = False
                    self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, enemy_pos)
                    if drop_loot:
                        drop_count = jewel_count_for_enemy(enemy)
                        if drop_count > 0:
                            self._spawn_jewels_at(enemy_pos, drop_count)
                    self._register_roster_kill(enemy)
                    self._prune_dead_enemies()
                return resolve_projectile_after_hit(projectile, hit=True)
            if (enemy.pos - projectile.pos).length() <= enemy.radius + projectile.radius:
                hit_pos = Vec2(projectile.pos.x, projectile.pos.y)
                enemy_pos = Vec2(enemy.pos.x, enemy.pos.y)
                piercing = projectile.pierce_remaining > 0 and projectile.explosive_radius <= 0.0
                spawn_weapon_hit_fx(self, hit_pos, projectile, piercing=piercing)
                enemy.alive = False
                self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, enemy_pos)
                if drop_loot:
                    drop_count = jewel_count_for_enemy(enemy)
                    if drop_count > 0:
                        self._spawn_jewels_at(enemy_pos, drop_count)
                self._register_roster_kill(enemy)
                self._prune_dead_enemies()
                return resolve_projectile_after_hit(projectile, hit=True)
        return "none"

    def _projectile_hits_squid_pods(self, projectile: Projectile) -> HitDisposition:
        if projectile.hostile or not self.squid_pods:
            return "none"
        if projectile.explosive_radius > 0.0:
            for pod in self.squid_pods:
                if not pod.alive:
                    continue
                if (pod.pos - projectile.pos).length() <= pod.hit_radius() + projectile.radius:
                    apply_explosive_burst(
                        self,
                        Vec2(projectile.pos.x, projectile.pos.y),
                        projectile.explosive_radius,
                        drop_loot=not projectile.from_ally,
                    )
                    return "consume"
            return "none"
        for pod in self.squid_pods:
            if not pod.alive:
                continue
            if (pod.pos - projectile.pos).length() > pod.hit_radius() + projectile.radius:
                continue
            hit_pos = Vec2(pod.pos.x, pod.pos.y)
            self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, hit_pos)
            pod.alive = False
            return resolve_projectile_after_hit(projectile, hit=True)
        return "none"

    def _projectile_hits_egg_pods(self, projectile: Projectile) -> HitDisposition:
        if projectile.hostile or not self.egg_pods:
            return "none"
        if projectile.explosive_radius > 0.0:
            for pod in self.egg_pods:
                if not pod.alive:
                    continue
                if (pod.pos - projectile.pos).length() <= pod.radius + projectile.radius:
                    apply_explosive_burst(
                        self,
                        Vec2(projectile.pos.x, projectile.pos.y),
                        projectile.explosive_radius,
                        drop_loot=not projectile.from_ally,
                    )
                    return "consume"
            return "none"
        for pod in self.egg_pods:
            if not pod.alive:
                continue
            if (pod.pos - projectile.pos).length() > pod.radius + projectile.radius:
                continue
            hit_pos = Vec2(projectile.pos.x, projectile.pos.y)
            piercing = projectile.pierce_remaining > 0 and projectile.explosive_radius <= 0.0
            spawn_weapon_hit_fx(self, hit_pos, projectile, piercing=piercing)
            if pod.apply_shot():
                self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, Vec2(pod.pos.x, pod.pos.y), scale=1.6)
                on_egg_pod_destroyed(self, pod)
            return resolve_projectile_after_hit(projectile, hit=True)
        return "none"

    def _register_roster_kill(self, enemy: EnemyUnit) -> None:
        if not self.config.exit_requires_roster_clear:
            return
        roster_id = getattr(enemy, "skirmish_roster_id", None)
        if roster_id is None:
            return
        self.roster_enemies_remaining = max(0, self.roster_enemies_remaining - 1)

    def _register_mission_fail(self, reason: str) -> None:
        self.last_damage = DamageEvent(source=DamageSource.MISSION_FAIL, reason=reason)
        self.status = GameStatus.SHIP_HIT

    def _on_friendly_station_lost(self, station: SpaceStation) -> None:
        station_pos = Vec2(station.pos.x, station.pos.y)
        self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, station_pos, scale=2.0)
        label = station.station_label
        self._register_mission_fail(f"Relay {label} destroyed — sector overrun.")

    def _projectile_hits_friendly_stations(self, projectile: Projectile) -> bool:
        if not projectile.hostile or not self.friendly_stations:
            return False
        for station in self.friendly_stations:
            if not station.alive:
                continue
            if not station.body_hit_by_projectile(projectile.pos, projectile.radius):
                continue
            hit_pos = Vec2(projectile.pos.x, projectile.pos.y)
            if projectile.explosive_radius > 0.0:
                apply_explosive_burst(
                    self,
                    hit_pos,
                    projectile.explosive_radius,
                    drop_loot=False,
                )
                return True
            self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, hit_pos)
            if station.apply_shot():
                self._on_friendly_station_lost(station)
            return True
        return False

    def _projectile_hits_station(self, projectile: Projectile) -> HitDisposition:
        station = self.space_station
        if station is None or not station.alive or projectile.hostile:
            return "none"
        if not station.body_hit_by_projectile(projectile.pos, projectile.radius):
            return "none"
        hit_pos = Vec2(projectile.pos.x, projectile.pos.y)
        if projectile.explosive_radius > 0.0:
            apply_explosive_burst(
                self,
                hit_pos,
                projectile.explosive_radius,
                drop_loot=not projectile.from_ally,
            )
            return "consume"
        self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, hit_pos)
        if station.apply_shot():
            self._on_station_defeated()
        return resolve_projectile_after_hit(projectile, hit=True)

    def _on_station_defeated(self) -> None:
        station = self.space_station
        if station is None:
            return
        station_pos = Vec2(station.pos.x, station.pos.y)
        self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, station_pos, scale=2.0)
        drop_count = 10 + int(station.anchor.x) % 5
        self._spawn_jewels_at(station_pos, drop_count)
        self.station_cleared = True

    def _update_tractor_beam(self, dt: float) -> None:
        station = self.space_station
        tractor = self.tractor_beam
        if station is None or tractor is None or not station.alive:
            return
        station.tick_tractor(
            dt,
            tractor,
            self.asteroids,
            self.ship.pos,
            self.allies,
        )

    def _update_space_station(self, dt: float) -> None:
        station = self.space_station
        if station is None or not station.alive:
            return
        station.integrate(
            dt,
            self.wells,
            gravity_scale=self.config.gravity_scale,
            drag=self.config.drag,
        )
        station.tick_combat(dt)
        drone = self.drone_wingman
        drone_pos = drone.pos if drone is not None and drone.alive else None
        shot = station.try_fire(
            self.ship.pos,
            self.ship.vel,
            self.allies,
            drone_pos=drone_pos,
        )
        if shot is not None:
            self.projectiles.append(shot)
        alive_patrols = sum(
            1
            for e in self.enemies
            if e.alive
            and e.kind is not EnemyKind.SQUID
            and getattr(e, "skirmish_roster_id", None) is None
        )
        spawned = station.tick_spawns(dt, alive_patrols)
        if spawned is not None:
            self.enemies.append(spawned)

    def _station_ally_count(self, station: SpaceStation) -> int:
        low = 100 if station.station_label in ("ALPHA", "RELAY") else 200
        high = 200 if station.station_label in ("ALPHA", "RELAY") else 300
        return sum(1 for ally in self.allies if ally.alive and low <= ally.wing_id < high)

    def _update_friendly_stations(self, dt: float) -> None:
        if not self.friendly_stations:
            return
        for station in self.friendly_stations:
            if not station.alive:
                continue
            station.integrate(
                dt,
                self.wells,
                gravity_scale=self.config.gravity_scale,
                drag=self.config.drag,
            )
            station.tick_combat(dt)
            shot = station.try_fire_at_hostiles(
                self.enemies,
                boss=self.mega_squid,
                prioritize_boss=self._boss_alive() and not self.config.protection_mission,
            )
            if shot is not None:
                self.projectiles.append(shot)
            spawned = station.tick_friendly_spawns(dt, self._station_ally_count(station))
            if spawned is not None:
                self.allies.append(spawned)

    def _relay_homeward(self) -> tuple[Vec2 | None, float]:
        if not self.config.protection_mission or self.guard_layout is None:
            return None, 0.0
        return self.guard_layout.station_anchor, 380.0

    def _apply_relay_squid_ingress(self, squid: SquidEnemy) -> None:
        if self.guard_layout is None:
            return
        from gravity_ho_matey.levels.guard_layout import RELAY_INGRESS_SQUID_SPEED
        from gravity_ho_matey.levels.guard_waves import relay_ingress_velocity

        station = self.guard_layout.station_anchor
        squid.vel = relay_ingress_velocity(squid.pos, station, RELAY_INGRESS_SQUID_SPEED * 0.9)
        squid.approach_thrust = max(squid.approach_thrust, 580.0)
        squid.max_speed = max(squid.max_speed, 220.0)

    def _tick_wave_director(self, dt: float) -> None:
        if self.wave_director is None or self.guard_layout is None:
            return
        if self.status is not GameStatus.RUNNING:
            return
        self.wave_director.tick(self.elapsed, dt)
        hostiles = self.protection_hostiles_alive()
        while True:
            wave = self.wave_director.poll_spawn(self.elapsed, hostiles_alive=hostiles)
            if wave is None:
                break
            spawned = wave_spawn_for(self.guard_layout, wave)
            self.enemies.extend(spawned)
            hostiles = self.protection_hostiles_alive()
            if wave == 3:
                self.protection_wave_alert_ttl = 3.0
            if wave >= 2 and self.friendly_stations:
                for station in self.friendly_stations:
                    station.spawn_interval = 15.5

    def _tick_protection_relay_repair(self, interaction_hold: bool, dt: float) -> None:
        if not self.config.protection_mission or self.status is not GameStatus.RUNNING:
            self.relay_repair_hold = 0.0
            return
        if not self.friendly_stations or self.protection_hostiles_alive() > 0:
            self.relay_repair_hold = 0.0
            return
        if self.wave_director is None:
            return
        waves = self.wave_director.waves_spawned
        if waves < 1 or waves >= self.wave_director.total_waves:
            self.relay_repair_hold = 0.0
            return
        if self.relay_repair_charges_used >= waves:
            self.relay_repair_hold = 0.0
            return
        station = self.friendly_stations[0]
        if not station.alive or station.hits_remaining >= station.hits_max:
            self.relay_repair_hold = 0.0
            return
        if (self.ship.pos - station.pos).length() > 140.0:
            self.relay_repair_hold = 0.0
            return
        if not interaction_hold:
            self.relay_repair_hold = 0.0
            return
        self.relay_repair_hold += dt
        if self.relay_repair_hold < 2.0:
            return
        self.relay_repair_hold = 0.0
        self.relay_repair_charges_used += 1
        station.hits_remaining = min(station.hits_max, station.hits_remaining + 1)
        self.explosions.spawn(ExplosionKind.REACTOR_BURST, Vec2(station.pos.x, station.pos.y), scale=1.15)

    def _check_station_squid_cling_damage(self, dt: float) -> None:
        if self.status is not GameStatus.RUNNING or not self.friendly_stations:
            return
        for station in self.friendly_stations:
            if not station.alive:
                continue
            clinging = False
            for enemy in self.enemies:
                if not enemy.alive or enemy.kind is not EnemyKind.SQUID:
                    continue
                assert isinstance(enemy, SquidEnemy)
                if enemy.is_clinging(station.pos, station.radius):
                    clinging = True
                    break
            key = station.station_label
            if not clinging:
                self.station_cling_timers[key] = 0.0
                continue
            timer = self.station_cling_timers.get(key, 0.0) + dt
            self.station_cling_timers[key] = timer
            if timer < SQUID_CLING_DAMAGE_INTERVAL:
                continue
            self.station_cling_timers[key] = 0.0
            self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, Vec2(station.pos.x, station.pos.y))
            if station.apply_shot():
                self._on_friendly_station_lost(station)

    def _check_finish(self) -> None:
        if self.status is not GameStatus.RUNNING:
            return
        if self.config.protection_mission and not self.protection_combat_cleared:
            return
        if self.finish_unlocked and self.finish_gate.rect.intersects_circle(self.ship.pos, self.ship.radius):
            self.status = GameStatus.WON

    def _apply_boss_combat_hit(self, boss: MegaSquidBoss, *, tag_player: bool = False) -> bool:
        """Apply one chip of boss damage and resolve phase transition FX. Returns True if killed."""
        if boss.is_damage_immune():
            return False
        if tag_player:
            self.boss_tagged_by_player = True
        if boss.apply_shot():
            self._on_boss_defeated()
            return True
        if boss.phase_shift_pending:
            boss.phase_shift_pending = False
            self.explosions.spawn(
                ExplosionKind.REACTOR_BURST,
                Vec2(boss.pos.x, boss.pos.y),
                scale=1.85,
            )
        return False

    def _projectile_hits_boss(self, projectile: Projectile) -> HitDisposition:
        boss = self.mega_squid
        if boss is None or not boss.alive or projectile.hostile:
            return "none"
        if not boss.body_hit_by_projectile(projectile.pos, projectile.radius):
            return "none"
        hit_pos = Vec2(projectile.pos.x, projectile.pos.y)
        if boss.is_damage_immune():
            self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, hit_pos, scale=0.55)
            return resolve_projectile_after_hit(projectile, hit=True)
        if projectile.explosive_radius > 0.0:
            apply_explosive_burst(
                self,
                hit_pos,
                projectile.explosive_radius,
                drop_loot=not projectile.from_ally,
            )
            return "consume"
        self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, hit_pos)
        self._apply_boss_combat_hit(boss, tag_player=not projectile.from_ally)
        return resolve_projectile_after_hit(projectile, hit=True)

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
        if self.config.protection_mission or self.config.brood_moon_mission:
            return
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
                well_gravity_scale=0.12 if self.config.protection_mission else 0.35,
            )
            alive_squids = sum(1 for e in self.enemies if e.alive and e.kind is EnemyKind.SQUID)
            prey = self._boss_prey_pos()
            boss.tick_combat(dt)
            orb = boss.try_fire(self.ship.pos, self.ship.vel)
            if orb is not None:
                self.projectiles.append(orb)
            squid, pod = boss.tick_spawns(dt, prey, alive_squids)
            if squid is not None:
                if self.guard_layout is not None:
                    self._apply_relay_squid_ingress(squid)
                self.enemies.append(squid)
            if pod is not None:
                self.squid_pods.append(pod)
            if (
                self.status is GameStatus.RUNNING
                and not boss.is_damage_immune()
                and (boss.pos - self.ship.pos).length() <= boss.radius + self.ship.radius
                and self.invuln_remaining <= 0.0
            ):
                self.boss_scrape_flash = 0.45
                self._register_ship_hit(DamageSource.ENEMY, reason="Mega squid hull scrape — chunk lost.")

        kept_pods: list[SquidPod] = []
        for pod in self.squid_pods:
            if not pod.alive:
                continue
            if pod.tick(dt):
                squid = SquidEnemy(
                    pos=Vec2(pod.pos.x, pod.pos.y),
                    tentacle_reach=62.0,
                    max_speed=185.0,
                    detect_range=760.0,
                    engage_range=620.0,
                )
                if self.guard_layout is not None:
                    self._apply_relay_squid_ingress(squid)
                self.enemies.append(squid)
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

    def _patrol_threats(self) -> list[tuple[Vec2, Vec2]]:
        threats: list[tuple[Vec2, Vec2]] = [(self.ship.pos, self.ship.vel)]
        for ally in self.allies:
            if ally.alive:
                threats.append((ally.pos, ally.vel))
        drone = self.drone_wingman
        if drone is not None and drone.alive:
            threats.append((drone.pos, drone.vel))
        for station in self.friendly_stations:
            if station.alive:
                threats.append((station.pos, Vec2()))
        return threats

    def _squid_prey_for(self, squid_pos: Vec2) -> tuple[Vec2, Vec2, float]:
        best_pos = self.ship.pos
        best_vel = self.ship.vel
        best_radius = self.ship.radius
        best_dist = (self.ship.pos - squid_pos).length()
        for station in self.friendly_stations:
            if not station.alive:
                continue
            dist = (station.pos - squid_pos).length()
            if dist < best_dist:
                best_dist = dist
                best_pos = station.pos
                best_vel = Vec2()
                best_radius = station.radius
        return best_pos, best_vel, best_radius

    def _boss_prey_pos(self) -> Vec2:
        if not self.friendly_stations:
            return self.ship.pos
        best: Vec2 | None = None
        best_dist = float("inf")
        boss_pos = self.mega_squid.pos if self.mega_squid is not None else self.ship.pos
        for station in self.friendly_stations:
            if not station.alive:
                continue
            dist = (station.pos - boss_pos).length()
            if dist < best_dist:
                best_dist = dist
                best = station.pos
        return best if best is not None else self.ship.pos

    def _update_enemies(self, dt: float) -> None:
        patrol_threats = self._patrol_threats()
        homeward_target, homeward_thrust = self._relay_homeward()

        for enemy in self.enemies:
            if not enemy.alive:
                continue
            enemy.tick_combat(dt)
            if enemy.kind is EnemyKind.SQUID:
                assert isinstance(enemy, SquidEnemy)
                prey_pos, prey_vel, prey_radius = self._squid_prey_for(enemy.pos)
                enemy.integrate(
                    dt,
                    prey_pos,
                    prey_vel,
                    self.wells,
                    gravity_scale=self.config.gravity_scale,
                    drag=self.config.drag,
                    well_maw_radius=self.config.well_maw_radius,
                    prey_radius=prey_radius,
                    homeward_target=homeward_target,
                    homeward_thrust=homeward_thrust,
                )
                shot = enemy.try_fire(self.ship.pos, self.ship.vel)
            elif enemy.kind is EnemyKind.HOSTILE_FIGHTER:
                assert isinstance(enemy, HostileFighter)
                pursue = enemy.pick_pursue_target(patrol_threats)
                enemy.integrate(
                    dt,
                    self.wells,
                    gravity_scale=self.config.gravity_scale,
                    drag=self.config.drag,
                    well_maw_radius=self.config.well_maw_radius,
                    homeward_target=homeward_target,
                    homeward_thrust=homeward_thrust,
                    pursue_target=pursue,
                    pursue_thrust=260.0 if pursue is not None else 0.0,
                )
                shot = enemy.try_fire_at_threats(patrol_threats)
            else:
                assert isinstance(enemy, PatrolEnemy)
                enemy.integrate(
                    dt,
                    self.wells,
                    gravity_scale=self.config.gravity_scale,
                    drag=self.config.drag,
                    well_maw_radius=self.config.well_maw_radius,
                )
                shot = enemy.try_fire_at_threats(patrol_threats)
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
            threat = ally.pick_threat(
                self.enemies,
                self.mega_squid,
                player_pos=self.ship.pos,
                allow_boss=self.boss_tagged_by_player or not self.config.protection_mission,
            )
            nearby_asteroids = self._nearby_asteroids(ally.pos, ALLY_ASTEROID_QUERY_RADIUS)
            ally.integrate(
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
            )
            shot = ally.try_fire(threat)
            if shot is not None:
                self.projectiles.append(shot)
        self._check_ally_hazards()
        self._prune_dead_allies()

    def _nearby_asteroids(self, pos: Vec2, radius: float) -> list[Asteroid]:
        if self.asteroid_spatial.populated:
            return self.asteroid_spatial.query_circle(pos, radius)
        out: list[Asteroid] = []
        reach_sq = (radius + 48.0) ** 2
        for asteroid in self.asteroids:
            if (asteroid.pos - pos).length_sq() <= reach_sq:
                out.append(asteroid)
        return out

    def _nearby_asteroids_for_drone(self, pos: Vec2) -> list[Asteroid]:
        return self._nearby_asteroids(pos, DRONE_ASTEROID_QUERY_RADIUS)

    def _update_drone_wingman(self, dt: float) -> None:
        drone = self.drone_wingman
        if drone is None or not drone.alive:
            return
        drone.tick_combat(dt)
        nearby_asteroids = self._nearby_asteroids_for_drone(drone.pos)
        suspend_combat = False
        if self.config.brood_moon_mission and self.brood_moon is not None:
            from gravity_ho_matey.gameplay.brood_moon_mission import in_orbital_space_phase

            suspend_combat = in_orbital_space_phase(self.brood_moon.phase)
        threat = None
        if not suspend_combat:
            threat = drone.pick_threat(
                self.enemies,
                self.mega_squid,
                player_pos=self.ship.pos,
                asteroids=nearby_asteroids,
                allow_boss=self.boss_tagged_by_player or not self.config.protection_mission,
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
        shot = None if suspend_combat else drone.try_fire(threat)
        if shot is not None:
            self.projectiles.append(shot)
        self._check_drone_hazards()
        if not drone.alive:
            self.drone_wingman = None

    def _update_nifflerp(self, dt: float) -> None:
        buddy = self.nifflerp
        if buddy is None or not buddy.alive:
            return
        buddy.tick(dt)
        nearby_asteroids = self._nearby_asteroids(buddy.pos, NIFFLERP_ASTEROID_QUERY_RADIUS)
        buddy.integrate(
            dt,
            player_pos=self.ship.pos,
            player_vel=self.ship.vel,
            player_angle=self.ship.angle,
            elapsed=self.elapsed,
            wells=self.wells,
            gravity_scale=self.config.gravity_scale,
            drag=self.config.drag,
            well_maw_radius=self.config.well_maw_radius,
            jewels=self.jewels,
            asteroids=nearby_asteroids,
            enemies=self.enemies,
            hostile_projectiles=[p for p in self.projectiles if p.hostile],
        )
        self._check_nifflerp_hazards()
        if not buddy.alive:
            self.nifflerp = None

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

    def _projectile_hits_nifflerp(self, projectile: Projectile) -> bool:
        buddy = self.nifflerp
        if buddy is None or not buddy.alive:
            return False
        if not buddy.body_hit_by_projectile(projectile.pos, projectile.radius):
            return False
        self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, Vec2(projectile.pos.x, projectile.pos.y))
        if buddy.apply_shot():
            self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, Vec2(buddy.pos.x, buddy.pos.y), scale=0.55)
            self.nifflerp = None
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

    def _check_nifflerp_hazards(self) -> None:
        if self.status is not GameStatus.RUNNING:
            return
        buddy = self.nifflerp
        if buddy is None or not buddy.alive or buddy.hit_invuln > 0.0:
            return
        if self._asteroid_hit_at(buddy.pos, buddy.radius) is not None:
            self.explosions.spawn(ExplosionKind.SHIP_STRUCK, Vec2(buddy.pos.x, buddy.pos.y), scale=0.55)
            if buddy.apply_shot():
                self.nifflerp = None
            return
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if enemy.kind is EnemyKind.SQUID:
                assert isinstance(enemy, SquidEnemy)
                gap = (enemy.pos - buddy.pos).length() - enemy.tentacle_span() - buddy.radius
                if gap > 6.0:
                    continue
            elif (enemy.pos - buddy.pos).length() > enemy.radius + buddy.radius + 4.0:
                continue
            self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, Vec2(buddy.pos.x, buddy.pos.y), scale=0.55)
            if buddy.apply_shot():
                self.nifflerp = None
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
        buddy = self.nifflerp
        if buddy is not None and buddy.alive and buddy.body_hit_by_projectile(projectile.pos, projectile.radius):
            self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, Vec2(projectile.pos.x, projectile.pos.y))
            return True
        return False

    def _projectile_hits_ally_hostile(self, projectile: Projectile) -> bool:
        if not projectile.hostile:
            return False
        for ally in self.allies:
            if not ally.alive:
                continue
            if not ally.body_hit_by_projectile(projectile.pos, projectile.radius):
                continue
            self.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, Vec2(projectile.pos.x, projectile.pos.y))
            self.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, Vec2(ally.pos.x, ally.pos.y), scale=0.85)
            ally.alive = False
            return True
        return False

    def _check_ally_hazards(self) -> None:
        if self.status is not GameStatus.RUNNING:
            return
        for ally in self.allies:
            if not ally.alive:
                continue
            if self._asteroid_hit_at(ally.pos, ally.radius) is not None:
                self.explosions.spawn(ExplosionKind.SHIP_STRUCK, Vec2(ally.pos.x, ally.pos.y), scale=0.75)
                ally.alive = False
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
        helper_pos: Vec2 | None = None
        helper_radius = 0.0
        if self.nifflerp is not None and self.nifflerp.alive:
            helper_pos = self.nifflerp.pos
            helper_radius = self.nifflerp.radius
        self.jewels, collected = tick_jewels(
            self.jewels,
            self.ship.pos,
            self.ship.radius,
            dt,
            allow_collect=allow_collect,
            helper_pos=helper_pos,
            helper_radius=helper_radius,
        )
        if collected > 0 and allow_collect:
            self.on_jewels_collected(collected)
            fx_pos = self.ship.pos
            if self.nifflerp is not None and self.nifflerp.alive:
                fx_pos = self.nifflerp.pos
            fx_scale = 0.55 + min(collected, 6) * 0.1
            self.explosions.spawn(
                ExplosionKind.JEWEL_COLLECT,
                Vec2(fx_pos.x, fx_pos.y),
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
                self._register_roster_kill(enemy)
                self._prune_dead_enemies()
                self._register_ship_hit(DamageSource.ENEMY)
                return

    def _check_enemy_collisions(self, dt: float) -> None:
        self._check_squid_cling_damage(dt)
        if self.status is GameStatus.RUNNING:
            self._check_patrol_enemy_collisions()

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
