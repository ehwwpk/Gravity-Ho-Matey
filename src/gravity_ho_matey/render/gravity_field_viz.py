"""Shared gravity heatmap thresholds and black-hole footprint helpers."""

from __future__ import annotations

from gravity_ho_matey.gameplay.entities import GravityWell

HEATMAP_NORM_FLOOR = 0.20
_WELL_HEATMAP_SUPPRESS_FRAC = 0.92


def heatmap_cell_visible(norm: float) -> bool:
    return norm >= HEATMAP_NORM_FLOOR


def inside_black_hole_footprint(wells: tuple[GravityWell, ...] | list[GravityWell], wx: float, wy: float) -> bool:
    for well in wells:
        if well.kind != "black_hole":
            continue
        dx = wx - well.pos.x
        dy = wy - well.pos.y
        if dx * dx + dy * dy <= (well.radius * _WELL_HEATMAP_SUPPRESS_FRAC) ** 2:
            return True
    return False
