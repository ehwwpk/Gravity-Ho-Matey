from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import FinishGate, GravityWell, Ship

ARENA_WIDTH = 5200
ARENA_HEIGHT = 3200
CENTER = Vec2(ARENA_WIDTH * 0.5, ARENA_HEIGHT * 0.5)
SPIRAL_CENTER = CENTER
SPAWN_CLEAR_RADIUS = 200.0
SPIRAL_INNER = 380.0
SPIRAL_OUTER = 920.0
STATION_EXCLUSION = 280.0
ROSTER_KILL_QUOTA = 12
ALLY_WING_COUNT = 12
ROSTER_ENEMY_COUNT = 12

PLAYER_SPAWN = Vec2(420.0, 1600.0)
STATION_ANCHOR = Vec2(4680.0, 1600.0)
GATE_RECT = Rect(5060.0, 1480.0, 80.0, 240.0)


@dataclass(frozen=True, slots=True)
class SiegeLayout:
    width: int
    height: int
    spawn_ship: Ship
    finish_gate: FinishGate
    station_anchor: Vec2
    spiral_center: Vec2
    wells: tuple[GravityWell, ...]


def build_siege_layout() -> SiegeLayout:
    wells = (
        GravityWell(
            Vec2(CENTER.x, 400.0),
            strength=42000.0,
            radius=180.0,
            label="North Rift",
            kind="black_hole",
            maw_radius=12.0,
        ),
        GravityWell(
            Vec2(CENTER.x, 2800.0),
            strength=40000.0,
            radius=175.0,
            label="South Pit",
            kind="black_hole",
            maw_radius=12.0,
        ),
        GravityWell(
            Vec2(600.0, 600.0),
            strength=36000.0,
            radius=160.0,
            label="NW Singularity",
            kind="black_hole",
            maw_radius=11.0,
        ),
        GravityWell(
            Vec2(4600.0, 2600.0),
            strength=37000.0,
            radius=165.0,
            label="SE Singularity",
            kind="black_hole",
            maw_radius=11.0,
        ),
    )
    return SiegeLayout(
        width=ARENA_WIDTH,
        height=ARENA_HEIGHT,
        spawn_ship=Ship(pos=Vec2(PLAYER_SPAWN.x, PLAYER_SPAWN.y), angle=0.0),
        finish_gate=FinishGate(GATE_RECT),
        station_anchor=STATION_ANCHOR,
        spiral_center=SPIRAL_CENTER,
        wells=wells,
    )
