from __future__ import annotations

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Beacon
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.beacon_viz import beacon_seed_from_pos, draw_beacon_play
from gravity_ho_matey.render.camera import CHASE_BEACON_SCALE_FLOOR, CHASE_BEACON_VISUAL_BOOST
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.entity_viz import draw_gate_glyph
from gravity_ho_matey.render.enemy_viz import draw_patrol_enemy_chase
from gravity_ho_matey.render.lighting import LightRig
from gravity_ho_matey.render.squid_viz import draw_squid_enemy_chase


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
    enemy,
    camera,
    ship_pos: Vec2,
    ship_angle: float,
    scale: float,
    rig: LightRig,
    elapsed: float,
) -> None:
    draw_patrol_enemy_chase(
        canvas,
        pos,
        enemy,
        camera=camera,
        ship_pos=ship_pos,
        ship_angle=ship_angle,
        scale=scale,
        rig=rig,
        elapsed=elapsed,
    )


def draw_chase_squid(
    canvas: tk.Canvas,
    pos: Vec2,
    *,
    enemy: SquidEnemy,
    scale: float,
    ship_world: Vec2,
    ship_radius: float,
    tip_screen: tuple[tuple[float, float], ...] | None,
    rig: LightRig,
    elapsed: float,
) -> None:
    draw_squid_enemy_chase(
        canvas,
        pos,
        enemy,
        scale=scale,
        ship_world=ship_world,
        ship_radius=ship_radius,
        tip_screen=tip_screen,
        rig=rig,
        elapsed=elapsed,
    )


def draw_chase_jewel(canvas: tk.Canvas, pos: Vec2, *, elapsed: float = 0.0) -> None:
    from gravity_ho_matey.render.jewel_viz import draw_jewel_orb

    draw_ground_fog_glow(canvas, pos.x, pos.y + 4, 12, (palette.JEWEL_GLOW, palette.JEWEL_CORE), pulse=elapsed * 4.0)
    draw_jewel_orb(canvas, pos.x, pos.y, elapsed=elapsed, depth_scale=1.0)


def draw_chase_pickup(canvas: tk.Canvas, pos: Vec2, kind: PowerUpKind) -> None:
    color = {
        PowerUpKind.THRUST_BOOST: palette.PICKUP_THRUST,
        PowerUpKind.RAPID_FIRE: palette.PICKUP_RAPID,
        PowerUpKind.BOOST_TAP: palette.PICKUP_BOOST,
        PowerUpKind.RUBBER_HULL: palette.PICKUP_RUBBER,
    }.get(kind, palette.BEACON)
    draw_ground_fog_glow(canvas, pos.x, pos.y + 4, 10, (color, color), pulse=0.0)
    canvas.create_polygon(pos.x, pos.y - 8, pos.x + 7, pos.y, pos.x, pos.y + 8, pos.x - 7, pos.y, fill=color, outline="#fff")
