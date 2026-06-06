from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode, ViewCamera


def draw_gravity_heatmap(
    canvas: tk.Canvas,
    field: GravityField,
    camera: ViewCamera,
    *,
    y_offset: float = 0.0,
    alpha_step: int = 2,
    world: GameWorld | None = None,
) -> None:
    from gravity_ho_matey.render.chase_threat import threat_at_point, threat_color

    for row in range(0, field.rows, alpha_step):
        for col in range(0, field.cols, alpha_step):
            cell = field.cell_at(col, row)
            if cell.magnitude <= 1e-6:
                continue
            norm = cell.magnitude / field.max_magnitude
            wx = field.origin.x + col * field.cell_size
            wy = field.origin.y + row * field.cell_size
            projected = camera.world_to_screen(Vec2(wx, wy), Vec2(), 0.0)
            if camera.mode is not CameraMode.TACTICAL:
                continue
            sx = projected.x
            sy = projected.y + y_offset
            size = field.cell_size * alpha_step
            if sx + size < 0 or sy + size < y_offset or sx > camera.viewport_width or sy > camera.viewport_height:
                continue
            if world is not None:
                tone = threat_color(threat_at_point(world, Vec2(wx, wy)), norm=norm)
            else:
                tone = gravity_field_color(norm)
            canvas.create_rectangle(sx, sy, sx + size, sy + size, fill=tone, outline="")


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
) -> None:
    for row in range(0, field.rows, step):
        for col in range(0, field.cols - 1, step):
            a = Vec2(field.origin.x + col * field.cell_size, field.origin.y + row * field.cell_size)
            b = Vec2(field.origin.x + (col + step) * field.cell_size, field.origin.y + row * field.cell_size)
            _draw_field_segment(canvas, field, camera, ship_pos, ship_angle, a, b, y_offset, world=world)
    for col in range(0, field.cols, step):
        for row in range(0, field.rows - 1, step):
            a = Vec2(field.origin.x + col * field.cell_size, field.origin.y + row * field.cell_size)
            b = Vec2(field.origin.x + col * field.cell_size, field.origin.y + (row + step) * field.cell_size)
            _draw_field_segment(canvas, field, camera, ship_pos, ship_angle, a, b, y_offset, world=world)


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
) -> None:
    from gravity_ho_matey.render.chase_threat import ThreatLevel, ahead_emphasis, threat_at_point, threat_color

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
    if world is not None:
        threat = threat_at_point(world, mid)
        color = threat_color(threat, norm=norm)
        emphasis = ahead_emphasis(ship_pos, ship_angle, mid)
        width = max(1, int((1 + norm * 3) * emphasis))
        if threat is not ThreatLevel.SAFE:
            width = max(width, 2)
    else:
        color = gravity_field_color(norm)
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
) -> None:
    r = radius * scale
    if kind == "black_hole":
        for i, frac in enumerate(_BLACK_HOLE_RING_FRACS):
            ring = r * frac
            width = 2 if i < 3 or frac >= 0.58 else 1
            canvas.create_oval(pos.x - ring, pos.y - ring, pos.x + ring, pos.y + ring, outline=palette.BLACK_HOLE_RING, width=width)
        core = max(10.0, 22 * scale)
        canvas.create_oval(pos.x - core, pos.y - core, pos.x + core, pos.y + core, fill=palette.BLACK_HOLE_CORE, outline=palette.BLACK_HOLE, width=2)
        label_color = "#c58cff"
    elif kind == "planet":
        canvas.create_oval(pos.x - r, pos.y - r, pos.x + r, pos.y + r, outline=palette.PLANET_WELL, width=2)
        canvas.create_oval(pos.x - r * 0.55, pos.y - r * 0.55, pos.x + r * 0.55, pos.y + r * 0.55, fill=palette.PLANET_CORE, outline="")
        label_color = palette.PLANET_LABEL
    else:
        for frac in _WELL_RING_FRACS:
            ring = r * frac
            canvas.create_oval(pos.x - ring, pos.y - ring, pos.x + ring, pos.y + ring, outline=palette.WELL, width=2 if frac >= 0.72 else 1)
        core = 10 * scale
        canvas.create_oval(pos.x - core, pos.y - core, pos.x + core, pos.y + core, fill=palette.WELL_CORE, outline="")
        label_color = "#caaaff"
    if label and scale >= 0.35:
        font_size = max(6, int(8 * scale))
        canvas.create_text(pos.x, pos.y - r - 10 * scale, text=label, fill=label_color, font=("Courier", font_size))


def draw_ship(
    canvas: tk.Canvas,
    pos: Vec2,
    angle: float,
    boost: float,
    *,
    invuln: float = 0.0,
    elapsed: float = 0.0,
    scale: float = 1.0,
) -> None:
    if invuln > 0.0 and int(elapsed * 14) % 2 == 0:
        ring_r = 22 * scale
        canvas.create_oval(pos.x - ring_r, pos.y - ring_r, pos.x + ring_r, pos.y + ring_r, outline=palette.HUD_ACCENT, width=2)
    nose = pos + Vec2.from_angle(angle) * (18 * scale)
    left = pos + Vec2.from_angle(angle + 2.45) * (13 * scale)
    right = pos + Vec2.from_angle(angle - 2.45) * (13 * scale)
    canvas.create_polygon(nose.x, nose.y, left.x, left.y, right.x, right.y, fill=palette.SHIP, outline="#fff0b5", width=2)
    mast = pos - Vec2.from_angle(angle) * (4 * scale)
    sail_tip = mast + Vec2.from_angle(angle + 1.55) * (9 * scale)
    canvas.create_line(mast.x, mast.y, sail_tip.x, sail_tip.y, fill=palette.SHIP_TRIM, width=3)
    if boost < 0.98:
        flame = pos - Vec2.from_angle(angle) * (20 * scale)
        canvas.create_line(pos.x, pos.y, flame.x, flame.y, fill="#ff7a4a", width=3)


def draw_velocity_trail(canvas: tk.Canvas, ship_pos: Vec2, ship_vel: Vec2, screen_pos: Vec2) -> None:
    if ship_vel.length_sq() <= 25.0:
        return
    tail_world = ship_pos - ship_vel.normalized() * min(48.0, ship_vel.length() * 0.18)
    dx = screen_pos.x - (ship_pos.x - tail_world.x)
    dy = screen_pos.y - (ship_pos.y - tail_world.y)
    canvas.create_line(screen_pos.x - dx, screen_pos.y - dy, screen_pos.x, screen_pos.y, fill="#66e8ff", width=2)


def world_playfield_height(world: GameWorld, hud_top: int) -> int:
    return max(world.config.viewport_height, hud_top + (world.config.height - world.config.viewport_height))
