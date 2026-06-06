from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2


def intercept_time(rel: Vec2, target_vel: Vec2, shot_speed: float) -> float | None:
    """Smallest positive t where |rel + target_vel * t| == shot_speed * t."""
    if shot_speed <= 1e-6:
        return None
    a = target_vel.length_sq() - shot_speed * shot_speed
    b = 2.0 * rel.dot(target_vel)
    c = rel.length_sq()
    if abs(a) < 1e-9:
        if abs(b) < 1e-9:
            return None
        t = -c / b
        return t if t > 1e-6 else None
    disc = b * b - 4.0 * a * c
    if disc < 0.0:
        return None
    root = math.sqrt(disc)
    candidates = [t for t in ((-b - root) / (2.0 * a), (-b + root) / (2.0 * a)) if t > 1e-6]
    return min(candidates) if candidates else None


def lead_aim_direction(
    shooter_pos: Vec2,
    target_pos: Vec2,
    target_vel: Vec2,
    shot_speed: float,
    *,
    refine_passes: int = 2,
) -> Vec2 | None:
    """Unit vector toward predicted intercept; falls back to naive lead if no quadratic root."""
    rel = target_pos - shooter_pos
    dist = rel.length()
    if dist < 1e-6:
        return None

    t = intercept_time(rel, target_vel, shot_speed)
    if t is None:
        t = dist / shot_speed

    aim_point = target_pos
    for _ in range(max(1, refine_passes)):
        aim_point = target_pos + target_vel * t
        rel = aim_point - shooter_pos
        next_t = intercept_time(rel, target_vel, shot_speed)
        t = next_t if next_t is not None else rel.length() / shot_speed

    delta = aim_point - shooter_pos
    if delta.length_sq() < 1e-9:
        return None
    return delta.normalized()
