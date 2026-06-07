from __future__ import annotations

from collections.abc import Callable

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.explosions import Explosion, ExplosionKind, ExplosionParticle
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ProjectedPoint


def draw_explosions(
    canvas: tk.Canvas,
    explosions: list[Explosion],
    *,
    offset: tuple[float, float] = (0.0, 0.0),
    center: Vec2 | None = None,
    project: Callable[[Vec2], ProjectedPoint] | None = None,
) -> None:
    for explosion in explosions:
        _draw_single(canvas, explosion, offset=offset, center=center, project=project)


def _screen_pos(
    world_pos: Vec2,
    *,
    offset: tuple[float, float],
    center: Vec2 | None,
    project: Callable[[Vec2], ProjectedPoint] | None,
) -> Vec2:
    if project is not None:
        projected = project(world_pos)
        return Vec2(projected.x + offset[0], projected.y + offset[1])
    if center is not None:
        return Vec2(world_pos.x - center.x + offset[0], world_pos.y - center.y + offset[1])
    return Vec2(world_pos.x + offset[0], world_pos.y + offset[1])


def _particle_fill(particle: ExplosionParticle) -> str:
    t = max(0.0, particle.life / particle.max_life)
    if particle.particle_type == "spark":
        return "#fff8dc" if t > 0.45 else "#ffd27a"
    if particle.particle_type == "ember":
        if t > 0.55:
            return "#ff9a4a"
        if t > 0.25:
            return "#ff5c38"
        return "#8a2818"
    if t > 0.5:
        return "#6a4038"
    return "#3a2820"


def _ring_color(kind: ExplosionKind, life_ratio: float) -> str:
    if life_ratio <= 0.0:
        return palette.HUD_FRAME
    if kind is ExplosionKind.PROJECTILE_IMPACT:
        return "#ffe8a8" if life_ratio > 0.4 else "#ffb347"
    if kind is ExplosionKind.ENEMY_DESTROYED:
        return "#ffd27a" if life_ratio > 0.35 else "#ff6b3a"
    if kind is ExplosionKind.SHIP_STRUCK:
        return "#fff0b5" if life_ratio > 0.35 else "#ff8a4a"
    if kind is ExplosionKind.ASTEROID_DESTROYED:
        return "#c8b8a0" if life_ratio > 0.35 else "#8a7060"
    if kind is ExplosionKind.ASTEROID_BREAKUP:
        return "#ffd080" if life_ratio > 0.35 else "#c86830"
    return "#ffffff" if life_ratio > 0.45 else "#ff4a3a"


def _draw_single(
    canvas: tk.Canvas,
    explosion: Explosion,
    *,
    offset: tuple[float, float],
    center: Vec2 | None,
    project: Callable[[Vec2], ProjectedPoint] | None,
) -> None:
    pos = _screen_pos(explosion.pos, offset=offset, center=center, project=project)

    if explosion.flash_age < explosion.flash_life:
        flash_t = 1.0 - explosion.flash_age / explosion.flash_life
        flash_r = 6.0 + flash_t * (explosion.ring_max * 0.35)
        canvas.create_oval(
            pos.x - flash_r,
            pos.y - flash_r,
            pos.x + flash_r,
            pos.y + flash_r,
            fill="#fff8e8" if flash_t > 0.35 else "",
            outline="#fff2c8" if flash_t <= 0.35 else "",
            width=1,
        )

    if explosion.ring_age < explosion.ring_life:
        ring_t = 1.0 - explosion.ring_age / explosion.ring_life
        r = explosion.ring_radius
        color = _ring_color(explosion.kind, ring_t)
        canvas.create_oval(pos.x - r, pos.y - r, pos.x + r, pos.y + r, outline=color, width=2)
        if ring_t > 0.45:
            inner = r * 0.55
            canvas.create_oval(
                pos.x - inner,
                pos.y - inner,
                pos.x + inner,
                pos.y + inner,
                outline=color,
                width=1,
            )

    for particle in explosion.particles:
        fill = _particle_fill(particle)
        p = _screen_pos(particle.pos, offset=offset, center=center, project=project)
        size = particle.size
        canvas.create_oval(p.x - size, p.y - size, p.x + size, p.y + size, fill=fill, outline="")
        if particle.particle_type == "spark" and particle.life / particle.max_life > 0.35:
            tail = p - particle.vel.normalized() * (size * 2.8)
            canvas.create_line(tail.x, tail.y, p.x, p.y, fill=fill, width=1)
