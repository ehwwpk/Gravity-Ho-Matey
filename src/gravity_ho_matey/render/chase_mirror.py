from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.gravity_field import GravityField
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.gravity_field_viz import heatmap_cell_visible, inside_black_hole_footprint
from gravity_ho_matey.render.launch_countdown_overlay import accent_for_theme
from gravity_ho_matey.render.world_draw import gravity_field_color

# Rear-view mirror — ship-frame tactical display (presentation only).
_MIRROR_W = 332.0
_MIRROR_H = 96.0
_MIRROR_TOP_PAD = 8.0
_REAR_MIN_AFT = 10.0
_REAR_RANGE = 620.0
_LATERAL_RANGE = 420.0
_LATERAL_FRAC = 0.48
_HEAT_AFT_STEPS = 7
_HEAT_LAT_STEPS = 11
_RANGE_TICKS = (180.0, 360.0, 540.0)


def mirror_layout(camera: ViewCamera, hud_top: float) -> tuple[float, float, float, float]:
    vw = camera.viewport_width
    x = vw * 0.5 - _MIRROR_W * 0.5
    y = hud_top + _MIRROR_TOP_PAD
    return x, y, _MIRROR_W, _MIRROR_H


def _ship_frame(ship_angle: float) -> tuple[Vec2, Vec2]:
    forward = Vec2.from_angle(ship_angle)
    return forward, forward.rotated(math.pi / 2.0)


def world_to_mirror(
    world_pos: Vec2,
    ship_pos: Vec2,
    ship_angle: float,
    mirror_x: float,
    mirror_y: float,
    mirror_w: float,
    mirror_h: float,
    *,
    clamp: bool = False,
) -> tuple[float, float, float] | None:
    """Map world point to mirror pixel. Returns (x, y, aft) or None if not behind ship."""
    forward, right = _ship_frame(ship_angle)
    rel = world_pos - ship_pos
    aft = -rel.dot(forward)
    lateral = rel.dot(right)
    if aft < _REAR_MIN_AFT:
        return None

    cx = mirror_x + mirror_w * 0.5
    px = cx + (lateral / _LATERAL_RANGE) * (mirror_w * _LATERAL_FRAC)
    py = mirror_y + mirror_h - 12.0 - (aft / _REAR_RANGE) * (mirror_h - 18.0)
    inset = 6.0
    if clamp:
        px = max(mirror_x + inset, min(mirror_x + mirror_w - inset, px))
        py = max(mirror_y + inset, min(mirror_y + mirror_h - inset, py))
        return px, py, aft
    if px < mirror_x + inset or px > mirror_x + mirror_w - inset:
        return None
    if py < mirror_y + inset or py > mirror_y + mirror_h - inset:
        return None
    return px, py, aft


def _closing_from_behind(
    obj_pos: Vec2,
    obj_vel: Vec2,
    ship_pos: Vec2,
    ship_vel: Vec2,
    ship_angle: float,
) -> float:
    forward, _ = _ship_frame(ship_angle)
    rel = obj_pos - ship_pos
    if -rel.dot(forward) < _REAR_MIN_AFT:
        return 0.0
    return max(0.0, -(obj_vel - ship_vel).dot(forward))


def _draw_mirror_chrome(
    canvas: tk.Canvas,
    mx: float,
    my: float,
    mw: float,
    mh: float,
    *,
    accent: str,
    dim: str,
) -> None:
    canvas.create_rectangle(mx, my, mx + mw, my + mh, fill="#040810", outline=accent, width=2)
    canvas.create_rectangle(mx + 2, my + 2, mx + mw - 2, my + mh - 2, outline="#0a1828", width=1)
    for ox, oy in ((mx + 4, my + 4), (mx + mw - 4, my + 4)):
        canvas.create_line(ox, oy, ox + (8 if ox < mx + mw * 0.5 else -8), oy, fill=accent, width=2)
        canvas.create_line(ox, oy, ox, oy + 8, fill=accent, width=2)
    canvas.create_line(mx + 10, my + mh - 2, mx + mw - 10, my + mh - 2, fill=dim, width=1)
    canvas.create_line(mx + mw * 0.5, my + 14, mx + mw * 0.5, my + mh - 10, fill=dim, width=1, dash=(2, 5))
    canvas.create_text(mx + mw * 0.5, my + 10, text="◈ REAR TACTICAL ◈", fill=dim, font=("Courier", 7, "bold"))


def _draw_range_ruler(canvas: tk.Canvas, mx: float, my: float, mw: float, mh: float, *, dim: str) -> None:
    rx = mx + mw - 8
    for dist in _RANGE_TICKS:
        py = my + mh - 12.0 - (dist / _REAR_RANGE) * (mh - 18.0)
        if py < my + 16 or py > my + mh - 8:
            continue
        canvas.create_line(mx + mw - 22, py, rx, py, fill=dim, width=1)
        canvas.create_text(rx - 2, py, text=f"{int(dist)}", anchor="e", fill=dim, font=("Courier", 6))


def _draw_gravity_heatmap(
    canvas: tk.Canvas,
    world: GameWorld,
    field: GravityField,
    ship_pos: Vec2,
    ship_angle: float,
    mx: float,
    my: float,
    mw: float,
    mh: float,
    *,
    elapsed: float,
) -> None:
    forward, right = _ship_frame(ship_angle)
    pulse = 0.85 + 0.15 * math.sin(elapsed * 2.4)
    for ai in range(_HEAT_AFT_STEPS):
        aft = _REAR_MIN_AFT + (ai + 0.5) * (_REAR_RANGE - _REAR_MIN_AFT) / _HEAT_AFT_STEPS
        for li in range(_HEAT_LAT_STEPS):
            t = li / max(1, _HEAT_LAT_STEPS - 1) - 0.5
            lateral = t * _LATERAL_RANGE
            world_pt = ship_pos - forward * aft + right * lateral
            hit = world_to_mirror(world_pt, ship_pos, ship_angle, mx, my, mw, mh, clamp=True)
            if hit is None:
                continue
            px, py, _ = hit
            norm = field.normalized_magnitude_at(world_pt)
            if not heatmap_cell_visible(norm):
                continue
            if inside_black_hole_footprint(world.wells, world_pt.x, world_pt.y):
                continue
            tone = gravity_field_color(norm)
            tw = mw * _LATERAL_FRAC / _HEAT_LAT_STEPS * 0.92
            th = (mh - 18.0) / _HEAT_AFT_STEPS * 0.82
            alpha_strength = min(1.0, norm * 1.15 * pulse)
            if alpha_strength < 0.12:
                continue
            canvas.create_rectangle(
                px - tw * 0.5,
                py - th * 0.5,
                px + tw * 0.5,
                py + th * 0.5,
                fill=tone,
                outline="",
            )


def _draw_velocity_chevron(
    canvas: tk.Canvas,
    px: float,
    py: float,
    vel: Vec2,
    ship_angle: float,
    *,
    color: str,
    scale: float = 1.0,
) -> None:
    if vel.length_sq() < 400.0:
        return
    _, right = _ship_frame(ship_angle)
    forward, _ = _ship_frame(ship_angle)
    lat = vel.dot(right)
    mag = min(10.0, vel.length() * 0.04) * scale
    tip_x = px + right.x * lat * 0.015 * scale
    tip_y = py + right.y * lat * 0.015 * scale - forward.y * mag * 0.02
    canvas.create_line(px, py, tip_x, tip_y, fill=color, width=2)


def draw_rear_view_mirror(
    canvas: tk.Canvas,
    world: GameWorld,
    camera: ViewCamera,
    field: GravityField,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    ship_vel: Vec2,
    hud_top: float,
    elapsed: float = 0.0,
) -> None:
    mx, my, mw, mh = mirror_layout(camera, hud_top)
    accent = accent_for_theme(world.config.level_theme)
    dim = palette.HELM_HUD_DIM

    _draw_mirror_chrome(canvas, mx, my, mw, mh, accent=accent, dim=dim)
    _draw_gravity_heatmap(canvas, world, field, ship_pos, ship_angle, mx, my, mw, mh, elapsed=elapsed)
    _draw_range_ruler(canvas, mx, my, mw, mh, dim=dim)

    blips: list[tuple[float, float, str, float, float, float, str, Vec2 | None]] = []

    for well in world.wells:
        hit = world_to_mirror(well.pos, ship_pos, ship_angle, mx, my, mw, mh)
        if hit is None:
            continue
        px, py, aft = hit
        closing = _closing_from_behind(well.pos, Vec2(), ship_pos, ship_vel, ship_angle)
        if well.kind == "black_hole":
            color = palette.BLACK_HOLE_RING
            size = max(6.0, min(16.0, well.radius * 0.048))
            kind = "well_lethal"
        elif well.kind == "planet":
            color = palette.PLANET_WELL
            size = max(5.0, min(14.0, well.radius * 0.042))
            kind = "well_lethal"
        else:
            color = palette.WELL
            size = 6.0
            kind = "well"
        blips.append((aft, closing, kind, px, py, size, color, None))

    for beacon in world.beacons:
        if beacon.collected:
            continue
        hit = world_to_mirror(beacon.pos, ship_pos, ship_angle, mx, my, mw, mh)
        if hit is None:
            continue
        px, py, aft = hit
        closing = _closing_from_behind(beacon.pos, Vec2(), ship_pos, ship_vel, ship_angle)
        blips.append((aft, closing, "beacon", px, py, 6.0, palette.BEACON, None))

    for enemy in world.enemies:
        if not enemy.alive:
            continue
        hit = world_to_mirror(enemy.pos, ship_pos, ship_angle, mx, my, mw, mh)
        if hit is None:
            continue
        px, py, aft = hit
        closing = _closing_from_behind(enemy.pos, enemy.vel, ship_pos, ship_vel, ship_angle)
        if enemy.kind is EnemyKind.SQUID:
            blips.append((aft, closing, "squid", px, py, 7.0, palette.SQUID_TENTACLE, enemy.vel))
        else:
            blips.append((aft, closing, "enemy", px, py, 6.0, palette.ENEMY, enemy.vel))

    for asteroid in world.asteroids:
        hit = world_to_mirror(asteroid.pos, ship_pos, ship_angle, mx, my, mw, mh)
        if hit is None:
            continue
        px, py, aft = hit
        closing = _closing_from_behind(asteroid.pos, asteroid.vel, ship_pos, ship_vel, ship_angle)
        size = max(4.0, min(9.0, asteroid.approximate_radius() * 0.12))
        blips.append((aft, closing, "asteroid", px, py, size, palette.ASTEROID_EDGE, asteroid.vel))

    for projectile in world.projectiles:
        hit = world_to_mirror(projectile.pos, ship_pos, ship_angle, mx, my, mw, mh)
        if hit is None:
            continue
        px, py, aft = hit
        closing = _closing_from_behind(projectile.pos, projectile.vel, ship_pos, ship_vel, ship_angle)
        color = palette.HOSTILE_PROJECTILE if projectile.hostile else palette.PROJECTILE
        kind = "hostile_shot" if projectile.hostile else "shot"
        blips.append((aft, closing, kind, px, py, 4.0 if projectile.hostile else 3.0, color, projectile.vel))

    blips.sort(key=lambda item: item[0], reverse=True)
    pulse = 0.5 + 0.5 * math.sin(elapsed * 5.0)
    for _aft, closing, kind, px, py, size, color, vel in blips:
        boost = min(1.35, 1.0 + closing * 0.0018)
        draw_size = size * boost
        if kind in ("well_lethal", "enemy", "hostile_shot", "asteroid", "squid", "beacon") and closing > 40.0:
            ring_r = draw_size + 3.0 + pulse * 2.0
            if kind == "well_lethal":
                ring_color = palette.BLACK_HOLE_RING
            elif kind == "enemy":
                ring_color = palette.ENEMY_EDGE
            elif kind == "squid":
                ring_color = palette.SQUID_CORE
            elif kind == "beacon":
                ring_color = palette.BEACON
            elif kind == "hostile_shot":
                ring_color = palette.HOSTILE_PROJECTILE
            else:
                ring_color = palette.HOLO_ASTEROID_EDGE
            canvas.create_oval(px - ring_r, py - ring_r, px + ring_r, py + ring_r, outline=ring_color, width=1)

        if kind in ("well", "well_lethal"):
            r = draw_size
            canvas.create_oval(px - r, py - r * 0.55, px + r, py + r * 0.55, outline=color, width=2)
        elif kind == "beacon":
            s = draw_size
            glow_r = s + 4.0 + pulse * 3.0
            canvas.create_oval(px - glow_r, py - glow_r, px + glow_r, py + glow_r, outline=palette.BEACON, width=1)
            canvas.create_polygon(px, py - s, px + s, py, px, py + s, px - s, py, fill=color, outline=palette.BEACON_COLLECTED, width=1)
            canvas.create_oval(px - 2, py - 2, px + 2, py + 2, fill="#e8fff8", outline="")
        elif kind == "enemy":
            canvas.create_oval(px - draw_size, py - draw_size, px + draw_size, py + draw_size, fill=color, outline=palette.ENEMY_EDGE, width=1)
            if vel is not None:
                _draw_velocity_chevron(canvas, px, py, vel, ship_angle, color=palette.ENEMY_EDGE)
        elif kind == "squid":
            for i in range(5):
                angle = (math.tau * i / 5) + pulse * 0.5
                tx = px + math.cos(angle) * draw_size * 2.4
                ty = py + math.sin(angle) * draw_size * 2.4
                canvas.create_line(px, py, tx, ty, fill=palette.SQUID_TENTACLE, width=2)
            canvas.create_oval(px - draw_size, py - draw_size, px + draw_size, py + draw_size, fill=palette.SQUID_BODY, outline=palette.SQUID_CORE, width=1)
        elif kind == "asteroid":
            s = draw_size
            canvas.create_polygon(
                px,
                py - s,
                px + s * 0.85,
                py + s * 0.35,
                px,
                py + s,
                px - s * 0.9,
                py - s * 0.2,
                fill=palette.ASTEROID,
                outline=color,
                width=1,
            )
            if vel is not None:
                _draw_velocity_chevron(canvas, px, py, vel, ship_angle, color=color)
        elif kind == "hostile_shot":
            from gravity_ho_matey.render.chase_projectile_fx import draw_mirror_hostile_bolt

            draw_mirror_hostile_bolt(canvas, px, py, vel, ship_angle, draw_size=draw_size)
        else:
            canvas.create_oval(px - 2, py - 2, px + 2, py + 2, fill=color, outline="")

    ship_mx = mx + mw * 0.5
    ship_my = my + mh - 8
    canvas.create_polygon(
        ship_mx,
        ship_my,
        ship_mx - 6,
        ship_my + 9,
        ship_mx + 6,
        ship_my + 9,
        fill=accent,
        outline="#fff",
    )
    canvas.create_text(mx + 12, my + mh - 10, text="YOU", anchor="sw", fill=dim, font=("Courier", 6))
