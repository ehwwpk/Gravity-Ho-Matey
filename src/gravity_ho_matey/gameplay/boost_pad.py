from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.boost_lane import LaneState, probe_lane
from gravity_ho_matey.levels.membrane_layout import MembraneLayout


class BoostPadEntity(Protocol):
    pos: Vec2
    vel: Vec2
    radius: float
    boost_flash: float


@dataclass(slots=True)
class BoostPad:
    pos: Vec2
    tangent: Vec2
    radius: float = 52.0
    kick_speed: float = 98.0
    cooldown: float = 0.0
    cooldown_duration: float = 2.4
    pad_flash: float = 0.0


def tick_boost_pads(pads: list[BoostPad], dt: float) -> None:
    for pad in pads:
        if pad.cooldown > 0.0:
            pad.cooldown = max(0.0, pad.cooldown - dt)
        if pad.pad_flash > 0.0:
            pad.pad_flash = max(0.0, pad.pad_flash - dt)


def try_trigger_pad(
    pads: list[BoostPad],
    entity: BoostPadEntity,
    layout: MembraneLayout,
    *,
    pad_flash_seconds: float,
) -> bool:
    probe = probe_lane(entity.pos, layout)
    if probe.state is not LaneState.ON_RIBBON:
        return False
    triggered = False
    for pad in pads:
        if pad.cooldown > 0.0:
            continue
        if (entity.pos - pad.pos).length() > pad.radius + entity.radius:
            continue
        tangent = pad.tangent.normalized()
        entity.vel = entity.vel + tangent * pad.kick_speed
        pad.cooldown = pad.cooldown_duration
        pad.pad_flash = pad_flash_seconds
        entity.boost_flash = max(entity.boost_flash, pad_flash_seconds * 0.85)
        triggered = True
    return triggered
