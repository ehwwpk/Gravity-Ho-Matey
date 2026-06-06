from __future__ import annotations

from dataclasses import dataclass

import tkinter as tk

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Wall
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera

MAX_RAIL_WIDTH = 5


@dataclass(frozen=True, slots=True)
class WallRibbon:
    near_a: Vec2
    near_b: Vec2
    is_boundary: bool


def wall_ribbons(wall: Wall, world_width: float, world_height: float) -> list[WallRibbon]:
    r = wall.rect
    ribbons: list[WallRibbon] = []
    inset = 2.0

    if r.h <= 40 and r.w >= 80:
        ribbons.extend(_horizontal_ribbons(r, world_width, world_height, inset))
    elif r.w <= 40 and r.h >= 80:
        ribbons.extend(_vertical_ribbons(r, world_width, world_height, inset))
    else:
        ribbons.extend(_block_ribbons(r))

    return ribbons


def _horizontal_ribbons(r: Rect, ww: float, wh: float, inset: float) -> list[WallRibbon]:
    x0 = max(r.x + inset, inset)
    x1 = min(r.x + r.w - inset, ww - inset)
    boundary = r.y <= 1.0 or r.y + r.h >= wh - 1.0
    near_y = r.y + r.h if r.y <= wh * 0.5 else r.y
    return [WallRibbon(near_a=Vec2(x0, near_y), near_b=Vec2(x1, near_y), is_boundary=boundary)]


def _vertical_ribbons(r: Rect, ww: float, wh: float, inset: float) -> list[WallRibbon]:
    y0 = max(r.y + inset, inset)
    y1 = min(r.y + r.h - inset, wh - inset)
    boundary = r.x <= 1.0 or r.x + r.w >= ww - 1.0
    near_x = r.x + r.w if r.x <= ww * 0.5 else r.x
    return [WallRibbon(near_a=Vec2(near_x, y0), near_b=Vec2(near_x, y1), is_boundary=boundary)]


def _block_ribbons(r: Rect) -> list[WallRibbon]:
    if r.w >= r.h:
        y = r.y + r.h
        return [WallRibbon(near_a=Vec2(r.x, y), near_b=Vec2(r.x + r.w, y), is_boundary=False)]
    x = r.x + r.w
    return [WallRibbon(near_a=Vec2(x, r.y), near_b=Vec2(x, r.y + r.h), is_boundary=False)]


def collect_wall_rails(
    walls: list[Wall],
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    world_width: float,
    world_height: float,
) -> list[tuple[float, tuple]]:
    horizon = camera.chase_horizon_y()
    rails: list[tuple[float, tuple]] = []
    for wall in walls:
        for ribbon in wall_ribbons(wall, world_width, world_height):
            pn = camera.world_to_screen(ribbon.near_a, ship_pos, ship_angle)
            pnb = camera.world_to_screen(ribbon.near_b, ship_pos, ship_angle)
            if max(pn.y, pnb.y) < horizon - 8:
                continue
            depth = (pn.depth + pnb.depth) * 0.5
            if depth < camera.min_depth:
                continue
            scale = camera.perspective_scale(depth) / camera.focal_length
            width = max(1, min(MAX_RAIL_WIDTH, int(1 + scale * 3.5)))
            rails.append((depth, (pn.x, pn.y, pnb.x, pnb.y, width, ribbon.is_boundary)))
    return rails


def draw_wall_rails(
    canvas: tk.Canvas,
    rails: list[tuple[float, tuple]],
    *,
    solar: bool,
    urgency: float = 0.0,
) -> None:
    rails.sort(key=lambda item: item[0])
    for _, payload in rails:
        x0, y0, x1, y1, width, boundary = payload
        if urgency > 0.12:
            color = palette.HELM_THREAT_LETHAL if urgency > 0.45 else palette.HELM_THREAT_HEAVY
            width = min(MAX_RAIL_WIDTH + 2, width + int(urgency * 3))
        elif boundary:
            color = palette.HOLO_WALL_EDGE if not solar else palette.ASTEROID_EDGE
        else:
            color = palette.CHASE_WALL_CAP if not solar else palette.ASTEROID_EDGE
        canvas.create_line(x0, y0, x1, y1, fill=color, width=width)
