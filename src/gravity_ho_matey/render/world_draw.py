from __future__ import annotations

import math

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode, ViewCamera
from gravity_ho_matey.render.lighting import LightRig, arc_tone_for_point, material_for, well_material_kind
from gravity_ho_matey.gameplay.powerup_stacks import PowerUpStacks
from gravity_ho_matey.render.ship_viz import draw_fighter_ship, draw_fighter_ship_fallback


def draw_gravity_heatmap(
    canvas: tk.Canvas,
    field: GravityField,
    camera: ViewCamera,
    *,
    y_offset: float = 0.0,
    alpha_step: int = 2,
    ship_pos: Vec2 | None = None,
    world: GameWorld | None = None,
    check_asteroids: bool = False,
) -> None:
    _ = world, check_asteroids
    if camera.mode is not CameraMode.TACTICAL:
        return

    anchor = ship_pos if ship_pos is not None else camera.center
    step_world = field.cell_size * alpha_step

    for row in range(0, field.rows, alpha_step):
        for col in range(0, field.cols, alpha_step):
            cell = field.cell_at(col, row)
            if cell.magnitude <= 1e-6:
                continue
            norm = cell.magnitude / field.max_magnitude
            if norm < 0.14:
                continue
            wx = field.origin.x + col * field.cell_size
            wy = field.origin.y + row * field.cell_size
            p0 = camera.world_to_screen(Vec2(wx, wy), anchor, 0.0)
            p1 = camera.world_to_screen(Vec2(wx + step_world, wy + step_world), anchor, 0.0)
            sx = min(p0.x, p1.x)
            sy = min(p0.y, p1.y) + y_offset
            ex = max(p0.x, p1.x)
            ey = max(p0.y, p1.y) + y_offset
            if ex < 0 or ey < y_offset or sx > camera.viewport_width or sy > camera.viewport_height:
                continue
            tone = gravity_field_color(norm)
            cx = (sx + ex) * 0.5
            cy = (sy + ey) * 0.5
            radius = max(2.0, min(ex - sx, ey - sy) * 0.48)
            canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill=tone, outline="")


def draw_gravity_floor_grid(
    canvas: tk.Canvas,
    field: GravityField,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    *,
    y_offset: float,
    step: int = 2,
    world: GameWorld | None = None,
    check_asteroids: bool = False,
) -> None:
    for row in range(0, field.rows, step):
        for col in range(0, field.cols - 1, step):
            a = Vec2(field.origin.x + col * field.cell_size, field.origin.y + row * field.cell_size)
            b = Vec2(field.origin.x + (col + step) * field.cell_size, field.origin.y + row * field.cell_size)
            _draw_field_segment(
                canvas, field, camera, ship_pos, ship_angle, a, b, y_offset,
                world=world, check_asteroids=check_asteroids,
            )
    for col in range(0, field.cols, step):
        for row in range(0, field.rows - 1, step):
            a = Vec2(field.origin.x + col * field.cell_size, field.origin.y + row * field.cell_size)
            b = Vec2(field.origin.x + col * field.cell_size, field.origin.y + (row + step) * field.cell_size)
            _draw_field_segment(
                canvas, field, camera, ship_pos, ship_angle, a, b, y_offset,
                world=world, check_asteroids=check_asteroids,
            )


def _draw_field_segment(
    canvas: tk.Canvas,
    field: GravityField,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    a: Vec2,
    b: Vec2,
    y_offset: float,
    *,
    world: GameWorld | None = None,
    check_asteroids: bool = False,
) -> None:
    from gravity_ho_matey.render.chase_threat import ahead_emphasis

    pa = camera.world_to_screen(a, ship_pos, ship_angle)
    pb = camera.world_to_screen(b, ship_pos, ship_angle)
    if camera.mode is CameraMode.TACTICAL:
        if pa.x < -24 and pb.x < -24:
            return
        if pa.y < -24 and pb.y < -24:
            return
        if pa.x > camera.viewport_width + 24 and pb.x > camera.viewport_width + 24:
            return
        if pa.y + y_offset > camera.viewport_height + 24 and pb.y + y_offset > camera.viewport_height + 24:
            return
    elif not pa.visible and not pb.visible:
        return
    mid = Vec2((a.x + b.x) * 0.5, (a.y + b.y) * 0.5)
    norm = field.normalized_magnitude_at(mid)
    _ = world, check_asteroids
    color = gravity_field_color(norm)
    if world is not None and camera.mode is CameraMode.TACTICAL:
        emphasis = ahead_emphasis(ship_pos, ship_angle, mid)
        width = max(1, int((1 + norm * 3) * emphasis))
    else:
        width = max(1, int(1 + norm * 3))
    canvas.create_line(pa.x, pa.y + y_offset, pb.x, pb.y + y_offset, fill=color, width=width)


def gravity_field_color(norm: float) -> str:
    """Purple intensifies with local gravity — shared tactical + chase grid."""
    t = max(0.0, min(1.0, norm))
    if t > 0.88:
        return palette.CHASE_GRID_HIGH
    if t > 0.72:
        return palette.BLACK_HOLE_RING
    if t > 0.55:
        return "#5a1840"
    if t > 0.35:
        return palette.CHASE_GRID_MID
    if t > 0.18:
        return palette.CHASE_GRID_LOW
    return "#0e2230"


# Ring art uses full gameplay radius — overlap on Cove is intentional (soul of the game).
WELL_RING_VISUAL_SCALE = 1.0

_BLACK_HOLE_RING_FRACS = (1.0, 0.86, 0.72, 0.58, 0.44)
_WELL_RING_FRACS = (1.0, 0.72, 0.44)


def well_screen_radius(world_radius: float, scale: float) -> float:
    """Perspective or tactical scale — no art shrink; rings match pull zone size."""
    return world_radius * scale * WELL_RING_VISUAL_SCALE


def draw_well(
    canvas: tk.Canvas,
    pos: Vec2,
    radius: float,
    label: str,
    kind: str,
    *,
    scale: float = 1.0,
    rig: LightRig | None = None,
) -> None:
    r = radius * scale
    theme = rig.theme if rig is not None else "cove"
    material = material_for(well_material_kind(kind), theme=theme)
    cx, cy = pos.x, pos.y
    if kind == "black_hole":
        ring_fracs = _BLACK_HOLE_RING_FRACS
    else:
        ring_fracs = _WELL_RING_FRACS
    for i, frac in enumerate(ring_fracs):
        ring = r * frac
        width = 2 if (kind == "black_hole" and (i < 3 or frac >= 0.58)) or frac >= 0.72 else 1
        if rig is not None:
            _draw_lit_ring_oval(canvas, cx, cy, ring, rig, material, width)
        else:
            color = material.rim
            canvas.create_oval(cx - ring, cy - ring, cx + ring, cy + ring, outline=color, width=width)
    core = max(10.0, 22 * scale) if kind == "black_hole" else 10 * scale
    if kind == "planet":
        canvas.create_oval(cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55, fill=material.mid, outline="")
    canvas.create_oval(cx - core, cy - core, cx + core, cy + core, fill=material.deep, outline=material.rim, width=2)
    if rig is not None:
        hx = cx + rig.key_dir.x * core * 0.35
        hy = cy + rig.key_dir.y * core * 0.35
        canvas.create_oval(hx - core * 0.35, hy - core * 0.35, hx + core * 0.25, hy + core * 0.25, fill=material.highlight, outline="")
    if kind == "black_hole":
        label_color = "#c58cff"
    elif kind == "planet":
        label_color = palette.PLANET_LABEL
    else:
        label_color = "#caaaff"
    if label and scale >= 0.35:
        font_size = max(6, int(8 * scale))
        canvas.create_text(cx, cy - r - 10 * scale, text=label, fill=label_color, font=("Courier", font_size))


def _draw_lit_ring_oval(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    radius: float,
    rig: LightRig,
    material,
    width: int,
) -> None:
    segments = 24
    for i in range(segments):
        a0 = (i / segments) * math.tau
        a1 = ((i + 1) / segments) * math.tau
        x0 = cx + math.cos(a0) * radius
        y0 = cy + math.sin(a0) * radius
        x1 = cx + math.cos(a1) * radius
        y1 = cy + math.sin(a1) * radius
        mx, my = (x0 + x1) * 0.5, (y0 + y1) * 0.5
        color = arc_tone_for_point(mx, my, cx, cy, rig, material)
        canvas.create_line(x0, y0, x1, y1, fill=color, width=width)


def draw_ship(
    canvas: tk.Canvas,
    pos: Vec2,
    angle: float,
    boost_energy: float,
    *,
    boost_burst: float = 0.0,
    invuln: float = 0.0,
    elapsed: float = 0.0,
    scale: float = 1.0,
    rig: LightRig | None = None,
    powerup_stacks: PowerUpStacks | None = None,
) -> None:
    if invuln > 0.0 and int(elapsed * 14) % 2 == 0:
        ring_r = 22 * scale
        canvas.create_oval(pos.x - ring_r, pos.y - ring_r, pos.x + ring_r, pos.y + ring_r, outline=palette.HUD_ACCENT, width=2)
    if rig is not None:
        draw_fighter_ship(
            canvas,
            pos,
            angle,
            scale=scale,
            rig=rig,
            boost_burst=boost_burst,
            powerup_stacks=powerup_stacks,
        )
    else:
        draw_fighter_ship_fallback(canvas, pos, angle, scale=scale)
    _ = boost_energy


def draw_velocity_trail(canvas: tk.Canvas, ship_pos: Vec2, ship_vel: Vec2, screen_pos: Vec2) -> None:
    if ship_vel.length_sq() <= 25.0:
        return
    tail_world = ship_pos - ship_vel.normalized() * min(48.0, ship_vel.length() * 0.18)
    dx = screen_pos.x - (ship_pos.x - tail_world.x)
    dy = screen_pos.y - (ship_pos.y - tail_world.y)
    canvas.create_line(screen_pos.x - dx, screen_pos.y - dy, screen_pos.x, screen_pos.y, fill="#66e8ff", width=2)


def world_playfield_height(world: GameWorld, hud_top: int) -> int:
    return max(world.config.viewport_height, hud_top + (world.config.height - world.config.viewport_height))
