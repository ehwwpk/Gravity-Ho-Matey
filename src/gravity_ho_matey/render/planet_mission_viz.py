from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.planet_mission import PlanetBody, in_planet_landing_band
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.lighting import lerp_hex
from gravity_ho_matey.render import palette


def _dash_ring_segments(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    radius: float,
    *,
    y_scale: float = 1.0,
    color: str,
    width: int,
    segments: int,
    elapsed: float,
    speed: float = 2.4,
) -> None:
    """Animated tick ring — dash offset via rotating segment gaps."""
    phase = (elapsed * speed) % 1.0
    seg_arc = math.tau / segments
    gap = seg_arc * 0.38
    for i in range(segments):
        a0 = i * seg_arc + phase * seg_arc
        a1 = a0 + seg_arc - gap
        steps = 4
        pts: list[float] = []
        for s in range(steps + 1):
            a = a0 + (a1 - a0) * s / steps
            pts.extend((cx + math.cos(a) * radius, cy + math.sin(a) * radius * y_scale))
        if len(pts) >= 4:
            canvas.create_line(*pts, fill=color, width=width, smooth=True)


def draw_planet_landing_band_tactical(
    canvas: tk.Canvas,
    body: PlanetBody,
    *,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
    accent: str,
    dim: str,
    elapsed: float = 0.0,
) -> None:
    """Highlight the full limb approach shell around a planet/moon."""
    center = camera.world_to_screen(body.center, ship_pos, ship_angle)
    scale = camera.tactical_scale / 1.1
    surface_r = body.surface_radius * scale
    inner_r = body.landing_band_inner * scale
    outer_r = body.landing_band_outer * scale
    cx, cy = center.x, center.y + hud_top
    in_band = in_planet_landing_band(ship_pos, body)
    pulse = 0.65 + 0.35 * math.sin(elapsed * 3.6)

    draw_ground_fog_glow(
        canvas, cx, cy, surface_r * 0.55,
        palette.CHASE_FOG_BROOD if accent == palette.BROOD_MOON_HUD_ACCENT else lerp_hex(accent, "#081018", 0.5),
        pulse=elapsed * 2.2,
    )
    if in_band:
        canvas.create_oval(
            cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
            fill=lerp_hex(accent, "#120818", 0.78), outline="", stipple="gray25",
        )
        canvas.create_oval(
            cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r,
            fill=palette.BROOD_MOON_BG if accent == palette.BROOD_MOON_HUD_ACCENT else "#081018",
            outline="",
        )

    canvas.create_oval(
        cx - surface_r,
        cy - surface_r,
        cx + surface_r,
        cy + surface_r,
        outline=accent if in_band else dim,
        width=2 if in_band else 1,
    )
    _dash_ring_segments(
        canvas, cx, cy, inner_r, color=accent if in_band else dim,
        width=1, segments=24, elapsed=elapsed,
    )
    _dash_ring_segments(
        canvas, cx, cy, outer_r, color=accent if in_band else dim,
        width=1, segments=32, elapsed=elapsed, speed=1.8,
    )
    if in_band:
        canvas.create_oval(
            cx - outer_r - 4,
            cy - outer_r - 4,
            cx + outer_r + 4,
            cy + outer_r + 4,
            outline=accent,
            width=max(1, int(2 * pulse)),
        )


def draw_planet_landing_band_chase(
    canvas: tk.Canvas,
    body: PlanetBody,
    *,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    accent: str,
    dim: str,
    elapsed: float = 0.0,
) -> None:
    """Perspective landing annulus projected toward the chase horizon."""
    center = camera.world_to_chase_screen(
        body.center, ship_pos, ship_angle, min_ahead=80.0, screen_margin=480.0,
    )
    if center.depth < 80.0:
        return
    scale = max(0.15, camera.perspective_scale(center.depth) / camera.focal_length)
    surface_r = body.surface_radius * scale * 1.8
    inner_r = body.landing_band_inner * scale * 1.8
    outer_r = body.landing_band_outer * scale * 1.8
    cx, cy = center.x, center.y
    in_band = in_planet_landing_band(ship_pos, body)
    pulse = 0.65 + 0.35 * math.sin(elapsed * 3.6)
    color = accent if in_band else dim

    draw_ground_fog_glow(
        canvas, cx, cy, surface_r * 0.9,
        palette.CHASE_FOG_BROOD if accent == palette.BROOD_MOON_HUD_ACCENT else lerp_hex(accent, "#081018", 0.55),
        pulse=elapsed * 2.2,
    )
    if in_band:
        canvas.create_oval(
            cx - outer_r, cy - outer_r * 0.55, cx + outer_r, cy + outer_r * 0.55,
            fill=lerp_hex(accent, "#120818", 0.82), outline="", stipple="gray25",
        )
        canvas.create_oval(
            cx - inner_r, cy - inner_r * 0.55, cx + inner_r, cy + inner_r * 0.55,
            fill="#120818", outline="",
        )

    canvas.create_oval(
        cx - surface_r, cy - surface_r * 0.55,
        cx + surface_r, cy + surface_r * 0.55,
        outline=color, width=2 if in_band else 1,
    )
    _dash_ring_segments(
        canvas, cx, cy, inner_r, y_scale=0.55, color=color,
        width=1, segments=20, elapsed=elapsed,
    )
    _dash_ring_segments(
        canvas, cx, cy, outer_r, y_scale=0.55, color=color,
        width=1, segments=28, elapsed=elapsed, speed=1.6,
    )
    if in_band:
        canvas.create_oval(
            cx - outer_r - 6, cy - (outer_r + 6) * 0.55,
            cx + outer_r + 6, cy + (outer_r + 6) * 0.55,
            outline=accent,
            width=max(1, int(2 * pulse)),
        )
