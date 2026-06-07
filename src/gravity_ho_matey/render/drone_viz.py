from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.drone_wingman import DroneWingman
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.lighting import LightRig
from gravity_ho_matey.render.ship_viz import draw_fighter_ship


def draw_drone_wingman_tactical(
    canvas: tk.Canvas,
    pos: Vec2,
    angle: float,
    *,
    scale: float,
    drone: DroneWingman,
    rig: LightRig,
) -> None:
    draw_fighter_ship(
        canvas,
        pos,
        angle,
        scale=scale * 0.82,
        rig=rig,
        boost_burst=0.12 if drone.overheat_timer <= 0.0 and drone.heat > 0.35 else 0.0,
    )
    cx, cy = pos.x, pos.y
    r = 5.0 * scale
    if drone.is_overheated:
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=palette.HUD_WARN, width=2)
    elif drone.heat > 0.2:
        heat_frac = min(1.0, drone.heat)
        canvas.create_arc(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            start=90,
            extent=-360 * heat_frac,
            outline=palette.DRONE_HEAT,
            width=2,
            style=tk.ARC,
        )


def draw_drone_wingman_chase(
    canvas: tk.Canvas,
    pos: Vec2,
    angle: float,
    *,
    scale: float,
    drone: DroneWingman,
) -> None:
    cx, cy = pos.x, pos.y
    forward = Vec2.from_angle(angle)
    right = forward.rotated(math.pi / 2.0)
    body = palette.DRONE_BODY
    trim = palette.DRONE_TRIM
    core = palette.DRONE_CORE if not drone.is_overheated else palette.HUD_WARN
    nose = pos + forward * (10.0 * scale)
    tail = pos - forward * (8.0 * scale)
    wing_l = pos + right * (-7.0 * scale) - forward * (2.0 * scale)
    wing_r = pos + right * (7.0 * scale) - forward * (2.0 * scale)
    canvas.create_polygon(
        nose.x,
        nose.y,
        wing_r.x,
        wing_r.y,
        tail.x,
        tail.y,
        wing_l.x,
        wing_l.y,
        fill=body,
        outline=trim,
        width=max(1, int(scale)),
    )
    canvas.create_oval(
        cx - 3.5 * scale,
        cy - 3.5 * scale,
        cx + 3.5 * scale,
        cy + 3.5 * scale,
        fill=core,
        outline=trim,
        width=1,
    )
    if drone.heat > 0.15 and not drone.is_overheated:
        bar_w = 14.0 * scale
        bar_h = 3.0 * scale
        bx = cx - bar_w * 0.5
        by = cy - 14.0 * scale
        canvas.create_rectangle(bx, by, bx + bar_w, by + bar_h, fill=palette.DRONE_HEAT_BG, outline="")
        canvas.create_rectangle(
            bx,
            by,
            bx + bar_w * min(1.0, drone.heat),
            by + bar_h,
            fill=palette.DRONE_HEAT,
            outline="",
        )
