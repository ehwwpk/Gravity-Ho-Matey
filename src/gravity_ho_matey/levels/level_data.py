from __future__ import annotations

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Beacon, FinishGate, GravityWell, Ship, Wall, WorldConfig
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.settings import CANVAS_HEIGHT, CANVAS_WIDTH


def build_cove_run_level() -> GameWorld:
    walls = [
        # Outer cove rocks.
        Wall(Rect(0, 0, CANVAS_WIDTH, 22)),
        Wall(Rect(0, CANVAS_HEIGHT - 22, CANVAS_WIDTH, 22)),
        Wall(Rect(0, 0, 22, CANVAS_HEIGHT)),
        Wall(Rect(CANVAS_WIDTH - 22, 0, 22, CANVAS_HEIGHT)),
        # Light interior obstacles (~70% fewer maze walls than original).
        Wall(Rect(145, 490, 250, 34)),
        Wall(Rect(650, 300, 34, 245)),
    ]
    wells = [
        GravityWell(Vec2(240, 420), strength=34000, radius=210, label="Black Rum Eddy"),
        GravityWell(Vec2(470, 295), strength=42000, radius=235, label="Dead Star Reef"),
        GravityWell(Vec2(705, 120), strength=31000, radius=185, label="Kraken Moon"),
        GravityWell(Vec2(720, 430), strength=39000, radius=210, label="Maelstrom"),
    ]
    beacons = [
        Beacon(Vec2(95, 560)),
        Beacon(Vec2(335, 90)),
        Beacon(Vec2(600, 390)),
        Beacon(Vec2(870, 115)),
    ]
    return GameWorld(
        config=WorldConfig(width=CANVAS_WIDTH, height=CANVAS_HEIGHT),
        ship=Ship(pos=Vec2(80, 70), angle=0.58),
        walls=walls,
        wells=wells,
        beacons=beacons,
        finish_gate=FinishGate(Rect(880, 550, 54, 54)),
    )
