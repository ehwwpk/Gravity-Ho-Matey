from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.lighting import LightRig, MaterialTones, arc_tone_for_point, lerp_hex


def draw_squid_tentacles(
    canvas: tk.Canvas,
    body: tuple[float, float],
    tips: tuple[tuple[float, float], ...],
    *,
    coiled: bool,
    tentacle_color: str | None = None,
    touch_color: str | None = None,
    touch_tips: frozenset[int] | None = None,
) -> None:
    bx, by = body
    base = tentacle_color or palette.SQUID_TENTACLE
    touch = touch_color or palette.SQUID_TOUCH_TIP
    width = 3 if coiled else 2
    for i, tip in enumerate(tips):
        tx, ty = tip
        mx = bx + (tx - bx) * 0.48
        my = by + (ty - by) * 0.48
        color = touch if touch_tips and i in touch_tips else base
        w = 4 if touch_tips and i in touch_tips else width
        canvas.create_line(bx, by, mx, my, tx, ty, fill=color, width=w, smooth=True)


def draw_squid_body(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    radius: float,
    scale: float = 1.0,
    rig: LightRig | None = None,
    material: MaterialTones | None = None,
) -> None:
    r = radius * scale
    if rig is not None and material is not None:
        body_fill = arc_tone_for_point(x - r * 0.2, y, x, y, rig, material)
        rim = material.rim
        core = lerp_hex(material.highlight, material.mid, 0.35)
    else:
        body_fill = palette.SQUID_BODY
        rim = palette.SQUID_CORE
        core = palette.SQUID_CORE
    canvas.create_oval(
        x - r,
        y - r * 0.65,
        x + r,
        y + r * 0.55,
        fill=body_fill,
        outline=rim,
        width=2,
    )
    canvas.create_oval(
        x - r * 0.35,
        y - r * 0.25,
        x + r * 0.38,
        y + r * 0.2,
        fill=core,
        outline="",
    )
    if rig is not None and material is not None:
        glint = lerp_hex(material.highlight, "#ffffff", 0.25)
        canvas.create_oval(
            x - r * 0.12,
            y - r * 0.18,
            x + r * 0.08,
            y - r * 0.02,
            fill=glint,
            outline="",
        )


def draw_squid_body_lit(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    radius: float,
    scale: float,
    rig: LightRig,
    kind: str = "squid",
) -> None:
    from gravity_ho_matey.render.lighting import material_for

    material = material_for(kind, theme=rig.theme, view=rig.view)
    draw_squid_body(canvas, x, y, radius=radius, scale=scale, rig=rig, material=material)


def project_tips_to_screen(
    tips: tuple[Vec2, ...],
    project,
) -> tuple[tuple[float, float], ...]:
    out: list[tuple[float, float]] = []
    for tip in tips:
        p = project(tip)
        if p is None:
            continue
        out.append(p)
    return tuple(out)
