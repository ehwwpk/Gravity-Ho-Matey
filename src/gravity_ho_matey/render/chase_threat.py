from __future__ import annotations

import math
from enum import Enum, auto

from gravity_ho_matey.core.geometry import Rect
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import GravityWell
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at
from gravity_ho_matey.gameplay.world import GameWorld
from gravity_ho_matey.render import palette

_LETHAL_WELL_KINDS = frozenset({"black_hole", "planet"})


class ThreatLevel(Enum):
    SAFE = auto()
    HEAVY = auto()
    LETHAL = auto()


def threat_at_point(world: GameWorld, point: Vec2, *, ship_radius: float | None = None) -> ThreatLevel:
    """Red only where physics would kill the ship soon."""
    radius = ship_radius if ship_radius is not None else world.ship.radius
    cfg = world.config
    margin = 4.0

    if point.x < -margin or point.y < -margin or point.x > cfg.width + margin or point.y > cfg.height + margin:
        return ThreatLevel.LETHAL

    for wall in world.walls:
        if wall.rect.intersects_circle(point, radius * 0.92):
            return ThreatLevel.LETHAL

    for well in world.wells:
        level = _well_threat_at(point, well, cfg.well_maw_radius)
        if level is ThreatLevel.LETHAL:
            return ThreatLevel.LETHAL

    for well in world.wells:
        level = _well_threat_at(point, well, cfg.well_maw_radius)
        if level is ThreatLevel.HEAVY:
            return ThreatLevel.HEAVY

    return ThreatLevel.SAFE


def _well_threat_at(point: Vec2, well: GravityWell, default_maw: float) -> ThreatLevel:
    maw = well.maw_radius if well.maw_radius is not None else default_maw
    dist = (point - well.pos).length()
    if well.kind in _LETHAL_WELL_KINDS:
        if dist <= maw * 1.35:
            return ThreatLevel.LETHAL
        if dist <= well.radius * 0.62:
            return ThreatLevel.HEAVY
        return ThreatLevel.SAFE
    if dist <= maw * 1.1:
        return ThreatLevel.LETHAL
    if dist <= well.radius * 0.45:
        return ThreatLevel.HEAVY
    return ThreatLevel.SAFE


def threat_color(level: ThreatLevel, *, norm: float = 0.0) -> str:
    if level is ThreatLevel.LETHAL:
        return palette.HELM_THREAT_LETHAL
    if level is ThreatLevel.HEAVY:
        return palette.HELM_THREAT_HEAVY
    from gravity_ho_matey.render.world_draw import gravity_field_color

    return gravity_field_color(norm)


def predict_path_with_threats(
    world: GameWorld,
    *,
    steps: int = 22,
    step_dt: float = 0.045,
) -> list[tuple[Vec2, ThreatLevel]]:
    pos = Vec2(world.ship.pos.x, world.ship.pos.y)
    vel = Vec2(world.ship.vel.x, world.ship.vel.y)
    cfg = world.config
    samples: list[tuple[Vec2, ThreatLevel]] = [(pos, threat_at_point(world, pos))]
    for _ in range(steps):
        accel = gravity_acceleration_at(pos, world.wells) * cfg.gravity_scale
        vel = (vel + accel * step_dt) * cfg.drag
        vel = vel.clamped_length(cfg.max_ship_speed)
        pos = pos + vel * step_dt
        samples.append((Vec2(pos.x, pos.y), threat_at_point(world, pos)))
    return samples


def wall_rail_urgency(world: GameWorld) -> float:
    """0–1 heat for hull-close rails."""
    dist, closing = nearest_wall_threat(world)
    if dist > 110.0 or closing < 18.0:
        return 0.0
    return max(0.0, min(1.0, (110.0 - dist) / 110.0) * min(1.0, closing / 90.0))


def nearest_wall_threat(world: GameWorld) -> tuple[float, float]:
    ship = world.ship
    best_dist = 9999.0
    best_closing = 0.0
    for wall in world.walls:
        dist, closing = _wall_surface_distance_and_closing(ship.pos, ship.vel, ship.radius, wall.rect)
        if dist < best_dist:
            best_dist = dist
            best_closing = closing
    return best_dist, best_closing


def _wall_surface_distance_and_closing(pos: Vec2, vel: Vec2, radius: float, rect: Rect) -> tuple[float, float]:
    nx = min(max(pos.x, rect.left), rect.right)
    ny = min(max(pos.y, rect.top), rect.bottom)
    nearest = Vec2(nx, ny)
    delta = pos - nearest
    dist_sq = delta.length_sq()
    if dist_sq < 1e-6:
        if rect.contains_point(pos):
            return 0.0, vel.length()
        return 0.0, 0.0
    dist = math.sqrt(dist_sq) - radius
    closing = max(0.0, -vel.dot(delta.normalized()))
    return max(0.0, dist), closing


def ahead_emphasis(ship_pos: Vec2, ship_angle: float, point: Vec2, *, radius: float = 340.0) -> float:
    """Brighter grid ahead of the nose."""
    forward = Vec2.from_angle(ship_angle)
    rel = point - ship_pos
    dist = rel.length()
    if dist >= radius:
        return 0.55
    ahead = rel.dot(forward) / max(dist, 1.0)
    if ahead < 0.15:
        return 0.65
    t = 1.0 - dist / radius
    return 0.65 + max(0.0, ahead) * t * 0.35
