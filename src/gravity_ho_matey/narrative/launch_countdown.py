from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.levels.level_registry import LEVEL_ORDER

DEFAULT_STEP_SECONDS = 0.5
DEFAULT_DIGITS = (3, 2, 1)


@dataclass(frozen=True, slots=True)
class LaunchCountdownSpec:
    """Per-level launch countdown — seconds per digit and optional custom sequence."""

    step_seconds: float = DEFAULT_STEP_SECONDS
    digits: tuple[int, ...] = DEFAULT_DIGITS

    @property
    def total_seconds(self) -> float:
        return self.step_seconds * len(self.digits)


# Per-level tuning — omit entries to use defaults (3-2-1 @ 1s each).
LEVEL_LAUNCH_COUNTDOWNS: dict[str, LaunchCountdownSpec] = {}


def launch_countdown_for(level_id: str) -> LaunchCountdownSpec:
    return LEVEL_LAUNCH_COUNTDOWNS.get(level_id, LaunchCountdownSpec())


def validate_launch_countdown_registry() -> None:
    unknown = [level_id for level_id in LEVEL_LAUNCH_COUNTDOWNS if level_id not in LEVEL_ORDER]
    if unknown:
        raise RuntimeError(f"LEVEL_LAUNCH_COUNTDOWNS references unknown levels: {unknown}")


validate_launch_countdown_registry()
