from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Asteroid, Ship


def resolve_rubber_hull_bounce(ship: Ship, asteroid: Asteroid) -> None:
    """Push the ship off the asteroid and reflect velocity — no hull damage."""
    delta = ship.pos - asteroid.pos
    dist_sq = delta.length_sq()
    if dist_sq <= 1e-9:
        normal = Vec2.from_angle(ship.angle + 3.14159)
    else:
        normal = delta.normalized()
    reach = asteroid.approximate_radius() + ship.radius
    dist = dist_sq**0.5
    overlap = reach - dist
    if overlap > 0.0:
        ship.pos = ship.pos + normal * (overlap + 3.0)
    v_dot_n = ship.vel.dot(normal)
    if v_dot_n < 0.0:
        ship.vel = ship.vel - normal * (2.0 * v_dot_n * 0.88)
