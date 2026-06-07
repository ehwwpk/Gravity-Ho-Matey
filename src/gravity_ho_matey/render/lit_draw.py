from __future__ import annotations

import math

import tkinter as tk

from gravity_ho_matey.gameplay.asteroid_shape import crater_offsets
from gravity_ho_matey.render.lighting import (
    LightRig,
    MaterialTones,
    face_normal_outward,
    normal_dot_key,
    poly_centroid,
    shade_band,
    tone_for_band,
)


def _flat(points: list[tuple[float, float]]) -> list[float]:
    out: list[float] = []
    for x, y in points:
        out.extend((x, y))
    return out


def draw_illustrated_polygon(
    canvas: tk.Canvas,
    screen_pts: list[tuple[float, float]],
    *,
    rig: LightRig,
    material: MaterialTones,
    seed: int,
    radius_hint: float,
    outline_width: int = 2,
    edge_override: str | None = None,
    crater_count: int | None = None,
) -> None:
    """Faceted 2D rock — light from rig.key_dir, no extrusion."""
    if len(screen_pts) < 3:
        return
    cx, cy = poly_centroid(screen_pts)
    n = len(screen_pts)

    canvas.create_polygon(*_flat(screen_pts), fill=material.mid, outline="")

    for i in range(n):
        j = (i + 1) % n
        ax, ay = screen_pts[i]
        bx, by = screen_pts[j]
        nx, ny = face_normal_outward(ax, ay, bx, by, cx, cy)
        band = shade_band(normal_dot_key(nx, ny, rig))
        canvas.create_polygon(cx, cy, ax, ay, bx, by, fill=tone_for_band(material, band), outline="")

    shadow_pts = _inset_toward(screen_pts, cx, cy, rig.key_dir.x * -0.18, rig.key_dir.y * -0.18, 0.72)
    if len(shadow_pts) >= 3:
        canvas.create_polygon(*_flat(shadow_pts), fill=material.deep, outline="")

    highlight_pts = _inset_toward(screen_pts, cx, cy, rig.key_dir.x * 0.14, rig.key_dir.y * 0.14, 0.58)
    if len(highlight_pts) >= 3:
        canvas.create_polygon(*_flat(highlight_pts), fill=material.highlight, outline="")

    edge = edge_override or material.rim
    canvas.create_polygon(*_flat(screen_pts), fill="", outline=edge, width=outline_width)

    count = crater_count if crater_count is not None else min(4, 2 + (seed % 3))
    scale = max(0.4, min(1.0, radius_hint / 48.0))
    for idx, (lx, ly, lr) in enumerate(crater_offsets(seed, count, radius_hint)):
        _draw_crater_pit(
            canvas,
            cx + lx * scale,
            cy + ly * scale * 0.88,
            lr * scale,
            rig=rig,
            material=material,
            seed=seed + idx,
        )

    for i in range(n):
        j = (i + 1) % n
        ax, ay = screen_pts[i]
        bx, by = screen_pts[j]
        nx, ny = face_normal_outward(ax, ay, bx, by, cx, cy)
        if normal_dot_key(nx, ny, rig) > 0.22 * rig.rim_strength:
            canvas.create_line(ax, ay, bx, by, fill=material.highlight, width=1)


def draw_simplified_polygon(
    canvas: tk.Canvas,
    screen_pts: list[tuple[float, float]],
    *,
    rig: LightRig,
    material: MaterialTones,
    outline_width: int = 1,
) -> None:
    """Two-band glyph for holo map — full illustrated detail later at larger scale."""
    if len(screen_pts) < 3:
        return
    cx, cy = poly_centroid(screen_pts)
    lit_pts = _inset_toward(screen_pts, cx, cy, rig.key_dir.x * 0.12, rig.key_dir.y * 0.12, 0.62)
    canvas.create_polygon(*_flat(screen_pts), fill=material.shadow, outline=material.rim, width=outline_width)
    if len(lit_pts) >= 3:
        canvas.create_polygon(*_flat(lit_pts), fill=material.mid, outline="")


def draw_lit_ship_hull(
    canvas: tk.Canvas,
    nose: tuple[float, float],
    left: tuple[float, float],
    right: tuple[float, float],
    *,
    rig: LightRig,
    material: MaterialTones,
    outline: str,
    outline_width: int = 2,
) -> None:
    pts = [nose, left, right]
    cx = (nose[0] + left[0] + right[0]) / 3.0
    cy = (nose[1] + left[1] + right[1]) / 3.0
    canvas.create_polygon(*_flat(pts), fill=material.shadow, outline="")
    lit = [
        (nose[0] * 0.55 + cx * 0.45, nose[1] * 0.55 + cy * 0.45),
        (left[0] * 0.85 + cx * 0.15, left[1] * 0.85 + cy * 0.15),
        (right[0] * 0.85 + cx * 0.15, right[1] * 0.85 + cy * 0.15),
    ]
    canvas.create_polygon(*_flat(lit), fill=material.mid, outline="")
    canvas.create_polygon(nose[0], nose[1], lit[0][0], lit[0][1], left[0], left[1], fill=material.highlight, outline="")
    canvas.create_polygon(*_flat(pts), fill="", outline=outline, width=outline_width)


def _inset_toward(
    pts: list[tuple[float, float]],
    cx: float,
    cy: float,
    shift_x: float,
    shift_y: float,
    shrink: float,
) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for x, y in pts:
        out.append((cx + (x - cx) * shrink + shift_x * radius_scale(pts), cy + (y - cy) * shrink + shift_y * radius_scale(pts)))
    return out


def radius_scale(pts: list[tuple[float, float]]) -> float:
    cx, cy = poly_centroid(pts)
    return max(8.0, max(math.hypot(x - cx, y - cy) for x, y in pts))


def _draw_crater_pit(
    canvas: tk.Canvas,
    x: float,
    y: float,
    radius: float,
    *,
    rig: LightRig,
    material: MaterialTones,
    seed: int,
) -> None:
    if radius < 1.2:
        return
    canvas.create_oval(x - radius, y - radius * 0.85, x + radius, y + radius * 0.85, fill=material.crater_pit, outline="")
    hx = x + rig.key_dir.x * radius * 0.35
    hy = y + rig.key_dir.y * radius * 0.35
    canvas.create_oval(hx - radius * 0.35, hy - radius * 0.3, hx + radius * 0.35, hy + radius * 0.3, fill=material.crater_rim_hi, outline="")
    sx = x - rig.key_dir.x * radius * 0.25
    sy = y - rig.key_dir.y * radius * 0.25
    canvas.create_oval(sx - radius * 0.5, sy - radius * 0.42, sx + radius * 0.15, sy + radius * 0.15, fill=material.deep, outline="")
