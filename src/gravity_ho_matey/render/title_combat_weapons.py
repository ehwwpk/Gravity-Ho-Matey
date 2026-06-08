"""Animated weapon-doctrine previews for the nav-station combat tab."""

from __future__ import annotations

import math
from dataclasses import replace

import tkinter as tk

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemies import PatrolEnemy
from gravity_ho_matey.gameplay.entities import Projectile
from gravity_ho_matey.gameplay.explosions import ExplosionKind, spawn_explosion
from gravity_ho_matey.gameplay.weapon_config import EXPLOSIVE_ADV_BLAST_RADIUS, EXPLOSIVE_BLAST_RADIUS
from gravity_ho_matey.gameplay.weapon_fire import spawn_player_shots
from gravity_ho_matey.gameplay.weapon_kinds import (
    WEAPON_TRACK_ADV_LABELS,
    WEAPON_TRACK_ADV_SHORT,
    WEAPON_TRACK_LABELS,
    WEAPON_TRACK_SHORT,
    WEAPON_TRACK_TAGS,
    WeaponTrack,
)
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode
from gravity_ho_matey.render.chase_fx import draw_ground_fog_glow
from gravity_ho_matey.render.enemy_viz import draw_patrol_enemy_tactical
from gravity_ho_matey.render.explosion_fx import draw_explosions
from gravity_ho_matey.render.lighting import LightRig
from gravity_ho_matey.render.menu_ui import draw_fitted_text, draw_wrapped_text
from gravity_ho_matey.render.title_codex_tactical import make_codex_camera
from gravity_ho_matey.render.weapon_projectile_fx import draw_tactical_projectile
from gravity_ho_matey.render.world_draw import draw_ship

_TRACKS: tuple[WeaponTrack, ...] = (
    WeaponTrack.LASER,
    WeaponTrack.SHOTGUN,
    WeaponTrack.EXPLOSIVE,
)

_TRACK_COLOR: dict[WeaponTrack, str] = {
    WeaponTrack.LASER: palette.WEAPON_LASER_MID,
    WeaponTrack.SHOTGUN: palette.WEAPON_SHOTGUN_MID,
    WeaponTrack.EXPLOSIVE: palette.WEAPON_EXPLOSIVE_MID,
}

_TRACK_PHASE: dict[WeaponTrack, float] = {
    WeaponTrack.LASER: 0.0,
    WeaponTrack.SHOTGUN: 1.05,
    WeaponTrack.EXPLOSIVE: 2.1,
}

_PREVIEW_SHIP = Vec2(-52.0, 0.0)
_PREVIEW_CENTER = Vec2(8.0, 0.0)
_SHIP_ANGLE = 0.0
_SHIP_RADIUS = 12.0
_PROJECTILE_SPEED = 315.0
_CYCLE_SEC = 3.35
_FIRE_PHASE = 0.12
_ACTIVE_PHASE = 2.15


def _track_brief(track: WeaponTrack) -> str:
    base = WEAPON_TRACK_LABELS[track]
    if " — " in base:
        return base.split(" — ", 1)[1]
    return base


def _integrate_shots(track: WeaponTrack, phase: float, *, advanced: bool) -> list[Projectile]:
    if phase < _FIRE_PHASE or phase > _ACTIVE_PHASE:
        return []
    age = phase - _FIRE_PHASE
    shots = spawn_player_shots(
        ship_pos=_PREVIEW_SHIP,
        ship_vel=Vec2(0.0, 0.0),
        ship_angle=_SHIP_ANGLE,
        ship_radius=_SHIP_RADIUS,
        projectile_speed=_PROJECTILE_SPEED,
        track=track,
        advanced=advanced,
    )
    live: list[Projectile] = []
    for shot in shots:
        pos = shot.pos + shot.vel * age
        ttl = shot.ttl - age
        if ttl <= 0.0 or pos.x > 118.0:
            continue
        live.append(replace(shot, pos=pos, ttl=ttl))
    return live


def _nova_explosion(track: WeaponTrack, phase: float, *, advanced: bool) -> list:
    if track is not WeaponTrack.EXPLOSIVE:
        return []
    if phase < _FIRE_PHASE or phase > _ACTIVE_PHASE + 0.55:
        return []
    age = phase - _FIRE_PHASE
    speed_mult = 0.72 if advanced else 0.55
    travel = _PROJECTILE_SPEED * speed_mult * age
    if travel < 58.0:
        return []
    blast_age = age - 58.0 / (_PROJECTILE_SPEED * speed_mult)
    if blast_age > 0.72:
        return []
    target = Vec2(62.0, 0.0)
    blast = EXPLOSIVE_ADV_BLAST_RADIUS if advanced else EXPLOSIVE_BLAST_RADIUS
    explosion = spawn_explosion(
        ExplosionKind.NOVA_BLAST,
        target,
        scale=0.82,
        aoe_radius_world=blast,
    )
    explosion.flash_age = blast_age
    explosion.ring_age = blast_age
    for particle in explosion.particles:
        particle.pos = particle.pos + particle.vel * blast_age
        particle.life = max(0.0, particle.max_life - blast_age)
    return [explosion]


def _draw_preview_scene(
    canvas: tk.Canvas,
    *,
    cx: float,
    cy: float,
    w: float,
    h: float,
    track: WeaponTrack,
    elapsed: float,
    rig: LightRig,
    accent: str,
    frame: str,
) -> None:
    scale = min(w, h * 1.35) / 175.0
    camera = make_codex_camera(cx, cy, _PREVIEW_CENTER, scale=scale)
    phase = (elapsed + _TRACK_PHASE[track]) % _CYCLE_SEC
    advanced = True
    track_color = _TRACK_COLOR[track]

    hp.draw_panel(canvas, cx - w / 2, cy - h / 2, w, h, frame=frame, accent=track_color, fill="#060c14")
    canvas.create_rectangle(cx - w / 2 + 1, cy - h / 2 + 1, cx + w / 2 - 1, cy - h / 2 + 4, fill=track_color, outline="")

    grid_step = 18.0 * scale
    left = cx - w / 2 + 6
    right = cx + w / 2 - 6
    top = cy - h / 2 + 8
    bottom = cy + h / 2 - 6
    for gx in range(int(left), int(right), max(8, int(grid_step))):
        canvas.create_line(gx, top, gx, bottom, fill="#0e1a28", width=1)
    for gy in range(int(top), int(bottom), max(8, int(grid_step))):
        canvas.create_line(left, gy, right, gy, fill="#0e1a28", width=1)

    ship_screen = camera.world_to_screen(_PREVIEW_SHIP, _PREVIEW_CENTER, 0.0)
    draw_ship(
        canvas,
        Vec2(ship_screen.x, ship_screen.y),
        _SHIP_ANGLE,
        boost_energy=1.0,
        scale=1.05,
        rig=rig,
        elapsed=elapsed,
        weapon_heat=0.18 if phase < _ACTIVE_PHASE else 0.0,
    )

    if track is WeaponTrack.LASER:
        targets = (Vec2(36.0, -10.0), Vec2(72.0, 8.0))
    else:
        targets = (Vec2(62.0, 0.0),)
    for index, target in enumerate(targets):
        enemy = PatrolEnemy(
            waypoints=(target,),
            pos=target,
            facing_angle=math.pi + 0.18 * index,
        )
        draw_patrol_enemy_tactical(
            canvas,
            enemy,
            camera=camera,
            ship_pos=_PREVIEW_CENTER,
            hud_top=0.0,
            rig=rig,
            elapsed=elapsed + index * 0.4,
        )

    explosions = _nova_explosion(track, phase, advanced=advanced)
    if explosions:
        draw_explosions(
            canvas,
            explosions,
            project=lambda p: camera.world_to_screen(p, _PREVIEW_CENTER, 0.0),
        )
        blast = EXPLOSIVE_ADV_BLAST_RADIUS if advanced else EXPLOSIVE_BLAST_RADIUS
        target = Vec2(62.0, 0.0)
        edge = camera.world_to_screen(target + Vec2(blast, 0.0), _PREVIEW_CENTER, 0.0)
        center = camera.world_to_screen(target, _PREVIEW_CENTER, 0.0)
        aoe_px = abs(edge.x - center.x)
        draw_ground_fog_glow(
            canvas,
            center.x,
            center.y,
            aoe_px * 1.05,
            (palette.WEAPON_EXPLOSIVE_GLOW, palette.WEAPON_EXPLOSIVE_MID),
            pulse=elapsed * 5.0,
        )
        canvas.create_oval(
            center.x - aoe_px,
            center.y - aoe_px,
            center.x + aoe_px,
            center.y + aoe_px,
            outline=palette.WEAPON_EXPLOSIVE_MID,
            width=1,
            dash=(4, 3),
        )

    for shot in _integrate_shots(track, phase, advanced=advanced):
        draw_tactical_projectile(
            canvas,
            shot,
            camera=camera,
            ship_pos=_PREVIEW_CENTER,
            hud_top=0.0,
            elapsed=elapsed,
        )

    muzzle = camera.world_to_screen(_PREVIEW_SHIP + Vec2.from_angle(_SHIP_ANGLE) * (_SHIP_RADIUS + 8.0), _PREVIEW_CENTER, 0.0)
    if _FIRE_PHASE <= phase <= _FIRE_PHASE + 0.08:
        draw_ground_fog_glow(canvas, muzzle.x, muzzle.y, 10.0, (track_color, track_color), pulse=0.0)
        canvas.create_oval(muzzle.x - 3, muzzle.y - 3, muzzle.x + 3, muzzle.y + 3, fill=track_color, outline="")


def _draw_weapon_card(
    canvas: tk.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    track: WeaponTrack,
    *,
    elapsed: float,
    rig: LightRig,
    accent: str,
    dim: str,
    frame: str,
) -> None:
    track_color = _TRACK_COLOR[track]
    tag = WEAPON_TRACK_TAGS[track]
    preview_h = h * 0.52
    text_y = y + preview_h + 10.0

    canvas.create_text(
        x + 10,
        y + 8,
        anchor="w",
        text=tag,
        fill=track_color,
        font=hp.FONT_BODY_BOLD,
    )
    canvas.create_text(
        x + w - 10,
        y + 8,
        anchor="e",
        text="SHOP UPGRADE",
        fill=dim,
        font=hp.FONT_SMALL,
    )

    _draw_preview_scene(
        canvas,
        cx=x + w / 2,
        cy=y + 8 + preview_h / 2,
        w=w - 8,
        h=preview_h - 4,
        track=track,
        elapsed=elapsed,
        rig=rig,
        accent=accent,
        frame=frame,
    )

    draw_fitted_text(
        canvas,
        x + 8,
        text_y,
        WEAPON_TRACK_SHORT[track],
        max_width=w - 16,
        color=dim,
        font=hp.FONT_SMALL,
    )
    draw_fitted_text(
        canvas,
        x + 8,
        text_y + 14,
        WEAPON_TRACK_ADV_SHORT[track],
        max_width=w - 16,
        color=track_color,
        font=hp.FONT_BODY_BOLD,
    )
    draw_wrapped_text(
        canvas,
        x + 8,
        text_y + 32,
        _track_brief(track),
        max_width=w - 16,
        line_height=13.0,
        color=accent,
        font=hp.FONT_BODY,
        max_lines=2,
    )
    adv_line = WEAPON_TRACK_ADV_LABELS[track]
    if " — " in adv_line:
        adv_line = adv_line.split(" — ", 1)[1]
    draw_wrapped_text(
        canvas,
        x + 8,
        text_y + 58,
        adv_line,
        max_width=w - 16,
        line_height=12.0,
        color=dim,
        font=hp.FONT_SMALL,
        max_lines=2,
    )


def draw_weapon_doctrine_row(
    canvas: tk.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    elapsed: float,
    accent: str,
    dim: str,
    frame: str,
) -> None:
    """Three live firing lanes — one per Holo Bazaar weapon track."""
    rig = LightRig.for_play(theme="cove", camera_mode=CameraMode.TACTICAL)
    gap = 10.0
    pad = 2.0
    col_w = (w - gap * 2 - pad * 2) / 3.0
    for index, track in enumerate(_TRACKS):
        cx = x + pad + index * (col_w + gap)
        hp.draw_panel(canvas, cx, y, col_w, h, frame=frame, accent=_TRACK_COLOR[track], fill="#080e18")
        _draw_weapon_card(
            canvas,
            cx + 4,
            y + 4,
            col_w - 8,
            h - 8,
            track,
            elapsed=elapsed,
            rig=rig,
            accent=accent,
            dim=dim,
            frame=frame,
        )
