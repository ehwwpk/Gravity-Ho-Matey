from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.chart_bounds import chart_edge_hints_for_ship
from gravity_ho_matey.gameplay.entities import WorldConfig
from gravity_ho_matey.render.camera import ViewCamera

# Floor-hugging rim — orange-tinted, with a few px of fake vertical depth.
_EDGE_FLOOR_PULL = 11.0
_EDGE_DEPTH_LAYERS = (
    (5.0, 2, "#2a2018"),
    (3.0, 1, "#523628"),
    (1.0, 1, None),  # top layer uses strength-based dash color
)


def draw_chase_chart_edge_hints(
    canvas: tk.Canvas,
    *,
    config: WorldConfig,
    ship_pos: Vec2,
    ship_angle: float,
    camera: ViewCamera,
) -> None:
    """Soft dotted chart rim in chase view — only when approaching an edge."""
    hints = chart_edge_hints_for_ship(ship_pos, config)
    if not hints:
        return

    ww = config.width
    wh = config.height
    edge_segments: dict[str, tuple[Vec2, Vec2]] = {
        "left": (Vec2(0.0, 0.0), Vec2(0.0, wh)),
        "right": (Vec2(ww, 0.0), Vec2(ww, wh)),
        "top": (Vec2(0.0, 0.0), Vec2(ww, 0.0)),
        "bottom": (Vec2(0.0, wh), Vec2(ww, wh)),
    }

    for tag, strength in hints:
        segment = edge_segments.get(tag)
        if segment is None:
            continue
        _draw_projected_dotted_edge(
            canvas,
            camera,
            ship_pos,
            ship_angle,
            segment[0],
            segment[1],
            strength=strength,
        )


def _hint_color(strength: float) -> str:
    """Soft orange rim — slightly warmer when hugging the boundary."""
    if strength >= 0.85:
        return "#c88858"
    if strength >= 0.45:
        return "#9a6848"
    return "#6e4a38"


def _floor_screen_point(
    camera: ViewCamera,
    projected_x: float,
    projected_y: float,
    depth: float,
) -> tuple[float, float]:
    """Pull projected points down onto the chase floor plane."""
    depth_scale = camera.perspective_scale(depth) / camera.focal_length
    y_floor = projected_y + _EDGE_FLOOR_PULL * depth_scale + 3.0
    return projected_x, y_floor


def _collect_edge_points(
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    start: Vec2,
    end: Vec2,
) -> list[tuple[float, float, float]]:
    span = (end - start).length()
    steps = max(10, int(span / 36.0))
    points: list[tuple[float, float, float]] = []
    for i in range(steps + 1):
        t = i / steps
        world = Vec2(start.x + (end.x - start.x) * t, start.y + (end.y - start.y) * t)
        projected = camera.world_to_screen(world, ship_pos, ship_angle)
        if not projected.visible or projected.depth < camera.min_depth:
            continue
        sx, sy = _floor_screen_point(camera, projected.x, projected.y, projected.depth)
        points.append((sx, sy, projected.depth))
    return points


def _draw_polyline(
    canvas: tk.Canvas,
    points: list[tuple[float, float, float]],
    *,
    y_offset: float,
    color: str,
    width: int,
    dash: tuple[int, ...] | None = None,
) -> None:
    prev: tuple[float, float] | None = None
    for sx, sy, _depth in points:
        point = (sx, sy + y_offset)
        if prev is not None:
            canvas.create_line(
                prev[0],
                prev[1],
                point[0],
                point[1],
                fill=color,
                dash=dash,
                width=width,
                smooth=False,
            )
        prev = point


def _draw_projected_dotted_edge(
    canvas: tk.Canvas,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    start: Vec2,
    end: Vec2,
    *,
    strength: float,
) -> None:
    points = _collect_edge_points(camera, ship_pos, ship_angle, start, end)
    if len(points) < 2:
        return

    top_color = _hint_color(strength)
    dash_on = max(2, int(3 + strength * 2))
    dash_off = max(7, int(14 - strength * 3))

    for y_offset, width, color in _EDGE_DEPTH_LAYERS:
        if color is None:
            _draw_polyline(
                canvas,
                points,
                y_offset=y_offset,
                color=top_color,
                width=width,
                dash=(dash_on, dash_off),
            )
        else:
            _draw_polyline(canvas, points, y_offset=y_offset, color=color, width=width)
