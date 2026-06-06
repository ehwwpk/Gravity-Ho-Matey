from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class DamageSeverity(Enum):
    CHIP = auto()
    LETHAL = auto()


class DamageSource(Enum):
    ASTEROID = auto()
    OUT_OF_BOUNDS = auto()
    CHART_RADIATION = auto()
    ENEMY = auto()
    ENEMY_PROJECTILE = auto()
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
    DamageSource.ASTEROID: DamageSpec(DamageSeverity.CHIP, 1),
    DamageSource.OUT_OF_BOUNDS: DamageSpec(DamageSeverity.CHIP, 1),
    DamageSource.CHART_RADIATION: DamageSpec(DamageSeverity.CHIP, 1),
    DamageSource.ENEMY: DamageSpec(DamageSeverity.CHIP, 1),
    DamageSource.ENEMY_PROJECTILE: DamageSpec(DamageSeverity.CHIP, 1),
    DamageSource.GRAVITY_MAW: DamageSpec(DamageSeverity.LETHAL, 3),
}


def damage_spec_for(source: DamageSource) -> DamageSpec:
    return DAMAGE_RULES[source]


def default_reason(source: DamageSource, level_theme: str = "cove") -> str:
    solar = level_theme == "solar"
    if source is DamageSource.ASTEROID:
        return "Hull cracked on a rogue asteroid." if solar else "Hull smashed on drifting reef rock."
    if source is DamageSource.OUT_OF_BOUNDS:
        return "Drifted beyond the star chart." if solar else "Lost beyond the reef."
    if source is DamageSource.CHART_RADIATION:
        return "Chart radiation exceeded safe exposure." if solar else "Void radiation breached the hull."
    if source is DamageSource.ENEMY:
        return "Hull breached by a patrol skiff."
    if source is DamageSource.ENEMY_PROJECTILE:
        return "Patrol battery scored a direct hit."
    if source is DamageSource.GRAVITY_MAW:
        return "Consumed by a gravity maw."
    return "Hull failure."
