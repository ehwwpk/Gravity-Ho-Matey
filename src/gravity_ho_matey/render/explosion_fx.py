from __future__ import annotations

import math
from collections.abc import Callable

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.explosions import Explosion, ExplosionKind, ExplosionParticle
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ProjectedPoint
from gravity_ho_matey.render.lighting import lerp_hex


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


def _particle_fill(particle: ExplosionParticle, *, kind: ExplosionKind | None = None) -> str:
    t = max(0.0, particle.life / particle.max_life)
    if kind is ExplosionKind.NOVA_BLAST:
        if particle.particle_type == "spark":
            return palette.WEAPON_EXPLOSIVE_CORE if t > 0.4 else palette.WEAPON_EXPLOSIVE_MID
        if t > 0.5:
            return palette.WEAPON_EXPLOSIVE_MID
        if t > 0.2:
            return palette.WEAPON_EXPLOSIVE_TAIL
        return palette.WEAPON_EXPLOSIVE_GLOW
    if kind is ExplosionKind.LASER_PIERCE:
        return palette.WEAPON_LASER_CORE if t > 0.35 else palette.WEAPON_LASER_MID
    if kind is ExplosionKind.REACTOR_BURST:
        if particle.particle_type == "spark":
            return "#fff0c0" if t > 0.4 else "#ffd080"
        if t > 0.5:
            return "#ffb848"
        if t > 0.25:
            return "#ff7020"
        return "#8a3010"
    if kind is ExplosionKind.JEWEL_COLLECT:
        if particle.particle_type == "gem":
            return palette.JEWEL_HIGHLIGHT if t > 0.45 else palette.JEWEL_CORE
        return palette.JEWEL_EDGE if t > 0.35 else palette.JEWEL_GLOW
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
    if kind is ExplosionKind.JEWEL_COLLECT:
        return palette.JEWEL_GLOW if life_ratio > 0.35 else palette.JEWEL_EDGE
    if kind is ExplosionKind.NOVA_BLAST:
        return palette.WEAPON_EXPLOSIVE_CORE if life_ratio > 0.4 else palette.WEAPON_EXPLOSIVE_MID if life_ratio > 0.15 else palette.WEAPON_EXPLOSIVE_TAIL
    if kind is ExplosionKind.LASER_PIERCE:
        return palette.WEAPON_LASER_CORE if life_ratio > 0.35 else palette.WEAPON_LASER_GLOW
    if kind is ExplosionKind.REACTOR_BURST:
        return lerp_hex("#ffd080", "#ff6020", 1.0 - life_ratio)
    return "#ffffff" if life_ratio > 0.45 else "#ff4a3a"


def _aoe_screen_radius(
    explosion: Explosion,
    center: Vec2,
    *,
    offset: tuple[float, float],
    center_mode: Vec2 | None,
    project: Callable[[Vec2], ProjectedPoint] | None,
) -> float:
    if explosion.aoe_radius_world <= 0.0:
        return 0.0
    edge_world = Vec2(explosion.pos.x + explosion.aoe_radius_world, explosion.pos.y)
    edge = _screen_pos(edge_world, offset=offset, center=center_mode, project=project)
    return max(8.0, math.hypot(edge.x - center.x, edge.y - center.y))


def _draw_nova_aoe_rings(
    canvas: tk.Canvas,
    pos: Vec2,
    *,
    aoe_r: float,
    ring_t: float,
) -> None:
    if aoe_r <= 0.0 or ring_t <= 0.0:
        return
    expand = min(1.0, ring_t * 1.15)
    outer = aoe_r * expand
    inner = aoe_r * expand * 0.62
    color_outer = palette.WEAPON_EXPLOSIVE_MID if ring_t > 0.25 else palette.WEAPON_EXPLOSIVE_TAIL
    color_inner = palette.WEAPON_EXPLOSIVE_CORE if ring_t > 0.35 else palette.WEAPON_EXPLOSIVE_MID
    canvas.create_oval(
        pos.x - outer, pos.y - outer, pos.x + outer, pos.y + outer,
        outline=color_outer, width=3 if ring_t > 0.4 else 2, dash=(6, 4) if ring_t > 0.55 else None,
    )
    canvas.create_oval(
        pos.x - inner, pos.y - inner, pos.x + inner, pos.y + inner,
        outline=color_inner, width=2,
    )
    fill_r = inner * 0.45
    canvas.create_oval(
        pos.x - fill_r, pos.y - fill_r, pos.x + fill_r, pos.y + fill_r,
        fill=lerp_hex(palette.WEAPON_EXPLOSIVE_GLOW, "#000000", 0.55) if ring_t > 0.2 else "",
        outline="",
    )


def _draw_single(
    canvas: tk.Canvas,
    explosion: Explosion,
    *,
    offset: tuple[float, float],
    center: Vec2 | None,
    project: Callable[[Vec2], ProjectedPoint] | None,
) -> None:
    pos = _screen_pos(explosion.pos, offset=offset, center=center, project=project)
    aoe_r = _aoe_screen_radius(explosion, pos, offset=offset, center_mode=center, project=project)

    if explosion.flash_age < explosion.flash_life:
        flash_t = 1.0 - explosion.flash_age / explosion.flash_life
        flash_r = 6.0 + flash_t * (explosion.ring_max * 0.35)
        if explosion.kind is ExplosionKind.NOVA_BLAST:
            flash_r = max(flash_r, aoe_r * 0.25 * flash_t)
            flash_fill = palette.WEAPON_EXPLOSIVE_CORE
            flash_outline = palette.WEAPON_EXPLOSIVE_MID
        elif explosion.kind is ExplosionKind.LASER_PIERCE:
            flash_fill = palette.WEAPON_LASER_CORE
            flash_outline = palette.WEAPON_LASER_MID
        elif explosion.kind is ExplosionKind.JEWEL_COLLECT:
            flash_fill = palette.JEWEL_HIGHLIGHT
            flash_outline = palette.JEWEL_GLOW
        else:
            flash_fill = "#fff8e8"
            flash_outline = "#fff2c8"
        canvas.create_oval(
            pos.x - flash_r,
            pos.y - flash_r,
            pos.x + flash_r,
            pos.y + flash_r,
            fill=flash_fill if flash_t > 0.35 else "",
            outline=flash_outline if flash_t <= 0.35 else "",
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
        if explosion.kind is ExplosionKind.NOVA_BLAST:
            _draw_nova_aoe_rings(canvas, pos, aoe_r=aoe_r, ring_t=ring_t)
        elif explosion.kind is ExplosionKind.LASER_PIERCE and ring_t > 0.3:
            canvas.create_line(pos.x - r * 1.4, pos.y, pos.x + r * 1.4, pos.y, fill=color, width=2)
            canvas.create_line(pos.x, pos.y - r * 0.8, pos.x, pos.y + r * 0.8, fill=color, width=1)

    for particle in explosion.particles:
        fill = _particle_fill(particle, kind=explosion.kind)
        p = _screen_pos(particle.pos, offset=offset, center=center, project=project)
        size = particle.size
        if explosion.kind is ExplosionKind.JEWEL_COLLECT and particle.particle_type == "gem":
            _draw_jewel_spark(canvas, p.x, p.y, size, fill)
        else:
            canvas.create_oval(p.x - size, p.y - size, p.x + size, p.y + size, fill=fill, outline="")
        if particle.particle_type == "spark" and particle.life / particle.max_life > 0.35:
            tail = p - particle.vel.normalized() * (size * 2.8)
            canvas.create_line(tail.x, tail.y, p.x, p.y, fill=fill, width=1)


def _draw_jewel_spark(canvas: tk.Canvas, x: float, y: float, size: float, fill: str) -> None:
    arm = size * 1.6
    canvas.create_line(x - arm, y, x + arm, y, fill=fill, width=1)
    canvas.create_line(x, y - arm, x, y + arm, fill=fill, width=1)
    canvas.create_oval(x - size, y - size, x + size, y + size, fill=fill, outline="")
