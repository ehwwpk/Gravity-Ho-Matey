from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Ship
from gravity_ho_matey.gameplay.planet_mission import in_planet_landing_band, limb_point_toward
from gravity_ho_matey.levels.brood_moon_layout import (
    BOSS_COMBAT_RADIUS,
    CINEMATIC_DEFAULT_SECONDS,
    LANDING_CHARGE_SECONDS,
    LIFTOFF_CHARGE_SECONDS,
    SEAL_TRAVEL_DISTANCE,
    BroodMoonOrbitalLayout,
)

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_NARRATIVE_DIR = _PACKAGE_ROOT / "assets" / "narrative"


class BroodPhase(Enum):
    ORBITAL = auto()
    LANDING_CINEMATIC = auto()
    SURFACE = auto()
    ASCENT_CINEMATIC = auto()
    ORBITAL_RETURN = auto()


@dataclass(slots=True)
class BroodMoonState:
    phase: BroodPhase = BroodPhase.ORBITAL
    layout: BroodMoonOrbitalLayout | None = None
    landing_charge: float = 0.0
    liftoff_charge: float = 0.0
    cinematic_elapsed: float = 0.0
    cinematic_seconds: float = CINEMATIC_DEFAULT_SECONDS
    cinematic_kind: str = "landing"
    seal_travel: float = 0.0
    seal_complete: bool = False
    objectives_complete: bool = False
    boss_spawned: bool = False
    boss_intro_flash: float = 0.0
    ascent_ready: bool = False
    dock_unlocked: bool = False
    last_ship_x: float = 0.0
    orbital_ship_pos: Vec2 = field(default_factory=Vec2)
    orbital_ship_vel: Vec2 = field(default_factory=Vec2)
    orbital_ship_angle: float = 0.0
    hud_prompt: str = ""
    transition_asset_stem: str = ""
    terrain_scrape_cd: float = 0.0

    @property
    def in_cinematic(self) -> bool:
        return self.phase in (BroodPhase.LANDING_CINEMATIC, BroodPhase.ASCENT_CINEMATIC)

    @property
    def on_surface(self) -> bool:
        return self.phase is BroodPhase.SURFACE


def resolve_transition_asset(stem: str) -> Path | None:
    for ext in (".gif", ".png"):
        path = _NARRATIVE_DIR / f"{stem}{ext}"
        if path.is_file():
            return path
    if stem.startswith("brood_moon_"):
        for ext in (".gif", ".png"):
            fallback = _NARRATIVE_DIR / f"cove{ext}"
            if fallback.is_file():
                return fallback
    return None


def transition_playback_seconds(stem: str, measured: float | None) -> float:
    if measured is not None and measured > 0.5:
        return measured
    return CINEMATIC_DEFAULT_SECONDS


def in_landing_zone(ship_pos: Vec2, layout: BroodMoonOrbitalLayout) -> bool:
    return in_planet_landing_band(ship_pos, layout.planet)


def landing_limb_hint(ship_pos: Vec2, layout: BroodMoonOrbitalLayout) -> Vec2:
    return limb_point_toward(ship_pos, layout.planet)


def in_orbital_space_phase(phase: BroodPhase) -> bool:
    """Orbital approach / RTB — surface combat and escort fire stay grounded."""
    return phase in (
        BroodPhase.ORBITAL,
        BroodPhase.ORBITAL_RETURN,
        BroodPhase.LANDING_CINEMATIC,
        BroodPhase.ASCENT_CINEMATIC,
    )


def liftoff_blocked(world) -> bool:
    bm = world.brood_moon
    boss = world.mega_squid
    if bm is None or not bm.on_surface or boss is None or not boss.alive:
        return False
    dist = (world.ship.pos - boss.pos).length()
    return dist <= BOSS_COMBAT_RADIUS


def surface_objectives_met(world) -> bool:
    if not world.beacons:
        beacons_done = True
    else:
        beacons_done = world.beacons_remaining == 0
    pods_done = not any(pod.alive for pod in world.egg_pods)
    return beacons_done and pods_done


def tick_seal_progress(world, dt: float) -> None:
    _ = dt
    bm = world.brood_moon
    if bm is None or not bm.on_surface or not bm.objectives_complete or bm.seal_complete:
        return
    wrap_width = float(world.config.width)
    dx = world.ship.pos.x - bm.last_ship_x
    if abs(dx) > wrap_width * 0.5:
        dx -= wrap_width if dx > 0.0 else -wrap_width
    bm.seal_travel += abs(dx)
    bm.last_ship_x = world.ship.pos.x
    if bm.seal_travel >= SEAL_TRAVEL_DISTANCE:
        bm.seal_complete = True
        bm.ascent_ready = True
        bm.hud_prompt = "SEAL COMPLETE — HOLD E TO ASCEND"


def wrap_surface_x(x: float, wrap_width: float) -> float:
    if wrap_width <= 0.0:
        return x
    while x < 0.0:
        x += wrap_width
    while x >= wrap_width:
        x -= wrap_width
    return x
