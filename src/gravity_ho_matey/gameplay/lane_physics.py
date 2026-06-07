from __future__ import annotations

import math
from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.boost_lane import LaneProbe, LaneState
from gravity_ho_matey.gameplay.entities import Ship

# On-ribbon only — no forward shove, just cruise bonuses.
_ON_RIBBON_THRUST_MULT = 1.06
_ON_RIBBON_MAX_SPEED_MULT = 1.12
_ON_RIBBON_DRAG = 0.998


@dataclass(frozen=True, slots=True)
class LaneModifiers:
    gravity_scale: float
    drag: float
    thrust_mult: float
    max_speed: float
    center_accel: float


def _neutral_mods(*, base_drag: float, base_max_speed: float) -> LaneModifiers:
    return LaneModifiers(
        gravity_scale=1.0,
        drag=base_drag,
        thrust_mult=1.0,
        max_speed=base_max_speed,
        center_accel=0.0,
    )


def lane_modifiers(
    probe: LaneProbe,
    *,
    base_drag: float,
    base_max_speed: float,
) -> LaneModifiers:
    if probe.state is not LaneState.ON_RIBBON:
        return _neutral_mods(base_drag=base_drag, base_max_speed=base_max_speed)
    return LaneModifiers(
        gravity_scale=1.0,
        drag=min(_ON_RIBBON_DRAG, base_drag + 0.008),
        thrust_mult=_ON_RIBBON_THRUST_MULT,
        max_speed=base_max_speed * _ON_RIBBON_MAX_SPEED_MULT,
        center_accel=0.0,
    )


def apply_lane_centering(accel: Vec2, probe: LaneProbe, mods: LaneModifiers) -> Vec2:
    if mods.center_accel <= 0.0 or probe.state is not LaneState.ON_RIBBON:
        return accel
    tangent = probe.tangent
    if tangent.length_sq() < 1e-9:
        return accel
    return accel + tangent.normalized() * mods.center_accel


def ribbon_tangent_angle(probe: LaneProbe) -> float:
    tangent = probe.tangent
    return math.atan2(tangent.y, tangent.x)
