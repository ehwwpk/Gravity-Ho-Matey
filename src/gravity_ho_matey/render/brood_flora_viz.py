from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.brood_moon_layout import SURFACE_FLOOR_Y
from gravity_ho_matey.levels.brood_moon_props import props_near_ship
from gravity_ho_matey.render.brood_surface_mesh import mesh_for
from gravity_ho_matey.render.brood_viz_helpers import draw_brood_rim_bloom, draw_brood_vein_glow_line
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon
from gravity_ho_matey.render import palette

FLORA_DRAW_MAX = 16
_FLORA_KINDS = frozenset({"stalk", "chitin_bloom", "float_bulb"})


def _flora_material(kind: str, rig: LightRig):
    if kind == "chitin_bloom":
        return material_for("brood_chitin", theme=rig.theme, view=rig.view)
    return material_for("brood_flora", theme=rig.theme, view=rig.view)


def _draw_flora_prop(
    canvas: tk.Canvas,
    prop,
    *,
    rig: LightRig,
    world: GameWorld,
    to_screen,
    illustrated: bool = True,
) -> None:
    material = _flora_material(prop.kind, rig)
    wobble = math.sin(world.elapsed * 1.8 + prop.seed) * 4.0
    lift = math.sin(world.elapsed * 1.2 + prop.seed * 0.7) * 6.0 if prop.kind == "float_bulb" else 0.0
    local = mesh_for(prop.kind, prop.seed, prop.scale)
    screen_pts: list[tuple[float, float]] = []
    for v in local:
        wv = prop.pos + Vec2(v.x + wobble * 0.2, v.y - lift)
        screen_pts.append(to_screen(wv))
    if len(screen_pts) < 3:
        return
    sp, sy = to_screen(prop.pos + Vec2(0.0, -lift))
    if illustrated:
        draw_illustrated_polygon(
            canvas,
            screen_pts,
            rig=rig,
            material=material,
            seed=prop.seed,
            radius_hint=22.0 * prop.scale,
            crater_count=0,
            outline_width=1,
        )
    tip = min(screen_pts, key=lambda pt: pt[1])
    draw_ground_fog_glow(
        canvas, tip[0], tip[1] - 2.0, 16.0 * prop.scale,
        palette.CHASE_FOG_BROOD, pulse=world.elapsed * 2.8 + prop.seed,
    )
    if prop.kind in ("chitin_bloom", "float_bulb"):
        draw_brood_rim_bloom(canvas, sp, sy, 18.0 * prop.scale, material, flatten=0.4)


def draw_brood_flora_tactical(
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
    scroll = (ship_pos.x * 0.18) % 640.0

    def to_screen(wv: Vec2) -> tuple[float, float]:
        p = camera.world_to_screen(wv, ship_pos, ship_angle)
        return p.x, p.y + hud_top

    for prop in props_near_ship(ship_pos.x):
        if prop.kind not in _FLORA_KINDS:
            continue
        if drawn >= FLORA_DRAW_MAX:
            break
        _draw_flora_prop(canvas, prop, rig=rig, world=world, to_screen=to_screen)
        drawn += 1

    pulse = world.elapsed * 3.0
    for i in range(8):
        vx = ship_pos.x + ((i * 503) % 1800) - 900.0 + scroll
        p0 = camera.world_to_screen(Vec2(vx, SURFACE_FLOOR_Y + 12.0), ship_pos, ship_angle)
        p1 = camera.world_to_screen(Vec2(vx + 40.0, SURFACE_FLOOR_Y + 18.0), ship_pos, ship_angle)
        draw_brood_vein_glow_line(
            canvas, p0.x, p0.y + hud_top, p1.x, p1.y + hud_top,
            pulse=pulse + i * 0.5, width=1,
        )


def draw_brood_flora_chase(
    canvas: tk.Canvas,
    camera: ViewCamera,
    world: GameWorld,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    rig: LightRig,
) -> None:
    drawn = 0
    for prop in props_near_ship(ship_pos.x):
        if prop.kind not in _FLORA_KINDS:
            continue
        if drawn >= FLORA_DRAW_MAX:
            break

        def to_screen(wv: Vec2) -> tuple[float, float]:
            p = camera.world_to_chase_screen(wv, ship_pos, ship_angle, min_ahead=6.0, screen_margin=320.0)
            return p.x, p.y

        _draw_flora_prop(canvas, prop, rig=rig, world=world, to_screen=to_screen)
        drawn += 1

    scroll = (ship_pos.x * 0.18) % 640.0
    pulse = world.elapsed * 3.0
    for i in range(8):
        vx = ship_pos.x + ((i * 503) % 1800) - 900.0 + scroll
        p0 = camera.world_to_chase_screen(
            Vec2(vx, SURFACE_FLOOR_Y + 12.0), ship_pos, ship_angle, min_ahead=6.0, screen_margin=320.0,
        )
        p1 = camera.world_to_chase_screen(
            Vec2(vx + 40.0, SURFACE_FLOOR_Y + 18.0), ship_pos, ship_angle, min_ahead=6.0, screen_margin=320.0,
        )
        if p0.depth >= 6.0 and p1.depth >= 6.0:
            draw_brood_vein_glow_line(canvas, p0.x, p0.y, p1.x, p1.y, pulse=pulse + i * 0.5, width=1)
