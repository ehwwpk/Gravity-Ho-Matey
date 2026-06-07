from __future__ import annotations

from gravity_ho_matey.levels.level_registry import LEVEL_ORDER
from gravity_ho_matey.settings import DEV_UNLOCK_ALL_LEVELS

_ALWAYS_SELECTABLE = frozenset({LEVEL_ORDER[0]} if LEVEL_ORDER else ())
_unlocked_levels: set[str] = set(_ALWAYS_SELECTABLE)


def record_level_cleared(level_id: str) -> None:
    """Unlock the next campaign stage after a level win."""
    try:
        index = LEVEL_ORDER.index(level_id)
    except ValueError:
        return
    _unlocked_levels.add(level_id)
    next_index = index + 1
    if next_index < len(LEVEL_ORDER):
        _unlocked_levels.add(LEVEL_ORDER[next_index])


def is_level_selectable(level_id: str) -> bool:
    if DEV_UNLOCK_ALL_LEVELS and level_id in LEVEL_ORDER:
        return True
    return level_id in _unlocked_levels


def reset_progress() -> None:
    """Test helper — restore default unlock state."""
    _unlocked_levels.clear()
    _unlocked_levels.update(_ALWAYS_SELECTABLE)
