from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_threat import ThreatLevel, ahead_emphasis, threat_at_point, threat_color


def draw_chase_gravity_grid(
    canvas: tk.Canvas,
    field: GravityField,
    camera: ViewCamera,
    world: GameWorld,
    ship_pos: Vec2,
    ship_angle: float,
    *,
    elapsed: float,
    step: int = 2,
) -> None:
    horizon = camera.chase_horizon_y()
    fade_line = horizon + 18.0
    for row in range(0, field.rows, step):
        for col in range(0, field.cols - 1, step):
            a = Vec2(field.origin.x + col * field.cell_size, field.origin.y + row * field.cell_size)
            b = Vec2(field.origin.x + (col + step) * field.cell_size, field.origin.y + row * field.cell_size)
            _draw_segment(canvas, field, world, camera, ship_pos, ship_angle, a, b, horizon, fade_line, elapsed)
    for col in range(0, field.cols, step):
        for row in range(0, field.rows - 1, step):
            a = Vec2(field.origin.x + col * field.cell_size, field.origin.y + row * field.cell_size)
            b = Vec2(field.origin.x + col * field.cell_size, field.origin.y + (row + step) * field.cell_size)
            _draw_segment(canvas, field, world, camera, ship_pos, ship_angle, a, b, horizon, fade_line, elapsed)


def _draw_segment(
    canvas: tk.Canvas,
    field: GravityField,
    world: GameWorld,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    a: Vec2,
    b: Vec2,
    horizon: float,
    fade_line: float,
    _elapsed: float,
) -> None:
    pa = camera.world_to_screen(a, ship_pos, ship_angle)
    pb = camera.world_to_screen(b, ship_pos, ship_angle)
    if pa.y < horizon and pb.y < horizon:
        return
    if not pa.visible and not pb.visible:
        return
    mid = Vec2((a.x + b.x) * 0.5, (a.y + b.y) * 0.5)
    norm = field.normalized_magnitude_at(mid)
    threat = threat_at_point(world, mid)
    depth = (pa.depth + pb.depth) * 0.5
    depth_scale = camera.perspective_scale(depth) / camera.focal_length
    emphasis = ahead_emphasis(ship_pos, ship_angle, mid)
    width = max(1, int((1 + norm * 3 * depth_scale) * emphasis))
    if threat is ThreatLevel.LETHAL:
        width = max(width, 2)
    elif threat is ThreatLevel.HEAVY:
        width = max(width, 2)
    color = threat_color(threat, norm=norm)
    avg_y = (pa.y + pb.y) * 0.5
    if avg_y < fade_line:
        return
    canvas.create_line(pa.x, pa.y, pb.x, pb.y, fill=color, width=width)
