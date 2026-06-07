from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.space_station import SpaceStation


def station_visual_seed(station: SpaceStation) -> int:
    label_hash = sum(ord(ch) * (idx + 19) for idx, ch in enumerate(station.station_label))
    return (label_hash + int(station.pos.x) * 5 + int(station.pos.y) * 11) & 0x7FFFFFFF


@dataclass(frozen=True, slots=True)
class PanelRecess:
    cx: float
    cy: float
    half_w: float
    half_h: float
    angle: float


@dataclass(frozen=True, slots=True)
class GreebleLamp:
    x: float
    y: float
    radius: float


@dataclass(frozen=True, slots=True)
class GreeblePod:
    cx: float
    cy: float
    rx: float
    ry: float
    angle: float


@dataclass(frozen=True, slots=True)
class GreebleAntenna:
    bx: float
    by: float
    tx: float
    ty: float
    dish: float


@dataclass(slots=True)
class StationMesh:
    """Layered ring-hub dock — local space, +X = facing, unit radius = station.radius."""

    back_ring: list[tuple[float, float]]
    mid_arms: list[list[tuple[float, float]]]
    front_hub: list[tuple[float, float]]
    turret: list[tuple[float, float]]
    spawn_bay: list[tuple[float, float]] | None
    truss_lines: list[tuple[float, float, float, float]] = field(default_factory=list)
    panel_recesses: list[PanelRecess] = field(default_factory=list)
    lamps: list[GreebleLamp] = field(default_factory=list)
    pods: list[GreeblePod] = field(default_factory=list)
    antennas: list[GreebleAntenna] = field(default_factory=list)
    window_slits: list[tuple[float, float, float, float]] = field(default_factory=list)


def _ring_points(rng: random.Random, *, segments: int, radius: float, wobble: float) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(segments):
        angle = math.tau * i / segments
        bump = 1.0 + (rng.random() - 0.5) * wobble
        r = radius * bump
        pts.append((math.cos(angle) * r, math.sin(angle) * r))
    return pts


def _rotate_point(x: float, y: float, angle: float) -> tuple[float, float]:
    c = math.cos(angle)
    s = math.sin(angle)
    return x * c - y * s, x * s + y * c


def _rotate_poly(points: list[tuple[float, float]], angle: float) -> list[tuple[float, float]]:
    return [_rotate_point(x, y, angle) for x, y in points]


def _regular_polygon(sides: int, radius: float, *, phase: float = 0.0) -> list[tuple[float, float]]:
    return [
        (math.cos(phase + math.tau * i / sides) * radius, math.sin(phase + math.tau * i / sides) * radius)
        for i in range(sides)
    ]


def _arm_quad(
    rng: random.Random,
    *,
    angle: float,
    inner_r: float,
    outer_r: float,
    half_width: float,
    jitter: float,
) -> list[tuple[float, float]]:
    reach = outer_r + (rng.random() - 0.5) * jitter
    spread = half_width * (0.92 + rng.random() * 0.14)
    ca = math.cos(angle)
    sa = math.sin(angle)
    px, py = -sa, ca
    inner = (ca * inner_r, sa * inner_r)
    outer = (ca * reach, sa * reach)
    return [
        (inner[0] + px * spread, inner[1] + py * spread),
        (inner[0] - px * spread, inner[1] - py * spread),
        (outer[0] - px * spread * 0.55, outer[1] - py * spread * 0.55),
        (outer[0] + px * spread * 0.55, outer[1] + py * spread * 0.55),
    ]


def _rotate_mesh(mesh: StationMesh, angle: float) -> StationMesh:
    truss: list[tuple[float, float, float, float]] = []
    for x1, y1, x2, y2 in mesh.truss_lines:
        ax, ay = _rotate_point(x1, y1, angle)
        bx, by = _rotate_point(x2, y2, angle)
        truss.append((ax, ay, bx, by))
    return StationMesh(
        back_ring=_rotate_poly(mesh.back_ring, angle),
        mid_arms=[_rotate_poly(arm, angle) for arm in mesh.mid_arms],
        front_hub=_rotate_poly(mesh.front_hub, angle),
        turret=_rotate_poly(mesh.turret, angle),
        spawn_bay=_rotate_poly(mesh.spawn_bay, angle) if mesh.spawn_bay else None,
        truss_lines=truss,
        panel_recesses=[
            PanelRecess(
                cx=_rotate_point(r.cx, r.cy, angle)[0],
                cy=_rotate_point(r.cx, r.cy, angle)[1],
                half_w=r.half_w,
                half_h=r.half_h,
                angle=r.angle + angle,
            )
            for r in mesh.panel_recesses
        ],
        lamps=[
            GreebleLamp(x=_rotate_point(l.x, l.y, angle)[0], y=_rotate_point(l.x, l.y, angle)[1], radius=l.radius)
            for l in mesh.lamps
        ],
        pods=[
            GreeblePod(
                cx=_rotate_point(p.cx, p.cy, angle)[0],
                cy=_rotate_point(p.cx, p.cy, angle)[1],
                rx=p.rx,
                ry=p.ry,
                angle=p.angle + angle,
            )
            for p in mesh.pods
        ],
        antennas=[
            GreebleAntenna(
                bx=_rotate_point(a.bx, a.by, angle)[0],
                by=_rotate_point(a.bx, a.by, angle)[1],
                tx=_rotate_point(a.tx, a.ty, angle)[0],
                ty=_rotate_point(a.tx, a.ty, angle)[1],
                dish=a.dish,
            )
            for a in mesh.antennas
        ],
        window_slits=[
            (
                _rotate_point(x0, y0, angle)[0],
                _rotate_point(x0, y0, angle)[1],
                _rotate_point(x1, y1, angle)[0],
                _rotate_point(x1, y1, angle)[1],
            )
            for x0, y0, x1, y1 in mesh.window_slits
        ],
    )


def build_station_mesh(*, seed: int, facing_angle: float, spawn_bay: bool) -> StationMesh:
    """Procedural ring-hub with D-lite greeble — same topology for all factions."""
    rng = random.Random(seed)

    ring_segments = 20
    ring = _ring_points(rng, segments=ring_segments, radius=0.93, wobble=0.055)
    hub = _regular_polygon(8, 0.36, phase=math.pi / 8.0)

    arms: list[list[tuple[float, float]]] = []
    arm_angles = [0.0, math.pi * 0.5, math.pi, -math.pi * 0.5]
    for i, base in enumerate(arm_angles):
        jitter = 0.06 if i == 0 else 0.11
        width = 0.16 if i == 0 else 0.11 + rng.random() * 0.04
        arms.append(_arm_quad(rng, angle=base, inner_r=0.38, outer_r=0.78, half_width=width, jitter=jitter))

    turret_len = 0.34 + rng.random() * 0.06
    turret_w = 0.09
    turret = [
        (0.22, turret_w),
        (0.22, -turret_w),
        (0.22 + turret_len, -turret_w * 0.65),
        (0.22 + turret_len, turret_w * 0.65),
    ]

    bay: list[tuple[float, float]] | None = None
    if spawn_bay:
        bay = [(0.08, 0.14), (0.08, -0.14), (-0.12, -0.18), (-0.12, 0.18)]

    truss: list[tuple[float, float, float, float]] = []
    for i in range(0, ring_segments, 4):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 5) % ring_segments]
        truss.append((x1, y1, x2 * 0.55, y2 * 0.55))

    recesses: list[PanelRecess] = []
    for _ in range(5 + rng.randint(0, 2)):
        angle = rng.random() * math.tau
        dist = 0.28 + rng.random() * 0.48
        recesses.append(
            PanelRecess(
                cx=math.cos(angle) * dist,
                cy=math.sin(angle) * dist,
                half_w=0.05 + rng.random() * 0.05,
                half_h=0.025 + rng.random() * 0.035,
                angle=angle + rng.uniform(-0.4, 0.4),
            )
        )

    lamps: list[GreebleLamp] = []
    for _ in range(3 + rng.randint(0, 2)):
        angle = rng.random() * math.tau
        lamps.append(
            GreebleLamp(
                x=math.cos(angle) * 0.86,
                y=math.sin(angle) * 0.86,
                radius=0.018 + rng.random() * 0.012,
            )
        )

    pods: list[GreeblePod] = []
    for base in arm_angles[1:]:
        dist = 0.58 + rng.random() * 0.12
        pods.append(
            GreeblePod(
                cx=math.cos(base) * dist,
                cy=math.sin(base) * dist,
                rx=0.07 + rng.random() * 0.03,
                ry=0.045 + rng.random() * 0.02,
                angle=base,
            )
        )
    if rng.random() > 0.35:
        angle = rng.random() * math.tau
        pods.append(
            GreeblePod(
                cx=math.cos(angle) * 0.72,
                cy=math.sin(angle) * 0.72,
                rx=0.06,
                ry=0.04,
                angle=angle,
            )
        )

    antennas: list[GreebleAntenna] = []
    for _ in range(3 + rng.randint(0, 2)):
        angle = rng.random() * math.tau
        bx = math.cos(angle) * 0.88
        by = math.sin(angle) * 0.88
        length = 0.12 + rng.random() * 0.14
        tx = bx + math.cos(angle) * length
        ty = by + math.sin(angle) * length
        antennas.append(GreebleAntenna(bx=bx, by=by, tx=tx, ty=ty, dish=0.025 + rng.random() * 0.02))

    windows: list[tuple[float, float, float, float]] = []
    for i in range(4 + rng.randint(0, 2)):
        angle = -math.pi * 0.5 + (i - 1.5) * 0.22
        wx = 0.12 + math.cos(angle) * 0.14
        wy = math.sin(angle) * 0.14
        windows.append((wx - 0.04, wy - 0.012, wx + 0.04, wy + 0.012))

    local = StationMesh(
        back_ring=ring,
        mid_arms=arms,
        front_hub=hub,
        turret=turret,
        spawn_bay=bay,
        truss_lines=truss,
        panel_recesses=recesses,
        lamps=lamps,
        pods=pods,
        antennas=antennas,
        window_slits=windows,
    )
    return _rotate_mesh(local, facing_angle)


def mesh_for_station(station: SpaceStation) -> StationMesh:
    seed = station_visual_seed(station)
    return build_station_mesh(
        seed=seed,
        facing_angle=station.facing_angle,
        spawn_bay=station.can_spawn or station.spawn_bay_open > 0.05,
    )


def ring_wobble_points(mesh: StationMesh, station: SpaceStation) -> list[tuple[float, float]]:
    """Slow ring crawl — rotates back ring vertices slightly."""
    wobble = station.ring_angle
    return _rotate_poly(mesh.back_ring, wobble)


def local_to_world(point: tuple[float, float], station: SpaceStation) -> Vec2:
    lx, ly = point
    scale = station.radius
    return Vec2(station.pos.x + lx * scale, station.pos.y + ly * scale)
