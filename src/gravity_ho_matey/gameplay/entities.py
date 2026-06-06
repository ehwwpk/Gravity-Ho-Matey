from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind


class GameStatus(Enum):
    RUNNING = auto()
    WON = auto()
    SHIP_HIT = auto()


@dataclass(slots=True)
class Ship:
    pos: Vec2
    vel: Vec2 = field(default_factory=Vec2)
    angle: float = 0.0
    radius: float = 12.0
    cooldown: float = 0.0
    boost_energy: float = 1.0
    boost_flash: float = 0.0
    thrust_multiplier: float = 1.0
    fire_cooldown_multiplier: float = 1.0
    turn_rate_multiplier: float = 1.0


@dataclass(slots=True)
class Projectile:
    pos: Vec2
    vel: Vec2
    ttl: float = 2.3
    radius: float = 4.0
    hostile: bool = False


@dataclass(slots=True)
class PowerUpPickup:
    pos: Vec2
    kind: PowerUpKind
    radius: float = 11.0


@dataclass(frozen=True, slots=True)
class GravityWell:
    pos: Vec2
    strength: float
    radius: float
    label: str = ""
    kind: str = "well"
    maw_radius: float | None = None


@dataclass(slots=True)
class Asteroid:
    pos: Vec2
    vel: Vec2
    angle: float
    spin: float
    local_verts: tuple[Vec2, ...]
    size_class: str = "rock"
    drift_kind: str = "medium"
    seed: int = 0
    ring_anchor: Vec2 | None = None
    ring_radius: float = 0.0
    ring_sign: float = 1.0

    def approximate_radius(self) -> float:
        if not self.local_verts:
            return 20.0
        return max(v.length() for v in self.local_verts)

    def world_vertices(self) -> list[Vec2]:
        c = math.cos(self.angle)
        s = math.sin(self.angle)
        out: list[Vec2] = []
        for v in self.local_verts:
            out.append(Vec2(self.pos.x + v.x * c - v.y * s, self.pos.y + v.x * s + v.y * c))
        return out


@dataclass(slots=True)
class Beacon:
    pos: Vec2
    radius: float = 9.0
    collected: bool = False


@dataclass(frozen=True, slots=True)
class FinishGate:
    rect: Rect


@dataclass(frozen=True, slots=True)
class WorldConfig:
    width: int
    height: int
    viewport_width: int = 960
    viewport_height: int = 640
    gravity_scale: float = 0.5
    turn_rate: float = 5.0
    thrust: float = 250.0
    boost_burst_fraction: float = 0.32
    boost_energy_cost: float = 0.22
    boost_regen_rate: float = 0.14
    boost_overspeed_cap: float = 1.12
    boost_flash_seconds: float = 0.35
    drag: float = 0.988
    max_ship_speed: float = 330.0
    projectile_speed: float = 315.0
    ship_fire_cooldown: float = 0.18
    well_maw_radius: float = 10.0
    level_theme: str = "cove"
    level_name: str = "Level"
    open_bounds: bool = True
