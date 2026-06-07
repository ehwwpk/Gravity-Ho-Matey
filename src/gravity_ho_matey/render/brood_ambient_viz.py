from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.brood_moon_layout import SURFACE_FLOOR_Y, SURFACE_WRAP_WIDTH
from gravity_ho_matey.render.brood_surface_mesh import mesh_for
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import draw_fog_glow, draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon, draw_simplified_polygon
from gravity_ho_matey.render import palette

AMBIENT_DRAW_MAX = 28

_LARVA_FRACS = (0.045, 0.11, 0.18, 0.26, 0.34, 0.45, 0.55, 0.66, 0.76, 0.86, 0.94)
_SPORE_FRACS = tuple(0.028 + i * 0.058 for i in range(20))


def _wrap_near(ship_x: float, target_x: float) -> float:
    return min(
        abs(target_x - ship_x),
        abs(target_x - ship_x - SURFACE_WRAP_WIDTH),
        abs(target_x - ship_x + SURFACE_WRAP_WIDTH),
    )


def _draw_larva_mote(
    canvas: tk.Canvas,
    sx: float,
    sy: float,
    *,
    rig: LightRig,
    seed: int,
    scale: float,
) -> None:
    material = material_for("brood_flora", theme=rig.theme, view=rig.view)
    local = mesh_for("spore_jelly", seed, scale * 0.35)
    pts = [(sx + v.x, sy + v.y) for v in local]
    if len(pts) >= 3:
        draw_illustrated_polygon(
            canvas, pts, rig=rig, material=material, seed=seed,
            radius_hint=8.0 * scale, crater_count=0, outline_width=1,
        )
    canvas.create_line(sx - 6.0 * scale, sy, sx + 10.0 * scale, sy, fill=palette.BROOD_MOON_VEIN, width=1)


def draw_brood_ambient_chase(
    canvas: tk.Canvas,
    camera: ViewCamera,
    world: GameWorld,
    *,
    ship_pos: Vec2,
    ship_angle: float,
) -> None:
    drawn = 0
    t = world.elapsed
    rig = LightRig.for_play(theme="brood_moon", camera_mode=camera.mode)

    for i, frac_x in enumerate(_LARVA_FRACS):
        if drawn >= AMBIENT_DRAW_MAX:
            break
        x = SURFACE_WRAP_WIDTH * frac_x
        if _wrap_near(ship_pos.x, x) > 1600.0:
            continue
        drift_y = SURFACE_FLOOR_Y - 120.0 + math.sin(t * 0.6 + i) * 18.0
        pos = Vec2(x + math.sin(t * 0.4 + i * 1.7) * 40.0, drift_y)
        p = camera.world_to_chase_screen(pos, ship_pos, ship_angle, min_ahead=6.0, screen_margin=280.0)
        if p.depth < 6.0:
            continue
        _draw_larva_mote(canvas, p.x, p.y, rig=rig, seed=i + 5, scale=1.0 + (i % 3) * 0.15)
        drawn += 1

    pulse = t * 2.0
    for i, frac_x in enumerate(_SPORE_FRACS):
        if drawn >= AMBIENT_DRAW_MAX:
            break
        x = SURFACE_WRAP_WIDTH * frac_x
        if _wrap_near(ship_pos.x, x) > 1800.0:
            continue
        y = SURFACE_FLOOR_Y - 60.0 - (i % 4) * 22.0
        pos = Vec2(x, y + math.sin(t + i) * 8.0)
        p = camera.world_to_chase_screen(pos, ship_pos, ship_angle, min_ahead=6.0, screen_margin=240.0)
        if p.depth < 6.0:
            continue
        draw_ground_fog_glow(canvas, p.x, p.y, 12.0 + (i % 3) * 4.0, palette.CHASE_FOG_BROOD, pulse=pulse + i)
        crystal = material_for("brood_crystal", theme=rig.theme, view=rig.view)
        draw_simplified_polygon(
            canvas,
            [(p.x - 3, p.y - 2), (p.x + 3, p.y - 2), (p.x, p.y - 7)],
            rig=rig, material=crystal, outline_width=0,
        )
        drawn += 1


def draw_brood_ambient_tactical(
    canvas: tk.Canvas,
    camera: ViewCamera,
    world: GameWorld,
    *,
    hud_top: float,
    ship_pos: Vec2,
    ship_angle: float,
    rig: LightRig,
) -> None:
    drawn = 0
    t = world.elapsed

    for i, frac_x in enumerate(_LARVA_FRACS):
        if drawn >= AMBIENT_DRAW_MAX:
            break
        base_x = SURFACE_WRAP_WIDTH * frac_x
        if _wrap_near(ship_pos.x, base_x) > 1600.0:
            continue
        drift_y = SURFACE_FLOOR_Y - 120.0 + math.sin(t * 0.6 + i) * 18.0
        pos = Vec2(base_x + math.sin(t * 0.4 + i * 1.7) * 40.0, drift_y)
        p = camera.world_to_screen(pos, ship_pos, ship_angle)
        _draw_larva_mote(canvas, p.x, p.y + hud_top, rig=rig, seed=i + 5, scale=1.0 + (i % 3) * 0.15)
        drawn += 1

    pulse = t * 2.0
    crystal = material_for("brood_crystal", theme=rig.theme, view=rig.view)
    for i, frac_x in enumerate(_SPORE_FRACS):
        if drawn >= AMBIENT_DRAW_MAX:
            break
        x = SURFACE_WRAP_WIDTH * frac_x
        if _wrap_near(ship_pos.x, x) > 1800.0:
            continue
        y = SURFACE_FLOOR_Y - 60.0 - (i % 4) * 22.0
        pos = Vec2(x, y + math.sin(t + i) * 8.0)
        p = camera.world_to_screen(pos, ship_pos, ship_angle)
        sy = p.y + hud_top
        draw_ground_fog_glow(
            canvas, p.x, sy, 10.0 + (i % 3) * 3.0,
            palette.CHASE_FOG_BROOD, pulse=pulse + i,
        )
        draw_simplified_polygon(
            canvas,
            [(p.x - 3, sy - 2), (p.x + 3, sy - 2), (p.x, sy - 7)],
            rig=rig, material=crystal, outline_width=0,
        )
        drawn += 1
