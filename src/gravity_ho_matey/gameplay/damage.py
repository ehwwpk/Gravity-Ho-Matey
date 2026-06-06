from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class DamageSeverity(Enum):
    CHIP = auto()
    LETHAL = auto()


class DamageSource(Enum):
    WALL = auto()
    OUT_OF_BOUNDS = auto()
    ENEMY = auto()
    GRAVITY_MAW = auto()


@dataclass(frozen=True, slots=True)
class DamageSpec:
    severity: DamageSeverity
    chunks: int = 1


@dataclass(frozen=True, slots=True)
class DamageEvent:
    source: DamageSource
    reason: str = ""


@dataclass(frozen=True, slots=True)
class DamageResult:
    life_lost: bool
    campaign_over: bool
    hull_chunks: int
    lives: int
    reason: str
    chipped: bool


DAMAGE_RULES: dict[DamageSource, DamageSpec] = {
    DamageSource.WALL: DamageSpec(DamageSeverity.CHIP, 1),
    DamageSource.OUT_OF_BOUNDS: DamageSpec(DamageSeverity.CHIP, 1),
    DamageSource.ENEMY: DamageSpec(DamageSeverity.CHIP, 1),
    DamageSource.GRAVITY_MAW: DamageSpec(DamageSeverity.LETHAL, 3),
}


def damage_spec_for(source: DamageSource) -> DamageSpec:
    return DAMAGE_RULES[source]


def default_reason(source: DamageSource, level_theme: str = "cove") -> str:
    solar = level_theme == "solar"
    if source is DamageSource.WALL:
        return "Hull cracked on an asteroid." if solar else "Hull smashed on the rocks."
    if source is DamageSource.OUT_OF_BOUNDS:
        return "Drifted beyond the star chart." if solar else "Lost beyond the reef."
    if source is DamageSource.ENEMY:
        return "Hull breached by a patrol skiff."
    if source is DamageSource.GRAVITY_MAW:
        return "Consumed by a gravity maw."
    return "Hull failure."
