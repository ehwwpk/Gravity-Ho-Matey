from __future__ import annotations

import math
import tkinter as tk
from collections.abc import Callable

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.space_station import SpaceStation
from gravity_ho_matey.render.lighting import LightRig, MaterialTones, lerp_hex
from gravity_ho_matey.render.lit_draw import draw_illustrated_polygon
from gravity_ho_matey.render.station_mesh import GreebleAntenna, GreebleLamp, GreeblePod, PanelRecess, local_to_world


def layer_material(base: MaterialTones, layer: str) -> MaterialTones:
    if layer == "back":
        return MaterialTones(
            highlight=lerp_hex(base.highlight, base.shadow, 0.55),
            mid=lerp_hex(base.mid, base.deep, 0.35),
            shadow=lerp_hex(base.shadow, base.deep, 0.25),
            deep=base.deep,
            rim=lerp_hex(base.rim, base.deep, 0.4),
            crater_pit=base.crater_pit,
            crater_rim_hi=lerp_hex(base.crater_rim_hi, base.shadow, 0.35),
        )
    if layer == "front":
        return MaterialTones(
            highlight=base.highlight,
            mid=lerp_hex(base.mid, base.highlight, 0.12),
            shadow=base.shadow,
            deep=base.deep,
            rim=base.rim,
            crater_pit=base.crater_pit,
            crater_rim_hi=base.crater_rim_hi,
        )
    return base


def _flat(points: list[tuple[float, float]]) -> list[float]:
    out: list[float] = []
    for x, y in points:
        out.extend((x, y))
    return out


def _to_screen_poly(
    local_pts: list[tuple[float, float]],
    station: SpaceStation,
    *,
    to_screen: Callable[[Vec2], tuple[float, float]],
    nudge: tuple[float, float],
) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for lx, ly in local_pts:
        world = local_to_world((lx, ly), station)
        sx, sy = to_screen(world)
        out.append((sx + nudge[0], sy + nudge[1]))
    return out


def _world_size(normalized: float, station: SpaceStation, px_per_unit: float) -> float:
    return normalized * station.radius * px_per_unit


def _draw_panel_recess(
    canvas: tk.Canvas,
    recess: PanelRecess,
    station: SpaceStation,
    *,
    to_screen: Callable[[Vec2], tuple[float, float]],
    px_per_unit: float,
    nudge: tuple[float, float],
    rig: LightRig,
    material: MaterialTones,
) -> None:
    screen: list[tuple[float, float]] = []
    for clx, cly in [
        (-recess.half_w, -recess.half_h),
        (recess.half_w, -recess.half_h),
        (recess.half_w, recess.half_h),
        (-recess.half_w, recess.half_h),
    ]:
        ox = recess.cx + clx * math.cos(recess.angle) - cly * math.sin(recess.angle)
        oy = recess.cy + clx * math.sin(recess.angle) + cly * math.cos(recess.angle)
        wx, wy = to_screen(local_to_world((ox, oy), station))
        screen.append((wx + nudge[0], wy + nudge[1]))
    if len(screen) < 3:
        return
    cx = sum(x for x, _ in screen) / len(screen)
    cy = sum(y for _, y in screen) / len(screen)
    canvas.create_polygon(*_flat(screen), fill=material.crater_pit, outline="")
    hw = _world_size(recess.half_w, station, px_per_unit)
    hx = cx + rig.key_dir.x * hw * 0.35
    hy = cy + rig.key_dir.y * hw * 0.35
    canvas.create_line(hx - hw * 0.5, hy, hx + hw * 0.25, hy, fill=material.crater_rim_hi, width=1)


def _draw_pod(
    canvas: tk.Canvas,
    pod: GreeblePod,
    station: SpaceStation,
    *,
    to_screen: Callable[[Vec2], tuple[float, float]],
    px_per_unit: float,
    nudge: tuple[float, float],
    material: MaterialTones,
) -> None:
    cx, cy = to_screen(local_to_world((pod.cx, pod.cy), station))
    cx += nudge[0]
    cy += nudge[1]
    rx = _world_size(pod.rx, station, px_per_unit)
    ry = _world_size(pod.ry, station, px_per_unit)
    canvas.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, fill=material.shadow, outline=material.rim, width=1)


def _draw_lamp(
    canvas: tk.Canvas,
    lamp: GreebleLamp,
    station: SpaceStation,
    *,
    to_screen: Callable[[Vec2], tuple[float, float]],
    px_per_unit: float,
    nudge: tuple[float, float],
    glow: str,
    elapsed: float,
) -> None:
    pulse = 0.65 + 0.35 * math.sin(elapsed * 4.2 + lamp.x * 8.0)
    sx, sy = to_screen(local_to_world((lamp.x, lamp.y), station))
    sx += nudge[0]
    sy += nudge[1]
    r = _world_size(lamp.radius, station, px_per_unit) * (0.9 + pulse * 0.2)
    canvas.create_oval(sx - r * 1.8, sy - r * 1.8, sx + r * 1.8, sy + r * 1.8, fill=lerp_hex(glow, "#000000", 0.75), outline="")
    canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill=glow if pulse > 0.55 else lerp_hex(glow, "#000000", 0.35), outline="")


def _draw_antenna(
    canvas: tk.Canvas,
    antenna: GreebleAntenna,
    station: SpaceStation,
    *,
    to_screen: Callable[[Vec2], tuple[float, float]],
    px_per_unit: float,
    nudge: tuple[float, float],
    material: MaterialTones,
) -> None:
    bx, by = to_screen(local_to_world((antenna.bx, antenna.by), station))
    tx, ty = to_screen(local_to_world((antenna.tx, antenna.ty), station))
    bx += nudge[0]
    by += nudge[1]
    tx += nudge[0]
    ty += nudge[1]
    canvas.create_line(bx, by, tx, ty, fill=material.rim, width=2)
    dr = _world_size(antenna.dish, station, px_per_unit)
    canvas.create_oval(tx - dr, ty - dr, tx + dr, ty + dr, fill=material.mid, outline=material.highlight, width=1)


def _draw_window_slit(
    canvas: tk.Canvas,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    station: SpaceStation,
    *,
    to_screen: Callable[[Vec2], tuple[float, float]],
    nudge: tuple[float, float],
    glow: str,
) -> None:
    ax, ay = to_screen(local_to_world((x0, y0), station))
    bx, by = to_screen(local_to_world((x1, y1), station))
    canvas.create_line(ax + nudge[0], ay + nudge[1], bx + nudge[0], by + nudge[1], fill=glow, width=2)


def layer_nudge(layer: str, rig: LightRig, *, pixel_scale: float) -> tuple[float, float]:
    mag = max(1.5, pixel_scale * 2.8)
    if layer == "back":
        return (-rig.key_dir.x * mag, -rig.key_dir.y * mag)
    if layer == "front":
        return (rig.key_dir.x * mag * 0.85, rig.key_dir.y * mag * 0.85)
    return (0.0, 0.0)


def draw_station_layer_polygons(
    canvas: tk.Canvas,
    polys: list[list[tuple[float, float]]],
    *,
    station: SpaceStation,
    to_screen: Callable[[Vec2], tuple[float, float]],
    px_per_unit: float,
    rig: LightRig,
    material: MaterialTones,
    layer: str,
    seed: int,
    nudge: tuple[float, float],
) -> None:
    mat = layer_material(material, layer)
    radius_hint = station.radius * px_per_unit
    for poly in polys:
        if len(poly) < 3:
            continue
        screen = _to_screen_poly(poly, station, to_screen=to_screen, nudge=nudge)
        draw_illustrated_polygon(
            canvas,
            screen,
            rig=rig,
            material=mat,
            seed=seed + len(poly),
            radius_hint=radius_hint,
            outline_width=2 if layer == "front" else 1,
            crater_count=0,
        )


def draw_station_greeble_mid(
    canvas: tk.Canvas,
    *,
    pods: list[GreeblePod],
    truss_lines: list[tuple[float, float, float, float]],
    recesses: list[PanelRecess],
    station: SpaceStation,
    to_screen: Callable[[Vec2], tuple[float, float]],
    px_per_unit: float,
    rig: LightRig,
    material: MaterialTones,
    nudge: tuple[float, float],
) -> None:
    mat = layer_material(material, "mid")
    for x1, y1, x2, y2 in truss_lines:
        ax, ay = to_screen(local_to_world((x1, y1), station))
        bx, by = to_screen(local_to_world((x2, y2), station))
        canvas.create_line(
            ax + nudge[0],
            ay + nudge[1],
            bx + nudge[0],
            by + nudge[1],
            fill=mat.rim,
            width=1,
            dash=(4, 3),
        )
    for pod in pods:
        _draw_pod(canvas, pod, station, to_screen=to_screen, px_per_unit=px_per_unit, nudge=nudge, material=mat)
    split = max(3, len(recesses) // 2)
    for recess in recesses[:split]:
        _draw_panel_recess(
            canvas,
            recess,
            station,
            to_screen=to_screen,
            px_per_unit=px_per_unit,
            nudge=nudge,
            rig=rig,
            material=mat,
        )


def draw_station_greeble_front(
    canvas: tk.Canvas,
    *,
    recesses: list[PanelRecess],
    lamps: list[GreebleLamp],
    antennas: list[GreebleAntenna],
    window_slits: list[tuple[float, float, float, float]],
    station: SpaceStation,
    to_screen: Callable[[Vec2], tuple[float, float]],
    px_per_unit: float,
    rig: LightRig,
    material: MaterialTones,
    glow: str,
    elapsed: float,
    nudge: tuple[float, float],
) -> None:
    mat = layer_material(material, "front")
    split = max(3, len(recesses) // 2)
    for recess in recesses[split:]:
        _draw_panel_recess(
            canvas,
            recess,
            station,
            to_screen=to_screen,
            px_per_unit=px_per_unit,
            nudge=nudge,
            rig=rig,
            material=mat,
        )
    for slit in window_slits:
        _draw_window_slit(
            canvas,
            slit[0],
            slit[1],
            slit[2],
            slit[3],
            station,
            to_screen=to_screen,
            nudge=nudge,
            glow=glow,
        )
    for lamp in lamps:
        _draw_lamp(
            canvas,
            lamp,
            station,
            to_screen=to_screen,
            px_per_unit=px_per_unit,
            nudge=nudge,
            glow=glow,
            elapsed=elapsed,
        )
    for antenna in antennas:
        _draw_antenna(
            canvas,
            antenna,
            station,
            to_screen=to_screen,
            px_per_unit=px_per_unit,
            nudge=nudge,
            material=mat,
        )


def draw_spawn_bay_highlight(
    canvas: tk.Canvas,
    bay: list[tuple[float, float]],
    *,
    station: SpaceStation,
    to_screen: Callable[[Vec2], tuple[float, float]],
    px_per_unit: float,
    nudge: tuple[float, float],
    glow: str,
    open_frac: float,
) -> None:
    _ = px_per_unit
    if open_frac <= 0.05:
        return
    screen = _to_screen_poly(bay, station, to_screen=to_screen, nudge=nudge)
    if len(screen) < 3:
        return
    fill = lerp_hex(glow, "#000000", 1.0 - min(1.0, open_frac))
    canvas.create_polygon(*_flat(screen), fill=fill, outline=glow, width=1)


def draw_station_rim_bloom(
    canvas: tk.Canvas,
    ring: list[tuple[float, float]],
    *,
    station: SpaceStation,
    to_screen: Callable[[Vec2], tuple[float, float]],
    px_per_unit: float,
    material: MaterialTones,
    glow: str,
) -> None:
    screen = _to_screen_poly(ring, station, to_screen=to_screen, nudge=(0.0, 0.0))
    if len(screen) < 3:
        return
    cx = sum(x for x, _ in screen) / len(screen)
    cy = sum(y for _, y in screen) / len(screen)
    r = max(8.0, station.radius * px_per_unit * 0.35)
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=lerp_hex(glow, material.deep, 0.82), outline="")
    canvas.create_polygon(*_flat(screen), fill="", outline=material.rim, width=1)
