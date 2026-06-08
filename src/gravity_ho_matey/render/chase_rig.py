"""Unified chase banking — ship sprite, HUD horizon, and camera slip share one rig."""

from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.render.camera import CHASE_SCREEN_HEADING

# ~11° max bank — readable cockpit roll without losing horizon context.
BANK_MAX_RAD = math.radians(11.0)
_TURN_BANK_GAIN = 0.00062
_SLIP_BANK_GAIN = 0.55
_HIGHWAY_SLIP_GAIN = 0.28
_HIGHWAY_TURN_SCALE = 0.35


def slip_angle_rad(vel: Vec2, ship_angle: float) -> float:
    if vel.length_sq() < 16.0:
        return 0.0
    forward = Vec2.from_angle(ship_angle)
    right = forward.rotated(math.pi / 2.0)
    fwd = vel.dot(forward)
    lat = vel.dot(right)
    return math.atan2(lat, max(abs(fwd), 10.0))


def chase_bank_offset_rad(
    vel: Vec2,
    ship_angle: float,
    *,
    turn_rate: float = 0.0,
    on_highway: bool = False,
) -> float:
    """Signed bank offset (radians) from screen-up — positive rolls right wing down."""
    slip = slip_angle_rad(vel, ship_angle)
    slip_gain = _HIGHWAY_SLIP_GAIN if on_highway else _SLIP_BANK_GAIN
    turn_scale = _HIGHWAY_TURN_SCALE if on_highway else 1.0
    turn_cap = BANK_MAX_RAD * 0.55
    slip_cap = BANK_MAX_RAD * 0.88
    turn_bank = max(-turn_cap, min(turn_cap, turn_rate * _TURN_BANK_GAIN * turn_scale))
    slip_bank = max(-slip_cap, min(slip_cap, slip * slip_gain))
    combined = turn_bank + slip_bank
    return max(-BANK_MAX_RAD, min(BANK_MAX_RAD, combined))


def chase_bank_display_angle(
    vel: Vec2,
    ship_angle: float,
    *,
    turn_rate: float = 0.0,
    on_highway: bool = False,
) -> float:
    """Full Tk draw angle for chase ship sprite."""
    return CHASE_SCREEN_HEADING + chase_bank_offset_rad(
        vel, ship_angle, turn_rate=turn_rate, on_highway=on_highway,
    )
