from __future__ import annotations

import random
from enum import Enum, auto


class AsteroidTier(Enum):
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()


_HITS_RANGE: dict[AsteroidTier, tuple[int, int]] = {
    AsteroidTier.SMALL: (1, 3),
    AsteroidTier.MEDIUM: (3, 5),
    AsteroidTier.LARGE: (5, 10),
}

_FRAGMENT_RANGE: dict[AsteroidTier, tuple[int, int]] = {
    AsteroidTier.MEDIUM: (2, 3),
    AsteroidTier.LARGE: (2, 4),
}

MAX_GENERATION = 2
MAX_ASTEROIDS = 48

# Only the largest procedural rocks (upper ~5% of the 30–52 band) become MEDIUM.
ROCK_MEDIUM_MIN_RADIUS = 51.0


def tier_for_spawn(size_class: str, approximate_radius: float) -> AsteroidTier:
    if size_class == "boulder":
        return AsteroidTier.LARGE
    if size_class == "pebble":
        return AsteroidTier.SMALL
    if approximate_radius >= ROCK_MEDIUM_MIN_RADIUS:
        return AsteroidTier.MEDIUM
    return AsteroidTier.SMALL


def tier_for_size_class(size_class: str) -> AsteroidTier:
    """Legacy helper when radius is unknown — prefers SMALL for rocks."""
    if size_class == "boulder":
        return AsteroidTier.LARGE
    return AsteroidTier.SMALL


def roll_hits_max(tier: AsteroidTier, rng: random.Random) -> int:
    lo, hi = _HITS_RANGE[tier]
    return rng.randint(lo, hi)


def can_split(tier: AsteroidTier, generation: int) -> bool:
    return tier in (AsteroidTier.MEDIUM, AsteroidTier.LARGE) and generation < MAX_GENERATION


def fragment_count(rng: random.Random, tier: AsteroidTier) -> int:
    lo, hi = _FRAGMENT_RANGE[tier]
    return rng.randint(lo, hi)
