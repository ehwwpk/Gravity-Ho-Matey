from __future__ import annotations

from collections.abc import Callable

from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.level_data import (
    build_cove_run_level,
    build_drift_belt_level,
    build_membrane_run_level,
    build_solar_crossing_level,
)

LevelBuilder = Callable[[], GameWorld]

LEVEL_BUILDERS: dict[str, LevelBuilder] = {
    "cove": build_cove_run_level,
    "solar": build_solar_crossing_level,
    "drift": build_drift_belt_level,
    "rift": build_membrane_run_level,
}

LEVEL_ORDER: tuple[str, ...] = ("cove", "solar", "drift", "rift")

LEVEL_LABELS: dict[str, str] = {
    "cove": "1 — Smuggler's Cove",
    "solar": "2 — Singularity Crossing",
    "drift": "3 — The Drift",
    "rift": "4 — The Membrane Run",
}


def next_level_id(current: str) -> str | None:
    try:
        index = LEVEL_ORDER.index(current)
    except ValueError:
        return None
    next_index = index + 1
    if next_index >= len(LEVEL_ORDER):
        return None
    return LEVEL_ORDER[next_index]


def build_level(level_id: str) -> GameWorld:
    try:
        return LEVEL_BUILDERS[level_id]()
    except KeyError as exc:
        raise ValueError(f"Unknown level id: {level_id!r}") from exc


def _validate_registry() -> None:
    missing = [level_id for level_id in LEVEL_ORDER if level_id not in LEVEL_BUILDERS]
    if missing:
        raise RuntimeError(f"LEVEL_ORDER references unknown builders: {missing}")
    orphans = [level_id for level_id in LEVEL_BUILDERS if level_id not in LEVEL_ORDER]
    if orphans:
        raise RuntimeError(f"LEVEL_BUILDERS has ids not listed in LEVEL_ORDER: {orphans}")


_validate_registry()
