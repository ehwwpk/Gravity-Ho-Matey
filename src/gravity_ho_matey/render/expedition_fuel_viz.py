from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.squid_behavior import FuelFeedLine
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, lerp_hex, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon, draw_simplified_polygon


def draw_fuel_line_trench(
    canvas: tk.Canvas,
    line: FuelFeedLine,
    *,
    camera,
    follow: Vec2,
    hud_top: float,
    rig: LightRig,
) -> None:
    """Surface groove where volatile feed lines are buried in the regolith."""
    sp = camera.world_to_screen(line.start, follow, 0.0)
    ep = camera.world_to_screen(line.end, follow, 0.0)
    sx, sy = sp.x, sp.y + hud_top
    ex, ey = ep.x, ep.y + hud_top
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy)
    if length < 1.0:
        return
    nx, ny = -dy / length, dx / length
    half_w = 14.0 * camera.tactical_scale
    regolith = material_for("comet_regolith", theme=rig.theme, view=rig.view)
    pts = [
        (sx + nx * half_w, sy + ny * half_w),
        (ex + nx * half_w, ey + ny * half_w),
        (ex - nx * half_w, ey - ny * half_w),
        (sx - nx * half_w, sy - ny * half_w),
    ]
    draw_simplified_polygon(canvas, pts, rig=rig, material=regolith)
    canvas.create_line(sx, sy, ex, ey, fill=regolith.deep, width=3, smooth=True)


def draw_fuel_feed_line(
    canvas: tk.Canvas,
    line: FuelFeedLine,
    *,
    camera,
    follow: Vec2,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
) -> None:
    """Volatile charter feed hose — lit segments, vein glow, nozzle bloom."""
    sp = camera.world_to_screen(line.start, follow, 0.0)
    ep = camera.world_to_screen(line.end, follow, 0.0)
    sx, sy = sp.x, sp.y + hud_top
    ex, ey = ep.x, ep.y + hud_top
    pulse = 0.5 + 0.5 * math.sin(elapsed * 3.2 + hash(line.id) % 7)
    hose_mat = material_for("station_neutral", theme=rig.theme, view=rig.view)
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy)
    if length < 1.0:
        return
    nx, ny = -dy / length, dx / length
    half_w = 5.0 * camera.tactical_scale
    segments = max(3, int(length / (42.0 * camera.tactical_scale)))
    for i in range(segments):
        t0 = i / segments
        t1 = (i + 1) / segments
        x0, y0 = sx + dx * t0, sy + dy * t0
        x1, y1 = sx + dx * t1, sy + dy * t1
        pts = [
            (x0 + nx * half_w, y0 + ny * half_w),
            (x1 + nx * half_w, y1 + ny * half_w),
            (x1 - nx * half_w, y1 - ny * half_w),
            (x0 - nx * half_w, y0 - ny * half_w),
        ]
        draw_illustrated_polygon(
            canvas,
            pts,
            rig=rig,
            material=hose_mat,
            seed=hash(line.id) + i,
            radius_hint=half_w,
            crater_count=0,
        )
    canvas.create_line(sx, sy, ex, ey, fill=palette.COMET_HUD_ACCENT, width=2, smooth=True)
    canvas.create_line(sx, sy, ex, ey, fill=palette.COMET_VOLATILE_GLOW, width=1, smooth=True)
    draw_ground_fog_glow(canvas, sx, sy, 10.0 + pulse * 4.0, palette.CHASE_FOG_COMET, pulse=elapsed * 2.2)
    nozzle_r = 12.0 + pulse * 8.0
    draw_ground_fog_glow(canvas, ex, ey, nozzle_r, (palette.COMET_HUD_ACCENT, palette.COMET_VOLATILE_GLOW), pulse=elapsed * 3.0)
    canvas.create_oval(ex - 4.0, ey - 4.0, ex + 4.0, ey + 4.0, fill=palette.COMET_ICE_HIGHLIGHT, outline="")


def draw_fuel_valve_station(
    canvas: tk.Canvas,
    pos: Vec2,
    *,
    camera,
    follow: Vec2,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
    loaded: bool = False,
    active: bool = False,
) -> None:
    """Charter fuel load point — cryo tanks, hazard ring, volatile bloom."""
    p = camera.world_to_screen(pos, follow, 0.0)
    cx, cy = p.x, p.y + hud_top
    scale = camera.tactical_scale
    pulse = 0.5 + 0.5 * math.sin(elapsed * 3.6)
    tank = material_for("station_friendly", theme=rig.theme, view=rig.view)
    hazard = material_for("station_neutral", theme=rig.theme, view=rig.view)

    pad_r = 42.0 * scale
    canvas.create_oval(cx - pad_r, cy - pad_r * 0.85, cx + pad_r, cy + pad_r * 0.85, fill=lerp_hex(hazard.deep, palette.COMET_BG, 0.4), outline=palette.COMET_DEPOT_RIM, width=2)
    canvas.create_oval(
        cx - pad_r * 0.88,
        cy - pad_r * 0.75,
        cx + pad_r * 0.88,
        cy + pad_r * 0.75,
        outline=palette.COMET_HUD_ACCENT if active else palette.COMET_VEIN,
        width=2,
        dash=(6, 5) if not loaded else (),
    )

    for side in (-1.0, 1.0):
        tx = cx + side * 18.0 * scale
        tank_pts = [
            (tx - 10.0 * scale, cy - 16.0 * scale),
            (tx + 10.0 * scale, cy - 16.0 * scale),
            (tx + 12.0 * scale, cy + 14.0 * scale),
            (tx - 12.0 * scale, cy + 14.0 * scale),
        ]
        draw_illustrated_polygon(canvas, tank_pts, rig=rig, material=tank, seed=int(side * 17) + 901, radius_hint=14.0 * scale, crater_count=0)
        cap_y = cy - 18.0 * scale
        canvas.create_oval(tx - 8.0 * scale, cap_y - 6.0 * scale, tx + 8.0 * scale, cap_y + 6.0 * scale, fill=lerp_hex(tank.highlight, palette.COMET_ICE_HIGHLIGHT, 0.35), outline=tank.rim, width=1)

    draw_ground_fog_glow(
        canvas,
        cx,
        cy,
        22.0 + pulse * 14.0,
        (palette.COMET_VOLATILE_GLOW, palette.COMET_HUD_ACCENT) if not loaded else (palette.GATE_OPEN, palette.COMET_VEIN),
        pulse=elapsed * 2.8,
    )
    if loaded:
        canvas.create_text(cx, cy - pad_r - 6 * scale, text="LOADED", fill=palette.GATE_OPEN, font=("Consolas", max(8, int(8 * scale))))
    else:
        canvas.create_text(
            cx,
            cy - pad_r - 6 * scale,
            text="VALVE",
            fill=lerp_hex(palette.COMET_VEIN, palette.COMET_BG, 0.35),
            font=("Consolas", max(7, int(7 * scale))),
        )


def draw_rtb_extraction_beacon(
    canvas: tk.Canvas,
    pos: Vec2,
    *,
    camera,
    follow: Vec2,
    hud_top: float,
    elapsed: float,
    scale_hint: float = 1.0,
    ready: bool = False,
    blocked: bool = False,
) -> None:
    """RTB pad beacon — green when ready, amber when hostiles block extract."""
    p = camera.world_to_screen(pos, follow, 0.0)
    cx, cy = p.x, p.y + hud_top
    pulse = 0.5 + 0.5 * math.sin(elapsed * 3.0)
    r = (52.0 + pulse * 12.0) * scale_hint
    color = palette.GATE_OPEN if ready else (palette.COMET_HUD_ACCENT if blocked else palette.COMET_VEIN)
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=3, dash=(8, 6) if not ready else ())
    canvas.create_oval(cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55, outline=color, width=1)
    draw_ground_fog_glow(canvas, cx, cy, r * 0.65, (color, palette.COMET_VOLATILE_GLOW), pulse=elapsed * 2.0)


def draw_feeding_site_glow(
    canvas: tk.Canvas,
    pos: Vec2,
    *,
    camera,
    follow: Vec2,
    hud_top: float,
    elapsed: float,
    scale_hint: float = 1.0,
) -> None:
    """Leak bloom where squids feed on busted fuel lines."""
    p = camera.world_to_screen(pos, follow, 0.0)
    pulse = 0.5 + 0.5 * math.sin(elapsed * 4.2 + pos.x * 0.01)
    draw_ground_fog_glow(
        canvas,
        p.x,
        p.y + hud_top,
        (18.0 + pulse * 10.0) * scale_hint,
        (palette.COMET_VOLATILE_GLOW, palette.COMET_HUD_ACCENT),
        pulse=elapsed * 3.5,
    )
