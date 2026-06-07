from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.space_station import SpaceStation
from gravity_ho_matey.gameplay.station_kinds import StationFaction
from gravity_ho_matey.gameplay.tractor_beam import TractorBeamState, TractorPhase
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.fog_viz import draw_ground_fog_glow
from gravity_ho_matey.render.health_bar_viz import draw_health_bar
from gravity_ho_matey.render.lighting import LightRig


def _hull_colors(faction: StationFaction) -> tuple[str, str, str]:
    if faction is StationFaction.FRIENDLY:
        return palette.STATION_FRIENDLY_HULL, palette.STATION_FRIENDLY_RING, palette.STATION_FRIENDLY_GLOW
    if faction is StationFaction.NEUTRAL:
        return palette.STATION_NEUTRAL_HULL, palette.STATION_NEUTRAL_RING, palette.STATION_NEUTRAL_GLOW
    return palette.STATION_HOSTILE_HULL, palette.STATION_HOSTILE_RING, palette.STATION_HOSTILE_GLOW


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
    sp = camera.world_to_screen(station.pos, ship_pos, ship_angle)
    tp = camera.world_to_screen(tractor.target_asteroid.pos, ship_pos, ship_angle)
    sx, sy = sp.x, sp.y + hud_top
    tx, ty = tp.x, tp.y + hud_top
    strength = 1.0 if tractor.phase is TractorPhase.PULLING else 0.55
    color = palette.STATION_TRACTOR_BEAM if tractor.phase is TractorPhase.PULLING else palette.STATION_TRACTOR_CORE
    canvas.create_line(sx, sy, tx, ty, fill=color, width=2 + int(strength * 2))
    canvas.create_oval(tx - 6, ty - 6, tx + 6, ty + 6, outline=palette.STATION_TRACTOR_CORE, width=1)


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
    p = camera.world_to_screen(station.pos, ship_pos, ship_angle)
    sx, sy = p.x, p.y + hud_top
    scale = camera.tactical_scale
    r = station.radius * scale
    hull, ring_color, glow = _hull_colors(station.faction)
    draw_ground_fog_glow(canvas, sx, sy + r * 0.15, r * 1.8, palette.CHASE_FOG_STATION, pulse=elapsed * 3.0)
    canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill=hull, outline=ring_color, width=2)
    ring_r = r * 0.72
    ring_w = max(2.0, r * 0.08)
    canvas.create_oval(
        sx - ring_r,
        sy - ring_r,
        sx + ring_r,
        sy + ring_r,
        outline=ring_color,
        width=int(ring_w),
    )
    gun_len = r * 0.55
    gx = sx + math.cos(station.facing_angle) * gun_len
    gy = sy + math.sin(station.facing_angle) * gun_len
    canvas.create_line(sx, sy, gx, gy, fill=glow, width=3)
    canvas.create_oval(gx - 4, gy - 4, gx + 4, gy + 4, fill=glow, outline="")
    if station.spawn_bay_open > 0.0:
        bay = Vec2.from_angle(station.facing_angle) * (r * 0.35)
        bx, by = sx + bay.x, sy + bay.y
        canvas.create_rectangle(bx - 8, by - 5, bx + 8, by + 5, fill=glow, outline="")
    hp_frac = station.hits_remaining / max(1, station.hits_max)
    draw_health_bar(
        canvas,
        sx,
        sy - r - 10,
        r * 1.4,
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
) -> None:
    if not station.alive:
        return
    sp = camera.world_to_screen(station.pos, ship_pos, ship_angle)
    if not sp.visible:
        return
    entity_scale = max(0.35, camera.perspective_scale(sp.depth) / camera.focal_length)
    r = min(station.radius * entity_scale, 34.0)
    hull, ring_color, glow = _hull_colors(station.faction)
    draw_ground_fog_glow(canvas, sp.x, sp.y + r * 0.2, r * 2.0, palette.CHASE_FOG_STATION[:3], pulse=elapsed * 4.0)
    canvas.create_oval(sp.x - r, sp.y - r, sp.x + r, sp.y + r, fill=hull, outline=ring_color, width=2)
    gun_len = r * 0.65
    gx = sp.x + math.cos(station.facing_angle) * gun_len
    gy = sp.y + math.sin(station.facing_angle) * gun_len
    canvas.create_line(sp.x, sp.y, gx, gy, fill=glow, width=2)
    hp_frac = station.hits_remaining / max(1, station.hits_max)
    draw_health_bar(
        canvas,
        sp.x,
        sp.y - r - 8,
        r * 1.2,
        hp_frac,
        outline=ring_color,
        low_fill=palette.STATION_HOSTILE_GLOW,
    )
