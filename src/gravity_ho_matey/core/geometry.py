from __future__ import annotations

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
