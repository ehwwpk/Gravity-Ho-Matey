from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_combat import AsteroidCombatResult, apply_projectile_hit
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.entities import Asteroid, Projectile
from gravity_ho_matey.gameplay.explosions import ExplosionKind
from gravity_ho_matey.gameplay.jewel_drops import jewel_count_for_enemy
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack

if TYPE_CHECKING:
    from gravity_ho_matey.gameplay.world import GameWorld

HitDisposition = Literal["none", "consume", "pierce"]


def spawn_weapon_hit_fx(world: GameWorld, hit_pos: Vec2, projectile: Projectile, *, piercing: bool) -> None:
    """Doctrine-colored impact flash at projectile hit."""
    if projectile.hostile:
        world.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, hit_pos, scale=0.85)
        return
    track = projectile.weapon_track
    if piercing and track is WeaponTrack.LASER:
        world.explosions.spawn(ExplosionKind.LASER_PIERCE, hit_pos, scale=0.9)
        return
    if track is WeaponTrack.EXPLOSIVE:
        return
    if track is WeaponTrack.SHOTGUN:
        world.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, hit_pos, scale=0.72)
        return
    if track is WeaponTrack.LASER:
        world.explosions.spawn(ExplosionKind.LASER_PIERCE, hit_pos, scale=0.75)
        return
    world.explosions.spawn(ExplosionKind.PROJECTILE_IMPACT, hit_pos)


def resolve_projectile_after_hit(projectile: Projectile, *, hit: bool) -> HitDisposition:
    """Decide whether a projectile survives after a collision."""
    if not hit:
        return "none"
    if projectile.explosive_radius > 0.0:
        return "consume"
    if projectile.pierce_remaining > 0:
        projectile.pierce_remaining -= 1
        return "pierce"
    return "consume"


def apply_explosive_burst(world: GameWorld, center: Vec2, radius: float, *, drop_loot: bool) -> None:
    """Area damage — enemies, boss, station, and asteroids in blast radius."""
    world.explosions.spawn(ExplosionKind.NOVA_BLAST, center, scale=1.15, aoe_radius_world=radius)

    for asteroid in list(world.asteroids):
        if (asteroid.pos - center).length() <= radius + asteroid.approximate_radius():
            world._apply_asteroid_combat_result(
                apply_projectile_hit(
                    asteroid,
                    center,
                    Vec2(),
                    world_asteroid_count=len(world.asteroids),
                    max_asteroids=world.config.max_asteroids,
                )
            )

    boss = world.mega_squid
    if boss is not None and boss.alive and (boss.pos - center).length() <= radius + boss.radius:
        if boss.apply_shot():
            world._on_boss_defeated()

    station = world.space_station
    if station is not None and station.alive and (station.pos - center).length() <= radius + station.radius:
        if station.apply_shot():
            world._on_station_defeated()

    for friendly in world.friendly_stations:
        if not friendly.alive:
            continue
        if (friendly.pos - center).length() <= radius + friendly.radius:
            if friendly.apply_shot():
                world._on_friendly_station_lost(friendly)

    for enemy in world.enemies:
        if not enemy.alive:
            continue
        reach = enemy.radius + radius
        if (enemy.pos - center).length() > reach:
            continue
        if enemy.kind is EnemyKind.SQUID:
            assert isinstance(enemy, SquidEnemy)
            if enemy.apply_shot():
                enemy_pos = Vec2(enemy.pos.x, enemy.pos.y)
                enemy.alive = False
                world.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, enemy_pos)
                if drop_loot:
                    drop_count = jewel_count_for_enemy(enemy)
                    if drop_count > 0:
                        world._spawn_jewels_at(enemy_pos, drop_count)
                world._register_roster_kill(enemy)
            continue
        enemy_pos = Vec2(enemy.pos.x, enemy.pos.y)
        enemy.alive = False
        world.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, enemy_pos)
        if drop_loot:
            drop_count = jewel_count_for_enemy(enemy)
            if drop_count > 0:
                world._spawn_jewels_at(enemy_pos, drop_count)
        world._register_roster_kill(enemy)

    for pod in world.egg_pods:
        if not pod.alive:
            continue
        if (pod.pos - center).length() > pod.radius + radius:
            continue
        if pod.apply_shot():
            world.explosions.spawn(ExplosionKind.ENEMY_DESTROYED, Vec2(pod.pos.x, pod.pos.y), scale=1.6)
            from gravity_ho_matey.gameplay.brood_moon_controller import on_egg_pod_destroyed

            on_egg_pod_destroyed(world, pod)

    world._prune_dead_enemies()
