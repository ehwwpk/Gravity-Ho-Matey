from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Projectile
from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.chase_projectile_fx import _bolt_palette, tactical_bolt_style


def draw_tactical_projectile(
    canvas: tk.Canvas,
    projectile: Projectile,
    *,
    camera: ViewCamera,
    ship_pos: Vec2,
    hud_top: float,
    elapsed: float = 0.0,
) -> None:
    """Top-down bolt with doctrine-specific bloom, streak, and arming cues."""
    p = camera.world_to_screen(projectile.pos, ship_pos, 0.0)
    x, y = p.x, p.y + hud_top
    fill, tail_color, r = tactical_bolt_style(projectile)

    if projectile.hostile:
        draw_ground_fog_glow(canvas, x, y, r * 2.4, (palette.CHASE_BOLT_HOSTILE_GLOW, palette.CHASE_BOLT_HOSTILE_MID), pulse=0.0)
        canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline=palette.CHASE_BOLT_HOSTILE_CORE, width=1)
        vel = projectile.vel
        if vel.length_sq() > 1.0:
            tail = Vec2(x, y) - vel.normalized() * 16
            canvas.create_line(tail.x, tail.y, x, y, fill=tail_color, width=2)
        return

    track = projectile.weapon_track
    core, mid, tail, glow = _bolt_palette(projectile)
    vel = projectile.vel
    speed = vel.length()

    if track is WeaponTrack.EXPLOSIVE:
        pulse = 0.65 + 0.35 * math.sin(elapsed * 14.0)
        draw_ground_fog_glow(canvas, x, y, r * 3.2 * pulse, (glow, mid), pulse=elapsed * 6.0)
        canvas.create_oval(x - r * 1.35, y - r * 1.35, x + r * 1.35, y + r * 1.35, outline=core, width=2)
        canvas.create_oval(x - r, y - r, x + r, y + r, fill=mid, outline=core, width=1)
        canvas.create_oval(x - r * 0.35, y - r * 0.35, x + r * 0.35, y + r * 0.35, fill=core, outline="")
        if speed > 1.0:
            tail_len = 22
            tail = Vec2(x, y) - vel.normalized() * tail_len
            canvas.create_line(tail.x, tail.y, x, y, fill=tail, width=3)
            for i in range(3):
                frac = (i + 1) / 4.0
                ex = x - vel.normalized().x * tail_len * frac
                ey = y - vel.normalized().y * tail_len * frac
                er = 1.5 + i * 0.6
                canvas.create_oval(ex - er, ey - er, ex + er, ey + er, fill=tail_color if i % 2 else core, outline="")
        return

    if track is WeaponTrack.LASER:
        draw_ground_fog_glow(canvas, x, y, r * 2.8, (glow, mid), pulse=0.0)
        canvas.create_oval(x - r * 1.2, y - r * 1.2, x + r * 1.2, y + r * 1.2, outline=palette.WEAPON_LASER_GLOW, width=1)
        canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline=core, width=1)
        if speed > 1.0:
            streak = 28 if projectile.pierce_remaining > 0 else 20
            tail = Vec2(x, y) - vel.normalized() * streak
            canvas.create_line(tail.x, tail.y, x, y, fill=core, width=2)
            canvas.create_line(tail.x, tail.y, x, y, fill=mid, width=1)
            if projectile.pierce_remaining > 0:
                canvas.create_line(tail.x, tail.y, x, y, fill=palette.WEAPON_LASER_CORE, width=1, dash=(3, 2))
        return

    if track is WeaponTrack.SHOTGUN:
        draw_ground_fog_glow(canvas, x, y, r * 2.0, (glow, mid), pulse=0.0)
        canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline=core, width=1)
        if speed > 1.0:
            tail = Vec2(x, y) - vel.normalized() * 14
            canvas.create_line(tail.x, tail.y, x, y, fill=tail_color, width=2)
            side = vel.normalized().rotated(math.pi / 2.0) * 3.5
            canvas.create_line(tail.x + side.x, tail.y + side.y, x + side.x * 0.3, y + side.y * 0.3, fill=core, width=1)
        return

    draw_ground_fog_glow(canvas, x, y, r * 1.8, (glow, mid), pulse=0.0)
    canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline=fill, width=1)
    if speed > 1.0:
        tail = Vec2(x, y) - vel.normalized() * 14
        canvas.create_line(tail.x, tail.y, x, y, fill=tail_color, width=1)
