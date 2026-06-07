from __future__ import annotations

from enum import Enum, auto

from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind


class WeaponTrack(Enum):
    """Mutually exclusive player weapon doctrine — one track per campaign."""

    LASER = auto()
    SHOTGUN = auto()
    EXPLOSIVE = auto()


WEAPON_TRACK_LABELS: dict[WeaponTrack, str] = {
    WeaponTrack.LASER: "Phase Lance — piercing bursts pass through hostiles",
    WeaponTrack.SHOTGUN: "Scatter Cannon — twin bolts with slight spread",
    WeaponTrack.EXPLOSIVE: "Nova Shell — slow slugs, wide blast radius",
}

WEAPON_TRACK_TAGS: dict[WeaponTrack, str] = {
    WeaponTrack.LASER: "LANCE",
    WeaponTrack.SHOTGUN: "SCATTER",
    WeaponTrack.EXPLOSIVE: "NOVA",
}

WEAPON_TRACK_SHORT: dict[WeaponTrack, str] = {
    WeaponTrack.LASER: "Phase Lance",
    WeaponTrack.SHOTGUN: "Scatter Cannon",
    WeaponTrack.EXPLOSIVE: "Nova Shell",
}

POWERUP_TO_WEAPON_TRACK: dict[PowerUpKind, WeaponTrack] = {
    PowerUpKind.WEAPON_LASER: WeaponTrack.LASER,
    PowerUpKind.WEAPON_SHOTGUN: WeaponTrack.SHOTGUN,
    PowerUpKind.WEAPON_EXPLOSIVE: WeaponTrack.EXPLOSIVE,
}

WEAPON_TRACK_POWERUP_KINDS: frozenset[PowerUpKind] = frozenset(POWERUP_TO_WEAPON_TRACK)


def weapon_track_from_kind(kind: PowerUpKind) -> WeaponTrack | None:
    return POWERUP_TO_WEAPON_TRACK.get(kind)


def weapon_kind_for_track(track: WeaponTrack) -> PowerUpKind:
    for kind, mapped in POWERUP_TO_WEAPON_TRACK.items():
        if mapped is track:
            return kind
    raise KeyError(track)


def is_weapon_powerup(kind: PowerUpKind) -> bool:
    return kind in WEAPON_TRACK_POWERUP_KINDS
