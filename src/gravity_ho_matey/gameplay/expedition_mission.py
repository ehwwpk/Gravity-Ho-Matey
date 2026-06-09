from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.comet_body import CometBody
from gravity_ho_matey.gameplay.entities import Ship
from gravity_ho_matey.gameplay.planet_mission import in_planet_landing_band, limb_point_toward
from gravity_ho_matey.gameplay.squid_behavior import FuelFeedLine, SquidFeedPoint
from gravity_ho_matey.levels.comet_fuel_layout import (
    CINEMATIC_DEFAULT_SECONDS,
    DELIVERY_CHARGE_SECONDS,
    EXTRACT_CHARGE_SECONDS,
    FUEL_LOAD_CHARGE_SECONDS,
    FUEL_NODES_REQUIRED,
    LANDING_CHARGE_SECONDS,
    CometFuelOrbitalLayout,
)

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_NARRATIVE_DIR = _PACKAGE_ROOT / "assets" / "narrative"


class ExpeditionPhase(Enum):
    ORBITAL = auto()
    DOCK_CINEMATIC = auto()
    ON_FOOT = auto()
    UNDOCK_CINEMATIC = auto()
    ESCAPE_FLIGHT = auto()


class InteractKind(Enum):
    FUEL_VALVE = auto()
    EXTRACT_PAD = auto()
    DELIVERY_BEACON = auto()


@dataclass(frozen=True, slots=True)
class ExpeditionInteractNode:
    id: str
    pos: Vec2
    kind: InteractKind
    charge_seconds: float
    radius: float = 48.0
    one_shot: bool = True
    completed: bool = False


@dataclass(slots=True)
class ExpeditionSquidEntry:
    squid_index: int
    mode: str
    feed_point_id: str | None = None
    alert_timer: float = 0.0


@dataclass(slots=True)
class ExpeditionState:
    phase: ExpeditionPhase = ExpeditionPhase.ORBITAL
    layout: CometFuelOrbitalLayout | None = None
    comet: CometBody | None = None
    landing_charge: float = 0.0
    extract_charge: float = 0.0
    delivery_charge: float = 0.0
    interact_charge: float = 0.0
    active_interact_id: str = ""
    cinematic_elapsed: float = 0.0
    cinematic_seconds: float = CINEMATIC_DEFAULT_SECONDS
    cinematic_kind: str = "dock"
    hud_prompt: str = ""
    transition_asset_stem: str = ""
    fuel_nodes_loaded: int = 0
    hostiles_remaining: int = 0
    fuel_aboard: bool = False
    fuel_delivered: bool = False
    gate_unlocked: bool = False
    parked_ship_pos: Vec2 = field(default_factory=Vec2)
    parked_ship_vel: Vec2 = field(default_factory=Vec2)
    parked_ship_angle: float = 0.0
    feed_lines: list[FuelFeedLine] = field(default_factory=list)
    feed_points: list[SquidFeedPoint] = field(default_factory=list)
    interact_nodes: list[ExpeditionInteractNode] = field(default_factory=list)
    squid_entries: list[ExpeditionSquidEntry] = field(default_factory=list)
    completed_interact_ids: set[str] = field(default_factory=set)
    extract_pending: bool = False
    eva_cling_timer: float = 0.0

    @property
    def in_cinematic(self) -> bool:
        return self.phase in (ExpeditionPhase.DOCK_CINEMATIC, ExpeditionPhase.UNDOCK_CINEMATIC)

    @property
    def on_foot(self) -> bool:
        return self.phase is ExpeditionPhase.ON_FOOT


def is_expedition_foot(config) -> bool:
    return bool(getattr(config, "expedition_foot", False))


def resolve_transition_asset(stem: str) -> Path | None:
    for ext in (".gif", ".png"):
        path = _NARRATIVE_DIR / f"{stem}{ext}"
        if path.is_file():
            return path
    return None


def transition_playback_seconds(stem: str, measured: float | None) -> float:
    if measured is not None and measured > 0.5:
        return measured
    return CINEMATIC_DEFAULT_SECONDS


def in_docking_band(ship_pos: Vec2, comet: CometBody) -> bool:
    return in_planet_landing_band(ship_pos, comet.planet_body())


def comet_limb_hint(ship_pos: Vec2, comet: CometBody) -> Vec2:
    return limb_point_toward(ship_pos, comet.planet_body())


def in_flight_phase(phase: ExpeditionPhase) -> bool:
    return phase in (
        ExpeditionPhase.ORBITAL,
        ExpeditionPhase.ESCAPE_FLIGHT,
        ExpeditionPhase.DOCK_CINEMATIC,
        ExpeditionPhase.UNDOCK_CINEMATIC,
    )


def expedition_hostiles_cleared(exp: ExpeditionState) -> bool:
    return exp.hostiles_remaining <= 0


def expedition_fuel_loaded(exp: ExpeditionState) -> bool:
    return exp.fuel_nodes_loaded >= FUEL_NODES_REQUIRED


def expedition_foot_objectives_met(exp: ExpeditionState) -> bool:
    return expedition_fuel_loaded(exp)


def nearest_interact_node(exp: ExpeditionState, pos: Vec2) -> ExpeditionInteractNode | None:
    best: ExpeditionInteractNode | None = None
    best_dist = 1e18
    for node in exp.interact_nodes:
        if node.one_shot and node.id in exp.completed_interact_ids:
            continue
        if node.kind is InteractKind.FUEL_VALVE and expedition_fuel_loaded(exp):
            continue
        dist = (node.pos - pos).length()
        if dist <= node.radius and dist < best_dist:
            best = node
            best_dist = dist
    return best


def delivery_node(exp: ExpeditionState) -> ExpeditionInteractNode | None:
    for node in exp.interact_nodes:
        if node.kind is InteractKind.DELIVERY_BEACON:
            return node
    return None
