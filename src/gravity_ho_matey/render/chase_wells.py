from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GravityWell
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera

# Chase: 3 rings on the floor plane — same projection as the gravity grid (no screen ovals).
CHASE_RING_FRACS = (1.0, 0.72, 0.44)
_FLOOR_SEGMENTS = 40
_LETHAL_KINDS = frozenset({"black_hole", "planet"})


def project_floor_ring(
    camera: ViewCamera,
    center: Vec2,
    world_radius: float,
    ship_pos: Vec2,
    ship_angle: float,
) -> list[tuple[float, float]]:
    """Sample a world-space floor circle through the chase camera — matches grid vertices."""
    if world_radius <= 0.5:
        return []
    pts: list[tuple[float, float]] = []
    for i in range(_FLOOR_SEGMENTS + 1):
        a = (i / _FLOOR_SEGMENTS) * math.tau
        wp = center + Vec2(math.cos(a), math.sin(a)) * world_radius
        p = camera.world_to_screen(wp, ship_pos, ship_angle)
        pts.append((p.x, p.y))
    return pts


def floor_ring_span(pts: list[tuple[float, float]]) -> float:
    if len(pts) < 2:
        return 0.0
    xs = [x for x, _ in pts]
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
) -> None:
    """Gravity wells as floor discs — one projection truth shared with the purple grid."""
    _ = elapsed, pos, scale
    horizon = camera.chase_horizon_y()

    outer_pts = project_floor_ring(camera, well.pos, well.radius, ship_pos, ship_angle)
    if not _ring_on_floor(outer_pts, horizon):
        return

    if well.kind == "black_hole":
        ring_color = palette.BLACK_HOLE_RING
        core_fill = palette.BLACK_HOLE_CORE
        core_edge = palette.BLACK_HOLE
        label_color = "#c58cff"
    elif well.kind == "planet":
        ring_color = palette.PLANET_WELL
        core_fill = palette.PLANET_CORE
        core_edge = ""
        label_color = palette.PLANET_LABEL
    else:
        ring_color = palette.WELL
        core_fill = palette.WELL_CORE
        core_edge = ""
        label_color = "#caaaff"

    for frac in CHASE_RING_FRACS:
        pts = project_floor_ring(camera, well.pos, well.radius * frac, ship_pos, ship_angle)
        if not _ring_on_floor(pts, horizon):
            continue
        width = 2 if frac >= 0.72 else 1
        _stroke_ring(canvas, pts, ring_color, width)

    if well.kind in _LETHAL_KINDS:
        maw = well.maw_radius if well.maw_radius is not None else default_maw
        maw_pts = project_floor_ring(camera, well.pos, maw * 1.05, ship_pos, ship_angle)
        if _ring_on_floor(maw_pts, horizon):
            _stroke_ring(canvas, maw_pts, palette.HELM_THREAT_LETHAL, 2)
            _stroke_ring(canvas, maw_pts, "#ff8899", 1)

    core_r = max(10.0, min(22.0, well.radius * 0.09))
    if well.kind in _LETHAL_KINDS:
        maw = well.maw_radius if well.maw_radius is not None else default_maw
        core_r = max(8.0, min(18.0, maw * 0.85))
    core_pts = project_floor_ring(camera, well.pos, core_r, ship_pos, ship_angle)
    if _ring_on_floor(core_pts, horizon):
        flat = _flat_points(core_pts)
        canvas.create_polygon(*flat, fill=core_fill, outline=core_edge or core_fill, width=1)

    if well.label and depth < camera.focal_length * 2.5 and floor_ring_span(outer_pts) >= 24.0:
        cx = sum(x for x, _ in outer_pts) / len(outer_pts)
        top_y = min(y for _, y in outer_pts)
        font_size = max(7, min(10, int(7 + floor_ring_span(outer_pts) * 0.018)))
        canvas.create_text(cx, top_y - 8, text=well.label, fill=label_color, font=("Courier", font_size))


def _ring_on_floor(pts: list[tuple[float, float]], horizon: float) -> bool:
    if len(pts) < 4:
        return False
    avg_y = sum(y for _, y in pts) / len(pts)
    return avg_y >= horizon + 2.0


def _stroke_ring(canvas: tk.Canvas, pts: list[tuple[float, float]], color: str, width: int) -> None:
    flat = _flat_points(pts)
    canvas.create_line(*flat, fill=color, width=width, smooth=True)


def _flat_points(pts: list[tuple[float, float]]) -> list[float]:
    flat: list[float] = []
    for x, y in pts:
        flat.extend((x, y))
    return flat
