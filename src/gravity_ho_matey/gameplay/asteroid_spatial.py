from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Asteroid

# Uniform grid — ~1 belt spacing on Drift. Standard broad-phase (Game Programming Patterns / gamedev SE).
DEFAULT_CELL_SIZE = 240.0

# Polygon collision + HUD threat only inside these radii (honest wake zones).
SHIP_INTERACTION_RADIUS = 880.0
PROJECTILE_INTERACTION_RADIUS = 160.0


class AsteroidSpatialGrid:
    """Broad-phase partition — cheap rebuild O(n), queries touch 9–25 cells not all rocks."""

    __slots__ = ("cell_size", "_cells")

    def __init__(self, cell_size: float = DEFAULT_CELL_SIZE) -> None:
        self.cell_size = max(32.0, cell_size)
        self._cells: dict[tuple[int, int], list[Asteroid]] = {}

    def clear(self) -> None:
        self._cells.clear()

    def rebuild(self, asteroids: list[Asteroid]) -> None:
        self.clear()
        for asteroid in asteroids:
            key = self._cell_key(asteroid.pos)
            bucket = self._cells.get(key)
            if bucket is None:
                self._cells[key] = [asteroid]
            else:
                bucket.append(asteroid)

    @property
    def populated(self) -> bool:
        return bool(self._cells)

    def _cell_key(self, pos: Vec2) -> tuple[int, int]:
        size = self.cell_size
        return (int(math.floor(pos.x / size)), int(math.floor(pos.y / size)))

    def query_circle(self, center: Vec2, radius: float) -> list[Asteroid]:
        if radius <= 0.0 or not self._cells:
            return []
        size = self.cell_size
        x0 = int(math.floor((center.x - radius) / size))
        x1 = int(math.floor((center.x + radius) / size))
        y0 = int(math.floor((center.y - radius) / size))
        y1 = int(math.floor((center.y + radius) / size))
        radius_sq = radius * radius
        seen: set[int] = set()
        found: list[Asteroid] = []
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                for asteroid in self._cells.get((cx, cy), ()):
                    oid = id(asteroid)
                    if oid in seen:
                        continue
                    seen.add(oid)
                    reach = radius + asteroid.approximate_radius()
                    if (asteroid.pos - center).length_sq() <= reach * reach:
                        found.append(asteroid)
        return found

    def query_interaction_zones(
        self,
        ship_pos: Vec2,
        *,
        ship_radius: float = SHIP_INTERACTION_RADIUS,
        projectile_points: tuple[Vec2, ...] = (),
        projectile_radius: float = PROJECTILE_INTERACTION_RADIUS,
    ) -> list[Asteroid]:
        """Rocks that need narrow-phase meshes this frame (ship hull + stray shots)."""
        seen: set[int] = set()
        active: list[Asteroid] = []
        for asteroid in self.query_circle(ship_pos, ship_radius):
            oid = id(asteroid)
            if oid not in seen:
                seen.add(oid)
                active.append(asteroid)
        for point in projectile_points:
            for asteroid in self.query_circle(point, projectile_radius):
                oid = id(asteroid)
                if oid not in seen:
                    seen.add(oid)
                    active.append(asteroid)
        return active
