from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Projectile
from gravity_ho_matey.gameplay.weapon_config import (
    EXPLOSIVE_COOLDOWN_MULT,
    EXPLOSIVE_BLAST_RADIUS,
    EXPLOSIVE_PROJECTILE_RADIUS,
    EXPLOSIVE_SPEED_MULT,
    EXPLOSIVE_TTL,
    LASER_PIERCE_COUNT,
    LASER_PROJECTILE_RADIUS,
    LASER_SPEED_MULT,
    LASER_TTL,
    SHOTGUN_PELLET_COUNT,
    SHOTGUN_PROJECTILE_RADIUS,
    SHOTGUN_SPREAD_RAD,
)
from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack


def player_fire_cooldown(base_cooldown: float, ship_multiplier: float, track: WeaponTrack | None) -> float:
    cooldown = base_cooldown * ship_multiplier
    if track is WeaponTrack.EXPLOSIVE:
        cooldown *= EXPLOSIVE_COOLDOWN_MULT
    return cooldown


def spawn_player_shots(
    *,
    ship_pos: Vec2,
    ship_vel: Vec2,
    ship_angle: float,
    ship_radius: float,
    projectile_speed: float,
    track: WeaponTrack | None,
) -> list[Projectile]:
    direction = Vec2.from_angle(ship_angle)
    muzzle = ship_pos + direction * (ship_radius + 8.0)
    base_vel = ship_vel * 0.35 + direction * projectile_speed

    if track is WeaponTrack.SHOTGUN:
        shots: list[Projectile] = []
        half = (SHOTGUN_PELLET_COUNT - 1) / 2.0
        for index in range(SHOTGUN_PELLET_COUNT):
            offset = (index - half) * SHOTGUN_SPREAD_RAD
            aim = direction.rotated(offset)
            vel = ship_vel * 0.35 + aim * projectile_speed
            shots.append(
                Projectile(
                    pos=Vec2(muzzle.x, muzzle.y),
                    vel=vel,
                    radius=SHOTGUN_PROJECTILE_RADIUS,
                    weapon_track=WeaponTrack.SHOTGUN,
                )
            )
        return shots

    if track is WeaponTrack.LASER:
        vel = ship_vel * 0.35 + direction * (projectile_speed * LASER_SPEED_MULT)
        return [
            Projectile(
                pos=Vec2(muzzle.x, muzzle.y),
                vel=vel,
                ttl=LASER_TTL,
                radius=LASER_PROJECTILE_RADIUS,
                pierce_remaining=LASER_PIERCE_COUNT,
                weapon_track=WeaponTrack.LASER,
            )
        ]

    if track is WeaponTrack.EXPLOSIVE:
        vel = ship_vel * 0.35 + direction * (projectile_speed * EXPLOSIVE_SPEED_MULT)
        return [
            Projectile(
                pos=Vec2(muzzle.x, muzzle.y),
                vel=vel,
                ttl=EXPLOSIVE_TTL,
                radius=EXPLOSIVE_PROJECTILE_RADIUS,
                explosive_radius=EXPLOSIVE_BLAST_RADIUS,
                weapon_track=WeaponTrack.EXPLOSIVE,
            )
        ]

    return [Projectile(pos=Vec2(muzzle.x, muzzle.y), vel=base_vel, hostile=False)]
