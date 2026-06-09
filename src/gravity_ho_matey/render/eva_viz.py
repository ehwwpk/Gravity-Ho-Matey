from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import EvaAvatar
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.brood_viz_helpers import draw_brood_ground_shadow
from gravity_ho_matey.render.lighting import LightRig, lerp_hex, material_for
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon, draw_simplified_polygon


def _local_pts(local: tuple[tuple[float, float], ...], pos: Vec2, angle: float, scale: float) -> list[tuple[float, float]]:
    c = math.cos(angle)
    s = math.sin(angle)
    return [(pos.x + (lx * c - ly * s) * scale, pos.y + (lx * s + ly * c) * scale) for lx, ly in local]


def _local_point(lx: float, ly: float, pos: Vec2, angle: float, scale: float) -> tuple[float, float]:
    c = math.cos(angle)
    s = math.sin(angle)
    return (pos.x + (lx * c - ly * s) * scale, pos.y + (lx * s + ly * c) * scale)


def draw_eva_avatar(
    canvas: tk.Canvas,
    avatar: EvaAvatar,
    *,
    camera,
    ship_pos: Vec2,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
    interacting: bool = False,
) -> None:
    p = camera.world_to_screen(avatar.pos, ship_pos, 0.0)
    sx, sy = p.x, p.y + hud_top
    scale = camera.tactical_scale
    bob = math.sin(elapsed * 2.2) * (0.6 if interacting else 1.2)
    pos = Vec2(sx, sy + bob)
    body_angle = avatar.face_angle
    aim = avatar.aim_angle
    face_c = math.cos(body_angle)
    face_s = math.sin(body_angle)
    aim_c = math.cos(aim)
    aim_s = math.sin(aim)

    shadow_off = Vec2(face_c, face_s) * (5.0 * scale)
    draw_brood_ground_shadow(canvas, sx + shadow_off.x, sy + 8.0 * scale + shadow_off.y, 16.0 * scale, rig=rig)

    suit = material_for("eva_suit", theme=rig.theme, view=rig.view)
    pack_mat = material_for("station_neutral", theme=rig.theme, view=rig.view)

    # Legs — humanoid read from any angle
    for side in (-1.0, 1.0):
        foot = _local_pts(
            (
                (side * 4.0, 6.0),
                (side * 7.0, 10.0),
                (side * 6.0, 14.0),
                (side * 2.0, 14.0),
            ),
            pos,
            body_angle,
            scale,
        )
        draw_simplified_polygon(canvas, foot, rig=rig, material=suit)

    # Backpack + rear chevron (shows facing when viewed from behind)
    pack = _local_pts(((-7.0, -2.0), (7.0, -2.0), (8.0, 8.0), (-8.0, 8.0)), pos, body_angle, scale)
    draw_illustrated_polygon(canvas, pack, rig=rig, material=pack_mat, seed=703, radius_hint=9.0 * scale, crater_count=0)
    back_cx, back_cy = _local_point(0.0, 9.0, pos, body_angle, scale)
    canvas.create_polygon(
        back_cx + face_c * 4.5 * scale,
        back_cy + face_s * 4.5 * scale,
        back_cx - face_s * 3.5 * scale,
        back_cy + face_c * 3.5 * scale,
        back_cx + face_s * 3.5 * scale,
        back_cy - face_c * 3.5 * scale,
        fill=lerp_hex(suit.mid, palette.COMET_VEIN, 0.45),
        outline=palette.COMET_HUD_ACCENT,
    )

    # Torso + shoulders
    torso = _local_pts(
        (
            (0.0, -11.0),
            (9.0, -8.0),
            (11.0, 0.0),
            (9.0, 9.0),
            (0.0, 12.0),
            (-9.0, 9.0),
            (-11.0, 0.0),
            (-9.0, -8.0),
        ),
        pos,
        body_angle,
        scale,
    )
    draw_illustrated_polygon(canvas, torso, rig=rig, material=suit, seed=701, radius_hint=13.0 * scale, crater_count=0)

    if avatar.carrying_fuel:
        pulse = 0.5 + 0.5 * math.sin(elapsed * 5.0)
        tank = _local_pts(((-5.0, 0.0), (5.0, 0.0), (6.0, 9.0), (-6.0, 9.0)), pos, body_angle, scale)
        draw_illustrated_polygon(canvas, tank, rig=rig, material=pack_mat, seed=704, radius_hint=7.0 * scale, crater_count=0)
        tx, ty = _local_point(0.0, 4.0, pos, body_angle, scale)
        canvas.create_oval(
            tx - 5.0 * scale,
            ty - 5.0 * scale,
            tx + 5.0 * scale,
            ty + 5.0 * scale,
            fill=palette.COMET_VOLATILE_GLOW if pulse > 0.55 else "",
            outline=palette.COMET_HUD_ACCENT,
            width=2,
        )

    # Helmet + visor (front arc)
    helmet = _local_pts(
        ((0.0, -15.0), (8.0, -13.0), (9.0, -6.0), (0.0, -4.0), (-9.0, -6.0), (-8.0, -13.0)),
        pos,
        body_angle,
        scale,
    )
    draw_illustrated_polygon(canvas, helmet, rig=rig, material=suit, seed=702, radius_hint=11.0 * scale, crater_count=0)
    vx, vy = _local_point(7.0, -8.0, pos, body_angle, scale)
    canvas.create_oval(vx - 4.0 * scale, vy - 3.0 * scale, vx + 4.0 * scale, vy + 3.0 * scale, fill=palette.COMET_ICE_HIGHLIGHT, outline=palette.COMET_VEIN, width=1)

    if not interacting:
        gun_shoulder_x, gun_shoulder_y = _local_point(4.0, -1.0, pos, body_angle, scale)
        muzzle_x = pos.x + aim_c * 18.0 * scale
        muzzle_y = pos.y + aim_s * 18.0 * scale
        grip_x = pos.x + aim_c * 8.0 * scale - aim_s * 4.0 * scale
        grip_y = pos.y + aim_s * 8.0 * scale + aim_c * 4.0 * scale
        canvas.create_line(gun_shoulder_x, gun_shoulder_y, grip_x, grip_y, fill="#7898a8", width=3)
        canvas.create_line(grip_x, grip_y, muzzle_x, muzzle_y, fill="#506878", width=4)
        canvas.create_line(grip_x, grip_y, muzzle_x, muzzle_y, fill=palette.COMET_HUD_ACCENT, width=1)
        canvas.create_oval(
            muzzle_x - 2.5 * scale,
            muzzle_y - 2.5 * scale,
            muzzle_x + 2.5 * scale,
            muzzle_y + 2.5 * scale,
            fill=palette.PICKUP_RAPID,
            outline="",
        )
        if avatar.recoil_timer > 0.0:
            canvas.create_line(
                muzzle_x,
                muzzle_y,
                muzzle_x + aim_c * 8.0 * scale,
                muzzle_y + aim_s * 8.0 * scale,
                fill=palette.PICKUP_RAPID,
                width=2,
            )
