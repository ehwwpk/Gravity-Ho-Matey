from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import SpaceJunk

DEFAULT_CELL_SIZE = 240.0
SHIP_INTERACTION_RADIUS = 880.0
PROJECTILE_INTERACTION_RADIUS = 160.0


class JunkSpatialGrid:
    """Broad-phase partition for static scrap walls — mirrors asteroid grid."""

    __slots__ = ("cell_size", "_cells")

    def __init__(self, cell_size: float = DEFAULT_CELL_SIZE) -> None:
        self.cell_size = max(32.0, cell_size)
        self._cells: dict[tuple[int, int], list[SpaceJunk]] = {}

    def clear(self) -> None:
        self._cells.clear()

    def rebuild(self, space_junk: list[SpaceJunk]) -> None:
        self.clear()
        for junk in space_junk:
            key = self._cell_key(junk.pos)
            bucket = self._cells.get(key)
            if bucket is None:
                self._cells[key] = [junk]
            else:
                bucket.append(junk)

    @property
    def populated(self) -> bool:
        return bool(self._cells)

    def _cell_key(self, pos: Vec2) -> tuple[int, int]:
        size = self.cell_size
        return (int(math.floor(pos.x / size)), int(math.floor(pos.y / size)))

    def query_circle(self, center: Vec2, radius: float) -> list[SpaceJunk]:
        if radius <= 0.0 or not self._cells:
            return []
        size = self.cell_size
        x0 = int(math.floor((center.x - radius) / size))
        x1 = int(math.floor((center.x + radius) / size))
        y0 = int(math.floor((center.y - radius) / size))
        y1 = int(math.floor((center.y + radius) / size))
        radius_sq = radius * radius
        seen: set[int] = set()
        found: list[SpaceJunk] = []
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                for junk in self._cells.get((cx, cy), ()):
                    oid = id(junk)
                    if oid in seen:
                        continue
                    seen.add(oid)
                    reach = radius + junk.approximate_radius()
                    if (junk.pos - center).length_sq() <= reach * reach:
                        found.append(junk)
        return found

    def query_interaction_zones(
        self,
        ship_pos: Vec2,
        *,
        ship_radius: float = SHIP_INTERACTION_RADIUS,
        projectile_points: tuple[Vec2, ...] = (),
        projectile_radius: float = PROJECTILE_INTERACTION_RADIUS,
    ) -> list[SpaceJunk]:
        seen: set[int] = set()
        active: list[SpaceJunk] = []
        for junk in self.query_circle(ship_pos, ship_radius):
            oid = id(junk)
            if oid not in seen:
                seen.add(oid)
                active.append(junk)
        for point in projectile_points:
            for junk in self.query_circle(point, projectile_radius):
                oid = id(junk)
                if oid not in seen:
                    seen.add(oid)
                    active.append(junk)
        return active
