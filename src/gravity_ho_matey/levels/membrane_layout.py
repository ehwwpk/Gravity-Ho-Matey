from __future__ import annotations

import math
from dataclasses import dataclass

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import FinishGate, GravityWell, Ship
from gravity_ho_matey.gameplay.membrane_ribbons import RibbonSample, RibbonSpec, build_all_samples, nearest_ribbon

MEMBRANE_WIDTH = 2000
MEMBRANE_HEIGHT = 5000
RIBBON_HALF_WIDTH = 204.0  # ~33% wider than prior 153
RIBBON_CLEARANCE = 75.0
# Pocket centers must sit outside the drivable ribbon surface.
POCKET_MIN_RIBBON_GAP = 48.0
BOSS_STABLE_RADIUS = 780.0
MEMBRANE_SAMPLE_STEP = 44.0
# South merge — no highway auto-pull; player picks a braid manually.
STARTER_ZONE_MIN_Y = 3680.0
# No turbo pads north of this line — boss arena is open flight, not a railgun funnel.
PAD_ZONE_MIN_Y = 1400.0


@dataclass(frozen=True, slots=True)
class VoidPocketSpec:
    center: Vec2
    radius: float
    wells: tuple[GravityWell, ...]


@dataclass(frozen=True, slots=True)
class BoostPadSpec:
    pos: Vec2
    tangent: Vec2
    radius: float = 52.0
    kick_speed: float = 98.0


@dataclass(frozen=True, slots=True)
class MembraneLayout:
    width: int
    height: int
    ribbons: tuple[RibbonSpec, ...]
    samples: tuple[RibbonSample, ...]
    ribbon_chains: tuple[tuple[str, tuple[RibbonSample, ...]], ...]
    void_pockets: tuple[VoidPocketSpec, ...]
    boost_pads: tuple[BoostPadSpec, ...]
    road_squid_spawns: tuple[Vec2, ...]
    boss_anchor: Vec2
    boss_stable_radius: float
    spawn_ship: Ship
    finish_gate: FinishGate


def _ribbon_spec(ribbon_id: str, control_points: tuple[Vec2, ...]) -> RibbonSpec:
    return RibbonSpec(
        ribbon_id,
        control_points,
        half_width=RIBBON_HALF_WIDTH,
        sample_step=MEMBRANE_SAMPLE_STEP,
    )


def _ribbon_specs() -> tuple[RibbonSpec, ...]:
    """Three braided boost highways south → north."""
    return (
        _ribbon_spec(
            "strand_a",
            (
                Vec2(420, 4180),
                Vec2(340, 3840),
                Vec2(520, 3480),
                Vec2(320, 3080),
                Vec2(480, 2680),
                Vec2(360, 2280),
                Vec2(540, 1880),
                Vec2(400, 1480),
                Vec2(480, 1280),
                Vec2(520, 1080),
            ),
        ),
        _ribbon_spec(
            "strand_b",
            (
                Vec2(1000, 4180),
                Vec2(1080, 3840),
                Vec2(920, 3480),
                Vec2(1100, 3080),
                Vec2(960, 2680),
                Vec2(1040, 2280),
                Vec2(880, 1880),
                Vec2(1020, 1480),
                Vec2(1000, 1280),
                Vec2(1000, 1080),
            ),
        ),
        _ribbon_spec(
            "strand_c",
            (
                Vec2(1580, 4180),
                Vec2(1660, 3840),
                Vec2(1480, 3480),
                Vec2(1680, 3080),
                Vec2(1520, 2680),
                Vec2(1640, 2280),
                Vec2(1460, 1880),
                Vec2(1600, 1480),
                Vec2(1520, 1280),
                Vec2(1480, 1080),
            ),
        ),
    )


def _group_ribbon_chains(samples: tuple[RibbonSample, ...]) -> tuple[tuple[str, tuple[RibbonSample, ...]], ...]:
    groups: dict[str, list[RibbonSample]] = {}
    for sample in samples:
        groups.setdefault(sample.ribbon_id, []).append(sample)
    return tuple((ribbon_id, tuple(chain)) for ribbon_id, chain in groups.items())


def _void_pockets(samples: tuple[RibbonSample, ...]) -> tuple[VoidPocketSpec, ...]:
    """Place titans in membrane folds — grid cells farthest from boost ribbons."""
    labels = (
        "Membrane Maw",
        "Fold Leech",
        "Neck Kraken",
        "Pocket Void",
        "Lobe Titan",
        "Squeeze Well",
        "Crossing Abyss",
        "West Gullet",
        "East Gullet",
        "Central Rift",
        "Bay Maw",
        "Outer Leech",
        "Pre-Boss Pit",
        "West Fang",
        "East Fang",
    )
    candidates: list[tuple[float, Vec2]] = []
    min_dist = RIBBON_HALF_WIDTH + POCKET_MIN_RIBBON_GAP
    boss_anchor = Vec2(1000.0, 520.0)
    for gy in range(420, 4200, 160):
        for gx in range(220, 1781, 65):
            pos = Vec2(float(gx), float(gy))
            if (pos - boss_anchor).length() <= BOSS_STABLE_RADIUS:
                continue
            hit = nearest_ribbon(pos, samples)
            if hit is None:
                continue
            if hit.dist < min_dist:
                continue
            candidates.append((hit.dist, pos))
    candidates.sort(key=lambda item: item[0], reverse=True)
    pockets: list[VoidPocketSpec] = []
    min_sep = 200.0
    for dist, center in candidates:
        _ = dist
        if any((center - p.center).length() < min_sep for p in pockets):
            continue
        ribbon_hit = nearest_ribbon(center, samples)
        if ribbon_hit is not None and ribbon_hit.dist < ribbon_hit.sample.half_width + RIBBON_CLEARANCE:
            continue
        i = len(pockets)
        if i >= len(labels):
            break
        strength = 48000.0 + (i % 3) * 2400.0
        radius = 340.0
        well_radius = radius * 0.68
        wells: tuple[GravityWell, ...] = (
            GravityWell(
                center,
                strength=strength,
                radius=well_radius,
                label=labels[i],
                kind="black_hole",
                maw_radius=14.0,
            ),
        )
        if i % 2 == 0:
            offset = Vec2(radius * 0.38, -radius * 0.12)
            twin_center = center + offset
            twin_hit = nearest_ribbon(twin_center, samples)
            if twin_hit is not None and twin_hit.dist >= min_dist:
                wells = (
                    wells[0],
                    GravityWell(
                        twin_center,
                        strength=strength * 0.82,
                        radius=well_radius * 0.78,
                        label=f"{labels[i]} Twin",
                        kind="black_hole",
                        maw_radius=12.0,
                    ),
                )
        pockets.append(VoidPocketSpec(center=center, radius=radius, wells=wells))
        if len(pockets) >= 15:
            break
    return tuple(pockets)


def _spawn_on_ribbon(samples: tuple[RibbonSample, ...]) -> Ship:
    """Three-way merge — player picks left, center, or right braid."""
    hub = Vec2(1000.0, 4120.0)
    best: RibbonSample | None = None
    best_d = 1e18
    for sample in samples:
        if sample.ribbon_id not in ("strand_a", "strand_b", "strand_c"):
            continue
        d = (sample.pos - hub).length_sq()
        if d < best_d:
            best_d = d
            best = sample
    if best is None:
        return Ship(pos=Vec2(1000.0, 4120.0), angle=-math.pi / 2)
    angle = math.atan2(best.tangent.y, best.tangent.x)
    return Ship(pos=Vec2(best.pos.x, best.pos.y), angle=angle)


def _pads_from_samples(samples: tuple[RibbonSample, ...]) -> tuple[BoostPadSpec, ...]:
    """Place turbo pads on main braids — sparse MK-style boost strips."""
    pad_min_arc = 1320.0
    pad_cap = 8
    pads: list[BoostPadSpec] = []
    by_ribbon: dict[str, list[RibbonSample]] = {}
    for s in samples:
        if s.ribbon_id not in ("strand_a", "strand_b", "strand_c"):
            continue
        by_ribbon.setdefault(s.ribbon_id, []).append(s)
    for chain in by_ribbon.values():
        last_arc = -999.0
        for sample in chain:
            if sample.pos.y > STARTER_ZONE_MIN_Y:
                continue
            if sample.pos.y < PAD_ZONE_MIN_Y:
                continue
            if sample.arc_s - last_arc < pad_min_arc:
                continue
            last_arc = sample.arc_s
            pads.append(
                BoostPadSpec(
                    pos=Vec2(sample.pos.x, sample.pos.y),
                    tangent=Vec2(sample.tangent.x, sample.tangent.y),
                    radius=48.0,
                    kick_speed=102.0,
                )
            )
            if len(pads) >= pad_cap:
                return tuple(pads)
    return tuple(pads)


def _road_squid_spawns(samples: tuple[RibbonSample, ...]) -> tuple[Vec2, ...]:
    picks: list[Vec2] = []
    targets = (900.0, 2100.0, 3300.0, 3900.0, 4500.0)
    for target in targets:
        best: RibbonSample | None = None
        best_d = 99999.0
        for s in samples:
            d = abs(s.arc_s - target)
            if d < best_d:
                best_d = d
                best = s
        if best is not None:
            picks.append(best.pos)
    return tuple(picks)


def build_membrane_layout() -> MembraneLayout:
    ribbons = _ribbon_specs()
    samples = build_all_samples(ribbons)
    void_pockets = _void_pockets(samples)
    boss = Vec2(1000.0, 520.0)
    gate_half = 34.0
    return MembraneLayout(
        width=MEMBRANE_WIDTH,
        height=MEMBRANE_HEIGHT,
        ribbons=ribbons,
        samples=samples,
        ribbon_chains=_group_ribbon_chains(samples),
        void_pockets=void_pockets,
        boost_pads=_pads_from_samples(samples),
        road_squid_spawns=_road_squid_spawns(samples),
        boss_anchor=boss,
        boss_stable_radius=BOSS_STABLE_RADIUS,
        spawn_ship=_spawn_on_ribbon(samples),
        finish_gate=FinishGate(
            Rect(boss.x - gate_half, boss.y - gate_half - 90.0, gate_half * 2.0, gate_half * 2.0)
        ),
    )


def all_void_wells(layout: MembraneLayout) -> list[GravityWell]:
    wells: list[GravityWell] = []
    for pocket in layout.void_pockets:
        wells.extend(pocket.wells)
    return wells


def is_in_boss_stable_zone(pos: Vec2, layout: MembraneLayout) -> bool:
    return (pos - layout.boss_anchor).length() <= layout.boss_stable_radius


def validate_void_clearance(layout: MembraneLayout, *, min_gap: float = RIBBON_CLEARANCE) -> list[str]:
    errors: list[str] = []
    for pocket in layout.void_pockets:
        for well in pocket.wells:
            hit = nearest_ribbon(well.pos, layout.samples)
            if hit is None:
                continue
            if hit.dist < hit.sample.half_width + min_gap:
                errors.append(
                    f"Well {well.label} at {well.pos} only {hit.dist:.0f} from ribbon "
                    f"(need {hit.sample.half_width + min_gap:.0f})"
                )
    return errors
