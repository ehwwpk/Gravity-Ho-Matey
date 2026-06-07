from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Beacon
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.beacon_viz import beacon_seed_from_pos, draw_beacon_play
from gravity_ho_matey.render.camera import CHASE_BEACON_SCALE_FLOOR, CHASE_BEACON_VISUAL_BOOST
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.entity_viz import draw_gate_glyph
from gravity_ho_matey.render.lighting import LightRig


def draw_chase_beacon(
    canvas: tk.Canvas,
    pos: Vec2,
    beacon: Beacon,
    *,
    elapsed: float,
    depth_scale: float = 1.0,
    rig: LightRig | None = None,
) -> None:
    from gravity_ho_matey.render.camera import CameraMode

    scale = max(
        CHASE_BEACON_SCALE_FLOOR,
        min(1.42, depth_scale * CHASE_BEACON_VISUAL_BOOST),
    )
    play_rig = rig or LightRig.for_play(theme="cove", camera_mode=CameraMode.CHASE)
    draw_beacon_play(
        canvas,
        pos.x,
        pos.y,
        beacon,
        scale=scale,
        rig=play_rig,
        elapsed=elapsed,
        seed=beacon_seed_from_pos(beacon.pos),
        spark_orbits=not beacon.collected,
    )


def draw_chase_gate(
    canvas: tk.Canvas,
    pos: Vec2,
    *,
    unlocked: bool,
    solar: bool,
    gate_size: float,
    depth_scale: float = 1.0,
) -> None:
    scale = max(0.55, min(1.35, depth_scale))
    draw_gate_glyph(
        canvas,
        pos.x,
        pos.y,
        size=gate_size,
        unlocked=unlocked,
        solar=solar,
        scale=scale,
    )


def draw_chase_enemy(
    canvas: tk.Canvas,
    pos: Vec2,
    *,
    radius: float,
    facing: float,
    scale: float,
) -> None:
    r = min(radius * scale, 28.0)
    draw_ground_fog_glow(canvas, pos.x, pos.y + 4, r * 1.4, palette.CHASE_ENEMY_FOG[:2], pulse=0.0)
    canvas.create_oval(pos.x - r, pos.y - r * 0.55, pos.x + r, pos.y + r * 0.35, fill=palette.ENEMY, outline=palette.ENEMY_EDGE, width=2)
    spike = pos + Vec2.from_angle(facing) * (r + 4)
    canvas.create_line(pos.x, pos.y, spike.x, spike.y, fill=palette.ENEMY_EDGE, width=2)


def draw_chase_squid(
    canvas: tk.Canvas,
    pos: Vec2,
    *,
    radius: float,
    tentacle_reach: float,
    facing: float,
    scale: float,
    coiled: bool,
    elapsed: float,
    ship_world: Vec2 | None = None,
    tip_screen: tuple[tuple[float, float], ...] | None = None,
) -> None:
    r = min(radius * scale, 32.0)
    reach_world = tentacle_reach * scale
    pulse = 0.5 + 0.5 * math.sin(elapsed * 8.0 if coiled else elapsed * 4.0)
    if coiled:
        draw_ground_fog_glow(
            canvas,
            pos.x,
            pos.y + 4,
            (r + reach_world * 0.35) * (1.35 + pulse * 0.2),
            palette.SQUID_WRAP_GLOW,
            pulse=elapsed * 5.5,
        )
    else:
        draw_ground_fog_glow(canvas, pos.x, pos.y + 4, r * 1.35, palette.SQUID_WRAP_GLOW[:2], pulse=0.0)

    if tip_screen:
        width = 3 if coiled else 2
        for tx, ty in tip_screen:
            mx = pos.x + (tx - pos.x) * 0.48
            my = pos.y + (ty - pos.y) * 0.48
            canvas.create_line(pos.x, pos.y, mx, my, tx, ty, fill=palette.SQUID_TENTACLE, width=width, smooth=True)
    else:
        tentacles = 8
        for i in range(tentacles):
            base_angle = facing + (math.tau * i / tentacles)
            reach = reach_world * (1.55 + pulse * 0.22 if coiled else 1.18)
            if coiled and ship_world is not None:
                to_ship = ship_world - pos
                if to_ship.length_sq() > 1e-6:
                    coil_dir = to_ship.normalized()
                    blend = 0.72
                    dir_vec = (Vec2.from_angle(base_angle) * (1.0 - blend) + coil_dir * blend).normalized()
                    tip = pos + dir_vec * reach
                    mid = pos + dir_vec * (reach * 0.52)
                else:
                    tip = pos + Vec2.from_angle(base_angle) * reach
                    mid = pos + Vec2.from_angle(base_angle) * (reach * 0.52)
            else:
                sway = math.sin(elapsed * 6.0 + i * 0.9) * (10.0 if coiled else 5.0)
                tip = pos + Vec2.from_angle(base_angle) * reach + Vec2(sway, sway * 0.35)
                mid = pos + Vec2.from_angle(base_angle) * (reach * 0.5) + Vec2(sway * 0.4, 0.0)
            canvas.create_line(
                pos.x,
                pos.y,
                mid.x,
                mid.y,
                tip.x,
                tip.y,
                fill=palette.SQUID_TENTACLE,
                width=3 if coiled else 2,
                smooth=True,
            )
    canvas.create_oval(pos.x - r, pos.y - r * 0.65, pos.x + r, pos.y + r * 0.55, fill=palette.SQUID_BODY, outline=palette.SQUID_CORE, width=2)
    canvas.create_oval(pos.x - r * 0.35, pos.y - r * 0.25, pos.x + r * 0.35, pos.y + r * 0.2, fill=palette.SQUID_CORE, outline="")
    if coiled and ship_world is not None:
        canvas.create_oval(
            pos.x - r * 0.15,
            pos.y - r * 0.12,
            pos.x + r * 0.15,
            pos.y + r * 0.1,
            fill=palette.SQUID_TENTACLE,
            outline="",
        )


def draw_chase_pickup(canvas: tk.Canvas, pos: Vec2, kind: PowerUpKind) -> None:
    color = {
        PowerUpKind.THRUST_BOOST: palette.PICKUP_THRUST,
        PowerUpKind.RAPID_FIRE: palette.PICKUP_RAPID,
        PowerUpKind.STABILIZER: palette.PICKUP_STABILIZER,
    }.get(kind, palette.BEACON)
    draw_ground_fog_glow(canvas, pos.x, pos.y + 4, 10, (color, color), pulse=0.0)
    canvas.create_polygon(pos.x, pos.y - 8, pos.x + 7, pos.y, pos.x, pos.y + 8, pos.x - 7, pos.y, fill=color, outline="#fff")
