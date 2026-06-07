from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Projectile
from gravity_ho_matey.gameplay.weapon_config import (
    EXPLOSIVE_ADV_BLAST_RADIUS,
    EXPLOSIVE_ADV_COOLDOWN_MULT,
    EXPLOSIVE_ADV_SPEED_MULT,
    EXPLOSIVE_BLAST_RADIUS,
    EXPLOSIVE_COOLDOWN_MULT,
    EXPLOSIVE_PROJECTILE_RADIUS,
    EXPLOSIVE_SPEED_MULT,
    EXPLOSIVE_TTL,
    LASER_ADV_PIERCE_COUNT,
    LASER_ADV_PROJECTILE_RADIUS,
    LASER_ADV_SPEED_MULT,
    LASER_PIERCE_COUNT,
    LASER_PROJECTILE_RADIUS,
    LASER_SPEED_MULT,
    LASER_TTL,
    SHOTGUN_ADV_PELLET_COUNT,
    SHOTGUN_ADV_SIDE_SPREAD_RAD,
    SHOTGUN_PELLET_COUNT,
    SHOTGUN_PROJECTILE_RADIUS,
    SHOTGUN_SPREAD_RAD,
)
from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack


def player_fire_cooldown(
    base_cooldown: float,
    ship_multiplier: float,
    track: WeaponTrack | None,
    *,
    advanced: bool = False,
) -> float:
    cooldown = base_cooldown * ship_multiplier
    if track is WeaponTrack.EXPLOSIVE:
        cooldown *= EXPLOSIVE_ADV_COOLDOWN_MULT if advanced else EXPLOSIVE_COOLDOWN_MULT
    return cooldown


def spawn_player_shots(
    *,
    ship_pos: Vec2,
    ship_vel: Vec2,
    ship_angle: float,
    ship_radius: float,
    projectile_speed: float,
    track: WeaponTrack | None,
    advanced: bool = False,
) -> list[Projectile]:
    direction = Vec2.from_angle(ship_angle)
    muzzle = ship_pos + direction * (ship_radius + 8.0)
    base_vel = ship_vel * 0.35 + direction * projectile_speed

    if track is WeaponTrack.SHOTGUN:
        shots: list[Projectile] = []
        if advanced:
            offsets = (-SHOTGUN_ADV_SIDE_SPREAD_RAD, 0.0, SHOTGUN_ADV_SIDE_SPREAD_RAD)
        else:
            half = (SHOTGUN_PELLET_COUNT - 1) / 2.0
            offsets = tuple((index - half) * SHOTGUN_SPREAD_RAD for index in range(SHOTGUN_PELLET_COUNT))
        for offset in offsets:
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
        speed_mult = LASER_ADV_SPEED_MULT if advanced else LASER_SPEED_MULT
        vel = ship_vel * 0.35 + direction * (projectile_speed * speed_mult)
        return [
            Projectile(
                pos=Vec2(muzzle.x, muzzle.y),
                vel=vel,
                ttl=LASER_TTL,
                radius=LASER_ADV_PROJECTILE_RADIUS if advanced else LASER_PROJECTILE_RADIUS,
                pierce_remaining=LASER_ADV_PIERCE_COUNT if advanced else LASER_PIERCE_COUNT,
                weapon_track=WeaponTrack.LASER,
            )
        ]

    if track is WeaponTrack.EXPLOSIVE:
        speed_mult = EXPLOSIVE_ADV_SPEED_MULT if advanced else EXPLOSIVE_SPEED_MULT
        blast = EXPLOSIVE_ADV_BLAST_RADIUS if advanced else EXPLOSIVE_BLAST_RADIUS
        vel = ship_vel * 0.35 + direction * (projectile_speed * speed_mult)
        return [
            Projectile(
                pos=Vec2(muzzle.x, muzzle.y),
                vel=vel,
                ttl=EXPLOSIVE_TTL,
                radius=EXPLOSIVE_PROJECTILE_RADIUS,
                explosive_radius=blast,
                weapon_track=WeaponTrack.EXPLOSIVE,
            )
        ]

    return [Projectile(pos=Vec2(muzzle.x, muzzle.y), vel=base_vel, hostile=False)]
