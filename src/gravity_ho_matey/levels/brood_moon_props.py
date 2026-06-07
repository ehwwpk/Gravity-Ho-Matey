from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.levels.brood_moon_layout import (
    SURFACE_BOSS_ANCHOR_FRAC,
    SURFACE_FLOOR_Y,
    SURFACE_WRAP_WIDTH,
)

PropKind = str

PROP_VIEW_MARGIN = 1400.0
TACTICAL_PROP_DRAW_MAX = 28
CHASE_PROP_DRAW_MAX = 18

_PROP_ANCHOR_FRACS = (
    0.048,
    0.095,
    0.142,
    0.198,
    0.255,
    0.312,
    0.368,
    0.425,
    0.482,
    0.538,
    0.595,
    0.652,
    0.708,
    0.762,
    0.818,
    0.872,
    0.925,
    0.968,
)


@dataclass(frozen=True, slots=True)
class BroodSurfaceProp:
    kind: PropKind
    pos: Vec2
    seed: int
    scale: float
    zone: str


def zone_for_frac(frac: float) -> str:
    if frac < 0.22:
        return "landing_flats"
    if frac < 0.36:
        return "early_pods"
    if frac < 0.62:
        return "mid_nursery"
    if abs(frac - SURFACE_BOSS_ANCHOR_FRAC) < 0.07:
        return "boss_cathedral"
    return "seal_run"


def _prop_seed(x: float, kind: str) -> int:
    return int(x * 0.17) + sum(ord(c) for c in kind) * 13


def _prop_y(kind: str, i: int, zone: str) -> float:
    if kind == "float_bulb":
        return SURFACE_FLOOR_Y - 95.0 - (i % 3) * 35.0
    if kind == "chitin_bloom":
        return SURFACE_FLOOR_Y - 55.0 - (i % 4) * 22.0
    if kind == "spire":
        return SURFACE_FLOOR_Y - 40.0 - (i % 4) * 28.0 - 80.0 - (i % 3) * 40.0
    if zone == "boss_cathedral" and kind in ("vein_node", "crystal"):
        return SURFACE_FLOOR_Y - 70.0 - (i % 2) * 30.0
    return SURFACE_FLOOR_Y - 40.0 - (i % 4) * 28.0


def build_brood_surface_props() -> tuple[BroodSurfaceProp, ...]:
    """Static nursery geology/flora anchors — scaled to SURFACE_WRAP_WIDTH."""
    props: list[BroodSurfaceProp] = []
    kind_cycle: tuple[PropKind, ...] = (
        "scarp",
        "chitin_bloom",
        "vein_node",
        "float_bulb",
        "mound",
        "spire",
        "stalk",
        "crystal",
        "sinkhole_rim",
        "chitin_bloom",
    )
    for i, frac in enumerate(_PROP_ANCHOR_FRACS):
        x = SURFACE_WRAP_WIDTH * frac
        zone = zone_for_frac(frac)
        kind = kind_cycle[i % len(kind_cycle)]
        if zone == "boss_cathedral" and kind in ("mound", "scarp"):
            kind = "spire"
        if zone == "landing_flats" and kind == "spire":
            kind = "scarp"
        if zone == "seal_run" and kind == "float_bulb":
            kind = "vein_node"
        y = _prop_y(kind, i, zone)
        props.append(
            BroodSurfaceProp(
                kind=kind,
                pos=Vec2(x, y),
                seed=_prop_seed(x, kind),
                scale=1.0 + (i % 5) * 0.12,
                zone=zone,
            )
        )
    seal_step = 800.0 / max(1.0, float(SURFACE_WRAP_WIDTH))
    frac = 0.68
    while frac < 0.97 and len(props) < 56:
        x = SURFACE_WRAP_WIDTH * frac
        props.append(
            BroodSurfaceProp(
                kind="scarp" if int(x) % 1600 < 800 else "mound",
                pos=Vec2(x, SURFACE_FLOOR_Y - 32.0 - (int(x) % 3) * 18.0),
                seed=_prop_seed(x, "seal"),
                scale=0.9 + (int(x) % 4) * 0.08,
                zone="seal_run",
            )
        )
        frac += seal_step
    return tuple(props)


BROOD_SURFACE_PROPS = build_brood_surface_props()


def props_near_ship(ship_x: float, *, margin: float = PROP_VIEW_MARGIN) -> list[BroodSurfaceProp]:
    return [p for p in BROOD_SURFACE_PROPS if abs(p.pos.x - ship_x) <= margin]
