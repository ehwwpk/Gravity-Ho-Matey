from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CHASE_SCREEN_HEADING, ViewCamera
from gravity_ho_matey.render.chase_threat import (
    ThreatLevel,
    predict_path_with_threats,
)


def slip_angle_rad(vel: Vec2, ship_angle: float) -> float:
    if vel.length_sq() < 16.0:
        return 0.0
    forward = Vec2.from_angle(ship_angle)
    right = forward.rotated(math.pi / 2.0)
    fwd = vel.dot(forward)
    lat = vel.dot(right)
    return math.atan2(lat, max(abs(fwd), 10.0))


def bank_angle_for_chase(vel: Vec2, ship_angle: float) -> float:
    slip = slip_angle_rad(vel, ship_angle)
    return CHASE_SCREEN_HEADING + max(-0.42, min(0.42, slip * 0.75))


def predict_ship_path(world: GameWorld, *, steps: int = 16, step_dt: float = 0.05) -> list[Vec2]:
    return [p for p, _ in predict_path_with_threats(world, steps=steps, step_dt=step_dt)]


def draw_inertial_ribbon(
    canvas: tk.Canvas,
    world: GameWorld,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
) -> None:
    horizon = camera.chase_horizon_y()
    speed = world.ship.vel.length()
    if speed < 14.0:
        return

    samples = predict_path_with_threats(world, steps=24, step_dt=0.042)
    screen: list[tuple[float, float, ThreatLevel]] = []
    for wp, threat in samples:
        p = camera.world_to_screen(wp, ship_pos, ship_angle)
        if p.y < horizon + 4:
            continue
        screen.append((p.x, p.y, threat))

    if len(screen) < 2:
        return

    for i in range(len(screen) - 1):
        x0, y0, t0 = screen[i]
        x1, y1, t1 = screen[i + 1]
        threat = t0 if t0.value >= t1.value else t1
        if threat is ThreatLevel.LETHAL:
            color = palette.HELM_THREAT_LETHAL
            width = 3
        elif threat is ThreatLevel.HEAVY:
            color = palette.HELM_THREAT_HEAVY
            width = 2
        else:
            fade = 1.0 - i / max(1, len(screen) - 1)
            color = palette.HELM_RIBBON_SAFE if fade > 0.35 else palette.HELM_RIBBON_FADE
            width = max(1, int(2 * fade))
        canvas.create_line(x0, y0, x1, y1, fill=color, width=width, smooth=True)

    pulse = 0.5 + 0.5 * math.sin(world.elapsed * 4.5)
    for i, (x, y, threat) in enumerate(screen[::3]):
        if threat is not ThreatLevel.LETHAL:
            continue
        r = 3 + pulse * 2
        canvas.create_oval(x - r, y - r, x + r, y + r, outline=palette.HELM_THREAT_LETHAL, width=1)


def draw_drift_reticle(
    canvas: tk.Canvas,
    world: GameWorld,
    camera: ViewCamera,
    *,
    anchor_x: float,
    anchor_y: float,
    ship_pos: Vec2,
    ship_angle: float,
) -> None:
    vel = world.ship.vel
    if vel.length_sq() < 64.0:
        return

    tip_world = ship_pos + vel.normalized() * min(48.0, 16.0 + vel.length() * 0.12)
    tip = camera.world_to_screen(tip_world, ship_pos, ship_angle)
    dx = tip.x - anchor_x
    dy = tip.y - anchor_y
    dist = math.hypot(dx, dy)
    max_off = 30.0
    if dist > max_off:
        scale = max_off / dist
        dx *= scale
        dy *= scale
    cx = anchor_x + dx * 0.55
    cy = anchor_y + dy * 0.55 - 6

    slip = abs(slip_angle_rad(vel, ship_angle))
    reticle = palette.HELM_THREAT_LETHAL if slip > 0.55 else palette.HELM_RIBBON_SAFE
    size = 7
    canvas.create_line(cx - size, cy, cx + size, cy, fill=reticle, width=2)
    canvas.create_line(cx, cy - size, cx, cy + size, fill=reticle, width=2)

    if slip > 0.22:
        bracket = palette.HELM_THREAT_HEAVY if slip > 0.45 else palette.HUD_DIM
        canvas.create_arc(
            anchor_x - 22,
            anchor_y - 28,
            anchor_x + 22,
            anchor_y + 8,
            start=200,
            extent=140,
            style="arc",
            outline=bracket,
            width=1,
        )


def draw_tactical_helm_cues(
    canvas: tk.Canvas,
    world: GameWorld,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
) -> None:
    """Tactical tube — ribbon + drift tick only, no panels."""
    speed = world.ship.vel.length()
    if speed < 14.0:
        return
    ship_screen = camera.world_to_screen(world.ship.pos, ship_pos, ship_angle)
    sx, sy = ship_screen.x, ship_screen.y + hud_top
    samples = predict_path_with_threats(world, steps=14, step_dt=0.05)
    prev_x, prev_y = sx, sy
    for i, (wp, threat) in enumerate(samples[1:], start=1):
        p = camera.world_to_screen(wp, ship_pos, ship_angle)
        px, py = p.x, p.y + hud_top
        if threat is ThreatLevel.LETHAL:
            color = palette.HELM_THREAT_LETHAL
            width = 2
        elif threat is ThreatLevel.HEAVY:
            color = palette.HELM_THREAT_HEAVY
            width = 2
        else:
            color = palette.HELM_RIBBON_FADE
            width = 1
        canvas.create_line(prev_x, prev_y, px, py, fill=color, width=width, smooth=True)
        prev_x, prev_y = px, py

    vel = world.ship.vel
    tip_world = world.ship.pos + vel.normalized() * min(36.0, speed * 0.14)
    tip = camera.world_to_screen(tip_world, ship_pos, ship_angle)
    dx = (tip.x - sx) * 0.45
    dy = (tip.y + hud_top - sy) * 0.45
    canvas.create_line(sx, sy, sx + dx, sy + dy, fill=palette.HELM_RIBBON_SAFE, width=2)
