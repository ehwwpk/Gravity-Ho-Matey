from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode, ViewCamera


def draw_edge_hints(
    canvas: tk.Canvas,
    world: GameWorld,
    camera: ViewCamera,
    *,
    hud_top: float,
) -> None:
    vw = camera.viewport_width
    vh = camera.viewport_height
    cx = vw * 0.5
    cy = hud_top + (vh - hud_top) * 0.5
    margin = 14.0
    ship = world.ship.pos
    ship_angle = world.ship.angle

    hints: list[tuple[float, str, str]] = []
    for beacon in world.beacons:
        if beacon.collected:
            continue
        _maybe_hint(hints, camera, beacon.pos, ship, ship_angle, "◈", palette.BEACON, vw, vh, hud_top)

    if world.beacons_remaining == 0:
        gate = world.finish_gate.rect
        gc = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        color = palette.GATE_OPEN if world.finish_unlocked else palette.GATE_LOCKED
        tag = "GO" if world.finish_unlocked else "GT"
        _maybe_hint(hints, camera, gc, ship, ship_angle, tag, color, vw, vh, hud_top)

    hints.sort(key=lambda item: item[0])
    for angle, tag, color in hints[:4]:
        _draw_rim_chevron(canvas, cx, cy, angle, tag, color, vw, vh, hud_top, margin)


def _maybe_hint(
    hints: list[tuple[float, str, str]],
    camera: ViewCamera,
    world_pos: Vec2,
    ship_pos: Vec2,
    ship_angle: float,
    tag: str,
    color: str,
    vw: float,
    vh: float,
    hud_top: float,
    *,
    margin: float = 14.0,
) -> None:
    p = camera.world_to_screen(world_pos, ship_pos, ship_angle)
    sx = p.x
    sy = p.y + (0.0 if camera.mode is CameraMode.CHASE else hud_top)
    if margin <= sx <= vw - margin and hud_top + margin <= sy <= vh - margin:
        return
    if camera.mode is CameraMode.CHASE and not p.visible:
        pass
    cx = vw * 0.5
    cy = hud_top + (vh - hud_top) * 0.5
    angle = math.atan2(sy - cy, sx - cx)
    hints.append((angle, tag, color))


def _draw_rim_chevron(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    angle: float,
    tag: str,
    color: str,
    vw: float,
    vh: float,
    hud_top: float,
    margin: float,
) -> None:
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    play_h = vh - hud_top
    reach = min(
        (vw * 0.5 - margin) / max(abs(cos_a), 1e-6),
        (play_h * 0.5 - margin) / max(abs(sin_a), 1e-6),
    )
    x = cx + cos_a * reach
    y = cy + sin_a * reach
    canvas.create_text(x, y, text=tag, fill=color, font=("Courier New", 9, "bold"))
    tip = Vec2(x, y) + Vec2.from_angle(angle) * 10
    left = Vec2(x, y) + Vec2.from_angle(angle + 2.6) * 7
    right = Vec2(x, y) + Vec2.from_angle(angle - 2.6) * 7
    canvas.create_polygon(tip.x, tip.y, left.x, left.y, right.x, right.y, fill=color, outline="")
