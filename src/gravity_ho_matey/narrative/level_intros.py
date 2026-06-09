from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from gravity_ho_matey.levels.level_registry import LEVEL_ORDER

if TYPE_CHECKING:
    from gravity_ho_matey.render.animated_image import AnimatedImageSequence

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_NARRATIVE_DIR = _PACKAGE_ROOT / "assets" / "narrative"


@dataclass(frozen=True, slots=True)
class LevelIntroSpec:
    """Pre-play narrative clip shown after holo chart / shop, before launch."""

    asset_stem: str
    playback_seconds: float | None = None
    header_tag: str = "INCOMING TRANSMISSION"
    footer_hint: str = "Enter · click to launch sector"


LEVEL_INTROS: dict[str, LevelIntroSpec] = {
    "cove": LevelIntroSpec(
        asset_stem="cove",
        header_tag="ENEMY SPACE · CAPTAIN'S LOG",
    ),
    "solar": LevelIntroSpec(
        asset_stem="solar",
        header_tag="SINGULARITY CROSSING · CAPTAIN'S LOG",
    ),
    "drift": LevelIntroSpec(
        asset_stem="drift",
        header_tag="OPEN DRIFT · CAPTAIN'S LOG",
    ),
    "rift": LevelIntroSpec(
        asset_stem="rift",
        header_tag="RELAY HOLD · CAPTAIN'S LOG",
    ),
    "siege": LevelIntroSpec(
        asset_stem="siege",
        header_tag="SIEGE LINE · CAPTAIN'S LOG",
    ),
    "brood_moon": LevelIntroSpec(
        asset_stem="brood_moon",
        header_tag="BROOD MOON · CAPTAIN'S LOG",
    ),
    "comet_fuel": LevelIntroSpec(
        asset_stem="comet_fuel",
        header_tag="VOLATILE CHARTER · CAPTAIN'S LOG",
    ),
}


def intro_spec_for(level_id: str) -> LevelIntroSpec | None:
    return LEVEL_INTROS.get(level_id)


def has_level_intro(level_id: str) -> bool:
    spec = intro_spec_for(level_id)
    if spec is None:
        return False
    return resolve_intro_asset(spec) is not None


def resolve_intro_asset(spec: LevelIntroSpec) -> Path | None:
    for ext in (".gif", ".png"):
        path = _NARRATIVE_DIR / f"{spec.asset_stem}{ext}"
        if path.is_file():
            return path
    return None


def resolve_playback_seconds(spec: LevelIntroSpec, sequence: AnimatedImageSequence) -> float:
    """Bar fill + auto-launch duration — per-level override or measured GIF length."""
    if spec.playback_seconds is not None:
        return max(0.5, spec.playback_seconds)
    return max(0.5, sequence.duration_seconds())


def validate_intro_registry() -> None:
    unknown = [level_id for level_id in LEVEL_INTROS if level_id not in LEVEL_ORDER]
    if unknown:
        raise RuntimeError(f"LEVEL_INTROS references unknown levels: {unknown}")


validate_intro_registry()
