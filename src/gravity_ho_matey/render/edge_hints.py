from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode, ViewCamera
from gravity_ho_matey.render.asteroid_viz import ORBITAL_ASTEROID_THREAT_RADIUS


def draw_edge_hints(
    canvas: tk.Canvas,
    world: GameWorld,
    camera: ViewCamera,
    *,
    hud_top: float,
) -> None:
    vw = camera.viewport_width
    vh = camera.viewport_height
    play_top = camera.play_hud_top if camera.mode is CameraMode.CHASE else hud_top
    cx = vw * 0.5
    cy = play_top + (vh - play_top) * 0.5
    margin = 14.0
    ship = world.ship.pos
    ship_angle = world.ship.angle
    wrap_w = float(world.config.width) if world.config.surface_wrap else 0.0

    hints: list[tuple[float, str, str]] = []
    for beacon in world.beacons:
        if beacon.collected:
            continue
        _maybe_hint(
            hints,
            camera,
            beacon.pos,
            ship,
            ship_angle,
            "◈",
            palette.BEACON,
            vw,
            vh,
            play_top,
            wrap_width=wrap_w,
        )

    if world.finish_unlocked:
        gate = world.finish_gate.rect
        gc = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        color = palette.GATE_OPEN
        tag = "GO"
        _maybe_hint(hints, camera, gc, ship, ship_angle, tag, color, vw, vh, play_top, wrap_width=wrap_w)
    elif world.config.level_theme == "siege":
        gate = world.finish_gate.rect
        gc = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        _maybe_hint(hints, camera, gc, ship, ship_angle, "GT", palette.GATE_LOCKED, vw, vh, play_top)
    elif world.config.level_theme == "rift":
        gate = world.finish_gate.rect
        gc = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
        tag = "XT" if world.finish_unlocked else "PD"
        color = palette.GATE_OPEN if world.finish_unlocked else palette.RIFT_PAD_COOLDOWN
        _maybe_hint(hints, camera, gc, ship, ship_angle, tag, color, vw, vh, play_top)
        from gravity_ho_matey.render.wave_ingress_viz import draw_wave_ingress_edge_hints

        draw_wave_ingress_edge_hints(
            hints,
            camera,
            world,
            ship,
            ship_angle,
            vw=vw,
            vh=vh,
            play_top=play_top,
        )
    elif world.config.brood_moon_mission and world.brood_moon is not None:
        from gravity_ho_matey.gameplay.brood_moon_mission import BroodPhase

        bm = world.brood_moon
        if bm.phase is BroodPhase.ORBITAL and bm.layout is not None:
            from gravity_ho_matey.gameplay.brood_moon_mission import landing_limb_hint

            _maybe_hint(
                hints,
                camera,
                landing_limb_hint(ship, bm.layout),
                ship,
                ship_angle,
                "LD",
                palette.BROOD_MOON_HUD_ACCENT,
                vw,
                vh,
                play_top,
            )
            nearest_rock = _nearest_closing_asteroid(world, ship, ORBITAL_ASTEROID_THREAT_RADIUS)
            if nearest_rock is not None:
                _maybe_hint(
                    hints,
                    camera,
                    nearest_rock,
                    ship,
                    ship_angle,
                    "RK",
                    palette.HOLO_ASTEROID_EDGE,
                    vw,
                    vh,
                    play_top,
                )
        elif bm.phase is BroodPhase.ORBITAL_RETURN and not world.finish_unlocked:
            gate = world.finish_gate.rect
            gc = Vec2(gate.x + gate.w * 0.5, gate.y + gate.h * 0.5)
            _maybe_hint(hints, camera, gc, ship, ship_angle, "DK", palette.GATE_LOCKED, vw, vh, play_top)
        elif bm.on_surface:
            from gravity_ho_matey.gameplay.friendly_fighter_config import PATROL_ENGAGE_RANGE
            from gravity_ho_matey.gameplay.planetside_flight import PLANETSIDE_MAX_EDGE_HINTS, wrap_shortest_delta

            boss_hint: tuple[float, str, str] | None = None
            boss = world.mega_squid
            if bm.boss_spawned and boss is not None and boss.alive:
                boss_hints: list[tuple[float, str, str]] = []
                _maybe_hint(
                    boss_hints,
                    camera,
                    boss.pos,
                    ship,
                    ship_angle,
                    "BOSS",
                    palette.SQUID_WRAP_GLOW[-1],
                    vw,
                    vh,
                    play_top,
                    wrap_width=wrap_w,
                )
                if boss_hints:
                    boss_hint = boss_hints[0]

            alive_pods = [pod for pod in world.egg_pods if pod.alive]
            if alive_pods:
                ranked = sorted(
                    alive_pods,
                    key=lambda pod: wrap_shortest_delta(ship, pod.pos, wrap_w).length_sq(),
                )
                for pod in ranked[:PLANETSIDE_MAX_EDGE_HINTS]:
                    _maybe_hint(
                        hints,
                        camera,
                        pod.pos,
                        ship,
                        ship_angle,
                        "EG",
                        palette.SQUID_CORE,
                        vw,
                        vh,
                        play_top,
                        wrap_width=wrap_w,
                    )

            for enemy in world.enemies:
                if not enemy.alive:
                    continue
                engage = getattr(enemy, "engage_range", PATROL_ENGAGE_RANGE)
                if (enemy.pos - ship).length() > engage + 40.0:
                    continue
                _maybe_hint(
                    hints, camera, enemy.pos, ship, ship_angle,
                    "EN", palette.HOSTILE_PROJECTILE, vw, vh, play_top,
                    wrap_width=wrap_w,
                )
                break
            for projectile in world.projectiles:
                if not projectile.hostile:
                    continue
                if (projectile.pos - ship).length() > 520.0:
                    continue
                if getattr(projectile, "boss_energy_orb", False):
                    tag, color = "ORB", palette.BOSS_ORB_CORE
                else:
                    tag, color = "BL", palette.CHASE_BOLT_HOSTILE_CORE
                _maybe_hint(
                    hints, camera, projectile.pos, ship, ship_angle,
                    tag, color, vw, vh, play_top,
                    wrap_width=wrap_w,
                )
                break

            hints.sort(key=lambda item: item[0])
            max_other = 7 if boss_hint is not None else 8
            for angle, tag, color in hints[:max_other]:
                _draw_rim_chevron(canvas, cx, cy, angle, tag, color, vw, vh, play_top, margin)
            if boss_hint is not None:
                angle, tag, color = boss_hint
                ascent_fork = bm.ascent_ready and boss is not None and boss.alive
                if ascent_fork:
                    pulse = 0.5 + 0.5 * math.sin(world.elapsed * 2.8)
                    color = palette.SQUID_CORE
                    _draw_rim_chevron(
                        canvas,
                        cx,
                        cy,
                        angle,
                        tag,
                        color,
                        vw,
                        vh,
                        play_top,
                        margin,
                        font_size=11,
                        highlight=True,
                        pulse=pulse,
                    )
                else:
                    _draw_rim_chevron(
                        canvas,
                        cx,
                        cy,
                        angle,
                        tag,
                        color,
                        vw,
                        vh,
                        play_top,
                        margin,
                        font_size=10,
                    )
            return

    hints.sort(key=lambda item: item[0])
    for angle, tag, color in hints[:8]:
        _draw_rim_chevron(canvas, cx, cy, angle, tag, color, vw, vh, play_top, margin)


def _nearest_closing_asteroid(world: GameWorld, ship_pos: Vec2, radius: float) -> Vec2 | None:
    best: Vec2 | None = None
    best_dist = radius + 1.0
    ship_vel = world.ship.vel
    for asteroid in world.asteroids:
        rel = asteroid.pos - ship_pos
        dist = rel.length()
        if dist > radius + asteroid.approximate_radius():
            continue
        closing = rel.normalized().dot(ship_vel - asteroid.vel)
        if closing > -8.0 and dist < best_dist:
            best = asteroid.pos
            best_dist = dist
    return best


def _maybe_hint(
    hints: list[tuple[float, str, str]],
    camera: ViewCamera,
    world_pos: Vec2,
    ship_pos: Vec2,
    ship_angle: float,
    tag: str,
    color: str,
    vw: float,
    vh: float,
    hud_top: float,
    *,
    margin: float = 14.0,
    wrap_width: float = 0.0,
) -> None:
    hint_pos = world_pos
    if wrap_width > 0.0:
        from gravity_ho_matey.gameplay.planetside_flight import hint_world_pos

        hint_pos = hint_world_pos(ship_pos, world_pos, wrap_width)
    p = camera.world_to_screen(hint_pos, ship_pos, ship_angle)
    sx = p.x
    sy = p.y + (0.0 if camera.mode is CameraMode.CHASE else hud_top)
    if margin <= sx <= vw - margin and hud_top + margin <= sy <= vh - margin:
        return
    if camera.mode is CameraMode.CHASE and not p.visible:
        pass
    cx = vw * 0.5
    cy = hud_top + (vh - hud_top) * 0.5
    angle = math.atan2(sy - cy, sx - cx)
    hints.append((angle, tag, color))


def _draw_rim_chevron(
    canvas: tk.Canvas,
    cx: float,
    cy: float,
    angle: float,
    tag: str,
    color: str,
    vw: float,
    vh: float,
    hud_top: float,
    margin: float,
    *,
    font_size: int = 9,
    highlight: bool = False,
    pulse: float = 0.0,
) -> None:
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    play_h = vh - hud_top
    reach = min(
        (vw * 0.5 - margin) / max(abs(cos_a), 1e-6),
        (play_h * 0.5 - margin) / max(abs(sin_a), 1e-6),
    )
    x = cx + cos_a * reach
    y = cy + sin_a * reach
    if highlight:
        ring_r = 16.0 + 2.5 * pulse
        canvas.create_oval(
            x - ring_r,
            y - ring_r,
            x + ring_r,
            y + ring_r,
            outline=color,
            width=1,
            dash=(3, 4),
        )
    canvas.create_text(x, y, text=tag, fill=color, font=("Courier New", font_size, "bold"))
    tip_len = 12.0 if font_size >= 10 else 10.0
    wing = 8.0 if font_size >= 10 else 7.0
    tip = Vec2(x, y) + Vec2.from_angle(angle) * tip_len
    left = Vec2(x, y) + Vec2.from_angle(angle + 2.6) * wing
    right = Vec2(x, y) + Vec2.from_angle(angle - 2.6) * wing
    canvas.create_polygon(tip.x, tip.y, left.x, left.y, right.x, right.y, fill=color, outline="")
