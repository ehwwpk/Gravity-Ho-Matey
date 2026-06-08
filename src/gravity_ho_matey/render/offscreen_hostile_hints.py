"""Rim chevrons for hostiles that are alive but off-screen — no connector lines."""

from __future__ import annotations

import math

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.enemy_kinds import EnemyKind
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode, ViewCamera

# Keep nearby bearings readable when a wave clusters on one approach.
_ANGLE_MERGE_RAD = 0.17
_MAX_RIM_HINTS = 8


def append_offscreen_hostile_hints(
    hints: list[tuple[float, str, str]],
    camera: ViewCamera,
    world: GameWorld,
    ship_pos: Vec2,
    ship_angle: float,
    *,
    vw: float,
    vh: float,
    play_top: float,
    margin: float = 14.0,
    max_hints: int = _MAX_RIM_HINTS,
) -> None:
    """Add one rim marker per off-screen hostile bearing (nearest per arc)."""
    ranked: list[tuple[float, float, str, str]] = []
    for enemy in world.enemies:
        if not enemy.alive:
            continue
        angle = _offscreen_bearing(
            camera,
            enemy.pos,
            ship_pos,
            ship_angle,
            vw=vw,
            vh=vh,
            play_top=play_top,
            margin=margin,
        )
        if angle is None:
            continue
        tag, color = _hostile_rim_tag(enemy)
        dist = (enemy.pos - ship_pos).length()
        ranked.append((angle, dist, tag, color))

    ranked.sort(key=lambda item: (item[0], item[1]))
    merged: list[tuple[float, str, str]] = []
    for angle, _dist, tag, color in ranked:
        if merged and abs(angle - merged[-1][0]) < _ANGLE_MERGE_RAD:
            continue
        merged.append((angle, tag, color))
        if len(merged) >= max_hints:
            break
    hints.extend(merged)


def _hostile_rim_tag(enemy) -> tuple[str, str]:
    if enemy.kind is EnemyKind.SQUID:
        return "SQ", palette.ENEMY_EDGE
    if enemy.kind is EnemyKind.HOSTILE_FIGHTER:
        return "CR", palette.HOSTILE_PROJECTILE
    return "EN", palette.HOSTILE_PROJECTILE


def _offscreen_bearing(
    camera: ViewCamera,
    world_pos: Vec2,
    ship_pos: Vec2,
    ship_angle: float,
    *,
    vw: float,
    vh: float,
    play_top: float,
    margin: float,
) -> float | None:
    p = camera.world_to_screen(world_pos, ship_pos, ship_angle)
    sx = p.x
    sy = p.y + (0.0 if camera.mode is CameraMode.CHASE else play_top)
    if margin <= sx <= vw - margin and play_top + margin <= sy <= vh - margin:
        return None
    cx = vw * 0.5
    cy = play_top + (vh - play_top) * 0.5
    return math.atan2(sy - cy, sx - cx)
