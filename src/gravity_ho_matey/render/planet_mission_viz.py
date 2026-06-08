from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.planet_mission import PlanetBody, in_planet_landing_band
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import draw_fog_glow
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


def _brood_fog_colors(accent: str) -> tuple[str, ...]:
    if accent == palette.BROOD_MOON_HUD_ACCENT:
        return palette.CHASE_FOG_BROOD
    return (lerp_hex(accent, "#081018", 0.5),)


def _draw_planet_landing_fog_tactical(
    canvas: tk.Canvas,
    body: PlanetBody,
    *,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
    accent: str,
    elapsed: float,
) -> None:
    """Exosphere haze only — drawn under asteroids/beacons."""
    center = camera.world_to_screen(body.center, ship_pos, ship_angle)
    scale = camera.tactical_scale / 1.1
    surface_r = body.surface_radius * scale
    cx, cy = center.x, center.y + hud_top
    in_band = in_planet_landing_band(ship_pos, body)
    fog_r = surface_r * (0.32 if in_band else 0.52)
    draw_fog_glow(
        canvas,
        cx,
        cy,
        fog_r,
        _brood_fog_colors(accent),
        pulse=elapsed * 2.2,
    )


def _draw_planet_landing_rings_tactical(
    canvas: tk.Canvas,
    body: PlanetBody,
    *,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
    accent: str,
    dim: str,
    elapsed: float,
) -> None:
    """Outline landing annulus — no filled disks (those blinded rocks/objectives)."""
    center = camera.world_to_screen(body.center, ship_pos, ship_angle)
    scale = camera.tactical_scale / 1.1
    surface_r = body.surface_radius * scale
    inner_r = body.landing_band_inner * scale
    outer_r = body.landing_band_outer * scale
    cx, cy = center.x, center.y + hud_top
    in_band = in_planet_landing_band(ship_pos, body)
    pulse = 0.65 + 0.35 * math.sin(elapsed * 3.6)
    ring_color = accent if in_band else dim

    canvas.create_oval(
        cx - surface_r,
        cy - surface_r,
        cx + surface_r,
        cy + surface_r,
        outline=ring_color,
        width=2 if in_band else 1,
    )
    _dash_ring_segments(
        canvas, cx, cy, inner_r, color=ring_color,
        width=1, segments=24, elapsed=elapsed,
    )
    _dash_ring_segments(
        canvas, cx, cy, outer_r, color=ring_color,
        width=1, segments=32, elapsed=elapsed, speed=1.8,
    )
    if in_band:
        mid_r = (inner_r + outer_r) * 0.5
        _dash_ring_segments(
            canvas, cx, cy, mid_r, color=accent,
            width=2, segments=18, elapsed=elapsed, speed=2.8,
        )
        canvas.create_oval(
            cx - outer_r - 4,
            cy - outer_r - 4,
            cx + outer_r + 4,
            cy + outer_r + 4,
            outline=accent,
            width=max(1, int(2 * pulse)),
        )


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
    show_fog: bool = True,
    show_rings: bool = True,
) -> None:
    """Highlight the full limb approach shell around a planet/moon."""
    if show_fog:
        _draw_planet_landing_fog_tactical(
            canvas,
            body,
            camera=camera,
            ship_pos=ship_pos,
            ship_angle=ship_angle,
            hud_top=hud_top,
            accent=accent,
            elapsed=elapsed,
        )
    if show_rings:
        _draw_planet_landing_rings_tactical(
            canvas,
            body,
            camera=camera,
            ship_pos=ship_pos,
            ship_angle=ship_angle,
            hud_top=hud_top,
            accent=accent,
            dim=dim,
            elapsed=elapsed,
        )


def _draw_planet_landing_fog_chase(
    canvas: tk.Canvas,
    body: PlanetBody,
    *,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    accent: str,
    elapsed: float,
) -> None:
    center = camera.world_to_chase_screen(
        body.center, ship_pos, ship_angle, min_ahead=80.0, screen_margin=480.0,
    )
    if center.depth < 80.0:
        return
    scale = max(0.15, camera.perspective_scale(center.depth) / camera.focal_length)
    surface_r = body.surface_radius * scale * 1.8
    cx, cy = center.x, center.y
    in_band = in_planet_landing_band(ship_pos, body)
    fog_r = surface_r * (0.55 if in_band else 0.85)
    draw_fog_glow(
        canvas,
        cx,
        cy,
        fog_r,
        _brood_fog_colors(accent),
        pulse=elapsed * 2.2,
    )


def _draw_planet_landing_rings_chase(
    canvas: tk.Canvas,
    body: PlanetBody,
    *,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    accent: str,
    dim: str,
    elapsed: float,
) -> None:
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
        mid_r = (inner_r + outer_r) * 0.5
        _dash_ring_segments(
            canvas, cx, cy, mid_r, y_scale=0.55, color=accent,
            width=2, segments=16, elapsed=elapsed, speed=2.6,
        )
        canvas.create_oval(
            cx - outer_r - 6, cy - (outer_r + 6) * 0.55,
            cx + outer_r + 6, cy + (outer_r + 6) * 0.55,
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
    show_fog: bool = True,
    show_rings: bool = True,
) -> None:
    """Perspective landing annulus projected toward the chase horizon."""
    if show_fog:
        _draw_planet_landing_fog_chase(
            canvas,
            body,
            camera=camera,
            ship_pos=ship_pos,
            ship_angle=ship_angle,
            accent=accent,
            elapsed=elapsed,
        )
    if show_rings:
        _draw_planet_landing_rings_chase(
            canvas,
            body,
            camera=camera,
            ship_pos=ship_pos,
            ship_angle=ship_angle,
            accent=accent,
            dim=dim,
            elapsed=elapsed,
        )
