from __future__ import annotations

import math
from dataclasses import dataclass

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import FinishGate, GravityWell, Ship
from gravity_ho_matey.gameplay.space_station import STATION_RADIUS

ARENA_WIDTH = 4000
ARENA_HEIGHT = 3200
CENTER = Vec2(ARENA_WIDTH * 0.5, ARENA_HEIGHT * 0.5)
RELAY_Y = 1600.0
STATION_RELAY = Vec2(CENTER.x, RELAY_Y)
# Dock south of the relay — one ship length past the station hull.
_PLAYER_DOCK_GAP = 42.0
PLAYER_SPAWN = Vec2(STATION_RELAY.x, STATION_RELAY.y + STATION_RADIUS + _PLAYER_DOCK_GAP)
EXTRACT_GATE_HALF = 38.0
# South extract pad — same lane as spawn; fly here after the hold is clear.
EXTRACT_PAD_CENTER = Vec2(PLAYER_SPAWN.x, PLAYER_SPAWN.y + 52.0)
RELAY_INGRESS_SQUID_SPEED = 175.0
NORTHERN_RIFT = Vec2(CENTER.x, 520.0)
WAVE1_INGRESS_Y = 480.0
# Wave 1 dual-lane patrol ingress (NW / NE).
WAVE1_NW_SPAWNS = (Vec2(1100.0, 520.0), Vec2(1300.0, 480.0))
WAVE1_NE_SPAWNS = (Vec2(2700.0, 520.0), Vec2(2900.0, 480.0))
# Wave 3 corsair ingress — lateral north approach.
WAVE3_FIGHTER_SPAWNS = (
    Vec2(1050.0, 680.0),
    Vec2(1280.0, 620.0),
    Vec2(2720.0, 620.0),
    Vec2(2950.0, 680.0),
)


@dataclass(frozen=True, slots=True)
class GuardLayout:
    width: int
    height: int
    spawn_ship: Ship
    finish_gate: FinishGate
    station_anchor: Vec2
    wells: tuple[GravityWell, ...]
    squid_ring_center: Vec2


def squid_arc_positions(center: Vec2, count: int, *, seed_offset: int = 0) -> list[Vec2]:
    """Spawn on a south-facing arc from the rift — threats drop into the relay lane."""
    positions: list[Vec2] = []
    arc_center = Vec2(center.x, 880.0)
    radius = 520.0
    arc_span = math.pi * 0.78
    start = math.pi * 0.5 - arc_span * 0.5
    for i in range(count):
        angle = start + arc_span * i / max(1, count - 1) + seed_offset * 0.09
        positions.append(
            arc_center + Vec2(math.cos(angle), math.sin(angle)) * radius
        )
    return positions


def build_extract_gate() -> FinishGate:
    half = EXTRACT_GATE_HALF
    c = EXTRACT_PAD_CENTER
    return FinishGate(
        Rect(c.x - half, c.y - half, half * 2.0, half * 2.0),
    )


def build_guard_layout() -> GuardLayout:
    wells = (
        GravityWell(
            Vec2(620.0, 900.0),
            strength=47800.0,
            radius=280.0 * 5.5,
            label="Graviton Maw",
            kind="black_hole",
            maw_radius=14.0,
        ),
        GravityWell(
            Vec2(3380.0, 900.0),
            strength=46900.0,
            radius=270.0 * 5.5,
            label="Void Sink",
            kind="black_hole",
            maw_radius=14.0,
        ),
        GravityWell(
            NORTHERN_RIFT,
            strength=48000.0,
            radius=250.0 * 6.0,
            label="Northern Rift",
            kind="black_hole",
            maw_radius=14.0,
        ),
    )
    return GuardLayout(
        width=ARENA_WIDTH,
        height=ARENA_HEIGHT,
        spawn_ship=Ship(pos=Vec2(PLAYER_SPAWN.x, PLAYER_SPAWN.y), angle=1.5708),
        finish_gate=build_extract_gate(),
        station_anchor=STATION_RELAY,
        wells=wells,
        squid_ring_center=NORTHERN_RIFT,
    )
