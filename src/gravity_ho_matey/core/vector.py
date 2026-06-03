from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> "Vec2":
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide Vec2 by zero.")
        return Vec2(self.x / scalar, self.y / scalar)

    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def length(self) -> float:
        return math.sqrt(self.length_sq())

    def normalized(self) -> "Vec2":
        mag = self.length()
        if mag <= 1e-9:
            return Vec2()
        return self / mag

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def clamped_length(self, max_length: float) -> "Vec2":
        mag = self.length()
        if mag <= max_length or mag <= 1e-9:
            return self
        return self.normalized() * max_length

    def rotated(self, radians: float) -> "Vec2":
        c = math.cos(radians)
        s = math.sin(radians)
        return Vec2(self.x * c - self.y * s, self.x * s + self.y * c)

    @staticmethod
    def from_angle(radians: float) -> "Vec2":
        return Vec2(math.cos(radians), math.sin(radians))
