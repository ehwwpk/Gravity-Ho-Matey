from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import SpaceJunk
from gravity_ho_matey.gameplay.space_junk_prefabs import instantiate_junk

DEFAULT_SHIP_RADIUS = 12.0
MIN_GATE_GAP = 2 * DEFAULT_SHIP_RADIUS + 8.0
WALL_OVERLAP = 8.0


def junk_wall_line(
    start: Vec2,
    end: Vec2,
    *,
    prefab: str = "girder_a",
    angle: float | None = None,
    overlap: float = WALL_OVERLAP,
) -> list[SpaceJunk]:
    """Place prefab segments along a line with overlap so hulls do not leak."""
    delta = end - start
    length = delta.length()
    if length <= 1e-6:
        return []
    piece = instantiate_junk(prefab, Vec2(), angle=0.0)
    spacing = max(8.0, 2.0 * piece.approximate_radius() - overlap)
    direction = delta.normalized()
    heading = angle if angle is not None else math.atan2(direction.y, direction.x)
    count = max(1, int(math.ceil(length / spacing)))
    out: list[SpaceJunk] = []
    for i in range(count):
        t = (i + 0.5) / count
        pos = start + direction * (length * t)
        out.append(instantiate_junk(prefab, pos, angle=heading))
    return out


def junk_arc(
    center: Vec2,
    radius: float,
    start_deg: float,
    end_deg: float,
    *,
    prefab: str = "rib_arc_a",
    spacing: float | None = None,
) -> list[SpaceJunk]:
    piece = instantiate_junk(prefab, Vec2(), angle=0.0)
    step = spacing if spacing is not None else max(24.0, piece.approximate_radius() * 1.4)
    arc_len = abs(end_deg - start_deg) * math.pi / 180.0 * radius
    count = max(1, int(math.ceil(arc_len / step)))
    out: list[SpaceJunk] = []
    for i in range(count):
        t = i / max(1, count - 1) if count > 1 else 0.0
        deg = start_deg + (end_deg - start_deg) * t
        rad = math.radians(deg)
        pos = center + Vec2(math.cos(rad) * radius, math.sin(rad) * radius)
        out.append(instantiate_junk(prefab, pos, angle=rad + math.pi / 2.0))
    return out


def junk_gate_pair(
    center: Vec2,
    width: float,
    *,
    prefab: str = "truss_corner_a",
) -> list[SpaceJunk]:
    half = width * 0.5
    left = instantiate_junk(prefab, center + Vec2(-half, 0.0), angle=math.pi * 0.5)
    right = instantiate_junk(prefab, center + Vec2(half, 0.0), angle=-math.pi * 0.5)
    return [left, right]


def junk_box(
    rect_min: Vec2,
    rect_max: Vec2,
    *,
    prefab: str = "container_a",
    gap: float | None = None,
) -> list[SpaceJunk]:
    """Four walls with optional gap on the top edge center."""
    x0, y0 = rect_min.x, rect_min.y
    x1, y1 = rect_max.x, rect_max.y
    top_start = Vec2(x0, y0)
    top_end = Vec2(x1, y0)
    if gap is not None and gap > 0:
        mid = (x0 + x1) * 0.5
        half_gap = gap * 0.5
        walls = junk_wall_line(Vec2(x0, y0), Vec2(mid - half_gap, y0), prefab=prefab, angle=0.0)
        walls += junk_wall_line(Vec2(mid + half_gap, y0), Vec2(x1, y0), prefab=prefab, angle=0.0)
    else:
        walls = junk_wall_line(top_start, top_end, prefab=prefab, angle=0.0)
    walls += junk_wall_line(Vec2(x1, y0), Vec2(x1, y1), prefab=prefab, angle=math.pi * 0.5)
    walls += junk_wall_line(Vec2(x1, y1), Vec2(x0, y1), prefab=prefab, angle=math.pi)
    walls += junk_wall_line(Vec2(x0, y1), Vec2(x0, y0), prefab=prefab, angle=-math.pi * 0.5)
    return walls


def min_gate_gap_for_ship(ship_radius: float = DEFAULT_SHIP_RADIUS) -> float:
    return 2 * ship_radius + 8.0
