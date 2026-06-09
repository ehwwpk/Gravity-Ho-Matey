from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.render.chase_fx import draw_fog_glow, draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, MaterialTones, lerp_hex
from gravity_ho_matey.render import palette


def draw_brood_rim_bloom(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    radius: float,
    material: MaterialTones,
    *,
    flatten: float = 0.38,
) -> None:
    """Station-style underglow for brood sacs and large props."""
    rx = radius * 1.75
    ry = radius * flatten
    fill = lerp_hex(material.rim, material.deep, 0.78)
    canvas.create_oval(cx - rx, cy - ry * 0.35, cx + rx, cy + ry, fill=fill, outline="")


def draw_brood_vein_glow_line(
    canvas: tk.Canvas,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    pulse: float = 0.0,
    width: int = 2,
) -> None:
    """Biolum vein segment with endpoint bloom."""
    vein = palette.BROOD_MOON_VEIN
    canvas.create_line(x0, y0, x1, y1, fill=vein, width=width, smooth=True)
    glow_r = 8.0 + 3.0 * math.sin(pulse)
    draw_ground_fog_glow(canvas, x0, y0, glow_r, palette.CHASE_FOG_BROOD, pulse=pulse)
    draw_ground_fog_glow(canvas, x1, y1, glow_r * 0.85, palette.CHASE_FOG_BROOD, pulse=pulse + 1.2)


def draw_brood_ground_shadow(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    radius: float,
    *,
    rig: LightRig,
) -> None:
    """Elliptical ground shadow offset along key light (asteroid-style)."""
    dx = rig.key_dir.x * radius * 0.35
    dy = rig.key_dir.y * radius * 0.12 + radius * 0.08
    rx = radius * 1.15
    ry = radius * 0.28
    fill = palette.BROOD_REGOLITH_DEEP if rig.theme == "brood_moon" else palette.COMET_REGOLITH_DEEP
    canvas.create_oval(cx - rx + dx, cy - ry + dy, cx + rx + dx, cy + ry + dy, fill=fill, outline="")


def draw_brood_membrane_ring(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    radius: float,
    material: MaterialTones,
    *,
    pulse: float,
    rig: LightRig,
) -> None:
    """Pulsing sac membrane outline."""
    wobble = 1.0 + 0.06 * math.sin(pulse * 2.4)
    r = radius * wobble
    canvas.create_oval(
        cx - r * 1.05,
        cy - r * 0.92,
        cx + r * 1.05,
        cy + r * 0.92,
        outline=lerp_hex(material.highlight, material.rim, 0.35),
        width=2,
    )
    hi_x = cx + rig.key_dir.x * r * 0.35
    hi_y = cy + rig.key_dir.y * r * 0.35
    canvas.create_oval(
        hi_x - r * 0.22,
        hi_y - r * 0.18,
        hi_x + r * 0.22,
        hi_y + r * 0.18,
        fill=material.highlight,
        outline="",
    )
    draw_fog_glow(canvas, cx, cy, r * 0.55, palette.CHASE_FOG_BROOD, pulse=pulse)
