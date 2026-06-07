from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.brood_moon_layout import SURFACE_FLOOR_Y
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import _lerp_color, draw_fog_glow, draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon, draw_simplified_polygon
from gravity_ho_matey.render.brood_viz_helpers import draw_brood_vein_glow_line

# Chase floor fog — capped so the nursery never reads as a viewport-sized purple disc.
CHASE_BROOD_CENTER_FOG_MAX = 96.0
CHASE_BROOD_GROUND_FOG_COUNT = 3
CHASE_BROOD_GROUND_FOG_BASE = 48.0


def draw_brood_tactical_surface_band(
    canvas: tk.Canvas,
    camera: ViewCamera,
    world: GameWorld,
    *,
    hud_top: float,
    ship_pos: Vec2,
    ship_angle: float,
    rig: LightRig | None = None,
) -> None:
    """Low-altitude nursery floor — parallax crust band under the playfield."""
    vw = float(camera.viewport_width)
    floor_y = SURFACE_FLOOR_Y
    band_h = 420.0
    scroll = (ship_pos.x * 0.18) % 640.0
    if rig is None:
        rig = LightRig.for_play(theme="brood_moon", camera_mode=camera.mode)
    regolith = material_for("brood_regolith", theme=rig.theme, view=rig.view)
    for layer, (alpha, offset) in enumerate(((0.35, 0.0), (0.55, 120.0), (0.75, 240.0))):
        points: list[float] = []
        step = 48.0
        x = -step
        chunk_polys: list[list[tuple[float, float]]] = []
        while x <= vw + step:
            wx = ship_pos.x + (x - vw * 0.5) / max(0.55, camera.tactical_scale / 1.1)
            wave = math.sin((wx + scroll + offset) * 0.0045) * 28.0
            wave += math.sin((wx - offset) * 0.011) * 12.0
            p = camera.world_to_screen(Vec2(wx, floor_y + wave), ship_pos, ship_angle)
            points.extend((p.x, p.y + hud_top))
            if len(points) >= 4 and int(x / step) % 2 == 0:
                wx2 = wx + step * 0.5
                w2 = math.sin((wx2 + scroll + offset) * 0.0045) * 28.0
                w2 += math.sin((wx2 - offset) * 0.011) * 12.0
                p2 = camera.world_to_screen(Vec2(wx2, floor_y + w2), ship_pos, ship_angle)
                chunk_polys.append(
                    [
                        (points[-4], points[-3]),
                        (points[-2], points[-1]),
                        (p2.x, p2.y + hud_top),
                        (points[-4], points[-3]),
                    ]
                )
            x += step
        p_far = camera.world_to_screen(Vec2(ship_pos.x + vw, floor_y + band_h), ship_pos, ship_angle)
        p_near = camera.world_to_screen(Vec2(ship_pos.x - vw, floor_y + band_h), ship_pos, ship_angle)
        fill = _lerp_color(palette.BROOD_MOON_BG, palette.BROOD_MOON_SURFACE, alpha)
        if len(points) >= 4:
            canvas.create_polygon(
                *points,
                p_far.x,
                p_far.y + hud_top,
                p_near.x,
                p_near.y + hud_top,
                fill=fill,
                outline="",
            )
        if layer == 2:
            for i, poly in enumerate(chunk_polys[:10]):
                if len(poly) >= 3:
                    cx = sum(p[0] for p in poly) / len(poly)
                    cy = sum(p[1] for p in poly) / len(poly)
                    span = max(abs(poly[0][0] - poly[2][0]), 12.0)
                    draw_illustrated_polygon(
                        canvas,
                        poly,
                        rig=rig,
                        material=regolith,
                        seed=int(cx) + i * 17,
                        radius_hint=span * 0.45,
                        crater_count=1,
                        outline_width=1,
                    )
    pulse = world.elapsed * 3.0
    for i in range(10):
        vx = ship_pos.x + ((i * 791) % 3200) - 1600.0 + scroll * 2.0
        p0 = camera.world_to_screen(Vec2(vx, floor_y + 40.0), ship_pos, ship_angle)
        p1 = camera.world_to_screen(Vec2(vx + 180.0, floor_y + 90.0), ship_pos, ship_angle)
        draw_brood_vein_glow_line(
            canvas,
            p0.x,
            p0.y + hud_top,
            p1.x,
            p1.y + hud_top,
            pulse=pulse + i * 0.7,
            width=2,
        )


def draw_brood_chase_floor_wash(canvas: tk.Canvas, camera: ViewCamera, world: GameWorld) -> None:
    """Mauve exosphere + small biolum ground fog on the chase floor."""
    horizon = camera.chase_horizon_y()
    bottom = camera.viewport_height
    width = camera.viewport_width
    steps = 5
    band = max(1.0, (bottom - horizon) / steps)
    for i in range(steps):
        t = i / max(1, steps - 1)
        y0 = horizon + band * i
        y1 = horizon + band * (i + 1)
        color = _lerp_color("#1a1028", "#281830", t)
        canvas.create_rectangle(0, y0, width, y1, fill=color, outline="")
    pulse = world.elapsed * 2.4
    for i in range(CHASE_BROOD_GROUND_FOG_COUNT):
        wx = world.ship.pos.x + (i * 420.0 - 630.0)
        wy = SURFACE_FLOOR_Y - 24.0 - (i % 2) * 18.0
        p = camera.world_to_chase_screen(
            Vec2(wx, wy), world.ship.pos, world.ship.angle, min_ahead=6.0, screen_margin=360.0,
        )
        if p.depth < 6.0:
            continue
        draw_ground_fog_glow(
            canvas,
            p.x,
            max(horizon + 20, p.y),
            CHASE_BROOD_GROUND_FOG_BASE + i * 12.0,
            palette.CHASE_FOG_BROOD,
            pulse=pulse + i,
        )
    draw_fog_glow(
        canvas,
        width * 0.5,
        horizon + 24,
        min(CHASE_BROOD_CENTER_FOG_MAX, width * 0.12),
        palette.CHASE_FOG_BROOD,
        pulse=pulse * 0.7,
    )


def draw_brood_chase_surface_band(
    canvas: tk.Canvas,
    camera: ViewCamera,
    world: GameWorld,
    *,
    ship_pos: Vec2,
    ship_angle: float,
) -> None:
    """Project nursery crust waves onto the chase floor — parity with tactical band."""
    horizon = camera.chase_horizon_y()
    bottom = camera.viewport_height
    width = camera.viewport_width
    floor_y = SURFACE_FLOOR_Y
    scroll = (ship_pos.x * 0.18) % 640.0
    step = 48.0
    rig = LightRig.for_play(theme="brood_moon", camera_mode=camera.mode)
    regolith = material_for("brood_regolith", theme=rig.theme, view=rig.view)

    top_points: list[tuple[float, float]] = []
    x = ship_pos.x - 2400.0
    end_x = ship_pos.x + 2400.0
    while x <= end_x:
        wave = math.sin((x + scroll) * 0.0045) * 28.0
        wave += math.sin((x - 120.0) * 0.011) * 12.0
        wy = floor_y + wave
        p = camera.world_to_chase_screen(Vec2(x, wy), ship_pos, ship_angle, min_ahead=6.0, screen_margin=400.0)
        if p.depth >= 6.0:
            top_points.append((p.x, max(horizon, p.y)))
        x += step

    if len(top_points) >= 2:
        fill_pts: list[float] = []
        for sx, sy in top_points:
            fill_pts.extend((sx, sy))
        fill_pts.extend((top_points[-1][0], bottom))
        fill_pts.extend((top_points[0][0], bottom))
        canvas.create_polygon(*fill_pts, fill=palette.BROOD_MOON_SURFACE, outline="")

    vein_pulse = world.elapsed * 3.0
    for i in range(8):
        vx = ship_pos.x + ((i * 791) % 2400) - 1200.0 + scroll * 2.0
        p0 = camera.world_to_chase_screen(
            Vec2(vx, floor_y + 40.0), ship_pos, ship_angle, min_ahead=6.0, screen_margin=400.0,
        )
        p1 = camera.world_to_chase_screen(
            Vec2(vx + 180.0, floor_y + 90.0), ship_pos, ship_angle, min_ahead=6.0, screen_margin=400.0,
        )
        if p0.depth >= 6.0 and p1.depth >= 6.0:
            draw_brood_vein_glow_line(
                canvas, p0.x, p0.y, p1.x, p1.y,
                pulse=vein_pulse + i * 0.7,
                width=int(1 + 0.35 * math.sin(vein_pulse + i)),
            )

    # Lit crust chunks along the horizon line.
    chunk_x = ship_pos.x - 1800.0
    drawn = 0
    while chunk_x <= ship_pos.x + 1800.0 and drawn < 10:
        wave = math.sin((chunk_x + scroll) * 0.0045) * 28.0
        wy = floor_y + wave
        cx = chunk_x
        cy = wy
        half = 36.0
        corners = [
            Vec2(cx - half, cy),
            Vec2(cx + half, cy + 8.0),
            Vec2(cx + half * 0.6, cy + 22.0),
            Vec2(cx - half * 0.6, cy + 18.0),
        ]
        screen_pts: list[tuple[float, float]] = []
        ok = True
        for c in corners:
            p = camera.world_to_chase_screen(c, ship_pos, ship_angle, min_ahead=6.0, screen_margin=320.0)
            if p.depth < 6.0:
                ok = False
                break
            screen_pts.append((p.x, p.y))
        if ok and len(screen_pts) >= 3:
            span = max(abs(screen_pts[0][0] - screen_pts[2][0]), 8.0)
            draw_illustrated_polygon(
                canvas,
                screen_pts,
                rig=rig,
                material=regolith,
                seed=int(chunk_x) + drawn * 13,
                radius_hint=span * 0.5,
                crater_count=1,
                outline_width=1,
            )
            drawn += 1
        chunk_x += 180.0
