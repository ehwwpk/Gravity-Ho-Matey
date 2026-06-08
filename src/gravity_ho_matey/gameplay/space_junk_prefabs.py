from __future__ import annotations

import math
from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import ContactPolicy, JunkLayer, SpaceJunk

MAX_PREFAB_VERTS = 12


@dataclass(frozen=True, slots=True)
class JunkDrawSpec:
    rib_lines: tuple[tuple[Vec2, Vec2], ...] = ()
    rivet_points: tuple[Vec2, ...] = ()


@dataclass(frozen=True, slots=True)
class JunkPrefab:
    id: str
    local_verts: tuple[Vec2, ...]
    default_contact: ContactPolicy
    tactical_detail: JunkDrawSpec
    chase_depth_bias: float = 0.0


_instance_counter = 0


def _rect(hw: float, hh: float) -> tuple[Vec2, ...]:
    return (
        Vec2(-hw, -hh),
        Vec2(hw, -hh),
        Vec2(hw, hh),
        Vec2(-hw, hh),
    )


def _arc_sector(radius: float, start_deg: float, end_deg: float, segments: int = 8) -> tuple[Vec2, ...]:
    start = math.radians(start_deg)
    end = math.radians(end_deg)
    step = (end - start) / max(1, segments - 1)
    verts = [Vec2(0.0, 0.0)]
    for i in range(segments):
        a = start + step * i
        verts.append(Vec2(math.cos(a) * radius, math.sin(a) * radius))
    return tuple(verts)


def _convex_hull(points: list[Vec2]) -> tuple[Vec2, ...]:
    pts = sorted(set(points), key=lambda p: (p.x, p.y))
    if len(pts) <= 1:
        return tuple(pts)

    def cross(o: Vec2, a: Vec2, b: Vec2) -> float:
        return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)

    lower: list[Vec2] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[Vec2] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return tuple(lower[:-1] + upper[:-1])


def _signed_area(verts: tuple[Vec2, ...]) -> float:
    area = 0.0
    count = len(verts)
    for i in range(count):
        j = (i + 1) % count
        area += verts[i].x * verts[j].y - verts[j].x * verts[i].y
    return area * 0.5


def _is_convex_ccw(verts: tuple[Vec2, ...]) -> bool:
    if len(verts) < 3:
        return False
    if _signed_area(verts) <= 1e-6:
        return False
    count = len(verts)
    sign = 0
    for i in range(count):
        a = verts[i]
        b = verts[(i + 1) % count]
        c = verts[(i + 2) % count]
        cross = (b.x - a.x) * (c.y - b.y) - (b.y - a.y) * (c.x - b.x)
        if abs(cross) <= 1e-9:
            continue
        current = 1 if cross > 0 else -1
        if sign == 0:
            sign = current
        elif current != sign:
            return False
    return sign != 0


def _validate_prefab(prefab: JunkPrefab) -> None:
    if len(prefab.local_verts) > MAX_PREFAB_VERTS:
        raise ValueError(f"prefab {prefab.id} exceeds max vert count {MAX_PREFAB_VERTS}")
    if not _is_convex_ccw(prefab.local_verts):
        raise ValueError(f"prefab {prefab.id} is not convex CCW")
    if max(v.length() for v in prefab.local_verts) <= 0:
        raise ValueError(f"prefab {prefab.id} has zero radius")


def _rib_h(v: float, span: float) -> tuple[tuple[Vec2, Vec2], ...]:
    return ((Vec2(-span, v), Vec2(span, v)),)


_GIRDER_RIBS = _rib_h(-8.0, 52.0) + _rib_h(8.0, 52.0)
_HULL_RIBS = ((Vec2(-20.0, -12.0), Vec2(20.0, 12.0)),)
_CONTAINER_RIBS = _rib_h(-12.0, 24.0) + _rib_h(12.0, 24.0)


def _build_registry() -> dict[str, JunkPrefab]:
    truss_l = _convex_hull(
        [
            Vec2(-40.0, -40.0),
            Vec2(40.0, -40.0),
            Vec2(40.0, -20.0),
            Vec2(0.0, -20.0),
            Vec2(0.0, 40.0),
            Vec2(-40.0, 40.0),
        ]
    )
    pipe_verts = _convex_hull(
        [
            Vec2(-50.0, -18.0),
            Vec2(-42.0, -18.0),
            Vec2(-38.0, 0.0),
            Vec2(-42.0, 18.0),
            Vec2(-50.0, 18.0),
            Vec2(50.0, 18.0),
            Vec2(42.0, 18.0),
            Vec2(38.0, 0.0),
            Vec2(42.0, -18.0),
            Vec2(50.0, -18.0),
        ]
    )
    shrapnel = (
        Vec2(-38.0, -22.0),
        Vec2(12.0, -30.0),
        Vec2(44.0, -8.0),
        Vec2(28.0, 26.0),
        Vec2(-18.0, 32.0),
        Vec2(-42.0, 10.0),
    )
    claw = _convex_hull(
        [
            Vec2(-30.0, -36.0),
            Vec2(36.0, -36.0),
            Vec2(36.0, -8.0),
            Vec2(8.0, 8.0),
            Vec2(-8.0, 36.0),
            Vec2(-30.0, 20.0),
        ]
    )
    prefabs = [
        JunkPrefab(
            id="girder_a",
            local_verts=_rect(60.0, 14.0),
            default_contact=ContactPolicy.CHIP,
            tactical_detail=JunkDrawSpec(rib_lines=_GIRDER_RIBS, rivet_points=(Vec2(-48.0, 0.0), Vec2(48.0, 0.0))),
            chase_depth_bias=-4.0,
        ),
        JunkPrefab(
            id="hull_plate_a",
            local_verts=(Vec2(-45.0, -27.0), Vec2(45.0, -27.0), Vec2(30.0, 27.0), Vec2(-30.0, 27.0)),
            default_contact=ContactPolicy.CHIP,
            tactical_detail=JunkDrawSpec(rib_lines=_HULL_RIBS),
            chase_depth_bias=-6.0,
        ),
        JunkPrefab(
            id="rib_arc_a",
            local_verts=_arc_sector(70.0, -45.0, 45.0, segments=9),
            default_contact=ContactPolicy.CHIP,
            tactical_detail=JunkDrawSpec(),
            chase_depth_bias=-8.0,
        ),
        JunkPrefab(
            id="truss_corner_a",
            local_verts=truss_l,
            default_contact=ContactPolicy.CHIP,
            tactical_detail=JunkDrawSpec(rivet_points=(Vec2(-28.0, -28.0), Vec2(28.0, 28.0))),
            chase_depth_bias=-5.0,
        ),
        JunkPrefab(
            id="container_a",
            local_verts=_rect(32.0, 24.0),
            default_contact=ContactPolicy.CHIP,
            tactical_detail=JunkDrawSpec(rib_lines=_CONTAINER_RIBS),
            chase_depth_bias=-3.0,
        ),
        JunkPrefab(
            id="pipe_a",
            local_verts=pipe_verts,
            default_contact=ContactPolicy.CHIP,
            tactical_detail=JunkDrawSpec(rib_lines=((Vec2(-36.0, 0.0), Vec2(36.0, 0.0)),)),
            chase_depth_bias=-2.0,
        ),
        JunkPrefab(
            id="shrapnel_fan_a",
            local_verts=shrapnel,
            default_contact=ContactPolicy.CHIP,
            tactical_detail=JunkDrawSpec(),
            chase_depth_bias=-7.0,
        ),
        JunkPrefab(
            id="boom_segment_a",
            local_verts=_rect(100.0, 6.0),
            default_contact=ContactPolicy.CHIP,
            tactical_detail=JunkDrawSpec(rib_lines=((Vec2(-80.0, 0.0), Vec2(80.0, 0.0)),)),
            chase_depth_bias=-1.0,
        ),
        JunkPrefab(
            id="docking_claw_a",
            local_verts=claw,
            default_contact=ContactPolicy.BOUNCE,
            tactical_detail=JunkDrawSpec(rivet_points=(Vec2(0.0, -20.0),)),
            chase_depth_bias=-6.0,
        ),
    ]
    registry: dict[str, JunkPrefab] = {}
    for prefab in prefabs:
        if prefab.id in registry:
            raise ValueError(f"duplicate prefab id {prefab.id}")
        _validate_prefab(prefab)
        registry[prefab.id] = prefab
    return registry


PREFAB_REGISTRY: dict[str, JunkPrefab] = _build_registry()


def instantiate_junk(
    prefab_id: str,
    pos: Vec2,
    angle: float = 0.0,
    *,
    contact_policy: ContactPolicy | None = None,
) -> SpaceJunk:
    """Copy prefab verts into a new instance; registry validates convex at load."""
    global _instance_counter
    prefab = PREFAB_REGISTRY.get(prefab_id)
    if prefab is None:
        raise KeyError(f"unknown junk prefab: {prefab_id}")
    copied = tuple(Vec2(v.x, v.y) for v in prefab.local_verts)
    _instance_counter += 1
    return SpaceJunk(
        pos=Vec2(pos.x, pos.y),
        angle=angle,
        prefab_id=prefab_id,
        local_verts=copied,
        contact_policy=contact_policy if contact_policy is not None else prefab.default_contact,
        layer=JunkLayer.STRUCTURAL,
        instance_id=_instance_counter,
    )


def reset_instance_counter() -> None:
    global _instance_counter
    _instance_counter = 0


def validate_space_junk_list(junk_list: list[SpaceJunk], *, max_count: int) -> None:
    if len(junk_list) > max_count:
        raise ValueError(f"space junk count {len(junk_list)} exceeds max {max_count}")
    for junk in junk_list:
        if junk.layer is not JunkLayer.STRUCTURAL:
            continue
        if not _is_convex_ccw(junk.local_verts):
            raise ValueError(f"junk instance {junk.instance_id} is not convex CCW")
        if junk.approximate_radius() <= 0:
            raise ValueError(f"junk instance {junk.instance_id} has zero radius")
