from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CHASE_SCREEN_HEADING, ViewCamera
from gravity_ho_matey.render.chase_threat import predict_path_with_threats

# Instrument tuning — sensitive enough to read small pulls at cruise speed.
_G_REF = 145.0
_G_WARN = 0.38
_G_DANGER = 0.62
_SLIP_WARN = 0.22


def predict_ship_path(world: GameWorld, *, steps: int = 16, step_dt: float = 0.05) -> list[Vec2]:
    return [p for p, _ in predict_path_with_threats(world, steps=steps, step_dt=step_dt)]


def slip_angle_rad(vel: Vec2, ship_angle: float) -> float:
    if vel.length_sq() < 16.0:
        return 0.0
    forward = Vec2.from_angle(ship_angle)
    right = forward.rotated(math.pi / 2.0)
    fwd = vel.dot(forward)
    lat = vel.dot(right)
    return math.atan2(lat, max(abs(fwd), 10.0))


def bank_angle_for_chase(vel: Vec2, ship_angle: float, *, turn_rate: float = 0.0) -> float:
    slip = slip_angle_rad(vel, ship_angle)
    turn_bank = max(-0.38, min(0.38, turn_rate * 0.00055))
    slip_bank = max(-0.32, min(0.32, slip * 0.72))
    return CHASE_SCREEN_HEADING + turn_bank + slip_bank


def _hud_bank_rad(slip: float, turn_rate: float) -> float:
    return max(-0.42, min(0.42, slip * 0.6 + turn_rate * 0.0005))


def _ship_frame_accel(world: GameWorld, ship_angle: float) -> tuple[float, float, float]:
    """Forward, lateral, total gravity in ship frame."""
    accel = gravity_acceleration_at(world.ship.pos, world.wells) * world.config.gravity_scale
    forward = Vec2.from_angle(ship_angle)
    right = forward.rotated(math.pi / 2.0)
    g_fwd = accel.dot(forward)
    g_lat = accel.dot(right)
    return g_fwd, g_lat, accel.length()


def draw_xwing_cockpit_hud(
    canvas: tk.Canvas,
    world: GameWorld,
    camera: ViewCamera,
    *,
    anchor_x: float,
    anchor_y: float,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
) -> None:
    vw = camera.viewport_width
    vh = camera.viewport_height
    horizon = camera.chase_horizon_y()
    accent = palette.HELM_HUD_ACCENT
    dim = palette.HELM_HUD_DIM
    vel = world.ship.vel
    slip = slip_angle_rad(vel, ship_angle) if vel.length_sq() >= 16.0 else 0.0
    bank = _hud_bank_rad(slip, camera.turn_rate)
    g_fwd, g_lat, g_total = _ship_frame_accel(world, ship_angle)

    _draw_banked_horizon(canvas, horizon, vw, bank, turn_rate=camera.turn_rate, accent=accent, dim=dim)
    _draw_canopy_frame(canvas, vw, vh, hud_top, accent=accent, dim=dim)
    _draw_nose_reticle(canvas, anchor_x, anchor_y, accent=accent)
    _draw_speed_instruments(
        canvas,
        24,
        vh - 118,
        vel.length(),
        world.config.max_ship_speed,
        slip=slip,
        thrusting=world.ship.boost_energy < 0.98 and vel.length() > 20.0,
        accent=accent,
        dim=dim,
    )
    _draw_g_force_instruments(
        canvas,
        vw - 118,
        vh - 118,
        g_fwd,
        g_lat,
        g_total,
        accent=accent,
        dim=dim,
    )


def _draw_banked_horizon(
    canvas: tk.Canvas,
    horizon_y: float,
    vw: float,
    bank: float,
    *,
    turn_rate: float,
    accent: str,
    dim: str,
) -> None:
    span = vw * 0.48
    cx = vw * 0.5
    lift = math.sin(bank) * 18.0
    canvas.create_line(cx - span, horizon_y + lift, cx + span, horizon_y - lift, fill=accent, width=2)
    tick_step = 56
    for i in range(-5, 6):
        tx = cx + i * tick_step
        if tx < 12 or tx > vw - 12:
            continue
        t = i / 5.0
        ty = horizon_y + lift * t
        h = 8 if i % 2 == 0 else 5
        canvas.create_line(tx, ty - h, tx, ty + h, fill=dim, width=1)
    turn_x = cx + max(-80.0, min(80.0, turn_rate * 0.045))
    canvas.create_line(turn_x, horizon_y - 10, turn_x, horizon_y + 10, fill=palette.HELM_THREAT_HEAVY, width=3)


def _draw_canopy_frame(
    canvas: tk.Canvas,
    vw: float,
    vh: float,
    hud_top: float,
    *,
    accent: str,
    dim: str,
) -> None:
    inset = 14
    top = hud_top + 4
    bottom = vh - 8
    left = inset
    right = vw - inset
    arm = 32
    canvas.create_line(left, top, left + arm, top, fill=accent, width=2)
    canvas.create_line(left, top, left, top + arm, fill=accent, width=2)
    canvas.create_line(right, top, right - arm, top, fill=accent, width=2)
    canvas.create_line(right, top, right, top + arm, fill=accent, width=2)
    canvas.create_line(left, bottom, left + arm, bottom, fill=dim, width=1)
    canvas.create_line(left, bottom, left, bottom - arm, fill=dim, width=1)
    canvas.create_line(right, bottom, right - arm, bottom, fill=dim, width=1)
    canvas.create_line(right, bottom, right, bottom - arm, fill=dim, width=1)


def _draw_nose_reticle(canvas: tk.Canvas, cx: float, cy: float, *, accent: str) -> None:
    canvas.create_line(cx - 14, cy - 12, cx + 14, cy - 12, fill=accent, width=2)
    canvas.create_line(cx, cy - 20, cx, cy - 2, fill=accent, width=2)
    canvas.create_oval(cx - 3, cy - 15, cx + 3, cy - 9, fill=accent, outline="")


def _draw_speed_instruments(
    canvas: tk.Canvas,
    x: float,
    y: float,
    speed: float,
    max_speed: float,
    *,
    slip: float,
    thrusting: bool,
    accent: str,
    dim: str,
) -> None:
    bar_w = 148.0
    bar_h = 14.0
    norm = min(1.0, speed / max(1.0, max_speed))

    canvas.create_text(x, y, text="VELOCITY", anchor="sw", fill=dim, font=("Courier", 9, "bold"))
    canvas.create_text(x + bar_w, y, text=f"{int(speed)}", anchor="se", fill=accent, font=("Courier", 14, "bold"))
    by = y + 10
    canvas.create_rectangle(x, by, x + bar_w, by + bar_h, outline=accent, width=2)
    for tick in (0.25, 0.5, 0.75):
        tx = x + bar_w * tick
        canvas.create_line(tx, by, tx, by + bar_h, fill=dim, width=1)
    fill_color = palette.HELM_THREAT_LETHAL if norm > 0.88 else palette.HELM_THREAT_HEAVY if norm > 0.68 else accent
    canvas.create_rectangle(x + 2, by + 2, x + 2 + (bar_w - 4) * norm, by + bar_h - 2, fill=fill_color, outline="")

    slip_y = by + bar_h + 14
    canvas.create_text(x, slip_y, text="SLIP", anchor="sw", fill=dim, font=("Courier", 8))
    slip_norm = max(-1.0, min(1.0, slip / 0.65))
    slip_cx = x + bar_w * 0.5
    canvas.create_line(x + 8, slip_y + 12, x + bar_w - 8, slip_y + 12, fill=dim, width=1)
    canvas.create_line(slip_cx, slip_y + 6, slip_cx, slip_y + 18, fill=dim, width=1)
    slip_x = slip_cx + slip_norm * (bar_w * 0.42)
    slip_color = palette.HELM_THREAT_HEAVY if abs(slip) > _SLIP_WARN else accent
    canvas.create_oval(slip_x - 6, slip_y + 6, slip_x + 6, slip_y + 18, fill=slip_color, outline="#dff", width=1)

    if thrusting:
        boost_y = slip_y + 26
        canvas.create_text(x, boost_y, text="BOOST", anchor="sw", fill=palette.HELM_THREAT_HEAVY, font=("Courier", 8, "bold"))
        canvas.create_rectangle(x, boost_y + 8, x + bar_w * 0.55, boost_y + 16, fill=palette.HELM_THREAT_HEAVY, outline="")


def _draw_g_force_instruments(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    g_fwd: float,
    g_lat: float,
    g_total: float,
    *,
    accent: str,
    dim: str,
) -> None:
    radius = 46.0
    g_fwd_n = max(-1.0, min(1.0, g_fwd / _G_REF))
    g_lat_n = max(-1.0, min(1.0, g_lat / _G_REF))
    warn = palette.HELM_THREAT_HEAVY
    danger = palette.HELM_THREAT_LETHAL

    ring_color = danger if g_total > _G_REF * 1.4 else warn if g_total > _G_REF * 0.75 else accent
    canvas.create_text(cx, cy - radius - 18, text="GRAVITY PULL", anchor="n", fill=dim, font=("Courier", 9, "bold"))
    canvas.create_oval(cx - radius - 2, cy - radius - 2, cx + radius + 2, cy + radius + 2, outline=ring_color, width=2)
    canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=dim, width=1)
    canvas.create_line(cx - radius, cy, cx + radius, cy, fill=dim, width=1)
    canvas.create_line(cx, cy - radius, cx, cy + radius, fill=dim, width=1)

    canvas.create_text(cx, cy - radius + 10, text="FWD", fill=dim, font=("Courier", 7))
    canvas.create_text(cx, cy + radius - 6, text="AFT", fill=dim, font=("Courier", 7))
    canvas.create_text(cx + radius - 12, cy + 4, text="R", fill=dim, font=("Courier", 7))
    canvas.create_text(cx - radius + 10, cy + 4, text="L", fill=dim, font=("Courier", 7))

    bar_len = radius - 8.0
    bar_w = 7.0
    _draw_axis_bar(canvas, cx, cy, g_fwd_n, bar_len, bar_w, vertical=True, accent=accent, warn=warn, danger=danger)
    _draw_axis_bar(canvas, cx, cy, g_lat_n, bar_len, bar_w, vertical=False, accent=accent, warn=warn, danger=danger)

    dot_x = cx + g_lat_n * (radius - 10.0)
    dot_y = cy - g_fwd_n * (radius - 10.0)
    dot_r = 7 if g_total > _G_REF else 6
    dot_color = danger if g_total > _G_REF * 1.4 else warn if g_total > _G_REF * 0.65 else accent
    canvas.create_oval(dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r, fill=dot_color, outline="#eef", width=2)

    canvas.create_text(cx, cy + radius + 16, text=f"{g_total:.0f} G", anchor="n", fill=ring_color, font=("Courier", 12, "bold"))
    canvas.create_text(cx - radius - 4, cy + radius + 34, text=f"F{g_fwd:+.0f}", anchor="e", fill=accent, font=("Courier", 9))
    canvas.create_text(cx + radius + 4, cy + radius + 34, text=f"R{g_lat:+.0f}", anchor="w", fill=accent, font=("Courier", 9))


def _draw_axis_bar(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    norm: float,
    bar_len: float,
    bar_w: float,
    *,
    vertical: bool,
    accent: str,
    warn: str,
    danger: str,
) -> None:
    if abs(norm) < 0.03:
        return
    mag = abs(norm)
    color = danger if mag > _G_DANGER else warn if mag > _G_WARN else accent
    extent = mag * bar_len
    if vertical:
        if norm > 0:
            canvas.create_rectangle(cx - bar_w * 0.5, cy - extent, cx + bar_w * 0.5, cy, fill=color, outline="")
        else:
            canvas.create_rectangle(cx - bar_w * 0.5, cy, cx + bar_w * 0.5, cy + extent, fill=color, outline="")
    elif norm > 0:
        canvas.create_rectangle(cx, cy - bar_w * 0.5, cx + extent, cy + bar_w * 0.5, fill=color, outline="")
    else:
        canvas.create_rectangle(cx - extent, cy - bar_w * 0.5, cx, cy + bar_w * 0.5, fill=color, outline="")
