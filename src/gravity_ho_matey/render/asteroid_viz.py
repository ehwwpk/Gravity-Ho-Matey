from __future__ import annotations

import math

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Asteroid
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.lighting import (
    LightRig,
    chase_depth_fade,
    depth_faded_material,
    material_for,
)
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon, draw_simplified_polygon


def draw_tactical_asteroid(
    canvas: tk.Canvas,
    asteroid: Asteroid,
    camera: ViewCamera,
    *,
    hud_top: float,
    rig: LightRig,
    ship_pos: Vec2 | None = None,
    ship_angle: float = 0.0,
) -> None:
    anchor = ship_pos if ship_pos is not None else Vec2()
    material = material_for("asteroid", theme=rig.theme, view=rig.view)
    screen_points: list[tuple[float, float]] = []
    for vert in asteroid.world_vertices():
        p = camera.world_to_screen(vert, anchor, ship_angle)
        screen_points.append((p.x, p.y + hud_top))
    draw_illustrated_polygon(
        canvas,
        screen_points,
        rig=rig,
        material=material,
        seed=asteroid.seed,
        radius_hint=asteroid.approximate_radius(),
    )
    if asteroid.vel.length_sq() > 120.0:
        center = camera.world_to_screen(asteroid.pos, anchor, ship_angle)
        tail = asteroid.vel.normalized() * min(18.0, asteroid.vel.length() * 0.12)
        canvas.create_line(
            center.x - tail.x,
            center.y + hud_top - tail.y,
            center.x,
            center.y + hud_top,
            fill=material.rim,
            width=1,
        )


def draw_map_asteroid_glyph(
    canvas: tk.Canvas,
    center: Vec2,
    asteroid: Asteroid,
    *,
    scale: float,
    rig: LightRig,
) -> None:
    material = material_for("asteroid", theme=rig.theme, view=rig.view)
    points: list[tuple[float, float]] = []
    c = math.cos(asteroid.angle)
    s = math.sin(asteroid.angle)
    for v in asteroid.local_verts:
        lx = v.x * c - v.y * s
        ly = v.x * s + v.y * c
        points.append((center.x + lx * scale, center.y + ly * scale))
    draw_simplified_polygon(
        canvas,
        points,
        rig=rig,
        material=material,
        outline_width=1,
    )


def chase_asteroid_screen_outline(
    asteroid: Asteroid,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
) -> tuple[list[tuple[float, float]], float, float] | None:
    """Rigid-body chase projection — one depth per rock so faceted lighting stays clean."""
    center = camera.world_to_screen(asteroid.pos, ship_pos, ship_angle)
    if not center.visible or center.depth < camera.min_depth:
        return None
    if center.y < camera.chase_horizon_y() - 12:
        return None

    forward = Vec2.from_angle(ship_angle)
    right = forward.rotated(math.pi / 2.0)
    depth = center.depth
    scale = camera.focal_length / depth
    lateral_scale = scale * camera.chase_thrust_boost
    pitch = 0.48 + camera.chase_lift / camera.focal_length
    cx, cy = center.x, center.y

    screen_points: list[tuple[float, float]] = []
    for vert in asteroid.world_vertices():
        rel = vert - asteroid.pos
        ahead = rel.dot(forward)
        lateral = rel.dot(right)
        screen_points.append((cx + lateral * lateral_scale, cy - ahead * scale * pitch))

    if len(screen_points) < 3:
        return None

    display_scale = max(0.35, min(1.4, camera.focal_length / max(depth, 1.0)))
    return screen_points, display_scale, depth


def collect_chase_asteroid_sprites(
    asteroids: list[Asteroid],
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
) -> list[tuple[float, list[tuple[float, float]], Asteroid, float]]:
    sprites: list[tuple[float, list[tuple[float, float]], Asteroid, float]] = []
    for asteroid in asteroids:
        projected = chase_asteroid_screen_outline(asteroid, camera, ship_pos, ship_angle)
        if projected is None:
            continue
        screen_points, display_scale, depth = projected
        sprites.append((depth, screen_points, asteroid, display_scale))
    sprites.sort(key=lambda item: item[0])
    return sprites


def _draw_chase_rock_shadow(
    canvas: tk.Canvas,
    screen_points: list[tuple[float, float]],
    *,
    radius_hint: float,
    display_scale: float,
    depth_fade: float,
) -> None:
    cx = sum(x for x, _ in screen_points) / len(screen_points)
    cy = sum(y for _, y in screen_points) / len(screen_points)
    base = max(4.0, radius_hint * display_scale * 0.28)
    rx = base * 1.45
    ry = base * 0.42
    shadow_y = cy + radius_hint * display_scale * 0.42
    tone = palette.CHASE_ASTEROID_SHADOW if depth_fade < 0.35 else "#020306"
    canvas.create_oval(cx - rx, shadow_y - ry, cx + rx, shadow_y + ry, fill=tone, outline="")


def _draw_chase_motion_streak(
    canvas: tk.Canvas,
    asteroid: Asteroid,
    center_x: float,
    center_y: float,
    *,
    ship_angle: float,
    material_rim: str,
    display_scale: float,
) -> None:
    if asteroid.vel.length_sq() < 120.0:
        return
    forward = Vec2.from_angle(ship_angle)
    right = forward.rotated(math.pi / 2.0)
    drift = asteroid.vel.normalized()
    lateral = drift.dot(right)
    ahead = drift.dot(forward)
    streak = min(22.0, asteroid.vel.length() * 0.1) * max(0.65, display_scale)
    tail_x = center_x - lateral * streak
    tail_y = center_y + ahead * streak * 0.48
    canvas.create_line(tail_x, tail_y, center_x, center_y, fill=material_rim, width=1)


def draw_chase_asteroids(
    canvas: tk.Canvas,
    sprites: list[tuple[float, list[tuple[float, float]], Asteroid, float]],
    *,
    rig: LightRig,
    ship_angle: float = 0.0,
) -> None:
    base_material = material_for("asteroid", theme=rig.theme, view=rig.view)
    for _depth, screen_points, asteroid, display_scale in sprites:
        depth_fade = chase_depth_fade(_depth)
        material = depth_faded_material(base_material, depth_fade)
        radius_hint = asteroid.approximate_radius() * display_scale
        cx = sum(x for x, _ in screen_points) / len(screen_points)
        cy = sum(y for _, y in screen_points) / len(screen_points)

        _draw_chase_rock_shadow(
            canvas,
            screen_points,
            radius_hint=asteroid.approximate_radius(),
            display_scale=display_scale,
            depth_fade=depth_fade,
        )

        crater_cap = None
        if display_scale < 0.55:
            crater_cap = 1
        elif display_scale < 0.75:
            crater_cap = 2

        draw_illustrated_polygon(
            canvas,
            screen_points,
            rig=rig,
            material=material,
            seed=asteroid.seed,
            radius_hint=radius_hint,
            outline_width=max(1, min(2, int(1 + display_scale * 0.75))),
            crater_count=crater_cap,
        )
        _draw_chase_motion_streak(
            canvas,
            asteroid,
            cx,
            cy,
            ship_angle=ship_angle,
            material_rim=material.rim,
            display_scale=display_scale,
        )
