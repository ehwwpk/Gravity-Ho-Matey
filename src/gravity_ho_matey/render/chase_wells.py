from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GravityWell
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.lighting import (
    LightRig,
    arc_tone_for_point,
    material_for,
    well_material_kind,
)

# Chase: floor rings — segment-stitched (never chord through behind-camera collapse).
CHASE_RING_FRACS = (1.0, 0.82, 0.64, 0.46, 0.28)
CHASE_RING_FRACS_COMPACT = (1.0, 0.72, 0.44)
_FLOOR_SEGMENTS = 48
_MAX_SEGMENT_PX = 160.0
_HORIZON_RING_SLACK = 22.0
_MIN_RING_SPAN_PX = 10.0
_LETHAL_KINDS = frozenset({"black_hole", "planet"})


def project_floor_ring(
    camera: ViewCamera,
    center: Vec2,
    world_radius: float,
    ship_pos: Vec2,
    ship_angle: float,
    *,
    horizon: float,
) -> list[tuple[float, float] | None]:
    """Sample a floor circle; None breaks arcs (behind cam / below horizon)."""
    if world_radius <= 0.5:
        return []
    margin = max(240.0, world_radius * 0.42)
    min_ahead = -world_radius * 0.92
    pts: list[tuple[float, float] | None] = []
    for i in range(_FLOOR_SEGMENTS + 1):
        a = (i / _FLOOR_SEGMENTS) * math.tau
        wp = center + Vec2(math.cos(a), math.sin(a)) * world_radius
        p = camera.world_to_chase_screen(
            wp,
            ship_pos,
            ship_angle,
            min_ahead=min_ahead,
            screen_margin=margin,
        )
        if not p.visible or p.y < horizon - _HORIZON_RING_SLACK:
            pts.append(None)
        else:
            pts.append((p.x, p.y))
    return pts


def chase_well_drawable(
    camera: ViewCamera,
    well: GravityWell,
    ship_pos: Vec2,
    ship_angle: float,
) -> tuple[bool, Vec2, float]:
    """True when lateral/back ring arcs should render even if the well center is off-screen."""
    horizon = camera.chase_horizon_y()
    outer_pts = project_floor_ring(
        camera, well.pos, well.radius, ship_pos, ship_angle, horizon=horizon,
    )
    if not _ring_drawable(outer_pts, horizon):
        return False, Vec2(), 0.0
    visible = [p for p in outer_pts if p is not None]
    cx = sum(x for x, _ in visible) / len(visible)
    cy = sum(y for _, y in visible) / len(visible)
    cp = camera.world_to_chase_screen(
        well.pos,
        ship_pos,
        ship_angle,
        min_ahead=-well.radius * 0.5,
        screen_margin=max(240.0, well.radius * 0.35),
    )
    depth = max(cp.depth, camera.min_depth)
    return True, Vec2(cx, cy), depth


def _ring_fracs_for(well: GravityWell) -> tuple[float, ...]:
    if well.kind in _LETHAL_KINDS and well.radius >= 120.0:
        return CHASE_RING_FRACS
    return CHASE_RING_FRACS_COMPACT


def floor_ring_span(pts: list[tuple[float, float] | None]) -> float:
    visible = [p for p in pts if p is not None]
    if len(visible) < 2:
        return 0.0
    xs = [x for x, _ in visible]
    return max(xs) - min(xs)


def draw_chase_well(
    canvas: tk.Canvas,
    pos: Vec2,
    well: GravityWell,
    *,
    scale: float,
    elapsed: float,
    depth: float,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    default_maw: float,
    rig: LightRig,
) -> None:
    _ = elapsed, scale
    horizon = camera.chase_horizon_y()
    material = material_for(well_material_kind(well.kind), theme=rig.theme)
    screen_cx, screen_cy = pos.x, pos.y

    outer_pts = project_floor_ring(
        camera, well.pos, well.radius, ship_pos, ship_angle, horizon=horizon,
    )
    any_ring = _ring_drawable(outer_pts, horizon)

    if well.kind == "black_hole":
        label_color = "#c58cff"
    elif well.kind == "planet":
        label_color = palette.PLANET_LABEL
    else:
        label_color = "#caaaff"

    for frac in _ring_fracs_for(well):
        pts = project_floor_ring(
            camera, well.pos, well.radius * frac, ship_pos, ship_angle, horizon=horizon,
        )
        if not _ring_drawable(pts, horizon):
            continue
        any_ring = True
        width = 3 if frac >= 0.82 else (2 if frac >= 0.5 else 1)
        _stroke_ring_lit(canvas, pts, screen_cx, screen_cy, rig, material, width)

    if not any_ring:
        return

    core_r = max(10.0, min(22.0, well.radius * 0.09))
    if well.kind in _LETHAL_KINDS:
        maw = well.maw_radius if well.maw_radius is not None else default_maw
        core_r = max(8.0, min(18.0, maw * 0.85))
    core_pts = project_floor_ring(
        camera, well.pos, core_r, ship_pos, ship_angle, horizon=horizon,
    )
    if _ring_drawable(core_pts, horizon):
        _fill_ring_lit(canvas, core_pts, material)

    if well.label and depth < camera.focal_length * 2.5 and floor_ring_span(outer_pts) >= 24.0:
        visible = [p for p in outer_pts if p is not None]
        if visible:
            cx = sum(x for x, _ in visible) / len(visible)
            top_y = min(y for _, y in visible)
            font_size = max(7, min(10, int(7 + floor_ring_span(outer_pts) * 0.018)))
            canvas.create_text(cx, top_y - 8, text=well.label, fill=label_color, font=("Courier", font_size))


def _ring_drawable(pts: list[tuple[float, float] | None], horizon: float) -> bool:
    """True when any ring arc is worth stroking — including lateral side arcs."""
    visible = [p for p in pts if p is not None]
    if len(visible) < 2:
        return False
    if floor_ring_span(pts) >= _MIN_RING_SPAN_PX:
        return True
    max_y = max(y for _, y in visible)
    return len(visible) >= 3 and max_y >= horizon - _HORIZON_RING_SLACK * 0.35


def _stroke_ring_lit(
    canvas: tk.Canvas,
    pts: list[tuple[float, float] | None],
    center_x: float,
    center_y: float,
    rig: LightRig,
    material,
    width: int,
) -> None:
    for ax, ay, bx, by in _ring_segments(pts):
        mx, my = (ax + bx) * 0.5, (ay + by) * 0.5
        color = arc_tone_for_point(mx, my, center_x, center_y, rig, material)
        canvas.create_line(ax, ay, bx, by, fill=color, width=width)


def _fill_ring_lit(
    canvas: tk.Canvas,
    pts: list[tuple[float, float] | None],
    material,
) -> None:
    visible = [p for p in pts if p is not None]
    if len(visible) < 3:
        return
    flat: list[float] = []
    for x, y in visible:
        flat.extend((x, y))
    canvas.create_polygon(*flat, fill=material.deep, outline=material.rim, width=1)


def _stroke_ring(
    canvas: tk.Canvas,
    pts: list[tuple[float, float] | None],
    color: str,
    width: int,
) -> None:
    for ax, ay, bx, by in _ring_segments(pts):
        canvas.create_line(ax, ay, bx, by, fill=color, width=width)


def _fill_ring(
    canvas: tk.Canvas,
    pts: list[tuple[float, float] | None],
    fill: str,
    outline: str,
) -> None:
    visible = [p for p in pts if p is not None]
    if len(visible) < 3:
        return
    flat: list[float] = []
    for x, y in visible:
        flat.extend((x, y))
    canvas.create_polygon(*flat, fill=fill, outline=outline, width=1)


def _ring_segments(pts: list[tuple[float, float] | None]) -> list[tuple[float, float, float, float]]:
    """Short arc segments only — no wrap chords, no (0,0) spikes."""
    segments: list[tuple[float, float, float, float]] = []
    prev: tuple[float, float] | None = None
    first: tuple[float, float] | None = None
    last: tuple[float, float] | None = None
    max_sq = _MAX_SEGMENT_PX * _MAX_SEGMENT_PX

    for pt in pts:
        if pt is None:
            prev = None
            continue
        if first is None:
            first = pt
        if prev is not None:
            dx = pt[0] - prev[0]
            dy = pt[1] - prev[1]
            dist_sq = dx * dx + dy * dy
            if 0.25 < dist_sq <= max_sq:
                segments.append((prev[0], prev[1], pt[0], pt[1]))
        prev = pt
        last = pt

    if first is not None and last is not None and last != first:
        dx = first[0] - last[0]
        dy = first[1] - last[1]
        if dx * dx + dy * dy <= max_sq and dx * dx + dy * dy > 0.25:
            segments.append((last[0], last[1], first[0], first[1]))
    return segments
