from __future__ import annotations

import math
from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2


@dataclass(frozen=True, slots=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def contains_point(self, p: Vec2) -> bool:
        return self.left <= p.x <= self.right and self.top <= p.y <= self.bottom

    def expanded(self, amount: float) -> "Rect":
        return Rect(self.x - amount, self.y - amount, self.w + amount * 2, self.h + amount * 2)

    def intersects_circle(self, center: Vec2, radius: float) -> bool:
        nearest_x = min(max(center.x, self.left), self.right)
        nearest_y = min(max(center.y, self.top), self.bottom)
        dx = center.x - nearest_x
        dy = center.y - nearest_y
        return dx * dx + dy * dy <= radius * radius


def _cross(ax: float, ay: float, bx: float, by: float) -> float:
    return ax * by - ay * bx


def closest_point_on_segment(point: Vec2, a: Vec2, b: Vec2) -> Vec2:
    ab = b - a
    len_sq = ab.length_sq()
    if len_sq <= 1e-12:
        return Vec2(a.x, a.y)
    t = max(0.0, min(1.0, (point - a).dot(ab) / len_sq))
    return a + ab * t


def point_in_convex_polygon(point: Vec2, vertices: list[Vec2]) -> bool:
    if len(vertices) < 3:
        return False
    sign = 0
    count = len(vertices)
    for i in range(count):
        a = vertices[i]
        b = vertices[(i + 1) % count]
        cross = _cross(b.x - a.x, b.y - a.y, point.x - a.x, point.y - a.y)
        if abs(cross) <= 1e-9:
            continue
        current = 1 if cross > 0 else -1
        if sign == 0:
            sign = current
        elif current != sign:
            return False
    return sign != 0


def polygon_aabb(vertices: list[Vec2]) -> Rect:
    xs = [v.x for v in vertices]
    ys = [v.y for v in vertices]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    return Rect(x0, y0, x1 - x0, y1 - y0)


def circle_intersects_convex_polygon(center: Vec2, radius: float, vertices: list[Vec2]) -> bool:
    if len(vertices) < 3:
        return False
    if point_in_convex_polygon(center, vertices):
        return True
    r_sq = radius * radius
    count = len(vertices)
    for i in range(count):
        closest = closest_point_on_segment(center, vertices[i], vertices[(i + 1) % count])
        delta = center - closest
        if delta.length_sq() <= r_sq:
            return True
    return False


def nearest_point_on_polygon_boundary(point: Vec2, vertices: list[Vec2]) -> tuple[Vec2, float]:
    if len(vertices) < 2:
        return point, 0.0
    best = vertices[0]
    best_dist_sq = (point - best).length_sq()
    count = len(vertices)
    for i in range(count):
        closest = closest_point_on_segment(point, vertices[i], vertices[(i + 1) % count])
        dist_sq = (point - closest).length_sq()
        if dist_sq < best_dist_sq:
            best_dist_sq = dist_sq
            best = closest
    return best, math.sqrt(best_dist_sq)

