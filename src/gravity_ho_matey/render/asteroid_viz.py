from __future__ import annotations

import math

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_shape import crater_offsets
from gravity_ho_matey.gameplay.entities import Asteroid
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera


def _asteroid_colors(*, solar: bool) -> tuple[str, str, str]:
    if solar:
        return palette.ASTEROID, palette.ASTEROID_EDGE, palette.ASTEROID_CRATER
    return palette.HOLO_ASTEROID_FILL, palette.HOLO_ASTEROID_EDGE, palette.ASTEROID_CRATER


def _flatten_screen_points(points: list[tuple[float, float]]) -> list[float]:
    flat: list[float] = []
    for x, y in points:
        flat.extend((x, y))
    return flat


def draw_asteroid_polygon(
    canvas: tk.Canvas,
    screen_points: list[tuple[float, float]],
    *,
    fill: str,
    edge: str,
    crater: str,
    seed: int,
    radius_hint: float,
    outline_width: int = 2,
) -> None:
    if len(screen_points) < 3:
        return
    flat = _flatten_screen_points(screen_points)
    canvas.create_polygon(*flat, fill=fill, outline=edge, width=outline_width)
    cx = sum(p[0] for p in screen_points) / len(screen_points)
    cy = sum(p[1] for p in screen_points) / len(screen_points)
    crater_count = 1 + (seed % 3)
    scale = max(0.55, min(1.0, radius_hint / 48.0))
    for lx, ly, lr in crater_offsets(seed, crater_count, radius_hint):
        canvas.create_oval(
            cx + lx * scale - lr,
            cy + ly * scale - lr,
            cx + lx * scale + lr,
            cy + ly * scale + lr,
            fill=crater,
            outline="",
        )


def draw_tactical_asteroid(
    canvas: tk.Canvas,
    asteroid: Asteroid,
    camera: ViewCamera,
    *,
    hud_top: float,
    solar: bool,
    ship_pos: Vec2 | None = None,
    ship_angle: float = 0.0,
) -> None:
    anchor = ship_pos if ship_pos is not None else Vec2()
    fill, edge, crater = _asteroid_colors(solar=solar)
    screen_points: list[tuple[float, float]] = []
    for vert in asteroid.world_vertices():
        p = camera.world_to_screen(vert, anchor, ship_angle)
        screen_points.append((p.x, p.y + hud_top))
    draw_asteroid_polygon(
        canvas,
        screen_points,
        fill=fill,
        edge=edge,
        crater=crater,
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
            fill=edge,
            width=1,
        )


def draw_map_asteroid_glyph(
    canvas: tk.Canvas,
    center: Vec2,
    asteroid: Asteroid,
    *,
    scale: float,
    solar: bool,
) -> None:
    fill, edge, crater = _asteroid_colors(solar=solar)
    points: list[tuple[float, float]] = []
    c = math.cos(asteroid.angle)
    s = math.sin(asteroid.angle)
    for v in asteroid.local_verts:
        lx = v.x * c - v.y * s
        ly = v.x * s + v.y * c
        points.append((center.x + lx * scale, center.y + ly * scale))
    draw_asteroid_polygon(
        canvas,
        points,
        fill=fill,
        edge=edge,
        crater=crater,
        seed=asteroid.seed,
        radius_hint=asteroid.approximate_radius() * scale,
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
        avg_depth = center.depth
        sprites.append((avg_depth, screen_points, asteroid))
    sprites.sort(key=lambda item: item[0])
    return sprites


def draw_chase_asteroids(
    canvas: tk.Canvas,
    sprites: list[tuple[float, list[tuple[float, float]], Asteroid]],
    *,
    solar: bool,
    urgency: float = 0.0,
    focal_length: float,
) -> None:
    fill, edge, crater = _asteroid_colors(solar=solar)
    for depth, screen_points, asteroid in sprites:
        scale = max(0.35, min(1.4, focal_length / max(depth, 1.0)))
        width = max(1, int(1 + scale * 2.2))
        edge_color = edge
        if urgency > 0.12:
            edge_color = palette.HELM_THREAT_HEAVY if urgency > 0.45 else palette.HELM_THREAT_LETHAL
            width += 1
        draw_asteroid_polygon(
            canvas,
            screen_points,
            fill=fill,
            edge=edge_color,
            crater=crater,
            seed=asteroid.seed,
            radius_hint=asteroid.approximate_radius() * scale,
            outline_width=width,
        )
