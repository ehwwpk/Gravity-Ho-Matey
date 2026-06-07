from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera


def draw_chase_sky(canvas: tk.Canvas, camera: ViewCamera, world: GameWorld) -> None:
    """Gradient sky band + parallax starfield."""
    horizon = camera.chase_horizon_y()
    top = camera.play_hud_top
    width = camera.viewport_width
    solar = world.config.level_theme == "solar"
    drift = world.config.level_theme == "drift"
    deep_space = solar or drift
    sky_top = "#020408" if deep_space else "#040810"
    sky_horizon = "#0a1830" if deep_space else "#081420"
    steps = 8
    band = max(1.0, (horizon - top) / steps)
    for i in range(steps):
        t = i / max(1, steps - 1)
        y0 = top + band * i
        y1 = top + band * (i + 1)
        color = _lerp_color(sky_top, sky_horizon, t)
        canvas.create_rectangle(0, y0, width, y1, fill=color, outline="")
    _draw_parallax_stars(canvas, camera, world, horizon)


def draw_chase_floor_gradient(canvas: tk.Canvas, camera: ViewCamera) -> None:
    horizon = camera.chase_horizon_y()
    bottom = camera.viewport_height
    width = camera.viewport_width
    steps = 6
    band = max(1.0, (bottom - horizon) / steps)
    for i in range(steps):
        t = i / max(1, steps - 1)
        y0 = horizon + band * i
        y1 = horizon + band * (i + 1)
        color = _lerp_color(palette.CHASE_FLOOR_TOP, palette.CHASE_FLOOR_BOTTOM, t)
        canvas.create_rectangle(0, y0, width, y1, fill=color, outline="")


def draw_fog_glow(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    radius: float,
    colors: tuple[str, ...],
    *,
    pulse: float = 0.0,
) -> None:
    """Layered concentric ovals simulating volumetric fog (Tk-safe, no alpha)."""
    breathe = 1.0 + math.sin(pulse) * 0.08
    for i, color in enumerate(colors):
        frac = (i + 1) / len(colors)
        r = radius * frac * breathe
        canvas.create_oval(cx - r, cy - r * 0.72, cx + r, cy + r * 0.72, fill=color, outline="")


def draw_ground_fog_glow(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    radius: float,
    colors: tuple[str, ...],
    *,
    pulse: float = 0.0,
) -> None:
    """Floor-hugging well glow — squashed ellipses anchored on the grid plane."""
    breathe = 1.0 + math.sin(pulse) * 0.06
    base_y = cy + radius * 0.08
    for i, color in enumerate(colors):
        frac = (i + 1) / len(colors)
        r = radius * frac * breathe
        canvas.create_oval(cx - r, base_y - r * 0.28, cx + r, base_y + r * 0.1, fill=color, outline="")


def draw_speed_streaks(
    canvas: tk.Canvas,
    camera: ViewCamera,
    world: GameWorld,
    *,
    anchor_x: float,
    anchor_y: float,
    ship_pos: Vec2,
    ship_angle: float,
) -> None:
    speed = world.ship.vel.length()
    if speed < 38.0:
        return
    vel = world.ship.vel
    tail_world = ship_pos - vel.normalized() * min(140.0, speed * 0.55)
    tail = camera.world_to_screen(tail_world, ship_pos, ship_angle)
    dx = anchor_x - tail.x
    dy = anchor_y - tail.y
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return
    ux, uy = dx / length, dy / length
    px, py = -uy, ux

    thrusting = world.ship.boost_flash > 0.0
    count = min(18, int(6 + speed / 22.0))
    color = palette.CHASE_SPEED_STREAK_BOOST if thrusting else palette.CHASE_SPEED_STREAK
    horizon = camera.chase_horizon_y()
    streak_len = min(90.0, 16.0 + speed * 0.16)

    for i in range(count):
        t = (i + 1) / (count + 1)
        lateral = ((i * 53) % 27 - 13) * (1.2 - t * 0.4)
        sx = anchor_x - ux * (40 + t * 120) + px * lateral
        sy = anchor_y - uy * (40 + t * 120) + py * lateral * 0.35
        if sy < horizon + 8:
            continue
        ex = sx + ux * streak_len * (0.5 + t * 0.5)
        ey = sy + uy * streak_len * (0.5 + t * 0.5)
        canvas.create_line(sx, sy, ex, ey, fill=color, width=2 if thrusting else 1)


def draw_engine_bloom(
    canvas: tk.Canvas,
    anchor_x: float,
    anchor_y: float,
    *,
    boost_energy: float,
    thrusting: bool,
) -> None:
    for i, frac in enumerate((1.0, 0.72, 0.48)):
        r = 14 + i * 8
        color = palette.CHASE_ENGINE_CORE if i == 0 else palette.CHASE_ENGINE_GLOW
        canvas.create_oval(anchor_x - r, anchor_y - r * 0.4, anchor_x + r, anchor_y + r * 0.9, fill="", outline=color, width=2 - i)
    if thrusting and boost_energy > 0.02:
        flame_y = anchor_y + 22
        canvas.create_line(anchor_x, anchor_y + 8, anchor_x, flame_y, fill="#ff7a4a", width=4)
        canvas.create_oval(anchor_x - 8, flame_y - 4, anchor_x + 8, flame_y + 10, fill=palette.CHASE_ENGINE_GLOW, outline="")


def draw_speed_vignette(canvas: tk.Canvas, camera: ViewCamera, speed: float) -> None:
    if speed < 95.0:
        return
    strength = min(1.0, (speed - 95.0) / 140.0)
    if strength <= 0.05:
        return
    w = camera.viewport_width
    h = camera.viewport_height
    inset = int(40 + strength * 50)
    canvas.create_rectangle(0, camera.play_hud_top, inset, h, fill=palette.CHASE_VIGNETTE, outline="")
    canvas.create_rectangle(w - inset, camera.play_hud_top, w, h, fill=palette.CHASE_VIGNETTE, outline="")


def _draw_parallax_stars(canvas: tk.Canvas, camera: ViewCamera, world: GameWorld, horizon: float) -> None:
    width = camera.viewport_width
    top = camera.play_hud_top
    vel = world.ship.vel
    parallax = vel * (-0.018)
    for i in range(64):
        hx = (i * 7919 + 1237) % 10000
        hy = (i * 6271 + 4111) % 10000
        x = (hx / 10000.0) * width + parallax.x
        y = top + (hy / 10000.0) * max(1.0, horizon - top - 8) + parallax.y * 0.5
        size = 2 if i % 4 else 3
        tone = palette.CHASE_STAR_FAR if i % 3 else palette.CHASE_STAR_NEAR
        canvas.create_rectangle(x, y, x + size, y + size, fill=tone, outline="")


def _lerp_color(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    ar, ag, ab = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    br, bg, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    bl = int(ab + (bb - ab) * t)
    return f"#{r:02x}{g:02x}{bl:02x}"
