from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.hostile_fighter import HostileFighter
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.levels.guard_layout import (
    RELAY_INGRESS_SQUID_SPEED,
    WAVE1_NE_SPAWNS,
    WAVE1_NW_SPAWNS,
    WAVE3_FIGHTER_SPAWNS,
    GuardLayout,
    squid_arc_positions,
)

WAVE1_PATROL_COUNT = 4
WAVE2_SQUID_COUNT = 7
WAVE3_SQUID_COUNT = 8
WAVE3_FIGHTER_COUNT = 4

GuardWaveEnemy = PatrolEnemy | SquidEnemy | HostileFighter


def _station_target(layout: GuardLayout) -> Vec2:
    return layout.station_anchor


def _ingress_velocity(from_pos: Vec2, target: Vec2, speed: float) -> Vec2:
    delta = target - from_pos
    if delta.length_sq() <= 1.0:
        return Vec2()
    return delta.normalized() * speed


relay_ingress_velocity = _ingress_velocity


def _relay_squid(
    pos: Vec2,
    *,
    station: Vec2,
    orbit_sign: float,
    facing: float,
    detect_range: float,
    engage_range: float,
) -> SquidEnemy:
    return SquidEnemy(
        pos=pos,
        vel=_ingress_velocity(pos, station, RELAY_INGRESS_SQUID_SPEED),
        orbit_sign=orbit_sign,
        facing_angle=facing,
        detect_range=detect_range,
        engage_range=engage_range,
        approach_thrust=620.0,
        max_speed=228.0,
    )


def _patrol_ingress(spawn: Vec2, station: Vec2) -> tuple[Vec2, ...]:
    mid = Vec2((spawn.x + station.x) * 0.5, (spawn.y + station.y) * 0.5)
    to_station = station - spawn
    angle = math.atan2(to_station.y, to_station.x)
    right = Vec2.from_angle(angle + math.pi / 2.0)
    orbit = station - Vec2.from_angle(angle) * 170.0 + right * 55.0
    hold = station - Vec2.from_angle(angle) * 130.0 - right * 40.0
    return (spawn, mid, orbit, hold)


def spawn_wave1_patrols(layout: GuardLayout) -> list[PatrolEnemy]:
    station = _station_target(layout)
    enemies: list[PatrolEnemy] = []
    spawns = (*WAVE1_NW_SPAWNS, *WAVE1_NE_SPAWNS)
    for index, spawn in enumerate(spawns):
        enemies.append(
            PatrolEnemy(
                waypoints=_patrol_ingress(spawn, station),
                pos=Vec2(spawn.x, spawn.y),
                thrust=268.0,
                max_speed=118.0,
                can_shoot=True,
                fire_interval=2.15,
                fire_cooldown=0.25 + index * 0.18,
                engage_range=520.0,
            )
        )
    return enemies


def spawn_wave2_squids(layout: GuardLayout) -> list[SquidEnemy]:
    station = _station_target(layout)
    squids: list[SquidEnemy] = []
    for i, pos in enumerate(squid_arc_positions(layout.squid_ring_center, WAVE2_SQUID_COUNT, seed_offset=0)):
        facing = math.atan2(station.y - pos.y, station.x - pos.x)
        squids.append(
            _relay_squid(
                pos,
                station=station,
                orbit_sign=-1.0 if i % 2 else 1.0,
                facing=facing,
                detect_range=1580.0,
                engage_range=1380.0,
            )
        )
    return squids


def spawn_wave3_assault(layout: GuardLayout) -> list[GuardWaveEnemy]:
    station = _station_target(layout)
    enemies: list[GuardWaveEnemy] = []
    for i, pos in enumerate(squid_arc_positions(layout.squid_ring_center, WAVE3_SQUID_COUNT, seed_offset=3)):
        facing = math.atan2(station.y - pos.y, station.x - pos.x)
        enemies.append(
            _relay_squid(
                pos,
                station=station,
                orbit_sign=-1.0 if i % 2 else 1.0,
                facing=facing,
                detect_range=1620.0,
                engage_range=1420.0,
            )
        )
    for index, spawn in enumerate(WAVE3_FIGHTER_SPAWNS[:WAVE3_FIGHTER_COUNT]):
        facing = math.atan2(station.y - spawn.y, station.x - spawn.x)
        fighter = HostileFighter(
            pos=Vec2(spawn.x, spawn.y),
            vel=_ingress_velocity(spawn, station, 148.0),
            facing_angle=facing,
            fire_cooldown=0.35 + index * 0.22,
        )
        enemies.append(fighter)
    return enemies


def wave_spawn_for(layout: GuardLayout, wave: int) -> list[GuardWaveEnemy]:
    if wave == 1:
        return spawn_wave1_patrols(layout)
    if wave == 2:
        return spawn_wave2_squids(layout)
    if wave == 3:
        return spawn_wave3_assault(layout)
    return []
