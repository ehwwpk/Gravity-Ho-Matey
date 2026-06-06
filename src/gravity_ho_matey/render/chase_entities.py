from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Beacon
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CHASE_BEACON_SCALE_FLOOR, CHASE_BEACON_VISUAL_BOOST
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.entity_viz import draw_beacon_glyph, draw_gate_glyph


def draw_chase_beacon(
    canvas: tk.Canvas,
    pos: Vec2,
    beacon: Beacon,
    *,
    elapsed: float,
    depth_scale: float = 1.0,
) -> None:
    scale = max(
        CHASE_BEACON_SCALE_FLOOR,
        min(1.42, depth_scale * CHASE_BEACON_VISUAL_BOOST),
    )
    if not beacon.collected:
        pulse = elapsed * 2.0
        glow_r = 19.0 * scale
        draw_ground_fog_glow(
            canvas,
            pos.x,
            pos.y + 4,
            glow_r,
            ("#0a2818", "#143828"),
            pulse=pulse,
        )
    draw_beacon_glyph(canvas, pos.x, pos.y, collected=beacon.collected, scale=scale, show_ring=True)


def draw_chase_gate(
    canvas: tk.Canvas,
    pos: Vec2,
    *,
    unlocked: bool,
    solar: bool,
    gate_size: float,
    depth_scale: float = 1.0,
) -> None:
    scale = max(0.58, min(1.12, depth_scale * 1.08))
    if solar:
        draw_ground_fog_glow(
            canvas,
            pos.x,
            pos.y + 4,
            22.0 * scale,
            ("#0a1830", "#1a3050"),
            pulse=0.0,
        )
    draw_gate_glyph(canvas, pos.x, pos.y, size=gate_size, unlocked=unlocked, solar=solar, scale=scale)


def draw_chase_enemy(canvas: tk.Canvas, pos: Vec2, *, radius: float, facing: float, scale: float) -> None:
    r = min(radius * scale, 28.0)
    draw_ground_fog_glow(canvas, pos.x, pos.y + 4, r * 1.4, palette.CHASE_ENEMY_FOG[:2], pulse=0.0)
    canvas.create_oval(pos.x - r, pos.y - r * 0.55, pos.x + r, pos.y + r * 0.35, fill=palette.ENEMY, outline=palette.ENEMY_EDGE, width=2)
    spike = pos + Vec2.from_angle(facing) * (r + 4)
    canvas.create_line(pos.x, pos.y, spike.x, spike.y, fill=palette.ENEMY_EDGE, width=2)


def draw_chase_pickup(canvas: tk.Canvas, pos: Vec2, kind: PowerUpKind) -> None:
    color = {
        PowerUpKind.THRUST_BOOST: palette.PICKUP_THRUST,
        PowerUpKind.RAPID_FIRE: palette.PICKUP_RAPID,
        PowerUpKind.STABILIZER: palette.PICKUP_STABILIZER,
    }.get(kind, palette.BEACON)
    draw_ground_fog_glow(canvas, pos.x, pos.y + 4, 10, (color, color), pulse=0.0)
    canvas.create_polygon(pos.x, pos.y - 8, pos.x + 7, pos.y, pos.x, pos.y + 8, pos.x - 7, pos.y, fill=color, outline="#fff")


def draw_chase_projectile(canvas: tk.Canvas, pos: Vec2, vel: Vec2, *, hostile: bool = False) -> None:
    color = palette.HOSTILE_PROJECTILE if hostile else palette.PROJECTILE
    r = 3
    canvas.create_oval(pos.x - r, pos.y - r, pos.x + r, pos.y + r, fill=color, outline="")
    if vel.length_sq() > 1.0:
        tail = pos - vel.normalized() * (16 if hostile else 14)
        canvas.create_line(tail.x, tail.y, pos.x, pos.y, fill=color, width=2)
