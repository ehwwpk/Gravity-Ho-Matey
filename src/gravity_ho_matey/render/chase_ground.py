from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.world_draw import gravity_field_color


def draw_chase_gravity_heatmap(
    canvas: tk.Canvas,
    field: GravityField,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    *,
    step: int = 2,
    _world: GameWorld | None = None,
) -> None:
    """Purple floor wash — flat projection, no grid lines."""
    horizon = camera.chase_horizon_y()
    for row in range(0, field.rows, step):
        for col in range(0, field.cols, step):
            cell = field.cell_at(col, row)
            if cell.magnitude <= 1e-6:
                continue
            norm = cell.magnitude / field.max_magnitude
            if norm < 0.18:
                continue
            wx = field.origin.x + col * field.cell_size + field.cell_size * 0.5
            wy = field.origin.y + row * field.cell_size + field.cell_size * 0.5
            wp = Vec2(wx, wy)
            p = camera.world_to_chase_screen(
                wp,
                ship_pos,
                ship_angle,
                min_ahead=camera.min_depth * 0.5,
                screen_margin=160.0,
            )
            if p.y < horizon or not p.visible:
                continue
            depth_scale = camera.perspective_scale(p.depth) / camera.focal_length
            half_w = field.cell_size * step * 0.58 * depth_scale
            half_h = half_w * 0.32
            tone = gravity_field_color(norm)
            canvas.create_rectangle(
                p.x - half_w,
                p.y - half_h,
                p.x + half_w,
                p.y + half_h * 0.22,
                fill=tone,
                outline="",
            )
