from __future__ import annotations

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GravityWell

_LETHAL_WELL_KINDS = frozenset({"black_hole", "planet"})


def gravity_acceleration_at(point: Vec2, wells: list[GravityWell]) -> Vec2:
    total = Vec2()
    for well in wells:
        delta = well.pos - point
        dist_sq = max(delta.length_sq(), 100.0)
        dist = dist_sq ** 0.5
        if dist > well.radius:
            continue
        falloff = 1.0 - (dist / well.radius)
        # Tuned for arcade readability rather than physical realism.
        magnitude = well.strength * falloff / max(dist, 10.0)
        total += delta.normalized() * magnitude
    return total


def hazard_escape_acceleration_at(
    point: Vec2,
    wells: list[GravityWell],
    *,
    gravity_scale: float,
    default_maw_radius: float = 10.0,
) -> Vec2:
    """Outward steering bias so patrol craft resist diving into lethal maws."""
    escape = Vec2()
    for well in wells:
        if well.kind not in _LETHAL_WELL_KINDS:
            continue

        offset = point - well.pos
        distance = offset.length()
        if distance >= well.radius or distance < 1e-6:
            continue

        maw = well.maw_radius if well.maw_radius is not None else default_maw_radius
        falloff = 1.0 - distance / well.radius
        maw_pressure = max(0.0, 1.0 - distance / max(maw * 5.0, maw + 1.0))
        urgency = max(falloff**1.2, maw_pressure)

        base_thrust = 450.0 if well.kind == "black_hole" else 320.0
        escape += offset.normalized() * (base_thrust * urgency * gravity_scale)

    return escape
