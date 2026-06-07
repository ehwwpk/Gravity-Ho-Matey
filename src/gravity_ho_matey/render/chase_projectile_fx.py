from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Projectile
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow


def _screen_streak(
    projectile: Projectile,
    head: Vec2,
    *,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
) -> tuple[float, float, float, float, float]:
    """Return head/tail screen coords and unit direction (ux, uy)."""
    speed = projectile.vel.length()
    if speed < 1.0:
        return head.x, head.y, head.x, head.y, 0.0

    streak_len = min(56.0, 14.0 + speed * 0.16)
    if projectile.hostile:
        streak_len = min(62.0, 16.0 + speed * 0.18)

    tail_world = projectile.pos - projectile.vel.normalized() * streak_len
    tail_pt = camera.world_to_screen(tail_world, ship_pos, ship_angle)
    dx = head.x - tail_pt.x
    dy = head.y - tail_pt.y
    length = math.hypot(dx, dy)
    if length < 2.0:
        return head.x, head.y, head.x, head.y, length
    return head.x, head.y, tail_pt.x, tail_pt.y, length


def _draw_tapered_bolt(
    canvas: tk.Canvas,
    *,
    hx: float,
    hy: float,
    tx: float,
    ty: float,
    length: float,
    core: str,
    mid: str,
    tail: str,
    glow: str,
    hostile: bool,
) -> None:
    if length < 2.0:
        canvas.create_oval(hx - 2, hy - 2, hx + 2, hy + 2, fill=core, outline="")
        return

    ux = (hx - tx) / length
    uy = (hy - ty) / length
    px, py = -uy, ux

    # Volumetric bloom — ground-hugging so bolts read on the chase floor plane.
    bloom_r = 10.0 if hostile else 8.0
    draw_ground_fog_glow(canvas, hx, hy + 2, bloom_r, (glow, mid), pulse=0.0)

    # Layered energy streak (wide → narrow, tail → head).
    layers: tuple[tuple[float, str, int], ...]
    if hostile:
        layers = (
            (0.92, tail, 5),
            (0.72, mid, 3),
            (0.48, mid, 2),
            (0.22, core, 2),
        )
    else:
        layers = (
            (0.88, tail, 4),
            (0.62, mid, 2),
            (0.34, mid, 2),
            (0.14, core, 1),
        )

    for frac, color, width in layers:
        lx = hx - ux * length * frac
        ly = hy - uy * length * frac
        canvas.create_line(lx, ly, hx, hy, fill=color, width=width, capstyle=tk.ROUND)

    # Ion flicker side wisps (player) or plasma licks (hostile).
    wisp_count = 3 if hostile else 2
    for i in range(wisp_count):
        t = (i + 1) / (wisp_count + 1)
        wx = hx - ux * length * t
        wy = hy - uy * length * t
        side = (4.0 + i * 2.5) * (1.0 if i % 2 else -1.0)
        wlen = length * 0.08
        canvas.create_line(
            wx,
            wy,
            wx + px * side * 0.35 - ux * wlen,
            wy + py * side * 0.2 - uy * wlen,
            fill=mid if hostile else tail,
            width=1,
        )

    # Hot head — white core + corona ring.
    head_r = 4.5 if hostile else 3.8
    canvas.create_oval(hx - head_r * 1.5, hy - head_r, hx + head_r * 1.5, hy + head_r * 0.65, fill="", outline=mid, width=1)
    canvas.create_oval(hx - head_r, hy - head_r * 0.75, hx + head_r, hy + head_r * 0.55, fill=core, outline=mid, width=1)
    canvas.create_oval(hx - 1.6, hy - 1.2, hx + 1.6, hy + 1.0, fill="#ffffff", outline="")


def draw_chase_projectile(
    canvas: tk.Canvas,
    screen_pos: Vec2,
    projectile: Projectile,
    *,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
) -> None:
    """Perspective-correct energy bolt — streak aligned via world→screen tail projection."""
    hx, hy, tx, ty, length = _screen_streak(
        projectile,
        screen_pos,
        camera=camera,
        ship_pos=ship_pos,
        ship_angle=ship_angle,
    )

    if projectile.hostile:
        _draw_tapered_bolt(
            canvas,
            hx=hx,
            hy=hy,
            tx=tx,
            ty=ty,
            length=length,
            core=palette.CHASE_BOLT_HOSTILE_CORE,
            mid=palette.CHASE_BOLT_HOSTILE_MID,
            tail=palette.CHASE_BOLT_HOSTILE_TAIL,
            glow=palette.CHASE_BOLT_HOSTILE_GLOW,
            hostile=True,
        )
    else:
        _draw_tapered_bolt(
            canvas,
            hx=hx,
            hy=hy,
            tx=tx,
            ty=ty,
            length=length,
            core=palette.CHASE_BOLT_PLAYER_CORE,
            mid=palette.CHASE_BOLT_PLAYER_MID,
            tail=palette.CHASE_BOLT_PLAYER_TAIL,
            glow=palette.CHASE_BOLT_PLAYER_GLOW,
            hostile=False,
        )


def draw_mirror_hostile_bolt(
    canvas: tk.Canvas,
    px: float,
    py: float,
    vel: Vec2,
    ship_angle: float,
    *,
    draw_size: float,
) -> None:
    """Compact rear-mirror hostile bolt — chevron tail + hot core."""
    bloom = max(5.0, draw_size + 2.0)
    draw_ground_fog_glow(
        canvas,
        px,
        py,
        bloom,
        (palette.CHASE_BOLT_HOSTILE_GLOW, palette.CHASE_BOLT_HOSTILE_MID),
        pulse=0.0,
    )
    r = max(3.0, draw_size * 0.55)
    canvas.create_oval(px - r, py - r, px + r, py + r, fill=palette.CHASE_BOLT_HOSTILE_MID, outline=palette.CHASE_BOLT_HOSTILE_CORE, width=1)
    canvas.create_oval(px - 1.5, py - 1.5, px + 1.5, py + 1.5, fill="#ffffff", outline="")
    if vel.length_sq() >= 64.0:
        forward = Vec2.from_angle(ship_angle)
        right = forward.rotated(math.pi / 2.0)
        lat = vel.dot(right)
        mag = min(10.0, vel.length() * 0.04)
        tip_x = px + right.x * lat * 0.015
        tip_y = py + right.y * lat * 0.015 - forward.y * mag * 0.02
        canvas.create_line(px, py, tip_x, tip_y, fill=palette.CHASE_BOLT_HOSTILE_TAIL, width=2)
