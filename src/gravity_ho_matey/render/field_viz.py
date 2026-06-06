from __future__ import annotations

TACTICAL_FLOW_RADIUS = 360.0


def gravity_emphasis(dist: float, *, radius: float = TACTICAL_FLOW_RADIUS) -> float:
    if dist >= radius:
        return 0.08
    t = 1.0 - dist / radius
    return 0.08 + t * t * 0.92
