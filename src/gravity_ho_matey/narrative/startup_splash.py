from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gravity_ho_matey.render.animated_image import AnimatedImageSequence

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_NARRATIVE_DIR = _PACKAGE_ROOT / "assets" / "narrative"
_STARTUP_STEM = "startup"

MIN_PLAYBACK_SECONDS = 2.5
MAX_PLAYBACK_SECONDS = 5.0
SKIP_DEBOUNCE_SECONDS = 0.35


def startup_asset_path() -> Path:
    return _NARRATIVE_DIR / f"{_STARTUP_STEM}.gif"


def has_startup_splash() -> bool:
    return startup_asset_path().is_file()


def resolve_playback_seconds(sequence: AnimatedImageSequence) -> float:
    """One play-through, clamped for a quick welcome beat."""
    raw = max(0.5, sequence.duration_seconds())
    return max(MIN_PLAYBACK_SECONDS, min(MAX_PLAYBACK_SECONDS, raw))
