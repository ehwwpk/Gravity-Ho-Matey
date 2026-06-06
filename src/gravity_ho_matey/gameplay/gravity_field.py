from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GravityWell
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at


@dataclass(frozen=True, slots=True)
class GravityFieldCell:
    accel: Vec2
    magnitude: float


@dataclass(frozen=True, slots=True)
class GravityField:
    """Baked gravity samples over world bounds — same physics as runtime wells."""

    origin: Vec2
    cell_size: float
    cols: int
    rows: int
    cells: tuple[GravityFieldCell, ...]
    max_magnitude: float

    def cell_at(self, col: int, row: int) -> GravityFieldCell:
        return self.cells[row * self.cols + col]

    def sample_at(self, point: Vec2) -> GravityFieldCell:
        if self.cols <= 0 or self.rows <= 0:
            return GravityFieldCell(accel=Vec2(), magnitude=0.0)
        col = int((point.x - self.origin.x) / self.cell_size)
        row = int((point.y - self.origin.y) / self.cell_size)
        col = max(0, min(self.cols - 1, col))
        row = max(0, min(self.rows - 1, row))
        return self.cell_at(col, row)

    def normalized_magnitude_at(self, point: Vec2) -> float:
        if self.max_magnitude <= 1e-9:
            return 0.0
        return min(1.0, self.sample_at(point).magnitude / self.max_magnitude)

    @staticmethod
    def bake(
        wells: list[GravityWell],
        *,
        world_width: float,
        world_height: float,
        cols: int = 32,
        rows: int = 32,
        gravity_scale: float = 1.0,
    ) -> GravityField:
        cols = max(1, cols)
        rows = max(1, rows)
        cell_w = world_width / cols
        cell_h = world_height / rows
        cell_size = min(cell_w, cell_h)
        origin = Vec2(cell_size * 0.5, cell_size * 0.5)
        baked: list[GravityFieldCell] = []
        peak = 0.0
        for row in range(rows):
            for col in range(cols):
                center = Vec2(origin.x + col * cell_size, origin.y + row * cell_size)
                accel = gravity_acceleration_at(center, wells) * gravity_scale
                magnitude = accel.length()
                peak = max(peak, magnitude)
                baked.append(GravityFieldCell(accel=accel, magnitude=magnitude))
        return GravityField(
            origin=origin,
            cell_size=cell_size,
            cols=cols,
            rows=rows,
            cells=tuple(baked),
            max_magnitude=max(peak, 1e-9),
        )
