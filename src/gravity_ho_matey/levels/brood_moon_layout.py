from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import FinishGate, GravityWell, Ship
from gravity_ho_matey.gameplay.planet_mission import PlanetBody

ORBITAL_WIDTH = 4800
ORBITAL_HEIGHT = 3200
MOON_CENTER = Vec2(3400.0, 1900.0)
MOON_RADIUS = 520.0
# Full-limb landing shell — approach anywhere on the moon's edge, not a single patch.
LANDING_BAND_INNER_SLACK = 52.0
# Tighter limb shell — less sideways orbiting before hold-to-land reads true.
LANDING_BAND_OUTER_SLACK = 130.0
# Orbital debris must not spawn inside the landing approach shell.
ORBITAL_DEBRIS_EXCLUDE_INNER = 450.0
ORBITAL_DEBRIS_EXCLUDE_OUTER = 760.0
ORBITAL_DEBRIS_RING_MIN = 780.0
ORBITAL_DEBRIS_RING_MAX = 920.0
ORBITAL_ASTEROID_THREAT_RADIUS = 520.0
DOCK_GATE_CENTER = Vec2(820.0, 1580.0)
DOCK_GATE_HALF = 38.0

# Toroidal nursery run — 9240u (~30% shorter than prior 13200 seal lap).
SURFACE_WRAP_WIDTH = 9240
SURFACE_HEIGHT = 2200
SURFACE_SPAWN_FRAC = 0.032
SURFACE_SPAWN = Vec2(SURFACE_WRAP_WIDTH * SURFACE_SPAWN_FRAC, 1200.0)
SURFACE_FLOOR_Y = 1680.0
SURFACE_SCRAPE_Y = 1720.0
SURFACE_CEILING_Y = 520.0
SURFACE_EXOSPHERE_Y = 380.0
# Third beacon marks the nursery exit lane; boss nests just up-track of it.
SURFACE_FINAL_BEACON_FRAC = 0.78
SURFACE_BOSS_LEFT_OF_FINAL_FRAC = 0.045
SURFACE_BOSS_ANCHOR_FRAC = SURFACE_FINAL_BEACON_FRAC - SURFACE_BOSS_LEFT_OF_FINAL_FRAC
BOSS_ANCHOR = Vec2(SURFACE_WRAP_WIDTH * SURFACE_BOSS_ANCHOR_FRAC, 980.0)

BEACON_COUNT = 3
EGG_POD_COUNT = 8
LANDING_CHARGE_SECONDS = 1.0
LIFTOFF_CHARGE_SECONDS = 1.0
CINEMATIC_DEFAULT_SECONDS = 4.5
BOSS_COMBAT_RADIUS = 920.0
SEAL_TRAVEL_DISTANCE = SURFACE_WRAP_WIDTH
# Nursery skim — gentle downward pull (added to ship accel on surface phase).
SURFACE_GRAVITY_ACCEL = 38.0


@dataclass(frozen=True, slots=True)
class BroodMoonOrbitalLayout:
    width: int
    height: int
    spawn_ship: Ship
    finish_gate: FinishGate
    moon_well: GravityWell
    planet: PlanetBody
    wells: tuple[GravityWell, ...]


def build_brood_moon_orbital_layout() -> BroodMoonOrbitalLayout:
    moon_well = GravityWell(
        MOON_CENTER,
        strength=62000.0,
        radius=MOON_RADIUS * 2.4,
        label="Brood Moon",
        kind="planet",
    )
    debris_wells = (
        GravityWell(
            Vec2(2100.0, 900.0),
            strength=38000.0,
            radius=200.0 * 4.0,
            label="Shard Maw",
            kind="black_hole",
            maw_radius=12.0,
        ),
        GravityWell(
            Vec2(1200.0, 2500.0),
            strength=36000.0,
            radius=190.0 * 4.0,
            label="Tide Sink",
            kind="black_hole",
            maw_radius=12.0,
        ),
    )
    gate = FinishGate(
        Rect(
            DOCK_GATE_CENTER.x - DOCK_GATE_HALF,
            DOCK_GATE_CENTER.y - DOCK_GATE_HALF,
            DOCK_GATE_HALF * 2.0,
            DOCK_GATE_HALF * 2.0,
        )
    )
    spawn = Ship(pos=Vec2(620.0, 1580.0), angle=0.12)
    planet = PlanetBody.from_surface_radius(
        MOON_CENTER,
        MOON_RADIUS,
        inner_slack=LANDING_BAND_INNER_SLACK,
        outer_slack=LANDING_BAND_OUTER_SLACK,
    )
    return BroodMoonOrbitalLayout(
        width=ORBITAL_WIDTH,
        height=ORBITAL_HEIGHT,
        spawn_ship=spawn,
        finish_gate=gate,
        moon_well=moon_well,
        planet=planet,
        wells=(moon_well, *debris_wells),
    )
