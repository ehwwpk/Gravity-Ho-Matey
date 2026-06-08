"""Top-down tactical codex previews — same lit draw paths as in-game OG view."""

from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_motion import make_asteroid
from gravity_ho_matey.gameplay.drone_wingman import DroneWingman
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.entities import Beacon
from gravity_ho_matey.gameplay.space_station import SpaceStation
from gravity_ho_matey.gameplay.squid_enemy import SquidEnemy
from gravity_ho_matey.gameplay.station_kinds import StationFaction
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.asteroid_viz import draw_tactical_asteroid
from gravity_ho_matey.render.beacon_viz import beacon_seed_from_pos, draw_beacon_play
from gravity_ho_matey.render.camera import CameraMode, ViewCamera
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.drone_viz import draw_drone_wingman_tactical
from gravity_ho_matey.render.enemy_viz import draw_patrol_enemy_tactical
from gravity_ho_matey.render.lighting import LightRig
from gravity_ho_matey.render.squid_viz import (
    draw_squid_body_lit,
    draw_squid_coil_ring,
    draw_squid_tentacles_enhanced,
)
from gravity_ho_matey.render.station_viz import _draw_lit_station
from gravity_ho_matey.render.title_codex import CodexEntry
from gravity_ho_matey.render.ship_viz import draw_hostile_fighter_ship
from gravity_ho_matey.render.world_draw import WELL_RING_VISUAL_SCALE, draw_ship, draw_well


def make_codex_camera(cx: float, cy: float, anchor: Vec2, *, scale: float) -> ViewCamera:
    """Pin anchor world position to screen (cx, cy) in tactical space."""
    cam = ViewCamera(mode=CameraMode.TACTICAL, tactical_scale=scale)
    cam.center = Vec2(anchor.x - cx / scale, anchor.y - cy / scale)
    cam._smooth_center = cam.center
    return cam


def _station_mapper(
    camera: ViewCamera,
    station: SpaceStation,
    *,
    hud_top: float = 0.0,
):
    anchor = camera.world_to_screen(station.pos, station.pos, 0.0)
    east = camera.world_to_screen(station.pos + Vec2(120.0, 0.0), station.pos, 0.0)
    px_per_unit = abs(east.x - anchor.x) / 120.0

    def to_screen(world: Vec2) -> tuple[float, float]:
        sp = camera.world_to_screen(world, station.pos, 0.0)
        return sp.x, sp.y + hud_top

    return to_screen, px_per_unit


def draw_codex_tactical_preview(
    canvas: tk.Canvas,
    entry: CodexEntry,
    cx: float,
    cy: float,
    *,
    rig: LightRig,
    elapsed: float,
    yaw: float,
) -> None:
    kind = entry.preview_kind
    if kind == "skiff":
        _draw_skiff(canvas, cx, cy, rig=rig, elapsed=elapsed, yaw=yaw)
    elif kind == "relay_station":
        _draw_station(canvas, cx, cy, faction=StationFaction.FRIENDLY, label="RLY", rig=rig, elapsed=elapsed, scale=0.34)
    elif kind == "hostile_station":
        _draw_station(canvas, cx, cy, faction=StationFaction.HOSTILE, label="STN", rig=rig, elapsed=elapsed, scale=0.34)
    elif kind == "patrol":
        _draw_patrol(canvas, cx, cy, rig=rig, elapsed=elapsed, yaw=yaw)
    elif kind == "hostile_fighter":
        _draw_hostile_fighter(canvas, cx, cy, rig=rig, elapsed=elapsed, yaw=yaw)
    elif kind == "void_squid":
        _draw_squid(canvas, cx, cy, rig=rig, elapsed=elapsed, yaw=yaw)
    elif kind == "drone":
        _draw_drone(canvas, cx, cy, rig=rig, elapsed=elapsed, yaw=yaw)
    elif kind == "asteroid":
        _draw_asteroid(canvas, cx, cy, rig=rig, elapsed=elapsed)
    elif kind == "singularity":
        _draw_well(canvas, cx, cy, rig=rig)
    elif kind == "beacon":
        _draw_beacon(canvas, cx, cy, rig=rig, elapsed=elapsed)
    else:
        canvas.create_text(cx, cy, text="?", fill=palette.HUD_DIM, font=("Courier New", 12))


def _draw_skiff(canvas: tk.Canvas, cx: float, cy: float, *, rig: LightRig, elapsed: float, yaw: float) -> None:
    angle = math.pi * 0.5 + math.sin(yaw) * 0.22
    draw_ship(canvas, Vec2(cx, cy), angle, boost_energy=1.0, scale=1.38, rig=rig, elapsed=elapsed)


def _draw_station(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    *,
    faction: StationFaction,
    label: str,
    rig: LightRig,
    elapsed: float,
    scale: float,
) -> None:
    anchor = Vec2(0.0, 0.0)
    station = SpaceStation(pos=anchor, anchor=anchor, faction=faction, station_label=label)
    camera = make_codex_camera(cx, cy, anchor, scale=scale)
    to_screen, px_per_unit = _station_mapper(camera, station)
    glow = palette.CHASE_FOG_STATION
    sx, sy = to_screen(station.pos)
    draw_ground_fog_glow(canvas, sx, sy + station.radius * px_per_unit * 0.1, station.radius * px_per_unit * 1.1, glow, pulse=elapsed * 2.6)
    _draw_lit_station(
        canvas,
        station,
        to_screen=to_screen,
        px_per_unit=px_per_unit,
        rig=rig,
        elapsed=elapsed,
    )


def _draw_patrol(canvas: tk.Canvas, cx: float, cy: float, *, rig: LightRig, elapsed: float, yaw: float) -> None:
    anchor = Vec2(0.0, 0.0)
    enemy = PatrolEnemy(waypoints=(anchor,), pos=anchor, facing_angle=math.pi * 0.5 + math.sin(yaw) * 0.35)
    camera = make_codex_camera(cx, cy, anchor, scale=0.92)
    draw_patrol_enemy_tactical(
        canvas,
        enemy,
        camera=camera,
        ship_pos=anchor,
        hud_top=0.0,
        rig=rig,
        elapsed=elapsed,
    )


def _draw_squid(canvas: tk.Canvas, cx: float, cy: float, *, rig: LightRig, elapsed: float, yaw: float) -> None:
    anchor = Vec2(0.0, 0.0)
    facing = math.pi * 0.5 + math.sin(yaw) * 0.18
    squid = SquidEnemy(pos=anchor, facing_angle=facing)
    scale = 0.92
    camera = make_codex_camera(cx, cy, anchor, scale=scale)
    sx, sy = cx, cy
    engaging = True
    r_px = squid.radius * scale
    coil_r = (squid.tentacle_span() + 12.0) * scale * 0.92
    draw_ground_fog_glow(canvas, sx, sy + r_px * 0.12, squid.tentacle_span() * scale * 0.48, palette.SQUID_WRAP_GLOW[:2], pulse=elapsed * 4.2)
    draw_squid_coil_ring(
        canvas, sx, sy, coil_r,
        engaging=engaging, elapsed=elapsed, facing=facing,
        tentacle_count=len(squid.tentacle_tips()),
    )
    tips: list[tuple[float, float]] = []
    mids: list[tuple[float, float]] = []
    reach = squid.tentacle_reach * scale * 0.95
    pulse = 0.5 + 0.5 * math.sin(elapsed * 4.0)
    for i, _tip in enumerate(squid.tentacle_tips()):
        spread = facing + math.tau * i / len(squid.tentacle_tips())
        reach_len = reach * (1.22 + pulse * 0.12)
        sway = math.sin(elapsed * 5.5 + i * 0.85) * 4.0
        tip_x = sx + math.cos(spread) * reach_len + math.cos(spread + math.pi / 2) * sway
        tip_y = sy + math.sin(spread) * reach_len * 0.86 + math.sin(spread + math.pi / 2) * sway * 0.5
        mid_x = sx + math.cos(spread) * reach_len * 0.52
        mid_y = sy + math.sin(spread) * reach_len * 0.46
        tips.append((tip_x, tip_y))
        mids.append((mid_x, mid_y))
    draw_squid_tentacles_enhanced(
        canvas,
        squid,
        body=(sx, sy),
        tips=tips,
        touch_tips=frozenset({0, 3}),
        engaging=engaging,
        elapsed=elapsed,
        mids=mids,
    )
    draw_squid_body_lit(
        canvas, sx, sy,
        radius=squid.radius, scale=scale, rig=rig, kind="squid",
        facing=facing, pos=anchor, elapsed=elapsed, engaging=engaging,
    )
    _ = camera


def _draw_hostile_fighter(canvas: tk.Canvas, cx: float, cy: float, *, rig: LightRig, elapsed: float, yaw: float) -> None:
    angle = math.pi * 0.5 + math.sin(yaw + 0.4) * 0.18
    draw_hostile_fighter_ship(canvas, Vec2(cx, cy - 2.0), angle, scale=1.12, rig=rig)
    _ = elapsed


def _draw_drone(canvas: tk.Canvas, cx: float, cy: float, *, rig: LightRig, elapsed: float, yaw: float) -> None:
    drone = DroneWingman(pos=Vec2(cx, cy), facing_angle=math.pi * 0.5 + math.sin(yaw) * 0.25, heat=0.42)
    draw_drone_wingman_tactical(
        canvas,
        Vec2(cx, cy),
        drone.facing_angle,
        scale=1.05,
        drone=drone,
        rig=rig,
    )


def _draw_asteroid(canvas: tk.Canvas, cx: float, cy: float, *, rig: LightRig, elapsed: float) -> None:
    anchor = Vec2(0.0, 0.0)
    rock = make_asteroid(anchor, seed=412, size_class="rock", drift_kind="medium")
    camera = make_codex_camera(cx, cy, anchor, scale=0.58)
    draw_tactical_asteroid(
        canvas,
        rock,
        camera,
        hud_top=0.0,
        rig=rig,
        ship_pos=anchor,
        ship_angle=0.0,
    )
    _ = elapsed


def _draw_well(canvas: tk.Canvas, cx: float, cy: float, *, rig: LightRig) -> None:
    draw_well(
        canvas,
        Vec2(cx, cy),
        24.0,
        "",
        "black_hole",
        scale=0.72 * WELL_RING_VISUAL_SCALE,
        rig=rig,
    )


def _draw_beacon(canvas: tk.Canvas, cx: float, cy: float, *, rig: LightRig, elapsed: float) -> None:
    anchor = Vec2(0.0, 0.0)
    beacon = Beacon(pos=anchor, collected=False)
    bob = math.sin(elapsed * 3.0) * 2.0
    draw_beacon_play(
        canvas,
        cx,
        cy + bob,
        beacon,
        scale=0.72,
        rig=rig,
        elapsed=elapsed,
        seed=beacon_seed_from_pos(anchor),
        spark_orbits=True,
    )
