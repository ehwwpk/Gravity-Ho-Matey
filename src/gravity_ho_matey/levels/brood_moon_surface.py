from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.egg_pod_objective import EggPodObjective
from gravity_ho_matey.gameplay.entities import Beacon
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.levels.brood_moon_layout import (
    BEACON_COUNT,
    BOSS_ANCHOR,
    EGG_POD_COUNT,
    SURFACE_FINAL_BEACON_FRAC,
    SURFACE_HEIGHT,
    SURFACE_SPAWN,
    SURFACE_WRAP_WIDTH,
)


def surface_beacons() -> list[Beacon]:
    xs = [
        SURFACE_WRAP_WIDTH * 0.12,
        SURFACE_WRAP_WIDTH * 0.42,
        SURFACE_WRAP_WIDTH * SURFACE_FINAL_BEACON_FRAC,
    ]
    return [Beacon(Vec2(x, 1080.0 + (i % 2) * 140.0)) for i, x in enumerate(xs[:BEACON_COUNT])]


def surface_egg_pods() -> list[EggPodObjective]:
    # x as wrap fraction so map scale changes stay aligned.
    placements: list[tuple[float, float, bool]] = [
        (0.068, 1380.0, False),
        (0.121, 1520.0, True),
        (0.193, 1260.0, False),
        (0.288, 1450.0, True),
        (0.371, 1320.0, False),
        (0.470, 1500.0, True),
        (0.591, 1280.0, False),
        (0.750, 1420.0, True),
    ]
    pods: list[EggPodObjective] = []
    for i, (frac_x, y, alarm) in enumerate(placements[:EGG_POD_COUNT]):
        pods.append(
            EggPodObjective(
                pos=Vec2(SURFACE_WRAP_WIDTH * frac_x, y),
                alarm=alarm,
                pod_id=i,
            )
        )
    return pods


def surface_patrols() -> list[PatrolEnemy]:
    patrols: list[PatrolEnemy] = []
    frac_xs = [0.091, 0.235, 0.348, 0.523, 0.674, 0.841]
    for i, frac_x in enumerate(frac_xs):
        x = SURFACE_WRAP_WIDTH * frac_x
        y = 980.0 + (i % 3) * 80.0
        span = 180.0 + (i % 2) * 40.0
        patrols.append(
            PatrolEnemy(
                waypoints=(
                    Vec2(x - span, y),
                    Vec2(x + span, y),
                    Vec2(x + span, y + 80.0),
                    Vec2(x - span, y + 80.0),
                ),
                pos=Vec2(x, y),
                max_speed=165.0 + (i % 2) * 12.0,
                can_shoot=True,
                fire_interval=3.4,
            )
        )
    return patrols


def surface_squid_drifters() -> list[SquidEnemy]:
    squids: list[SquidEnemy] = []
    for i, frac_x in enumerate((0.155, 0.333, 0.538, 0.773)):
        x = SURFACE_WRAP_WIDTH * frac_x
        squids.append(
            SquidEnemy(
                pos=Vec2(x, 1180.0 + math.sin(i) * 60.0),
                tentacle_reach=58.0,
                max_speed=168.0,
                detect_range=640.0,
                engage_range=520.0,
            )
        )
    return squids


def surface_spawn_ship():
    from gravity_ho_matey.gameplay.entities import Ship

    return Ship(pos=Vec2(SURFACE_SPAWN.x, SURFACE_SPAWN.y), angle=0.08)


def boss_anchor() -> Vec2:
    return Vec2(BOSS_ANCHOR.x, BOSS_ANCHOR.y)


def surface_dimensions() -> tuple[int, int]:
    return SURFACE_WRAP_WIDTH, SURFACE_HEIGHT
