from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import FinishGate, GravityWell, Ship
from gravity_ho_matey.levels.level_profiles import BELT_CRUISE_SPEED

ARENA_SIZE = 4800
CENTER = Vec2(ARENA_SIZE * 0.5, ARENA_SIZE * 0.5)
BELT_SPACING = BELT_CRUISE_SPEED
SPAWN_CLEAR_RADIUS = 180.0
FINISH_PAST_FINAL_SEC = 1.5
FINISH_PAST_FINAL = FINISH_PAST_FINAL_SEC * BELT_CRUISE_SPEED

RING_SPECS: tuple[tuple[float, int, tuple[str, ...]], ...] = (
    (220.0, 12, ("pebble", "pebble", "rock")),
    (440.0, 14, ("pebble", "rock", "rock")),
    (660.0, 16, ("rock", "rock", "pebble", "rock")),
    (880.0, 16, ("rock", "rock", "boulder", "pebble")),
    (1100.0, 14, ("rock", "boulder", "rock", "pebble")),
    (1320.0, 12, ("boulder", "rock", "rock", "pebble")),
    (1980.0, 22, ("pebble", "rock", "rock", "rock", "boulder", "rock")),
)

FINAL_RING_RADIUS = RING_SPECS[-1][0]
FINISH_ORBIT_RADIUS = FINAL_RING_RADIUS + FINISH_PAST_FINAL

# Far-off titans — massive gravity footprint, small lethal maw (Drift mega wells).
TITAN_WELL_RADIUS_SCALE = 5.0
TITAN_WELLS: tuple[GravityWell, ...] = (
    GravityWell(
        Vec2(CENTER.x - 920.0, CENTER.y - 780.0),
        strength=54000.0,
        radius=310.0 * TITAN_WELL_RADIUS_SCALE,
        label="Graviton Kraken",
        kind="black_hole",
        maw_radius=14.0,
    ),
    GravityWell(
        Vec2(CENTER.x + 880.0, CENTER.y + 960.0),
        strength=51000.0,
        radius=295.0 * TITAN_WELL_RADIUS_SCALE,
        label="Void Leech",
        kind="black_hole",
        maw_radius=14.0,
    ),
    GravityWell(
        Vec2(CENTER.x + 1020.0, CENTER.y - 880.0),
        strength=53000.0,
        radius=305.0 * TITAN_WELL_RADIUS_SCALE,
        label="Rift Leviathan",
        kind="black_hole",
        maw_radius=14.0,
    ),
    GravityWell(
        Vec2(CENTER.x - 1280.0, CENTER.y + 420.0),
        strength=52000.0,
        radius=300.0 * TITAN_WELL_RADIUS_SCALE,
        label="Abyss Maw",
        kind="black_hole",
        maw_radius=14.0,
    ),
)

# Squid nest — just inside the final dense belt (prowling angles in degrees).
SQUID_RING_RADIUS = FINAL_RING_RADIUS - 60.0
SQUID_ANGLES_DEG: tuple[float, ...] = (35.0, 95.0, 155.0, 215.0, 275.0)


@dataclass(frozen=True, slots=True)
class DriftLayout:
    center: Vec2
    spawn_ship: Ship
    finish_gate: FinishGate
    wells: tuple[GravityWell, ...]
    squid_angles_deg: tuple[float, ...]
    squid_ring_radius: float


def build_drift_layout() -> DriftLayout:
    finish_center = Vec2(CENTER.x, CENTER.y - FINISH_ORBIT_RADIUS)
    gate_half = 28.0
    return DriftLayout(
        center=CENTER,
        spawn_ship=Ship(pos=Vec2(CENTER.x, CENTER.y), angle=1.5708),
        finish_gate=FinishGate(
            Rect(
                finish_center.x - gate_half,
                finish_center.y - gate_half,
                gate_half * 2.0,
                gate_half * 2.0,
            )
        ),
        wells=TITAN_WELLS,
        squid_angles_deg=SQUID_ANGLES_DEG,
        squid_ring_radius=SQUID_RING_RADIUS,
    )
