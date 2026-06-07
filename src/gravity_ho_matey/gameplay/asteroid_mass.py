from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2

_REFERENCE_BOULDER_MASS = 5200.0


def polygon_area(vertices: tuple[Vec2, ...]) -> float:
    """Shoelace area for a simple polygon (absolute value)."""
    count = len(vertices)
    if count < 3:
        return 0.0
    area = 0.0
    for i in range(count):
        a = vertices[i]
        b = vertices[(i + 1) % count]
        area += a.x * b.y - b.x * a.y
    return abs(area) * 0.5


def compute_mass(local_verts: tuple[Vec2, ...], *, radius_hint: float) -> float:
    area = polygon_area(local_verts)
    if area > 1e-6:
        return area
    return max(radius_hint * radius_hint, 1.0)


def scale_local_verts(local_verts: tuple[Vec2, ...], factor: float) -> tuple[Vec2, ...]:
    if factor <= 0.0:
        return local_verts
    return tuple(Vec2(v.x * factor, v.y * factor) for v in local_verts)


def size_class_for_scale(scale: float) -> str:
    if scale < 0.55:
        return "pebble"
    return "rock"


def explosion_scale_for_mass(mass: float) -> float:
    if mass <= 0.0:
        return 0.35
    ratio = math.sqrt(mass / _REFERENCE_BOULDER_MASS)
    return max(0.35, min(1.8, ratio))
