from __future__ import annotations

import math
import random

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_tiers import AsteroidTier
from gravity_ho_matey.gameplay.comet_body import CometBody
from gravity_ho_matey.gameplay.entities import Asteroid, WorldConfig
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.levels.comet_fuel_layout import (
    ORBITAL_DEBRIS_RING_MAX,
    ORBITAL_DEBRIS_RING_MIN,
    ORBITAL_HEIGHT,
    ORBITAL_WIDTH,
    CometFuelOrbitalLayout,
)


def _rock_verts(seed: int, scale: float) -> tuple[Vec2, ...]:
    rng = random.Random(seed)
    count = 7 + seed % 3
    verts: list[Vec2] = []
    for i in range(count):
        angle = (i / count) * math.tau + rng.uniform(-0.15, 0.15)
        radius = scale * rng.uniform(0.72, 1.08)
        verts.append(Vec2(math.cos(angle) * radius, math.sin(angle) * radius))
    return tuple(verts)


def _make_debris_rock(rng: random.Random, pos: Vec2, seed: int) -> Asteroid:
    scale = rng.uniform(14.0, 32.0)
    return Asteroid(
        pos=pos,
        vel=Vec2(rng.uniform(-16.0, 16.0), rng.uniform(-12.0, 12.0)),
        angle=rng.uniform(0.0, math.tau),
        spin=rng.uniform(-0.7, 0.7),
        local_verts=_rock_verts(seed, scale),
        size_class="rock",
        drift_kind="medium",
        seed=seed,
        tier=AsteroidTier.SMALL if scale < 22.0 else AsteroidTier.MEDIUM,
        hits_max=1 if scale < 22.0 else 2,
        hits_remaining=1 if scale < 22.0 else 2,
        mass=0.8 + scale * 0.04,
    )


def orbital_debris_asteroids(
    layout: CometFuelOrbitalLayout,
    config: WorldConfig,
    comet: CometBody,
) -> list[Asteroid]:
    rng = random.Random(77007)
    center = comet.position()
    asteroids: list[Asteroid] = []
    seed = 7000
    for i in range(32):
        angle = rng.uniform(0.0, math.tau)
        dist = rng.uniform(ORBITAL_DEBRIS_RING_MIN, ORBITAL_DEBRIS_RING_MAX)
        pos = center + Vec2.from_angle(angle) * dist
        px = max(120.0, min(float(ORBITAL_WIDTH - 120), pos.x))
        py = max(120.0, min(float(ORBITAL_HEIGHT - 120), pos.y))
        asteroids.append(_make_debris_rock(rng, Vec2(px, py), seed + i))
    return asteroids[: config.max_asteroids]


def escape_patrol_squids(layout: CometFuelOrbitalLayout) -> list[SquidEnemy]:
    _ = layout
    spots = (
        Vec2(1400.0, 1300.0),
        Vec2(1600.0, 1700.0),
        Vec2(2000.0, 1500.0),
        Vec2(2400.0, 1400.0),
    )
    return [
        SquidEnemy(
            pos=spot,
            tentacle_reach=68.0,
            max_speed=195.0,
            detect_range=900.0,
            engage_range=720.0,
        )
        for spot in spots
    ]
