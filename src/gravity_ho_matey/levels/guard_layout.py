from __future__ import annotations

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
RELAY_INGRESS_BOSS_SPEED = 145.0
# Brood-Mother pops tight on the relay hull (wave 3) — south quarter, not down-lane.
_MEGA_SQUID_BOSS_RADIUS = 42.0
_BOSS_STATION_CLEARANCE = 14.0
BOSS_SPAWN = Vec2(
    STATION_RELAY.x,
    STATION_RELAY.y + STATION_RADIUS + _MEGA_SQUID_BOSS_RADIUS + _BOSS_STATION_CLEARANCE,
)
# Legacy far-south spawn was PLAYER_SPAWN.y + 140 (~270 from relay anchor).
BOSS_SPAWN_RELAY_OFFSET = BOSS_SPAWN.y - STATION_RELAY.y
WAVE1_INGRESS_Y = 480.0
SQUID_SPAWN_RADIUS = 1320.0


@dataclass(frozen=True, slots=True)
class GuardLayout:
    width: int
    height: int
    spawn_ship: Ship
    finish_gate: FinishGate
    station_anchor: Vec2
    wells: tuple[GravityWell, ...]
    squid_ring_center: Vec2


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
            strength=52000.0,
            radius=280.0 * 6.0,
            label="Graviton Maw",
            kind="black_hole",
            maw_radius=14.0,
        ),
        GravityWell(
            Vec2(3380.0, 900.0),
            strength=51000.0,
            radius=270.0 * 6.0,
            label="Void Sink",
            kind="black_hole",
            maw_radius=14.0,
        ),
        GravityWell(
            Vec2(CENTER.x, 520.0),
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
        squid_ring_center=CENTER,
    )
