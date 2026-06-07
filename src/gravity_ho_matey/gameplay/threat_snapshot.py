from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.core.geometry import Rect, polygon_aabb
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Asteroid


@dataclass(frozen=True, slots=True)
class AsteroidThreatSnapshot:
    asteroid: Asteroid
    verts: tuple[Vec2, ...]
    aabb: Rect


def build_asteroid_threat_snapshots(asteroids: list[Asteroid]) -> tuple[AsteroidThreatSnapshot, ...]:
    """Narrow-phase hull meshes — only call for asteroids already filtered by broad phase."""
    snapshots: list[AsteroidThreatSnapshot] = []
    for asteroid in asteroids:
        verts = asteroid.world_vertices()
        if len(verts) < 3:
            continue
        snapshots.append(
            AsteroidThreatSnapshot(
                asteroid=asteroid,
                verts=tuple(verts),
                aabb=polygon_aabb(verts),
            )
        )
    return tuple(snapshots)
