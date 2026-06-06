from __future__ import annotations

import math

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Asteroid
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.lighting import LightRig, material_for
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
    material = material_for("asteroid", theme=rig.theme)
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
    material = material_for("asteroid", theme=rig.theme)
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


def collect_chase_asteroid_sprites(
    asteroids: list[Asteroid],
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
) -> list[tuple[float, list[tuple[float, float]], Asteroid]]:
    horizon = camera.chase_horizon_y()
    sprites: list[tuple[float, list[tuple[float, float]], Asteroid]] = []
    for asteroid in asteroids:
        center = camera.world_to_screen(asteroid.pos, ship_pos, ship_angle)
        if center.y < horizon - 12:
            continue
        if center.depth < camera.min_depth:
            continue
        screen_points: list[tuple[float, float]] = []
        for vert in asteroid.world_vertices():
            p = camera.world_to_screen(vert, ship_pos, ship_angle)
            if not p.visible and len(screen_points) == 0:
                continue
            screen_points.append((p.x, p.y))
        if len(screen_points) < 3:
            continue
        sprites.append((center.depth, screen_points, asteroid))
    sprites.sort(key=lambda item: item[0])
    return sprites


def draw_chase_asteroids(
    canvas: tk.Canvas,
    sprites: list[tuple[float, list[tuple[float, float]], Asteroid]],
    *,
    rig: LightRig,
    urgency: float = 0.0,
    focal_length: float,
) -> None:
    material = material_for("asteroid", theme=rig.theme)
    for depth, screen_points, asteroid in sprites:
        scale = max(0.35, min(1.4, focal_length / max(depth, 1.0)))
        width = max(1, int(1 + scale * 2.2))
        edge_override: str | None = None
        if urgency > 0.12:
            edge_override = palette.HELM_HUD_ACCENT if urgency > 0.45 else palette.HOLO_ASTEROID_EDGE
            width += 1
        draw_illustrated_polygon(
            canvas,
            screen_points,
            rig=rig,
            material=material,
            seed=asteroid.seed,
            radius_hint=asteroid.approximate_radius() * scale,
            outline_width=width,
            edge_override=edge_override,
        )
