from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.nifflerp import Nifflerp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.lighting import LightRig


def draw_nifflerp_tactical(
    canvas: tk.Canvas,
    pos: Vec2,
    angle: float,
    *,
    scale: float,
    buddy: Nifflerp,
    rig: LightRig,
) -> None:
    _draw_nifflerp_body(
        canvas,
        pos,
        angle,
        scale=scale * 0.62,
        boosting=buddy.boost_flash > 0.0,
    )
    cx, cy = pos.x, pos.y
    r = 4.2 * scale
    if buddy.boost_flash > 0.0:
        canvas.create_oval(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2, outline=palette.NIFFLERP_BOOST, width=1)
    _ = rig


def draw_nifflerp_chase(
    canvas: tk.Canvas,
    pos: Vec2,
    angle: float,
    *,
    scale: float,
    buddy: Nifflerp,
) -> None:
    _draw_nifflerp_body(
        canvas,
        pos,
        angle,
        scale=scale * 0.58,
        boosting=buddy.boost_flash > 0.0,
    )


def _draw_nifflerp_body(
    canvas: tk.Canvas,
    pos: Vec2,
    angle: float,
    *,
    scale: float,
    boosting: bool,
) -> None:
    cx, cy = pos.x, pos.y
    forward = Vec2.from_angle(angle)
    right = forward.rotated(math.pi / 2.0)
    body = palette.NIFFLERP_BODY
    trim = palette.NIFFLERP_TRIM
    core = palette.NIFFLERP_CORE if not boosting else palette.NIFFLERP_BOOST
    nose = pos + forward * (7.5 * scale)
    tail = pos - forward * (5.5 * scale)
    pod_l = pos + right * (-4.5 * scale) - forward * (1.5 * scale)
    pod_r = pos + right * (4.5 * scale) - forward * (1.5 * scale)
    canvas.create_polygon(
        nose.x,
        nose.y,
        pod_r.x,
        pod_r.y,
        tail.x,
        tail.y,
        pod_l.x,
        pod_l.y,
        fill=body,
        outline=trim,
        width=max(1, int(scale)),
    )
    canvas.create_oval(
        cx - 2.8 * scale,
        cy - 2.8 * scale,
        cx + 2.8 * scale,
        cy + 2.8 * scale,
        fill=core,
        outline=trim,
        width=1,
    )
    if boosting:
        exhaust = pos - forward * (8.0 * scale)
        canvas.create_line(
            exhaust.x,
            exhaust.y,
            exhaust.x - forward.x * 5.0 * scale,
            exhaust.y - forward.y * 5.0 * scale,
            fill=palette.NIFFLERP_BOOST,
            width=max(1, int(2 * scale)),
        )
