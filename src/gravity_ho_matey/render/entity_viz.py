from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Beacon, Wall
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera


def gate_label(*, unlocked: bool, solar: bool) -> str:
    if solar:
        return "WORMHOLE" if unlocked else "SEALED"
    return "OPEN" if unlocked else "LOCK"


def draw_gate_glyph(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    size: float,
    unlocked: bool,
    solar: bool,
    scale: float = 1.0,
) -> None:
    color = palette.GATE_OPEN if unlocked else palette.GATE_LOCKED
    r = max(14.0, size * 0.45) * scale
    canvas.create_arc(x - r, y - r, x + r, y + r, start=200, extent=140, style="arc", outline=color, width=3)
    canvas.create_line(x - r * 0.85, y + r * 0.35, x + r * 0.85, y + r * 0.35, fill=color, width=2)
    font_size = max(7, min(8, int(8 * scale)))
    canvas.create_text(x, y - 2, text=gate_label(unlocked=unlocked, solar=solar), fill=color, font=("Courier New", font_size, "bold"))


def draw_beacon_glyph(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    collected: bool,
    scale: float = 1.0,
    show_ring: bool = True,
) -> None:
    color = palette.BEACON_COLLECTED if collected else palette.BEACON
    ring = 12.0 * scale
    body = 6.0 * scale
    if show_ring and not collected:
        canvas.create_oval(x - ring, y - ring, x + ring, y + ring, outline=color, width=1)
    canvas.create_rectangle(x - body, y - body, x + body, y + body, fill=color, outline="#dff", width=1)
    canvas.create_polygon(
        x,
        y - 10 * scale,
        x + 5 * scale,
        y - 4 * scale,
        x,
        y + 2 * scale,
        x - 5 * scale,
        y - 4 * scale,
        fill=color,
        outline="",
    )


def draw_tactical_wall(
    canvas: tk.Canvas,
    wall: Wall,
    camera: ViewCamera,
    *,
    hud_top: float,
    solar: bool,
    world_width: float,
    world_height: float,
) -> None:
    r = wall.rect
    boundary = (
        r.x <= 1.0
        or r.y <= 1.0
        or r.x + r.w >= world_width - 1.0
        or r.y + r.h >= world_height - 1.0
    )
    if boundary:
        _draw_boundary_rail(canvas, r, camera, hud_top=hud_top, solar=solar, world_width=world_width, world_height=world_height)
    else:
        _draw_interior_obstacle(canvas, r, camera, hud_top=hud_top, solar=solar)


def _draw_boundary_rail(
    canvas: tk.Canvas,
    r: Rect,
    camera: ViewCamera,
    *,
    hud_top: float,
    solar: bool,
    world_width: float,
    world_height: float,
) -> None:
    edge = palette.HOLO_WALL_EDGE if not solar else palette.ASTEROID_EDGE
    if r.h <= 40 and r.w >= world_width * 0.5:
        y = r.y + r.h if r.y <= 1.0 else r.y
        pa = camera.world_to_screen(Vec2(r.x, y), Vec2(), 0.0)
        pb = camera.world_to_screen(Vec2(r.x + r.w, y), Vec2(), 0.0)
        canvas.create_line(pa.x, pa.y + hud_top, pb.x, pb.y + hud_top, fill=edge, width=2)
    elif r.w <= 40 and r.h >= world_height * 0.5:
        x = r.x + r.w if r.x <= 1.0 else r.x
        pa = camera.world_to_screen(Vec2(x, r.y), Vec2(), 0.0)
        pb = camera.world_to_screen(Vec2(x, r.y + r.h), Vec2(), 0.0)
        canvas.create_line(pa.x, pa.y + hud_top, pb.x, pb.y + hud_top, fill=edge, width=2)


def _draw_interior_obstacle(canvas: tk.Canvas, r: Rect, camera: ViewCamera, *, hud_top: float, solar: bool) -> None:
    fill = palette.HOLO_WALL_FILL if not solar else palette.ASTEROID
    edge = palette.HOLO_WALL_EDGE if not solar else palette.ASTEROID_EDGE
    corners = (
        Vec2(r.x, r.y),
        Vec2(r.x + r.w, r.y),
        Vec2(r.x + r.w, r.y + r.h),
        Vec2(r.x, r.y + r.h),
    )
    pts: list[float] = []
    for c in corners:
        p = camera.world_to_screen(c, Vec2(), 0.0)
        pts.extend((p.x, p.y + hud_top))
    canvas.create_polygon(*pts, fill=fill, outline=edge, width=2)


def draw_gate_portal(
    canvas: tk.Canvas,
    center: Vec2,
    *,
    size: float,
    unlocked: bool,
    solar: bool,
    hud_top: float = 0.0,
) -> None:
    draw_gate_glyph(
        canvas,
        center.x,
        center.y + hud_top,
        size=size,
        unlocked=unlocked,
        solar=solar,
        scale=1.0,
    )


def draw_beacon_marker(canvas: tk.Canvas, pos: Vec2, beacon: Beacon, *, hud_top: float) -> None:
    draw_beacon_glyph(
        canvas,
        pos.x,
        pos.y + hud_top,
        collected=beacon.collected,
        scale=1.0,
        show_ring=True,
    )
