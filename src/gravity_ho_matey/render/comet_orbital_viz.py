from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.comet_body import CometBody
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.chase_fx import draw_fog_glow, draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, lerp_hex, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon


def draw_comet_tactical(
    canvas: tk.Canvas,
    comet: CometBody,
    *,
    camera,
    ship_pos: Vec2,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
) -> None:
    pos = comet.position()
    p = camera.world_to_screen(pos, ship_pos, 0.0)
    cx, cy = p.x, p.y + hud_top
    scale = camera.tactical_scale
    pulse = 0.5 + 0.5 * math.sin(elapsed * 2.6)
    r = comet.surface_radius * scale
    ice = material_for("comet_ice", theme=rig.theme, view=rig.view)
    regolith = material_for("comet_regolith", theme=rig.theme, view=rig.view)

    # Coma halo — volatile outgassing (sci-fi illustration read)
    for layer, (rx, ry, alpha) in enumerate(((1.65, 1.35, 0.12), (1.38, 1.12, 0.22), (1.15, 0.98, 0.35))):
        fill = lerp_hex(palette.COMET_BG, palette.COMET_VEIN, alpha)
        canvas.create_oval(cx - r * rx, cy - r * ry, cx + r * rx, cy + r * ry, fill=fill, outline="")
    draw_fog_glow(canvas, cx, cy, r * 1.05, (palette.COMET_VOLATILE_GLOW, palette.COMET_VEIN), pulse=elapsed * 1.8)

    # Ion tail — dual tone dust + plasma
    tail = Vec2(-math.sin(comet.phase), math.cos(comet.phase))
    tail_len = r * 1.55
    for i, (width, color) in enumerate(
        (
            (16.0, "#503878"),
            (11.0, "#8060b0"),
            (7.0, "#48a8d8"),
            (3.0, palette.COMET_ICE_HIGHLIGHT),
        )
    ):
        fade = 1.0 - i * 0.18
        canvas.create_line(
            cx,
            cy,
            cx + tail.x * tail_len * fade,
            cy + tail.y * tail_len * 0.72 * fade,
            fill=color,
            width=width,
            smooth=True,
        )
    tx, ty = cx + tail.x * tail_len * 0.92, cy + tail.y * tail_len * 0.65
    draw_fog_glow(canvas, tx, ty, 34.0 + pulse * 18.0, ("#6840a0", "#48c8f0"), pulse=elapsed * 2.2)

    # Limb nucleus — dark carbon core + ice caps + rim light
    sun_angle = comet.phase * 0.35
    for i, (r_frac, mat, craters) in enumerate(
        (
            (0.62, regolith, 6),
            (0.46, regolith, 4),
            (0.32, ice, 3),
            (0.18, ice, 2),
        )
    ):
        wobble = math.sin(elapsed * 0.9 + i) * 0.04
        layer_r = comet.surface_radius * (r_frac + wobble)
        pts = [
            (
                cx + math.cos(a + comet.phase * 0.15 + sun_angle * 0.08) * layer_r * scale,
                cy + math.sin(a + comet.phase * 0.12) * layer_r * scale * 0.88,
            )
            for a in [i * 0.62 + 0.05 for i in range(12)]
        ]
        draw_illustrated_polygon(
            canvas,
            pts,
            rig=rig,
            material=mat,
            seed=880 + i,
            radius_hint=layer_r * scale,
            crater_count=craters,
        )

    # Sun-facing rim highlight
    rim_x = cx + math.cos(sun_angle) * r * 0.82
    rim_y = cy + math.sin(sun_angle) * r * 0.72
    canvas.create_arc(
        cx - r * 1.02,
        cy - r * 0.92,
        cx + r * 1.02,
        cy + r * 0.92,
        start=math.degrees(sun_angle) - 38,
        extent=76,
        style=tk.ARC,
        outline=palette.COMET_ICE_RIM,
        width=3,
    )
    draw_ground_fog_glow(canvas, rim_x, rim_y, 16.0 + pulse * 10.0, palette.CHASE_FOG_COMET, pulse=elapsed * 3.0)

    # Volatile jets at anti-sun point
    jet_angle = sun_angle + math.pi
    for j, spread in enumerate((0.0, 0.28, -0.28)):
        ja = jet_angle + spread
        jx = cx + math.cos(ja) * r * 0.42
        jy = cy + math.sin(ja) * r * 0.36
        draw_ground_fog_glow(
            canvas,
            jx,
            jy,
            14.0 + pulse * 10.0,
            (palette.COMET_VOLATILE_GLOW, palette.COMET_HUD_ACCENT),
            pulse=elapsed * 4.0 + j,
        )
        canvas.create_line(cx, cy, jx, jy, fill=palette.COMET_VOLATILE_GLOW, width=2)

    # Sparkle ice glints
    for i in range(8):
        ga = comet.phase * 1.4 + i * 0.9
        gx = cx + math.cos(ga) * r * (0.35 + 0.15 * math.sin(elapsed * 2.0 + i))
        gy = cy + math.sin(ga) * r * 0.32
        tw = 0.4 + 0.6 * math.sin(elapsed * 3.5 + i * 1.1)
        if tw > 0.55:
            canvas.create_oval(gx - 2, gy - 2, gx + 2, gy + 2, fill=palette.COMET_ICE_HIGHLIGHT, outline="")

    draw_ground_fog_glow(canvas, cx, cy, r * 0.62, palette.CHASE_FOG_COMET, pulse=elapsed * 1.6)
