from __future__ import annotations

import math
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.space_station import SpaceStation
from gravity_ho_matey.gameplay.station_kinds import StationFaction
from gravity_ho_matey.gameplay.tractor_beam import TractorBeamState, TractorPhase
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.health_bar_viz import draw_health_bar
from gravity_ho_matey.render.lighting import LightRig, MaterialTones, chase_depth_fade, depth_faded_material, lerp_hex, station_material_for
from gravity_ho_matey.render.lit_draw import draw_simplified_polygon
from gravity_ho_matey.render.station_lit_draw import (
    draw_spawn_bay_highlight,
    draw_station_greeble_front,
    draw_station_greeble_mid,
    draw_station_layer_polygons,
    draw_station_rim_bloom,
    layer_nudge,
)
from gravity_ho_matey.render.station_mesh import StationMesh, local_to_world, mesh_for_station, ring_wobble_points, station_visual_seed

# Chase close-up cap — prevents fill-frame shear and facet clutter.
CHASE_STATION_MAX_R_PX = 118.0


@dataclass(frozen=True, slots=True)
class _ChaseStationFrame:
    cx: float
    cy: float
    forward: Vec2
    right: Vec2
    scale: float
    lateral_scale: float
    pitch: float
    shrink: float
    depth_fade: float
    r_px: float


def _glow_for_faction(faction: StationFaction) -> str:
    if faction is StationFaction.FRIENDLY:
        return palette.STATION_FRIENDLY_GLOW
    if faction is StationFaction.NEUTRAL:
        return palette.STATION_NEUTRAL_GLOW
    return palette.STATION_HOSTILE_GLOW


def _chase_mesh_extent_locals(mesh: StationMesh) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = list(mesh.back_ring) + list(mesh.front_hub) + list(mesh.turret)
    for arm in mesh.mid_arms:
        pts.extend(arm)
    if mesh.spawn_bay is not None:
        pts.extend(mesh.spawn_bay)
    return pts


def _chase_station_frame(
    station: SpaceStation,
    mesh: StationMesh,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
) -> _ChaseStationFrame | None:
    """Shared chase anchor + shrink so ring, arms, and hub stay rigidly aligned."""
    center = camera.world_to_chase_screen(
        station.pos,
        ship_pos,
        ship_angle,
        min_ahead=camera.min_depth,
        screen_margin=180.0,
    )
    if not center.visible:
        return None
    forward = Vec2.from_angle(ship_angle)
    right = forward.rotated(math.pi / 2.0)
    depth = max(camera.min_depth, center.depth)
    scale = camera.focal_length / depth
    lateral_scale = scale * camera.chase_thrust_boost
    pitch = 0.48 + camera.chase_lift / camera.focal_length
    cx, cy = center.x, center.y

    max_r = 0.0
    for lx, ly in _chase_mesh_extent_locals(mesh):
        world = local_to_world((lx, ly), station)
        rel = world - station.pos
        ahead = rel.dot(forward)
        lateral = rel.dot(right)
        max_r = max(max_r, math.hypot(lateral * lateral_scale, ahead * scale * pitch))

    shrink = 1.0
    r_px = max_r
    if max_r > CHASE_STATION_MAX_R_PX:
        shrink = CHASE_STATION_MAX_R_PX / max_r
        r_px = CHASE_STATION_MAX_R_PX

    return _ChaseStationFrame(
        cx=cx,
        cy=cy,
        forward=forward,
        right=right,
        scale=scale,
        lateral_scale=lateral_scale,
        pitch=pitch,
        shrink=shrink,
        depth_fade=chase_depth_fade(depth),
        r_px=r_px,
    )


def _chase_project_locals(
    local_pts: list[tuple[float, float]],
    station: SpaceStation,
    frame: _ChaseStationFrame,
) -> list[tuple[float, float]]:
    screen: list[tuple[float, float]] = []
    for lx, ly in local_pts:
        world = local_to_world((lx, ly), station)
        rel = world - station.pos
        ahead = rel.dot(frame.forward)
        lateral = rel.dot(frame.right)
        sx = lateral * frame.lateral_scale * frame.shrink
        sy = ahead * frame.scale * frame.pitch * frame.shrink
        screen.append((frame.cx + sx, frame.cy - sy))
    return screen


def _chase_project_point(
    local_xy: tuple[float, float],
    station: SpaceStation,
    frame: _ChaseStationFrame,
) -> tuple[float, float]:
    pts = _chase_project_locals([local_xy], station, frame)
    return pts[0]


def _expand_poly(
    pts: list[tuple[float, float]],
    cx: float,
    cy: float,
    factor: float,
) -> list[tuple[float, float]]:
    return [(cx + (x - cx) * factor, cy + (y - cy) * factor) for x, y in pts]


def _draw_chase_ring_bloom(
    canvas: tk.Canvas,
    ring_pts: list[tuple[float, float]],
    *,
    cx: float,
    cy: float,
    glow: str,
    material: MaterialTones,
    pulse: float,
) -> None:
    """Ring-following underglow — reads as dock structure, not a flat circle."""
    outer = _expand_poly(ring_pts, cx, cy, 1.08 + pulse * 0.04)
    inner = _expand_poly(ring_pts, cx, cy, 0.92)
    if len(outer) >= 3:
        canvas.create_polygon(
            *[coord for pt in outer for coord in pt],
            fill=lerp_hex(glow, material.deep, 0.84),
            outline="",
        )
    if len(inner) >= 3:
        canvas.create_polygon(
            *[coord for pt in inner for coord in pt],
            fill=lerp_hex(glow, material.deep, 0.93),
            outline="",
        )


def _draw_chase_lamps(
    canvas: tk.Canvas,
    mesh: StationMesh,
    station: SpaceStation,
    frame: _ChaseStationFrame,
    *,
    glow: str,
    elapsed: float,
    px_scale: float,
) -> None:
    pulse = 0.55 + 0.45 * math.sin(elapsed * 4.8)
    for lamp in mesh.lamps[:2]:
        sx, sy = _chase_project_point((lamp.x, lamp.y), station, frame)
        lr = max(2.0, lamp.radius * station.radius * px_scale * frame.shrink * 0.85)
        canvas.create_oval(sx - lr * 1.6, sy - lr * 1.6, sx + lr * 1.6, sy + lr * 1.6, fill=lerp_hex(glow, "#000000", 0.78), outline="")
        canvas.create_oval(
            sx - lr,
            sy - lr,
            sx + lr,
            sy + lr,
            fill=glow if pulse > 0.5 else lerp_hex(glow, "#000000", 0.35),
            outline="",
        )


def _draw_chase_truss_ticks(
    canvas: tk.Canvas,
    mesh: StationMesh,
    station: SpaceStation,
    frame: _ChaseStationFrame,
    *,
    material: MaterialTones,
) -> None:
    """Two subtle ring-to-hub struts — enough structure, not full greeble pass."""
    hub_pts = _chase_project_locals(mesh.front_hub, station, frame)
    if len(hub_pts) < 3:
        return
    hx = sum(x for x, _ in hub_pts) / len(hub_pts)
    hy = sum(y for _, y in hub_pts) / len(hub_pts)
    ring = ring_wobble_points(mesh, station)
    step = max(1, len(ring) // 4)
    for idx in (0, step * 2):
        rx, ry = _chase_project_point(ring[idx], station, frame)
        canvas.create_line(hx, hy, rx, ry, fill=lerp_hex(material.rim, material.deep, 0.45), width=1, dash=(3, 4))


def _screen_mapper(
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
) -> tuple[Callable[[Vec2], tuple[float, float]], float]:
    anchor = camera.world_to_screen(ship_pos, ship_pos, ship_angle)
    east = camera.world_to_screen(ship_pos + Vec2(120.0, 0.0), ship_pos, ship_angle)
    px_per_unit = abs(east.x - anchor.x) / 120.0

    def to_screen(world: Vec2) -> tuple[float, float]:
        sp = camera.world_to_screen(world, ship_pos, ship_angle)
        return sp.x, sp.y + hud_top

    return to_screen, px_per_unit


def _draw_lit_station(
    canvas: tk.Canvas,
    station: SpaceStation,
    *,
    to_screen: Callable[[Vec2], tuple[float, float]],
    px_per_unit: float,
    rig: LightRig,
    elapsed: float,
    depth_fade: float = 0.0,
) -> None:
    mesh = mesh_for_station(station)
    seed = station_visual_seed(station)
    material = station_material_for(station.faction, theme=rig.theme, view=rig.view)
    if depth_fade > 0.01:
        material = depth_faded_material(material, depth_fade)
    glow = _glow_for_faction(station.faction)

    ring = ring_wobble_points(mesh, station)
    nudge_back = layer_nudge("back", rig, pixel_scale=px_per_unit)
    nudge_mid = layer_nudge("mid", rig, pixel_scale=px_per_unit)
    nudge_front = layer_nudge("front", rig, pixel_scale=px_per_unit)

    draw_station_rim_bloom(
        canvas,
        ring,
        station=station,
        to_screen=to_screen,
        px_per_unit=px_per_unit,
        material=material,
        glow=glow,
    )
    draw_station_layer_polygons(
        canvas,
        [ring],
        station=station,
        to_screen=to_screen,
        px_per_unit=px_per_unit,
        rig=rig,
        material=material,
        layer="back",
        seed=seed,
        nudge=nudge_back,
    )
    draw_station_layer_polygons(
        canvas,
        mesh.mid_arms,
        station=station,
        to_screen=to_screen,
        px_per_unit=px_per_unit,
        rig=rig,
        material=material,
        layer="mid",
        seed=seed + 11,
        nudge=nudge_mid,
    )
    draw_station_greeble_mid(
        canvas,
        pods=mesh.pods,
        truss_lines=mesh.truss_lines,
        recesses=mesh.panel_recesses,
        station=station,
        to_screen=to_screen,
        px_per_unit=px_per_unit,
        rig=rig,
        material=material,
        nudge=nudge_mid,
    )
    draw_station_layer_polygons(
        canvas,
        [mesh.front_hub],
        station=station,
        to_screen=to_screen,
        px_per_unit=px_per_unit,
        rig=rig,
        material=material,
        layer="front",
        seed=seed + 23,
        nudge=nudge_front,
    )
    draw_station_layer_polygons(
        canvas,
        [mesh.turret],
        station=station,
        to_screen=to_screen,
        px_per_unit=px_per_unit,
        rig=rig,
        material=material,
        layer="front",
        seed=seed + 37,
        nudge=nudge_front,
    )
    if mesh.spawn_bay is not None:
        draw_spawn_bay_highlight(
            canvas,
            mesh.spawn_bay,
            station=station,
            to_screen=to_screen,
            px_per_unit=px_per_unit,
            nudge=nudge_front,
            glow=glow,
            open_frac=station.spawn_bay_open,
        )
    draw_station_greeble_front(
        canvas,
        recesses=mesh.panel_recesses,
        lamps=mesh.lamps,
        antennas=mesh.antennas,
        window_slits=mesh.window_slits,
        station=station,
        to_screen=to_screen,
        px_per_unit=px_per_unit,
        rig=rig,
        material=material,
        glow=glow,
        elapsed=elapsed,
        nudge=nudge_front,
    )


def chase_station_screen_points(
    local_pts: list[tuple[float, float]],
    station: SpaceStation,
    camera: ViewCamera,
    ship_pos: Vec2,
    ship_angle: float,
) -> tuple[list[tuple[float, float]], float, float] | None:
    """Rigid chase projection anchored at station center — avoids per-vertex depth shear."""
    mesh = mesh_for_station(station)
    frame = _chase_station_frame(station, mesh, camera, ship_pos, ship_angle)
    if frame is None or len(local_pts) < 3:
        return None
    screen = _chase_project_locals(local_pts, station, frame)
    return screen, frame.r_px, frame.depth_fade


def _draw_chase_station(
    canvas: tk.Canvas,
    station: SpaceStation,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    rig: LightRig,
    elapsed: float,
) -> float | None:
    """Chase station — ring-hub-arms silhouette matching tactical topology without full greeble."""
    mesh = mesh_for_station(station)
    ring = ring_wobble_points(mesh, station)
    material = station_material_for(station.faction, theme=rig.theme, view=rig.view)
    glow = _glow_for_faction(station.faction)

    frame = _chase_station_frame(station, mesh, camera, ship_pos, ship_angle)
    if frame is None:
        return None

    if frame.depth_fade > 0.01:
        material = depth_faded_material(material, frame.depth_fade)

    ring_pts = _chase_project_locals(ring, station, frame)
    hub_pts = _chase_project_locals(mesh.front_hub, station, frame)
    if len(ring_pts) < 3 or len(hub_pts) < 3:
        return None

    cx = sum(x for x, _ in hub_pts) / len(hub_pts)
    cy = sum(y for _, y in hub_pts) / len(hub_pts)
    pulse = 0.82 + 0.18 * math.sin(elapsed * 2.4)

    arm_material = MaterialTones(
        highlight=lerp_hex(material.highlight, material.shadow, 0.35),
        mid=lerp_hex(material.mid, material.deep, 0.28),
        shadow=material.deep,
        deep=material.deep,
        rim=lerp_hex(material.rim, material.deep, 0.35),
        crater_pit=material.crater_pit,
        crater_rim_hi=material.crater_rim_hi,
    )
    turret_material = MaterialTones(
        highlight=material.highlight,
        mid=lerp_hex(material.mid, material.highlight, 0.18),
        shadow=material.shadow,
        deep=material.deep,
        rim=material.rim,
        crater_pit=material.crater_pit,
        crater_rim_hi=material.crater_rim_hi,
    )

    px_scale = frame.r_px / max(station.radius, 1.0)
    _draw_chase_ring_bloom(canvas, ring_pts, cx=cx, cy=cy, glow=glow, material=material, pulse=pulse)

    for arm in mesh.mid_arms:
        arm_pts = _chase_project_locals(arm, station, frame)
        if len(arm_pts) >= 3:
            draw_simplified_polygon(canvas, arm_pts, rig=rig, material=arm_material, outline_width=1)

    _draw_chase_truss_ticks(canvas, mesh, station, frame, material=material)
    draw_simplified_polygon(canvas, ring_pts, rig=rig, material=material, outline_width=2)
    draw_simplified_polygon(canvas, hub_pts, rig=rig, material=material, outline_width=1)

    turret_pts = _chase_project_locals(mesh.turret, station, frame)
    if len(turret_pts) >= 3:
        draw_simplified_polygon(canvas, turret_pts, rig=rig, material=turret_material, outline_width=1)

    if mesh.spawn_bay is not None and station.spawn_bay_open > 0.08:
        bay_pts = _chase_project_locals(mesh.spawn_bay, station, frame)
        if len(bay_pts) >= 3:
            canvas.create_polygon(
                *[coord for pt in bay_pts for coord in pt],
                fill=lerp_hex(glow, material.deep, 0.55),
                outline=glow,
                width=1,
            )

    _draw_chase_lamps(canvas, mesh, station, frame, glow=glow, elapsed=elapsed, px_scale=px_scale)

    canvas.create_polygon(
        *[coord for pt in ring_pts for coord in pt],
        fill="",
        outline=glow,
        width=1,
    )
    return frame.r_px


def draw_tractor_beam_tactical(
    canvas: tk.Canvas,
    station: SpaceStation,
    tractor: TractorBeamState,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
) -> None:
    if tractor.target_asteroid is None:
        return
    if tractor.phase in (TractorPhase.IDLE, TractorPhase.COOLDOWN):
        return
    to_screen, _ = _screen_mapper(camera, ship_pos, ship_angle, hud_top)
    sp = to_screen(station.pos)
    tp = to_screen(tractor.target_asteroid.pos)
    color = palette.STATION_TRACTOR_BEAM if tractor.phase is TractorPhase.PULLING else palette.STATION_TRACTOR_CORE
    canvas.create_line(sp[0], sp[1], tp[0], tp[1], fill=color, width=3)
    canvas.create_oval(tp[0] - 6, tp[1] - 6, tp[0] + 6, tp[1] + 6, outline=palette.STATION_TRACTOR_CORE, width=1)


def draw_space_station_tactical(
    canvas: tk.Canvas,
    station: SpaceStation,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
    tractor: TractorBeamState | None = None,
) -> None:
    if not station.alive:
        return
    if tractor is not None:
        draw_tractor_beam_tactical(
            canvas,
            station,
            tractor,
            camera,
            ship_pos=ship_pos,
            ship_angle=ship_angle,
            hud_top=hud_top,
        )
    to_screen, px_per_unit = _screen_mapper(camera, ship_pos, ship_angle, hud_top)
    center = to_screen(station.pos)
    r_px = station.radius * px_per_unit
    draw_ground_fog_glow(canvas, center[0], center[1] + r_px * 0.12, r_px * 1.6, palette.CHASE_FOG_STATION, pulse=elapsed * 3.0)
    _draw_lit_station(
        canvas,
        station,
        to_screen=to_screen,
        px_per_unit=px_per_unit,
        rig=rig,
        elapsed=elapsed,
    )
    hp_frac = station.hits_remaining / max(1, station.hits_max)
    ring_color = _glow_for_faction(station.faction)
    draw_health_bar(
        canvas,
        center[0],
        center[1] - r_px - 10,
        r_px * 1.35,
        hp_frac,
        outline=ring_color,
        low_fill=palette.STATION_HOSTILE_GLOW,
    )


def draw_space_station_chase(
    canvas: tk.Canvas,
    station: SpaceStation,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    elapsed: float,
    rig: LightRig,
    depth_fade: float = 0.0,
) -> None:
    if not station.alive:
        return
    sp = camera.world_to_screen(station.pos, ship_pos, ship_angle)
    if not sp.visible:
        return
    _ = depth_fade
    r_px = _draw_chase_station(
        canvas,
        station,
        camera,
        ship_pos=ship_pos,
        ship_angle=ship_angle,
        rig=rig,
        elapsed=elapsed,
    )
    if r_px is None:
        return
    draw_ground_fog_glow(
        canvas,
        sp.x,
        sp.y + r_px * 0.12,
        r_px * 1.05,
        palette.CHASE_FOG_STATION[:3],
        pulse=elapsed * 3.0,
    )
    hp_frac = station.hits_remaining / max(1, station.hits_max)
    draw_health_bar(
        canvas,
        sp.x,
        sp.y - r_px - 8,
        r_px * 1.05,
        hp_frac,
        outline=_glow_for_faction(station.faction),
        low_fill=palette.STATION_HOSTILE_GLOW,
    )


def draw_map_station_glyph(
    canvas: tk.Canvas,
    center: Vec2,
    station: SpaceStation,
    *,
    scale: float,
    rig: LightRig,
) -> None:
    """Holo chart station — simplified lit ring hub."""
    material = station_material_for(station.faction, theme=rig.theme, view=rig.view)
    mesh = mesh_for_station(station)
    cx, cy = center.x, center.y
    glyph_r = 10.0 * scale

    def local_to_screen(lx: float, ly: float) -> tuple[float, float]:
        return cx + lx * glyph_r, cy - ly * glyph_r

    def to_screen_from_local(local: tuple[float, float]) -> tuple[float, float]:
        return local_to_screen(local[0], local[1])

    ring_pts = [to_screen_from_local(p) for p in mesh.back_ring]
    if len(ring_pts) >= 3:
        draw_simplified_polygon(canvas, ring_pts, rig=rig, material=material, outline_width=1)
    hub_pts = [to_screen_from_local(p) for p in mesh.front_hub]
    if len(hub_pts) >= 3:
        draw_simplified_polygon(canvas, hub_pts, rig=rig, material=material, outline_width=1)
    glow = _glow_for_faction(station.faction)
    canvas.create_text(cx, cy - glyph_r - 6, text=station.station_label[:3], fill=glow, font=("Courier New", 7, "bold"))
