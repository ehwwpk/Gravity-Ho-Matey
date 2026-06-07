from __future__ import annotations

import math
import tkinter as tk
from collections.abc import Callable

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.enemy_mesh import (
    EnemySkiffMesh,
    enemy_visual_seed,
    local_to_world_rotated,
    mesh_for_enemy,
)
from gravity_ho_matey.render.lighting import LightRig, MaterialTones, chase_depth_fade, depth_faded_material, lerp_hex, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon, draw_simplified_polygon
from gravity_ho_matey.render.station_lit_draw import layer_nudge

CHASE_ENEMY_MAX_R_PX = 44.0


def _flat(points: list[tuple[float, float]]) -> list[float]:
    out: list[float] = []
    for x, y in points:
        out.extend((x, y))
    return out


def _to_screen_poly(
    local_pts: list[tuple[float, float]],
    *,
    pos: Vec2,
    radius: float,
    facing: float,
    to_screen: Callable[[Vec2], tuple[float, float]],
    nudge: tuple[float, float],
) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for lx, ly in local_pts:
        world = local_to_world_rotated((lx, ly), pos, radius, facing)
        sx, sy = to_screen(world)
        out.append((sx + nudge[0], sy + nudge[1]))
    return out


def _draw_layer_polygons(
    canvas: tk.Canvas,
    polys: list[list[tuple[float, float]]],
    *,
    pos: Vec2,
    radius: float,
    facing: float,
    to_screen: Callable[[Vec2], tuple[float, float]],
    px_per_unit: float,
    rig: LightRig,
    material: MaterialTones,
    layer: str,
    seed: int,
    nudge: tuple[float, float],
) -> None:
    base = material
    if layer == "back":
        base = MaterialTones(
            highlight=lerp_hex(material.highlight, material.shadow, 0.55),
            mid=lerp_hex(material.mid, material.deep, 0.35),
            shadow=lerp_hex(material.shadow, material.deep, 0.25),
            deep=material.deep,
            rim=lerp_hex(material.rim, material.deep, 0.4),
            crater_pit=material.crater_pit,
            crater_rim_hi=lerp_hex(material.crater_rim_hi, material.shadow, 0.35),
        )
    elif layer == "front":
        base = MaterialTones(
            highlight=material.highlight,
            mid=lerp_hex(material.mid, material.highlight, 0.12),
            shadow=material.shadow,
            deep=material.deep,
            rim=material.rim,
            crater_pit=material.crater_pit,
            crater_rim_hi=material.crater_rim_hi,
        )
    r_hint = radius * px_per_unit
    for idx, poly in enumerate(polys):
        screen = _to_screen_poly(poly, pos=pos, radius=radius, facing=facing, to_screen=to_screen, nudge=nudge)
        draw_illustrated_polygon(
            canvas,
            screen,
            rig=rig,
            material=base,
            seed=seed + idx * 7,
            radius_hint=r_hint,
            outline_width=1 if layer == "back" else 2,
            crater_count=0 if layer != "hull" else 2,
        )


def _draw_greebles(
    canvas: tk.Canvas,
    mesh: EnemySkiffMesh,
    *,
    pos: Vec2,
    radius: float,
    facing: float,
    to_screen: Callable[[Vec2], tuple[float, float]],
    px_per_unit: float,
    material: MaterialTones,
    glow: str,
    elapsed: float,
    nudge: tuple[float, float],
) -> None:
    pulse = 0.55 + 0.45 * math.sin(elapsed * 5.5)
    for x1, y1, x2, y2 in mesh.spine_lines:
        ax, ay = to_screen(local_to_world_rotated((x1, y1), pos, radius, facing))
        bx, by = to_screen(local_to_world_rotated((x2, y2), pos, radius, facing))
        canvas.create_line(
            ax + nudge[0], ay + nudge[1], bx + nudge[0], by + nudge[1],
            fill=material.rim, width=1,
        )
    for x1, y1, x2, y2 in mesh.panel_lines:
        ax, ay = to_screen(local_to_world_rotated((x1, y1), pos, radius, facing))
        bx, by = to_screen(local_to_world_rotated((x2, y2), pos, radius, facing))
        canvas.create_line(
            ax + nudge[0], ay + nudge[1], bx + nudge[0], by + nudge[1],
            fill=lerp_hex(material.shadow, material.deep, 0.35), width=1,
        )
    for lamp in mesh.lamps:
        sx, sy = to_screen(local_to_world_rotated((lamp.x, lamp.y), pos, radius, facing))
        sx += nudge[0]
        sy += nudge[1]
        lr = lamp.radius * radius * px_per_unit
        canvas.create_oval(sx - lr * 2.2, sy - lr * 2.2, sx + lr * 2.2, sy + lr * 2.2, fill=lerp_hex(glow, "#000000", 0.78), outline="")
        canvas.create_oval(
            sx - lr, sy - lr, sx + lr, sy + lr,
            fill=glow if pulse > 0.5 else lerp_hex(glow, "#000000", 0.4),
            outline="",
        )
    if mesh.antenna is not None:
        x1, y1, x2, y2 = mesh.antenna
        ax, ay = to_screen(local_to_world_rotated((x1, y1), pos, radius, facing))
        bx, by = to_screen(local_to_world_rotated((x2, y2), pos, radius, facing))
        canvas.create_line(
            ax + nudge[0], ay + nudge[1], bx + nudge[0], by + nudge[1],
            fill=material.rim, width=2,
        )
        dr = max(2.0, radius * px_per_unit * 0.06)
        canvas.create_oval(bx + nudge[0] - dr, by + nudge[1] - dr, bx + nudge[0] + dr, by + nudge[1] + dr, fill=material.mid, outline=material.highlight, width=1)


def _draw_engine_glow(
    canvas: tk.Canvas,
    mesh: EnemySkiffMesh,
    *,
    pos: Vec2,
    radius: float,
    facing: float,
    to_screen: Callable[[Vec2], tuple[float, float]],
    px_per_unit: float,
    glow: str,
    elapsed: float,
) -> None:
    cx = sum(p[0] for p in mesh.engine_block) / len(mesh.engine_block)
    cy = sum(p[1] for p in mesh.engine_block) / len(mesh.engine_block)
    ex, ey = to_screen(local_to_world_rotated((cx, cy), pos, radius, facing))
    pulse = 0.7 + 0.3 * math.sin(elapsed * 8.0)
    er = radius * px_per_unit * 0.22 * pulse
    canvas.create_oval(ex - er * 1.6, ey - er, ex + er * 0.4, ey + er, fill=lerp_hex(glow, "#000000", 0.55), outline="")
    canvas.create_oval(ex - er, ey - er * 0.65, ex + er * 0.2, ey + er * 0.65, fill=glow, outline="")


def _screen_mapper(
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
) -> tuple[Callable[[Vec2], tuple[float, float]], float]:
    anchor = camera.world_to_screen(ship_pos, ship_pos, ship_angle)
    east = camera.world_to_screen(ship_pos + Vec2(120.0, 0.0), ship_pos, ship_angle)
    px_per_unit = abs(east.x - anchor.x) / 120.0

    def to_screen(world: Vec2) -> tuple[float, float]:
        sp = camera.world_to_screen(world, ship_pos, ship_angle)
        return sp.x, sp.y + hud_top

    return to_screen, px_per_unit


def draw_patrol_enemy_tactical(
    canvas: tk.Canvas,
    enemy: PatrolEnemy,
    *,
    camera: ViewCamera,
    ship_pos: Vec2,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
) -> None:
    mesh = mesh_for_enemy(enemy)
    to_screen, px_per_unit = _screen_mapper(camera, ship_pos, 0.0, hud_top)
    material = material_for("enemy_patrol", theme=rig.theme, view=rig.view)
    glow = palette.STATION_HOSTILE_GLOW
    seed = enemy_visual_seed(enemy)
    nudge_back = layer_nudge("back", rig, pixel_scale=px_per_unit)
    nudge_mid = layer_nudge("mid", rig, pixel_scale=px_per_unit)
    nudge_front = layer_nudge("front", rig, pixel_scale=px_per_unit)

    cx, cy = to_screen(enemy.pos)
    r_glow = enemy.radius * px_per_unit * 1.35
    draw_ground_fog_glow(canvas, cx, cy + 3, r_glow, palette.CHASE_ENEMY_FOG[:2], pulse=elapsed * 3.0)

    _draw_layer_polygons(
        canvas, [mesh.left_wing, mesh.right_wing],
        pos=enemy.pos, radius=enemy.radius, facing=enemy.facing_angle,
        to_screen=to_screen, px_per_unit=px_per_unit, rig=rig, material=material,
        layer="back", seed=seed, nudge=nudge_back,
    )
    _draw_layer_polygons(
        canvas, [mesh.engine_block],
        pos=enemy.pos, radius=enemy.radius, facing=enemy.facing_angle,
        to_screen=to_screen, px_per_unit=px_per_unit, rig=rig, material=material,
        layer="back", seed=seed + 3, nudge=nudge_back,
    )
    _draw_layer_polygons(
        canvas, [mesh.hull],
        pos=enemy.pos, radius=enemy.radius, facing=enemy.facing_angle,
        to_screen=to_screen, px_per_unit=px_per_unit, rig=rig, material=material,
        layer="hull", seed=seed + 5, nudge=nudge_mid,
    )
    _draw_greebles(
        canvas, mesh,
        pos=enemy.pos, radius=enemy.radius, facing=enemy.facing_angle,
        to_screen=to_screen, px_per_unit=px_per_unit, material=material,
        glow=glow, elapsed=elapsed, nudge=nudge_mid,
    )
    _draw_layer_polygons(
        canvas, [mesh.weapon_pod],
        pos=enemy.pos, radius=enemy.radius, facing=enemy.facing_angle,
        to_screen=to_screen, px_per_unit=px_per_unit, rig=rig, material=material,
        layer="front", seed=seed + 11, nudge=nudge_front,
    )
    _draw_engine_glow(
        canvas, mesh,
        pos=enemy.pos, radius=enemy.radius, facing=enemy.facing_angle,
        to_screen=to_screen, px_per_unit=px_per_unit, glow=glow, elapsed=elapsed,
    )


def chase_enemy_screen_points(
    local_pts: list[tuple[float, float]],
    pos: Vec2,
    radius: float,
    facing: float,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
) -> tuple[list[tuple[float, float]], float, float] | None:
    center = camera.world_to_chase_screen(
        pos, ship_pos, ship_angle, min_ahead=camera.min_depth, screen_margin=140.0,
    )
    if not center.visible:
        return None
    forward = Vec2.from_angle(ship_angle)
    right = forward.rotated(math.pi / 2.0)
    depth = max(camera.min_depth, center.depth)
    scale = camera.focal_length / depth
    lateral_scale = scale * camera.chase_thrust_boost
    pitch = 0.48 + camera.chase_lift / camera.focal_length
    cx, cy = center.x, center.y
    c = math.cos(facing)
    s = math.sin(facing)

    screen: list[tuple[float, float]] = []
    for lx, ly in local_pts:
        wx = (lx * c - ly * s) * radius
        wy = (lx * s + ly * c) * radius
        ahead = wx * forward.x + wy * forward.y
        lateral = wx * right.x + wy * right.y
        screen.append((cx + lateral * lateral_scale, cy - ahead * scale * pitch))

    if len(screen) < 3:
        return None
    r_px = max(math.hypot(x - cx, y - cy) for x, y in screen)
    if r_px > CHASE_ENEMY_MAX_R_PX:
        shrink = CHASE_ENEMY_MAX_R_PX / r_px
        screen = [(cx + (x - cx) * shrink, cy + (y - cy) * shrink) for x, y in screen]
        r_px = CHASE_ENEMY_MAX_R_PX
    return screen, r_px, chase_depth_fade(depth)


def draw_patrol_enemy_chase(
    canvas: tk.Canvas,
    screen_pos: Vec2,
    enemy: PatrolEnemy,
    *,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    scale: float,
    rig: LightRig,
    elapsed: float,
) -> None:
    mesh = mesh_for_enemy(enemy)
    material = material_for("enemy_patrol", theme=rig.theme, view=rig.view)
    glow = palette.STATION_HOSTILE_GLOW

    hull_proj = chase_enemy_screen_points(
        mesh.hull, enemy.pos, enemy.radius, enemy.facing_angle, camera, ship_pos, ship_angle,
    )
    if hull_proj is None:
        r = min(enemy.radius * scale, 28.0)
        draw_ground_fog_glow(canvas, screen_pos.x, screen_pos.y + 4, r * 1.4, palette.CHASE_ENEMY_FOG[:2], pulse=0.0)
        canvas.create_oval(
            screen_pos.x - r, screen_pos.y - r * 0.55, screen_pos.x + r, screen_pos.y + r * 0.35,
            fill=palette.ENEMY, outline=palette.ENEMY_EDGE, width=2,
        )
        return

    hull_pts, r_px, depth_fade = hull_proj
    if depth_fade > 0.01:
        material = depth_faded_material(material, depth_fade)

    cx = sum(x for x, _ in hull_pts) / len(hull_pts)
    cy = sum(y for _, y in hull_pts) / len(hull_pts)
    pulse = 0.82 + 0.18 * math.sin(elapsed * 3.2)
    draw_ground_fog_glow(
        canvas, cx, cy + 4, r_px * 1.15 * pulse, palette.CHASE_ENEMY_FOG[:2], pulse=elapsed * 2.5,
    )
    canvas.create_oval(
        cx - r_px * 0.85 * pulse, cy - r_px * 0.55 * pulse,
        cx + r_px * 0.85 * pulse, cy + r_px * 0.55 * pulse,
        fill=lerp_hex(glow, "#000000", 0.82), outline="",
    )

    wing_l = chase_enemy_screen_points(
        mesh.left_wing, enemy.pos, enemy.radius, enemy.facing_angle, camera, ship_pos, ship_angle,
    )
    wing_r = chase_enemy_screen_points(
        mesh.right_wing, enemy.pos, enemy.radius, enemy.facing_angle, camera, ship_pos, ship_angle,
    )
    engine = chase_enemy_screen_points(
        mesh.engine_block, enemy.pos, enemy.radius, enemy.facing_angle, camera, ship_pos, ship_angle,
    )
    pod = chase_enemy_screen_points(
        mesh.weapon_pod, enemy.pos, enemy.radius, enemy.facing_angle, camera, ship_pos, ship_angle,
    )

    wing_material = MaterialTones(
        highlight=lerp_hex(material.highlight, material.shadow, 0.45),
        mid=material.shadow,
        shadow=material.deep,
        deep=material.deep,
        rim=lerp_hex(material.rim, material.deep, 0.35),
        crater_pit=material.crater_pit,
        crater_rim_hi=material.crater_rim_hi,
    )
    for part in (wing_l, wing_r, engine):
        if part is not None:
            draw_simplified_polygon(canvas, part[0], rig=rig, material=wing_material, outline_width=1)
    draw_simplified_polygon(canvas, hull_pts, rig=rig, material=material, outline_width=2)
    if pod is not None:
        pod_material = MaterialTones(
            highlight=material.highlight,
            mid=lerp_hex(material.mid, material.highlight, 0.22),
            shadow=material.mid,
            deep=material.deep,
            rim=material.rim,
            crater_pit=material.crater_pit,
            crater_rim_hi=material.crater_rim_hi,
        )
        draw_simplified_polygon(canvas, pod[0], rig=rig, material=pod_material, outline_width=1)

    er = r_px * 0.18 * (0.75 + 0.25 * math.sin(elapsed * 9.0))
    canvas.create_oval(cx - r_px * 0.42 - er, cy - er * 0.5, cx - r_px * 0.42 + er * 0.3, cy + er * 0.5, fill=glow, outline="")


def draw_patrol_enemy_map_glyph(
    canvas: tk.Canvas,
    mx: float,
    my: float,
    *,
    radius: float,
    facing: float,
) -> None:
    """Mini skiff chevron for chart map."""
    c = math.cos(facing)
    s = math.sin(facing)
    pts: list[tuple[float, float]] = []
    for lx, ly in ((0.9, 0.0), (-0.55, 0.42), (-0.75, 0.0), (-0.55, -0.42)):
        wx = lx * c - ly * s
        wy = lx * s + ly * c
        pts.append((mx + wx * radius, my + wy * radius))
    canvas.create_polygon(
        *[coord for pt in pts for coord in pt],
        fill=palette.STATION_HOSTILE_HULL,
        outline=palette.STATION_HOSTILE_GLOW,
        width=1,
    )
    ex = mx + math.cos(facing) * radius * 0.55
    ey = my + math.sin(facing) * radius * 0.55
    canvas.create_oval(ex - 2, ey - 2, ex + 2, ey + 2, fill=palette.STATION_HOSTILE_GLOW, outline="")
