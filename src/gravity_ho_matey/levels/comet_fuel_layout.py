from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.comet_body import CometBody
from gravity_ho_matey.gameplay.entities import FinishGate, GravityWell, Ship

ORBITAL_WIDTH = 4800
ORBITAL_HEIGHT = 3200
COMET_PATH_CENTER = Vec2(3000.0, 1750.0)
COMET_SEMI_MAJOR = 680.0
COMET_SEMI_MINOR = 420.0
COMET_ANGULAR_SPEED = 0.045
COMET_SURFACE_RADIUS = 180.0
COMET_LANDING_INNER = 132.0
COMET_LANDING_OUTER = 310.0
COMET_SPAWN_PHASE = 2.8

ORBITAL_DEBRIS_EXCLUDE_INNER = 320.0
ORBITAL_DEBRIS_EXCLUDE_OUTER = 580.0
ORBITAL_DEBRIS_RING_MIN = 600.0
ORBITAL_DEBRIS_RING_MAX = 820.0

DELIVERY_POINT = Vec2(920.0, 1520.0)
DELIVERY_RADIUS = 72.0
GATE_HALF = 42.0

EXPEDITION_WIDTH = 2400
EXPEDITION_HEIGHT = 1800
LANDER_PAD = Vec2(1200.0, 1500.0)

LANDING_CHARGE_SECONDS = 1.0
EXTRACT_CHARGE_SECONDS = 1.0
FUEL_LOAD_CHARGE_SECONDS = 1.2
DELIVERY_CHARGE_SECONDS = 1.0
CINEMATIC_DEFAULT_SECONDS = 4.5
FUEL_NODES_REQUIRED = 3
EXPEDITION_SQUID_COUNT = 16
EXPEDITION_FEEDING_SQUID_COUNT = 10
FUEL_FEED_LINE_COUNT = 6


@dataclass(frozen=True, slots=True)
class CometFuelOrbitalLayout:
    width: int
    height: int
    spawn_ship: Ship
    finish_gate: FinishGate
    delivery_point: Vec2
    comet: CometBody
    wells: tuple[GravityWell, ...]


def build_comet_fuel_orbital_layout() -> CometFuelOrbitalLayout:
    comet = CometBody(
        path_center=COMET_PATH_CENTER,
        orbit_semi_major=COMET_SEMI_MAJOR,
        orbit_semi_minor=COMET_SEMI_MINOR,
        angular_speed=COMET_ANGULAR_SPEED,
        surface_radius=COMET_SURFACE_RADIUS,
        landing_band_inner=COMET_LANDING_INNER,
        landing_band_outer=COMET_LANDING_OUTER,
        phase=COMET_SPAWN_PHASE,
    )
    pos = comet.position()
    comet_well = GravityWell(
        pos,
        strength=28000.0,
        radius=COMET_SURFACE_RADIUS * 2.2,
        label="Volatile Comet",
        kind="planet",
    )
    debris_wells = (
        GravityWell(
            Vec2(1800.0, 1100.0),
            strength=32000.0,
            radius=180.0 * 3.6,
            label="Shard Maw",
            kind="black_hole",
            maw_radius=11.0,
        ),
        GravityWell(
            Vec2(1100.0, 2400.0),
            strength=30000.0,
            radius=170.0 * 3.6,
            label="Tide Sink",
            kind="black_hole",
            maw_radius=11.0,
        ),
    )
    gate = FinishGate(
        Rect(
            DELIVERY_POINT.x + 140.0 - GATE_HALF,
            DELIVERY_POINT.y - GATE_HALF,
            GATE_HALF * 2.0,
            GATE_HALF * 2.0,
        )
    )
    spawn = Ship(pos=Vec2(680.0, 1560.0), angle=0.08)
    return CometFuelOrbitalLayout(
        width=ORBITAL_WIDTH,
        height=ORBITAL_HEIGHT,
        spawn_ship=spawn,
        finish_gate=gate,
        delivery_point=DELIVERY_POINT,
        comet=comet,
        wells=(comet_well, *debris_wells),
    )
