from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.levels.brood_moon_props import (
    CHASE_PROP_DRAW_MAX,
    TACTICAL_PROP_DRAW_MAX,
    props_near_ship,
)
from gravity_ho_matey.render.brood_surface_mesh import mesh_for
from gravity_ho_matey.render.brood_viz_helpers import draw_brood_ground_shadow, draw_brood_rim_bloom
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.lighting import LightRig, chase_depth_fade, depth_faded_material, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon, draw_simplified_polygon
from gravity_ho_matey.render import palette

_FLORA_KINDS = frozenset({"stalk", "chitin_bloom", "float_bulb"})


def _material_kind_for_prop(kind: str) -> str:
    if kind in _FLORA_KINDS:
        return "brood_flora"
    if kind == "spire":
        return "brood_chitin"
    if kind == "crystal":
        return "brood_crystal"
    if kind == "vein_node":
        return "brood_vein"
    return "brood_regolith"


def _world_verts(prop, angle: float = 0.0) -> list[Vec2]:
    local = mesh_for(prop.kind, prop.seed, prop.scale)
    c = math.cos(angle)
    s = math.sin(angle)
    return [prop.pos + Vec2(v.x * c - v.y * s, v.x * s + v.y * c) for v in local]


def _draw_geology_prop_tactical(
    canvas: tk.Canvas,
    prop,
    *,
    rig: LightRig,
    world: GameWorld,
    screen_pts: list[tuple[float, float]],
    material,
) -> None:
    if prop.kind == "sinkhole_rim":
        outer = screen_pts
        cx = sum(x for x, _ in outer) / len(outer)
        cy = sum(y for _, y in outer) / len(outer)
        inner = [(cx + (ox - cx) * 0.55, cy + (oy - cy) * 0.55) for ox, oy in outer]
        pit = material_for("brood_regolith", theme=rig.theme, view=rig.view)
        draw_simplified_polygon(canvas, inner, rig=rig, material=pit, outline_width=0)
        draw_illustrated_polygon(
            canvas, outer, rig=rig, material=material, seed=prop.seed,
            radius_hint=24.0 * prop.scale, crater_count=1, outline_width=1,
        )
    elif prop.kind in ("spire", "crystal", "mound", "scarp"):
        draw_illustrated_polygon(
            canvas,
            screen_pts,
            rig=rig,
            material=material,
            seed=prop.seed,
            radius_hint=28.0 * prop.scale,
            crater_count=1 if prop.kind in ("crystal", "scarp") else 0,
            outline_width=2 if prop.kind == "spire" else 1,
        )
        if prop.kind == "spire":
            cp = screen_pts[0]
            for pt in screen_pts:
                if pt[1] < cp[1]:
                    cp = pt
            draw_brood_rim_bloom(canvas, cp[0], cp[1] + 8.0, 22.0 * prop.scale, material, flatten=0.35)
    else:
        draw_illustrated_polygon(
            canvas, screen_pts, rig=rig, material=material, seed=prop.seed,
            radius_hint=24.0 * prop.scale, crater_count=1, outline_width=1,
        )

    if prop.kind in ("spire", "mound", "scarp", "vein_node"):
        cx = sum(x for x, _ in screen_pts) / len(screen_pts)
        cy = max(y for _, y in screen_pts)
        draw_brood_ground_shadow(canvas, cx, cy + 6.0, 20.0 * prop.scale, rig=rig)

    if prop.kind == "vein_node":
        cx = sum(x for x, _ in screen_pts) / len(screen_pts)
        cy = sum(y for _, y in screen_pts) / len(screen_pts)
        draw_ground_fog_glow(
            canvas, cx, cy + 4.0, 40.0 * prop.scale,
            palette.CHASE_FOG_BROOD, pulse=world.elapsed * 2.2 + prop.seed,
        )


def draw_brood_geology_tactical(
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
    for prop in props_near_ship(ship_pos.x):
        if drawn >= TACTICAL_PROP_DRAW_MAX:
            break
        if prop.kind in _FLORA_KINDS:
            continue
        material = material_for(_material_kind_for_prop(prop.kind), theme=rig.theme, view=rig.view)
        screen_pts: list[tuple[float, float]] = []
        for wv in _world_verts(prop):
            p = camera.world_to_screen(wv, ship_pos, ship_angle)
            screen_pts.append((p.x, p.y + hud_top))
        if len(screen_pts) < 3:
            continue
        _draw_geology_prop_tactical(
            canvas, prop, rig=rig, world=world, screen_pts=screen_pts, material=material,
        )
        drawn += 1


def draw_brood_geology_chase(
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
        if drawn >= CHASE_PROP_DRAW_MAX:
            break
        if prop.kind in _FLORA_KINDS:
            continue
        base_mat = material_for(_material_kind_for_prop(prop.kind), theme=rig.theme, view=rig.view)
        screen_pts: list[tuple[float, float]] = []
        depths: list[float] = []
        for wv in _world_verts(prop):
            p = camera.world_to_chase_screen(wv, ship_pos, ship_angle, min_ahead=6.0, screen_margin=360.0)
            if p.depth < 6.0:
                screen_pts.clear()
                break
            screen_pts.append((p.x, p.y))
            depths.append(p.depth)
        if len(screen_pts) < 3:
            continue
        depth = sum(depths) / len(depths)
        fade = chase_depth_fade(depth)
        material = depth_faded_material(base_mat, fade)
        if fade < 0.62:
            _draw_geology_prop_tactical(
                canvas, prop, rig=rig, world=world, screen_pts=screen_pts, material=material,
            )
        else:
            draw_simplified_polygon(canvas, screen_pts, rig=rig, material=material, outline_width=1)
        drawn += 1
