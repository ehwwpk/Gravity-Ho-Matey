from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Beacon
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow


def draw_chase_beacon(canvas: tk.Canvas, pos: Vec2, beacon: Beacon, *, elapsed: float) -> None:
    color = palette.BEACON_COLLECTED if beacon.collected else palette.CHASE_BEACON_PILLAR
    if not beacon.collected:
        pulse = elapsed * 2.0
        draw_ground_fog_glow(canvas, pos.x, pos.y + 6, 16, ("#0a3028", "#1a5048"), pulse=pulse)
    canvas.create_line(pos.x, pos.y + 4, pos.x, pos.y - 14, fill=color, width=2)
    canvas.create_polygon(
        pos.x,
        pos.y - 18,
        pos.x + 6,
        pos.y - 8,
        pos.x,
        pos.y - 4,
        pos.x - 6,
        pos.y - 8,
        fill=color,
        outline="#dff",
    )
    if not beacon.collected:
        canvas.create_oval(pos.x - 8, pos.y - 2, pos.x + 8, pos.y + 6, outline=color, width=1)


def draw_chase_gate(canvas: tk.Canvas, pos: Vec2, *, unlocked: bool, solar: bool) -> None:
    color = palette.GATE_OPEN if unlocked else palette.GATE_LOCKED
    if solar:
        draw_ground_fog_glow(canvas, pos.x, pos.y + 4, 24, ("#0a1830", "#1a3050"), pulse=0.0)
    canvas.create_arc(pos.x - 20, pos.y - 16, pos.x + 20, pos.y + 16, start=200, extent=140, style="arc", outline=color, width=3)
    canvas.create_line(pos.x - 20, pos.y + 12, pos.x + 20, pos.y + 12, fill=color, width=2)
    if unlocked or solar:
        tag = ("WORMHOLE" if unlocked else "SEALED") if solar else ("OPEN" if unlocked else "LOCK")
        canvas.create_text(pos.x, pos.y - 2, text=tag, fill=color, font=("Courier", 7, "bold"))


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


def draw_chase_projectile(canvas: tk.Canvas, pos: Vec2, vel: Vec2) -> None:
    canvas.create_oval(pos.x - 3, pos.y - 3, pos.x + 3, pos.y + 3, fill=palette.PROJECTILE, outline="")
    if vel.length_sq() > 1.0:
        tail = pos - vel.normalized() * 14
        canvas.create_line(tail.x, tail.y, pos.x, pos.y, fill=palette.PROJECTILE, width=2)
