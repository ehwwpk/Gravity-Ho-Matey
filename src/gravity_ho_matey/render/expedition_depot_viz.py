from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, lerp_hex, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon, draw_simplified_polygon


def draw_charter_depot(
    canvas: tk.Canvas,
    center: Vec2,
    *,
    camera,
    follow: Vec2,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
) -> None:
    """Comet fuel depot — layered hull, rim bloom, hazard valves."""
    p = camera.world_to_screen(center, follow, 0.0)
    cx, cy = p.x, p.y + hud_top
    scale = camera.tactical_scale
    pulse = 0.5 + 0.5 * math.sin(elapsed * 2.4)
    back_mat = material_for("station_neutral", theme=rig.theme, view=rig.view)
    front_mat = material_for("station_friendly", theme=rig.theme, view=rig.view)

    def _poly(local: tuple[tuple[float, float], ...]) -> list[tuple[float, float]]:
        return [(cx + lx * scale, cy + ly * scale) for lx, ly in local]

    bloom_r = 118.0 * scale
    canvas.create_oval(
        cx - bloom_r,
        cy - bloom_r * 0.85,
        cx + bloom_r,
        cy + bloom_r * 0.85,
        fill=lerp_hex(palette.COMET_DEPOT_RIM, palette.COMET_BG, 0.88),
        outline="",
    )
    draw_illustrated_polygon(
        canvas,
        _poly(((-110, -70), (110, -70), (130, 80), (-130, 80))),
        rig=rig,
        material=back_mat,
        seed=801,
        radius_hint=120.0 * scale,
        crater_count=2,
    )
    draw_illustrated_polygon(
        canvas,
        _poly(((-90, -50), (90, -50), (100, 55), (-100, 55))),
        rig=rig,
        material=front_mat,
        seed=802,
        radius_hint=95.0 * scale,
        crater_count=1,
    )
    stripe_y = cy - 18 * scale
    canvas.create_line(cx - 92 * scale, stripe_y, cx + 92 * scale, stripe_y, fill=palette.COMET_HUD_ACCENT, width=3)
    canvas.create_line(
        cx - 92 * scale,
        stripe_y + 8 * scale,
        cx + 92 * scale,
        stripe_y + 8 * scale,
        fill=palette.COMET_VOLATILE_GLOW,
        width=2,
        dash=(10, 8),
    )
    for vx in (-72.0, 0.0, 72.0):
        draw_simplified_polygon(
            canvas,
            _poly(((vx - 14, -58), (vx + 14, -58), (vx + 16, -38), (vx - 16, -38))),
            rig=rig,
            material=front_mat,
        )
        ring_r = 10.0 + pulse * 3.0
        vxs = cx + vx * scale
        vys = cy - 48 * scale
        canvas.create_oval(vxs - ring_r, vys - ring_r, vxs + ring_r, vys + ring_r, outline=palette.COMET_HUD_ACCENT, width=2)
        draw_ground_fog_glow(
            canvas,
            vxs,
            vys,
            ring_r + 6.0,
            (palette.COMET_HUD_ACCENT, palette.COMET_VOLATILE_GLOW),
            pulse=elapsed * 3.0 + vx,
        )
    # Fuel load manifold — twin cryo tanks flanking the bay
    for side in (-1.0, 1.0):
        tx = cx + side * 58.0 * scale
        ty = cy + 18.0 * scale
        draw_illustrated_polygon(
            canvas,
            [(tx + lx * scale, ty + ly * scale) for lx, ly in ((-12, -18), (12, -18), (14, 16), (-14, 16))],
            rig=rig,
            material=front_mat,
            seed=int(side * 31) + 805,
            radius_hint=16.0 * scale,
            crater_count=0,
        )
        canvas.create_oval(tx - 10 * scale, ty - 22 * scale, tx + 10 * scale, ty - 10 * scale, fill=palette.COMET_ICE_HIGHLIGHT, outline=palette.COMET_HUD_ACCENT, width=1)
    bay = _poly(((-38, 20), (38, 20), (42, 72), (-42, 72)))
    canvas.create_polygon(*[c for pt in bay for c in pt], fill=lerp_hex(front_mat.deep, palette.COMET_BG, 0.35), outline=palette.COMET_DEPOT_RIM, width=2)
    # Foundation legs only when the depot reads at distance — not a foreground bar when you are inside the apron.
    if (follow - center).length() > 220.0:
        for lx, ly in ((-95, 75), (95, 75), (-70, 78), (70, 78)):
            leg = _poly(((lx - 8, ly), (lx + 8, ly), (lx + 6, ly + 18), (lx - 6, ly + 18)))
            draw_simplified_polygon(canvas, leg, rig=rig, material=back_mat)
            foot = _poly(((lx - 10, ly + 16), (lx + 10, ly + 16), (lx + 11, ly + 22), (lx - 11, ly + 22)))
            draw_illustrated_polygon(canvas, foot, rig=rig, material=back_mat, seed=int(lx) + 810, radius_hint=10.0 * scale, crater_count=0)
    lamp_c = palette.GATE_OPEN if pulse > 0.5 else palette.COMET_VEIN
    canvas.create_oval(cx - 4 * scale, cy - 62 * scale, cx + 4 * scale, cy - 54 * scale, fill=lamp_c, outline="")
