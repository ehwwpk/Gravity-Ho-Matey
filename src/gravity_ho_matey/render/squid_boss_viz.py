from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.mega_squid_boss import MegaSquidBoss
from gravity_ho_matey.gameplay.squid_pod import PodPhase, SquidPod
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import ViewCamera
from gravity_ho_matey.render.chase_fx import draw_fog_glow, draw_ground_fog_glow
from gravity_ho_matey.render.health_bar_viz import draw_health_bar
from gravity_ho_matey.render.lighting import LightRig, lerp_hex, material_for


def boss_scrape_radius(boss: MegaSquidBoss, ship_radius: float) -> float:
    return boss.radius + ship_radius


def chase_boss_projected(
    camera: ViewCamera,
    boss: MegaSquidBoss,
    ship_pos: Vec2,
    ship_angle: float,
) -> tuple[Vec2, float, float] | None:
    """Extended chase frustum — brood-mother stays visible during north ingress."""
    if not boss.alive:
        return None
    p = camera.world_to_chase_screen(
        boss.pos,
        ship_pos,
        ship_angle,
        min_ahead=-980.0,
        screen_margin=320.0,
    )
    if p.y < camera.chase_horizon_y() - 56.0:
        return None
    depth = max(p.depth, camera.min_depth)
    scale = max(0.5, camera.perspective_scale(depth) / camera.focal_length)
    return Vec2(p.x, p.y), scale, depth


def _chase_ahead(camera: ViewCamera, depth: float) -> float:
    return max(depth, camera.min_depth)


def _chase_entity_scale(camera: ViewCamera, depth: float) -> float:
    return max(0.35, camera.perspective_scale(_chase_ahead(camera, depth)) / camera.focal_length)


def _chase_world_px(camera: ViewCamera, world_units: float, depth: float) -> float:
    return world_units * camera.perspective_scale(_chase_ahead(camera, depth)) * camera.chase_thrust_boost


def _clamp_glow(radius: float, *, cap: float = 280.0) -> float:
    return min(max(0.0, radius), cap)


def draw_boss_scrape_zone(
    canvas: tk.Canvas,
    sx: float,
    sy: float,
    scrape_r: float,
    *,
    ship_inside: bool,
    flash: float,
    elapsed: float,
    scale: float = 1.0,
    facing: float = 0.0,
) -> None:
    r = scrape_r * scale
    pulse = 0.88 + 0.12 * math.sin(elapsed * 6.0)
    if ship_inside or flash > 0.0:
        warn = palette.BOSS_SCRAPE_WARN if flash > 0.0 else palette.BOSS_SCRAPE_RING
        draw_fog_glow(
            canvas,
            sx,
            sy,
            _clamp_glow(r * (1.05 + flash * 0.35), cap=200.0),
            palette.CHASE_FOG_BROOD if flash <= 0.0 else palette.CHASE_FOG_BOSS,
            pulse=elapsed * 8.0,
        )
        segments = 14
        pts: list[float] = []
        for i in range(segments):
            angle = facing + math.tau * i / segments + math.sin(elapsed * 4.2 + i) * 0.06
            wobble = 1.0 + 0.08 * math.sin(elapsed * 5.0 + i * 0.9)
            pr = r * pulse * wobble
            pts.extend((sx + math.cos(angle) * pr, sy + math.sin(angle) * pr * 0.82))
        if len(pts) >= 6:
            canvas.create_polygon(*pts, fill="", outline=warn, width=3 if flash > 0.0 else 2)
    else:
        for i in range(8):
            angle = facing + math.tau * i / 8 + math.sin(elapsed * 3.5 + i) * 0.05
            ox = sx + math.cos(angle) * r
            oy = sy + math.sin(angle) * r * 0.82
            ix = sx + math.cos(angle) * r * 0.82
            iy = sy + math.sin(angle) * r * 0.68
            canvas.create_line(ix, iy, ox, oy, fill=palette.BOSS_SCRAPE_RING, width=1, dash=(4, 5))


def draw_mega_squid_tactical(
    canvas: tk.Canvas,
    boss: MegaSquidBoss,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    ship_radius: float,
    hud_top: float,
    rig: LightRig,
    elapsed: float,
    scrape_flash: float = 0.0,
) -> None:
    if not boss.alive:
        return
    p = camera.world_to_screen(boss.pos, ship_pos, ship_angle)
    ship_p = camera.world_to_screen(ship_pos, ship_pos, ship_angle)
    sx, sy = p.x, p.y + hud_top
    scale = camera.tactical_scale
    r = boss.radius * scale
    scrape_r = boss_scrape_radius(boss, ship_radius) * scale
    ship_inside = (boss.pos - ship_pos).length() <= boss.radius + ship_radius
    facing = math.atan2(ship_pos.y - boss.pos.y, ship_pos.x - boss.pos.x)
    brood = rig.theme == "brood_moon"
    fog = palette.CHASE_FOG_BROOD if brood else palette.CHASE_FOG_BOSS
    draw_ground_fog_glow(canvas, sx, sy + r * 0.2, r * 2.2, fog, pulse=elapsed * 4.0)
    draw_boss_scrape_zone(
        canvas,
        sx,
        sy,
        scrape_r,
        ship_inside=ship_inside,
        flash=scrape_flash,
        elapsed=elapsed,
        scale=1.0,
        facing=facing,
    )
    engaging = ship_inside or scrape_flash > 0.0
    from gravity_ho_matey.render.squid_viz import draw_boss_tentacle_crown, draw_squid_body_lit

    draw_boss_tentacle_crown(
        canvas, sx, sy,
        radius=boss.radius, scale=scale, facing=facing,
        prey_x=ship_p.x, prey_y=ship_p.y + hud_top,
        engaging=engaging, elapsed=elapsed,
    )
    draw_squid_body_lit(
        canvas,
        sx,
        sy,
        radius=boss.radius,
        scale=scale,
        rig=rig,
        kind="mega_squid",
        facing=math.atan2(ship_pos.y - boss.pos.y, ship_pos.x - boss.pos.x),
        elapsed=elapsed,
        engaging=engaging,
    )
    material = material_for("mega_squid", theme=rig.theme, view=rig.view)
    hp_frac = boss.hits_remaining / max(1, boss.hits_max)
    draw_health_bar(
        canvas,
        sx,
        sy - r - 14,
        r,
        hp_frac,
        outline=material.rim,
        fill=material.rim,
        low_fill=palette.BOSS_SCRAPE_WARN,
    )


def draw_mega_squid_chase(
    canvas: tk.Canvas,
    boss: MegaSquidBoss,
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    ship_radius: float,
    elapsed: float,
    scrape_flash: float = 0.0,
    rig: LightRig | None = None,
) -> None:
    if not boss.alive:
        return
    projected = chase_boss_projected(camera, boss, ship_pos, ship_angle)
    if projected is None:
        return
    sp_xy, entity_scale, ahead = projected
    sp_x, sp_y = sp_xy.x, sp_xy.y
    r = min(boss.radius * entity_scale, 42.0)
    scrape_r = min(_chase_world_px(camera, boss_scrape_radius(boss, ship_radius), ahead), 150.0)
    ship_inside = (boss.pos - ship_pos).length() <= boss.radius + ship_radius
    facing = math.atan2(ship_pos.y - boss.pos.y, ship_pos.x - boss.pos.x)
    brood = rig is not None and rig.theme == "brood_moon"
    fog = palette.CHASE_FOG_BROOD if brood else palette.CHASE_FOG_BOSS
    draw_ground_fog_glow(
        canvas,
        sp_x,
        sp_y + 6,
        _clamp_glow(r * 2.2, cap=220.0),
        fog,
        pulse=elapsed * 5.0,
    )
    draw_boss_scrape_zone(
        canvas,
        sp_x,
        sp_y,
        scrape_r,
        ship_inside=ship_inside,
        flash=scrape_flash,
        elapsed=elapsed,
        scale=1.0,
        facing=facing,
    )
    from gravity_ho_matey.render.squid_viz import draw_boss_tentacle_crown, draw_squid_body, draw_squid_body_lit

    engaging = ship_inside or scrape_flash > 0.0
    draw_boss_tentacle_crown(
        canvas, sp_x, sp_y,
        radius=boss.radius, scale=entity_scale, facing=facing,
        prey_x=sp_x, prey_y=sp_y,
        engaging=engaging, elapsed=elapsed,
    )
    if rig is not None:
        draw_squid_body_lit(
            canvas,
            sp_x,
            sp_y,
            radius=boss.radius,
            scale=entity_scale,
            rig=rig,
            kind="mega_squid",
            facing=math.atan2(ship_pos.y - boss.pos.y, ship_pos.x - boss.pos.x),
            elapsed=elapsed,
            engaging=ship_inside or scrape_flash > 0.0,
        )
    else:
        draw_squid_body(
            canvas,
            sp_x,
            sp_y,
            radius=boss.radius,
            scale=entity_scale,
            facing=math.atan2(ship_pos.y - boss.pos.y, ship_pos.x - boss.pos.x),
            elapsed=elapsed,
            engaging=ship_inside,
        )
    hp_frac = boss.hits_remaining / max(1, boss.hits_max)
    bar_w = r * 1.6
    draw_health_bar(
        canvas,
        sp_x,
        sp_y - r - 12,
        bar_w,
        hp_frac,
        outline="#c058ff",
        fill="#ff4080",
        low_fill=palette.BOSS_SCRAPE_WARN,
    )


def draw_squid_coil_ring_tactical(
    canvas: tk.Canvas,
    sx: float,
    sy: float,
    coil_r: float,
    *,
    engaging: bool,
    elapsed: float,
) -> None:
    from gravity_ho_matey.render.squid_viz import draw_squid_coil_ring

    draw_squid_coil_ring(canvas, sx, sy, coil_r, engaging=engaging, elapsed=elapsed)


def draw_squid_pods_tactical(
    canvas: tk.Canvas,
    pods: list[SquidPod],
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    hud_top: float,
    elapsed: float,
) -> None:
    for pod in pods:
        if not pod.alive:
            continue
        p = camera.world_to_screen(pod.pos, ship_pos, ship_angle)
        sx, sy = p.x, p.y + hud_top
        if pod.phase is PodPhase.HATCHING:
            shrink = max(0.2, 1.0 - pod.hatch_timer / pod.hatch_duration)
            r = 16.0 * shrink
            draw_fog_glow(canvas, sx, sy, r * 1.8, palette.CHASE_FOG_BOSS[:3], pulse=elapsed * 10.0)
            canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill="#401858", outline="#ff80c0", width=2)
        else:
            draw_ground_fog_glow(canvas, sx, sy + 3, 14.0, palette.CHASE_FOG_BOSS[:2], pulse=elapsed * 8.0)
            canvas.create_oval(sx - 9, sy - 9, sx + 9, sy + 9, fill="#602878", outline="#ffa0d0", width=2)


def draw_squid_pods_chase(
    canvas: tk.Canvas,
    pods: list[SquidPod],
    camera: ViewCamera,
    *,
    ship_pos: Vec2,
    ship_angle: float,
    elapsed: float,
) -> None:
    horizon = camera.chase_horizon_y()
    for pod in pods:
        if not pod.alive:
            continue
        sp = camera.world_to_screen(pod.pos, ship_pos, ship_angle)
        if sp.y < horizon:
            continue
        ahead = _chase_ahead(camera, sp.depth)
        entity_scale = _chase_entity_scale(camera, ahead)
        r = min(10.0 * entity_scale, 22.0)
        if pod.phase is PodPhase.HATCHING:
            shrink = max(0.2, 1.0 - pod.hatch_timer / pod.hatch_duration)
            r *= shrink
            draw_fog_glow(
                canvas,
                sp.x,
                sp.y,
                _clamp_glow(r * 2.2, cap=120.0),
                palette.CHASE_FOG_BOSS[:3],
                pulse=elapsed * 12.0,
            )
        canvas.create_oval(sp.x - r, sp.y - r, sp.x + r, sp.y + r, fill="#502070", outline="#ffa0d0", width=2)
