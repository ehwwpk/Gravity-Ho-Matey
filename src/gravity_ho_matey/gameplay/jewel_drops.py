from __future__ import annotations

import random

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_tiers import AsteroidTier
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.entities import Asteroid
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy

EnemyUnit = PatrolEnemy | SquidEnemy

BEACON_JEWEL_MIN = 2
BEACON_JEWEL_MAX = 5


def rng_at(pos: Vec2) -> random.Random:
    """Deterministic roll seed from world position — stable for tests and replays."""
    seed = int(abs(pos.x) * 17.0 + abs(pos.y) * 31.0) & 0xFFFFFFFF
    return random.Random(seed)


def jewel_count_for_asteroid(asteroid: Asteroid, rng: random.Random | None = None) -> int:
    roll = rng or rng_at(asteroid.pos)
    tier = asteroid.tier
    if tier is AsteroidTier.SMALL:
        return 1 if roll.random() < 0.5 else 0
    if tier is AsteroidTier.MEDIUM:
        return roll.randint(1, 3) if roll.random() < 0.9 else 0
    if tier is AsteroidTier.LARGE:
        return roll.randint(2, 5)
    return 0


def jewel_count_for_enemy(enemy: EnemyUnit, rng: random.Random | None = None) -> int:
    roll = rng or rng_at(enemy.pos)
    if enemy.kind is EnemyKind.SQUID:
        return roll.randint(1, 4) if roll.random() < 0.75 else 0
    return roll.randint(4, 9) if roll.random() < 0.85 else 0


def jewel_count_for_boss(anchor: Vec2, rng: random.Random | None = None) -> int:
    roll = rng or rng_at(anchor)
    return roll.randint(15, 22)


def jewel_count_for_beacon(pos: Vec2, rng: random.Random | None = None) -> int:
    roll = rng or rng_at(pos)
    return roll.randint(BEACON_JEWEL_MIN, BEACON_JEWEL_MAX)
