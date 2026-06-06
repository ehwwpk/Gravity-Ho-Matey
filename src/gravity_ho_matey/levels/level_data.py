from __future__ import annotations

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Beacon, FinishGate, GravityWell, Ship, WorldConfig
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.solar_patrols import solar_patrol_enemies
from gravity_ho_matey.settings import CANVAS_HEIGHT, CANVAS_WIDTH


def build_cove_run_level() -> GameWorld:
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
            viewport_width=CANVAS_WIDTH,
            viewport_height=CANVAS_HEIGHT,
            level_theme="cove",
            level_name="Smuggler's Cove",
            open_bounds=True,
        ),
        ship=Ship(pos=Vec2(80, 70), angle=0.58),
        walls=[],
        wells=wells,
        beacons=beacons,
        finish_gate=FinishGate(Rect(880, 550, 54, 54)),
    )


SOLAR_STRIP_HEIGHT = 1680


def build_solar_crossing_level() -> GameWorld:
    """Level 2 — vertical star strip; free forward/back flight with central singularity."""
    cx = CANVAS_WIDTH / 2
    strip_h = SOLAR_STRIP_HEIGHT
    wells = [
        GravityWell(
            Vec2(cx, strip_h * 0.5),
            strength=52000,
            radius=155,
            label="Singularity",
            kind="black_hole",
            maw_radius=22,
        ),
        GravityWell(Vec2(cx, 180), strength=19000, radius=78, label="Scorched Prince", kind="planet"),
        GravityWell(Vec2(755, strip_h * 0.38), strength=24000, radius=92, label="Verdant Shell", kind="planet"),
        GravityWell(Vec2(205, strip_h * 0.62), strength=21000, radius=82, label="Rust Belt", kind="planet"),
        GravityWell(Vec2(795, strip_h * 0.72), strength=27000, radius=118, label="Jolly Giant", kind="planet"),
        GravityWell(Vec2(175, strip_h * 0.28), strength=20000, radius=76, label="Ice Halo", kind="planet"),
    ]
    beacons = [
        Beacon(Vec2(915, strip_h * 0.22)),
        Beacon(Vec2(480, strip_h * 0.52)),
        Beacon(Vec2(165, strip_h * 0.78)),
    ]
    return GameWorld(
        config=WorldConfig(
            width=CANVAS_WIDTH,
            height=strip_h,
            viewport_width=CANVAS_WIDTH,
            viewport_height=CANVAS_HEIGHT,
            gravity_scale=0.45,
            turn_rate=5.2,
            thrust=255.0,
            level_theme="solar",
            level_name="Singularity Crossing",
            open_bounds=True,
        ),
        ship=Ship(pos=Vec2(52, 120), angle=1.52),
        walls=[],
        wells=wells,
        beacons=beacons,
        finish_gate=FinishGate(Rect(895, strip_h - 90, 50, 50)),
        enemies=solar_patrol_enemies(strip_h),
    )
