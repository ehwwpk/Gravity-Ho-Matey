from __future__ import annotations

import math
import random

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_tiers import AsteroidTier
from gravity_ho_matey.gameplay.entities import Asteroid, WorldConfig
from gravity_ho_matey.levels.brood_moon_layout import (
    MOON_CENTER,
    ORBITAL_DEBRIS_EXCLUDE_INNER,
    ORBITAL_DEBRIS_EXCLUDE_OUTER,
    ORBITAL_DEBRIS_RING_MAX,
    ORBITAL_DEBRIS_RING_MIN,
    ORBITAL_HEIGHT,
    ORBITAL_WIDTH,
    SURFACE_HEIGHT,
    SURFACE_WRAP_WIDTH,
)
from gravity_ho_matey.levels.brood_moon_layout import BroodMoonOrbitalLayout


def _rock_verts(seed: int, scale: float) -> tuple[Vec2, ...]:
    rng = random.Random(seed)
    count = 7 + seed % 3
    verts: list[Vec2] = []
    for i in range(count):
        angle = (i / count) * math.tau + rng.uniform(-0.15, 0.15)
        radius = scale * rng.uniform(0.72, 1.08)
        verts.append(Vec2(math.cos(angle) * radius, math.sin(angle) * radius))
    return tuple(verts)


def orbital_debris_asteroids(layout: BroodMoonOrbitalLayout, config: WorldConfig) -> list[Asteroid]:
    rng = random.Random(601)
    asteroids: list[Asteroid] = []
    moon = layout.moon_well.pos
    for i in range(22):
        angle = rng.uniform(0.0, math.tau)
        dist = ORBITAL_DEBRIS_RING_MIN + (i % 7) * ((ORBITAL_DEBRIS_RING_MAX - ORBITAL_DEBRIS_RING_MIN) / 6.0)
        dist += rng.uniform(-18.0, 18.0)
        dist = max(ORBITAL_DEBRIS_RING_MIN, min(ORBITAL_DEBRIS_RING_MAX, dist))
        pos = moon + Vec2(math.cos(angle), math.sin(angle)) * dist
        px = max(120.0, min(float(ORBITAL_WIDTH - 120), pos.x))
        py = max(120.0, min(float(ORBITAL_HEIGHT - 120), pos.y))
        pos = Vec2(px, py)
        scale = rng.uniform(14.0, 34.0)
        asteroids.append(
            Asteroid(
                pos=pos,
                vel=Vec2(rng.uniform(-18.0, 18.0), rng.uniform(-14.0, 14.0)),
                angle=rng.uniform(0.0, math.tau),
                spin=rng.uniform(-0.8, 0.8),
                local_verts=_rock_verts(600 + i, scale),
                size_class="rock",
                drift_kind="medium",
                seed=600 + i,
                tier=AsteroidTier.SMALL if scale < 22.0 else AsteroidTier.MEDIUM,
                hits_max=1 if scale < 22.0 else 2,
                hits_remaining=1 if scale < 22.0 else 2,
                mass=0.8 + scale * 0.04,
            )
        )
    for i in range(8):
        for _ in range(24):
            pos = Vec2(
                rng.uniform(400.0, MOON_CENTER.x - 400.0),
                rng.uniform(600.0, ORBITAL_HEIGHT - 400.0),
            )
            dist = (pos - moon).length()
            if ORBITAL_DEBRIS_EXCLUDE_INNER <= dist <= ORBITAL_DEBRIS_EXCLUDE_OUTER:
                continue
            break
        else:
            pos = Vec2(400.0 + i * 280.0, 600.0 + (i % 3) * 400.0)
        scale = rng.uniform(16.0, 28.0)
        asteroids.append(
            Asteroid(
                pos=pos,
                vel=Vec2(rng.uniform(-12.0, 12.0), rng.uniform(-10.0, 10.0)),
                angle=rng.uniform(0.0, math.tau),
                spin=rng.uniform(-0.5, 0.5),
                local_verts=_rock_verts(700 + i, scale),
                size_class="rock",
                drift_kind="slow",
                seed=700 + i,
                tier=AsteroidTier.SMALL,
            )
        )
    _ = config
    return asteroids


def surface_scree_asteroids(config: WorldConfig) -> list[Asteroid]:
    rng = random.Random(802)
    asteroids: list[Asteroid] = []
    for i in range(36):
        x = rng.uniform(200.0, float(SURFACE_WRAP_WIDTH - 200))
        y = rng.uniform(1320.0, 1620.0)
        scale = rng.uniform(10.0, 26.0)
        asteroids.append(
            Asteroid(
                pos=Vec2(x, y),
                vel=Vec2(rng.uniform(-8.0, 8.0), rng.uniform(-4.0, 4.0)),
                angle=rng.uniform(0.0, math.tau),
                spin=rng.uniform(-0.4, 0.4),
                local_verts=_rock_verts(800 + i, scale),
                size_class="rock",
                drift_kind="slow",
                seed=800 + i,
                tier=AsteroidTier.SMALL,
                free_bounds=True,
            )
        )
    _ = config
    return asteroids
