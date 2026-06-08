from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_mirror import draw_rear_view_mirror
from gravity_ho_matey.render.launch_countdown_overlay import accent_for_theme
from gravity_ho_matey.render.chase_threat import predict_path_with_threats

# Instrument tuning — sensitive enough to read small pulls at cruise speed.
_G_REF = 145.0
_G_WARN = 0.38
_G_DANGER = 0.62
_SLIP_WARN = 0.22


from gravity_ho_matey.render.chase_rig import slip_angle_rad  # re-export for tests / tactical HUD


def predict_ship_path(world: GameWorld, *, steps: int = 16, step_dt: float = 0.05) -> list[Vec2]:
    return [p for p, _ in predict_path_with_threats(world, steps=steps, step_dt=step_dt)]


def bank_angle_for_chase(vel: Vec2, ship_angle: float, *, turn_rate: float = 0.0, on_highway: bool = False) -> float:
    from gravity_ho_matey.render.chase_rig import chase_bank_display_angle

    return chase_bank_display_angle(
        vel, ship_angle, turn_rate=turn_rate, on_highway=on_highway,
    )


def ship_frame_gravity(world: GameWorld, ship_angle: float) -> tuple[float, float, float]:
    """Forward, lateral, total gravity in ship frame."""
    accel = gravity_acceleration_at(world.ship.pos, world.wells) * world.config.gravity_scale
    forward = Vec2.from_angle(ship_angle)
    right = forward.rotated(math.pi / 2.0)
    g_fwd = accel.dot(forward)
    g_lat = accel.dot(right)
    return g_fwd, g_lat, accel.length()


def _ship_frame_accel(world: GameWorld, ship_angle: float) -> tuple[float, float, float]:
    return ship_frame_gravity(world, ship_angle)


def _playfield_accent(level_theme: str) -> tuple[str, str]:
    if level_theme == "solar":
        return palette.HUD_ACCENT_SOLAR, palette.HUD_DIM
    if level_theme == "rift":
        return palette.RIFT_HUD_ACCENT, palette.HUD_DIM
    if level_theme == "siege":
        return palette.SIEGE_HUD_ACCENT, palette.HUD_DIM
    if level_theme == "brood_moon":
        return palette.BROOD_MOON_HUD_ACCENT, palette.HUD_DIM
    return palette.HUD_ACCENT, palette.HUD_DIM


def draw_tactical_flight_instruments(
    canvas: tk.Canvas,
    world: GameWorld,
    *,
    viewport_width: int,
    viewport_height: int,
    ship_angle: float,
) -> None:
    """Compact velocity + gravity summary for tactical mode — shared math with chase helm."""
    accent, dim = _playfield_accent(world.config.level_theme)
    vel = world.ship.vel
    slip = slip_angle_rad(vel, ship_angle) if vel.length_sq() >= 16.0 else 0.0
    g_fwd, g_lat, g_total = ship_frame_gravity(world, ship_angle)
    play_bottom = float(viewport_height) - 8.0

    _draw_speed_instruments(
        canvas,
        12.0,
        play_bottom - 78.0,
        vel.length(),
        world.config.max_ship_speed,
        slip=slip,
        thrusting=world.ship.boost_flash > 0.0,
        accent=accent,
        dim=dim,
        compact=True,
    )
    _draw_gravity_compact_summary(
        canvas,
        viewport_width - 12.0,
        play_bottom - 12.0,
        g_fwd,
        g_lat,
        g_total,
        accent=accent,
        dim=dim,
    )

def draw_xwing_cockpit_hud(
    canvas: tk.Canvas,
    world: GameWorld,
    camera: ViewCamera,
    field: GravityField,
    *,
    anchor_x: float,
    anchor_y: float,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
) -> None:
    vw = camera.viewport_width
    vh = camera.viewport_height
    play_top = camera.play_hud_top
    horizon = camera.chase_horizon_y()
    accent = accent_for_theme(world.config.level_theme)
    dim = palette.HELM_HUD_DIM
    vel = world.ship.vel
    slip = slip_angle_rad(vel, ship_angle) if vel.length_sq() >= 16.0 else 0.0
    bank = camera.bank_display
    g_fwd, g_lat, g_total = ship_frame_gravity(world, ship_angle)

    _draw_banked_horizon(canvas, horizon, vw, bank, turn_rate=camera.turn_rate, accent=accent, dim=dim)
    _draw_canopy_frame(canvas, vw, vh, play_top, accent=accent, dim=dim)
    _draw_nose_reticle(canvas, anchor_x, anchor_y, accent=accent)
    _draw_speed_instruments(
        canvas,
        24,
        vh - 118,
        vel.length(),
        world.config.max_ship_speed,
        slip=slip,
        thrusting=world.ship.boost_flash > 0.0,
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
    draw_rear_view_mirror(
        canvas,
        world,
        camera,
        field,
        ship_pos=ship_pos,
        ship_angle=ship_angle,
        ship_vel=world.ship.vel,
        hud_top=play_top,
        elapsed=world.elapsed,
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
    lift = math.sin(bank) * 22.0
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
    compact: bool = False,
) -> None:
    bar_w = 108.0 if compact else 148.0
    bar_h = 10.0 if compact else 14.0
    speed_font = ("Courier", 11, "bold") if compact else ("Courier", 14, "bold")
    label_font = ("Courier", 8, "bold") if compact else ("Courier", 9, "bold")
    norm = min(1.0, speed / max(1.0, max_speed))

    canvas.create_text(x, y, text="VELOCITY", anchor="sw", fill=dim, font=label_font)
    canvas.create_text(x + bar_w, y, text=f"{int(speed)}", anchor="se", fill=accent, font=speed_font)
    by = y + (8 if compact else 10)
    canvas.create_rectangle(x, by, x + bar_w, by + bar_h, outline=accent, width=2 if not compact else 1)
    for tick in (0.25, 0.5, 0.75):
        tx = x + bar_w * tick
        canvas.create_line(tx, by, tx, by + bar_h, fill=dim, width=1)
    fill_color = palette.HELM_THREAT_LETHAL if norm > 0.88 else palette.HELM_THREAT_HEAVY if norm > 0.68 else accent
    canvas.create_rectangle(x + 2, by + 2, x + 2 + (bar_w - 4) * norm, by + bar_h - 2, fill=fill_color, outline="")

    slip_y = by + bar_h + (10 if compact else 14)
    canvas.create_text(x, slip_y, text="SLIP", anchor="sw", fill=dim, font=("Courier", 7 if compact else 8))
    slip_norm = max(-1.0, min(1.0, slip / 0.65))
    slip_cx = x + bar_w * 0.5
    slip_h = 10 if compact else 12
    canvas.create_line(x + 8, slip_y + slip_h, x + bar_w - 8, slip_y + slip_h, fill=dim, width=1)
    canvas.create_line(slip_cx, slip_y + (4 if compact else 6), slip_cx, slip_y + slip_h + 6, fill=dim, width=1)
    slip_x = slip_cx + slip_norm * (bar_w * 0.42)
    slip_color = palette.HELM_THREAT_HEAVY if abs(slip) > _SLIP_WARN else accent
    dot_r = 5 if compact else 6
    canvas.create_oval(
        slip_x - dot_r,
        slip_y + (4 if compact else 6),
        slip_x + dot_r,
        slip_y + slip_h + 6,
        fill=slip_color,
        outline="#dff",
        width=1,
    )

    if thrusting and not compact:
        boost_y = slip_y + 26
        canvas.create_text(x, boost_y, text="BOOST", anchor="sw", fill=palette.HELM_THREAT_HEAVY, font=("Courier", 8, "bold"))
        canvas.create_rectangle(x, boost_y + 8, x + bar_w * 0.55, boost_y + 16, fill=palette.HELM_THREAT_HEAVY, outline="")
    elif thrusting:
        canvas.create_text(x + bar_w, slip_y + slip_h + 2, text="BOOST", anchor="ne", fill=palette.HELM_THREAT_HEAVY, font=("Courier", 7, "bold"))


def _draw_gravity_compact_summary(
    canvas: tk.Canvas,
    anchor_x: float,
    anchor_y: float,
    g_fwd: float,
    g_lat: float,
    g_total: float,
    *,
    accent: str,
    dim: str,
) -> None:
    """Tactical-only gravity summary — complements heatmap without full chase G-ball."""
    radius = 28.0
    cx = anchor_x - radius - 8.0
    cy = anchor_y - radius - 22.0
    g_fwd_n = max(-1.0, min(1.0, g_fwd / _G_REF))
    g_lat_n = max(-1.0, min(1.0, g_lat / _G_REF))
    warn = palette.HELM_THREAT_HEAVY
    danger = palette.HELM_THREAT_LETHAL
    ring_color = danger if g_total > _G_REF * 1.4 else warn if g_total > _G_REF * 0.75 else accent

    canvas.create_text(anchor_x, cy - radius - 6, text="GRAV", anchor="ne", fill=dim, font=("Courier", 8, "bold"))
    canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=ring_color, width=2)
    canvas.create_oval(cx - radius + 3, cy - radius + 3, cx + radius - 3, cy + radius - 3, outline=dim, width=1)
    canvas.create_line(cx - radius + 4, cy, cx + radius - 4, cy, fill=dim, width=1)
    canvas.create_line(cx, cy - radius + 4, cx, cy + radius - 4, fill=dim, width=1)
    dot_x = cx + g_lat_n * (radius - 8.0)
    dot_y = cy - g_fwd_n * (radius - 8.0)
    dot_color = danger if g_total > _G_REF * 1.4 else warn if g_total > _G_REF * 0.65 else accent
    canvas.create_oval(dot_x - 5, dot_y - 5, dot_x + 5, dot_y + 5, fill=dot_color, outline="#eef", width=1)
    canvas.create_text(anchor_x, cy + radius + 6, text=f"{g_total:.0f} G", anchor="ne", fill=ring_color, font=("Courier", 10, "bold"))
    canvas.create_text(
        anchor_x,
        cy + radius + 20,
        text=f"F{g_fwd:+.0f}  R{g_lat:+.0f}",
        anchor="ne",
        fill=accent,
        font=("Courier", 8),
    )

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
