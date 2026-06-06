from __future__ import annotations

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Beacon, FinishGate, GravityWell, Ship, Wall, WorldConfig
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.solar_patrols import solar_patrol_enemies
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
        config=WorldConfig(
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            level_theme="cove",
            level_name="Smuggler's Cove",
        ),
        ship=Ship(pos=Vec2(80, 70), angle=0.58),
        walls=walls,
        wells=wells,
        beacons=beacons,
        finish_gate=FinishGate(Rect(880, 550, 54, 54)),
    )


def build_solar_crossing_level() -> GameWorld:
    """Level 2 — open star chart with a central black hole and planetary wells."""
    cx, cy = CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2
    walls = [
        Wall(Rect(0, 0, CANVAS_WIDTH, 18)),
        Wall(Rect(0, CANVAS_HEIGHT - 18, CANVAS_WIDTH, 18)),
        Wall(Rect(0, 0, 18, CANVAS_HEIGHT)),
        Wall(Rect(CANVAS_WIDTH - 18, 0, 18, CANVAS_HEIGHT)),
    ]
    wells = [
        GravityWell(
            Vec2(cx, cy),
            strength=52000,
            radius=155,
            label="Singularity",
            kind="black_hole",
            maw_radius=22,
        ),
        GravityWell(Vec2(cx, 118), strength=19000, radius=78, label="Scorched Prince", kind="planet"),
        GravityWell(Vec2(755, 248), strength=24000, radius=92, label="Verdant Shell", kind="planet"),
        GravityWell(Vec2(205, 455), strength=21000, radius=82, label="Rust Belt", kind="planet"),
        GravityWell(Vec2(795, 495), strength=27000, radius=118, label="Jolly Giant", kind="planet"),
        GravityWell(Vec2(175, 195), strength=20000, radius=76, label="Ice Halo", kind="planet"),
    ]
    beacons = [
        Beacon(Vec2(915, 320)),
        Beacon(Vec2(480, 595)),
        Beacon(Vec2(165, 520)),
    ]
    return GameWorld(
        config=WorldConfig(
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            gravity_scale=0.45,
            turn_rate=5.2,
            thrust=255.0,
            level_theme="solar",
            level_name="Singularity Crossing",
        ),
        ship=Ship(pos=Vec2(52, 320), angle=0.05),
        walls=walls,
        wells=wells,
        beacons=beacons,
        finish_gate=FinishGate(Rect(895, 285, 50, 50)),
        enemies=solar_patrol_enemies(),
    )
