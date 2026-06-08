from __future__ import annotations

from gravity_ho_matey.core.geometry import (
    circle_intersects_convex_polygon,
    nearest_point_on_polygon_boundary,
)
from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import JunkLayer, Ship, SpaceJunk
from gravity_ho_matey.gameplay.space_junk_spatial import JunkSpatialGrid

JUNK_SEPARATION_PASSES = 3
JUNK_SEPARATION_SLOP = 3.0
JUNK_QUERY_PADDING = 72.0
JUNK_SWEEP_SAMPLES = 5


def junk_hit_at(
    junk_list: list[SpaceJunk],
    spatial: JunkSpatialGrid,
    pos: Vec2,
    radius: float,
) -> SpaceJunk | None:
    if not junk_list:
        return None
    query_r = radius + JUNK_QUERY_PADDING
    candidates = spatial.query_circle(pos, query_r) if spatial.populated else junk_list
    for junk in candidates:
        if junk.layer is not JunkLayer.STRUCTURAL:
            continue
        reach = junk.approximate_radius() + radius
        if (junk.pos - pos).length_sq() > reach * reach:
            continue
        if circle_intersects_convex_polygon(pos, radius, junk.world_vertices()):
            return junk
    return None


def junk_contact_at(
    junk_list: list[SpaceJunk],
    spatial: JunkSpatialGrid,
    pos: Vec2,
    vel: Vec2,
    radius: float,
    *,
    dt: float,
) -> SpaceJunk | None:
    """Point + swept samples along this frame's displacement — catches fast tunneling."""
    hit = junk_hit_at(junk_list, spatial, pos, radius)
    if hit is not None:
        return hit
    speed = vel.length()
    travel = speed * dt
    if travel <= 1.0:
        return None
    step = travel / JUNK_SWEEP_SAMPLES
    direction = vel.normalized()
    for i in range(1, JUNK_SWEEP_SAMPLES + 1):
        probe = pos - direction * (step * i)
        hit = junk_hit_at(junk_list, spatial, probe, radius)
        if hit is not None:
            return hit
    return None


def junk_crossed_between(
    junk_list: list[SpaceJunk],
    spatial: JunkSpatialGrid,
    start: Vec2,
    end: Vec2,
    radius: float,
) -> SpaceJunk | None:
    """Sample along motion segment — catches tunneling when end point is already past junk."""
    delta = end - start
    dist = delta.length()
    if dist <= 1e-6:
        return junk_hit_at(junk_list, spatial, end, radius)
    steps = max(3, int(dist / max(6.0, radius * 0.45)) + 1)
    for i in range(steps + 1):
        sample = start + delta * (i / steps)
        hit = junk_hit_at(junk_list, spatial, sample, radius)
        if hit is not None:
            return hit
    return None


def apply_unit_junk_separation(
    motion_start: Vec2,
    pos: Vec2,
    vel: Vec2,
    radius: float,
    junk_list: list[SpaceJunk],
    spatial: JunkSpatialGrid,
    *,
    dt: float,
) -> tuple[Vec2, Vec2]:
    """Separation with integrate segment check — motion_start is pre-step position."""
    pos, vel = apply_junk_separation(pos, vel, radius, junk_list, spatial, dt=dt)
    crossed = junk_crossed_between(junk_list, spatial, motion_start, pos, radius)
    if crossed is not None:
        mid = motion_start + (pos - motion_start) * 0.5
        pos, vel = resolve_circle_against_junk(mid, vel, radius, crossed, reflect_velocity=True)
        pos, vel = apply_junk_separation(pos, vel, radius, junk_list, spatial, dt=dt)
    return pos, vel


def resolve_circle_against_junk(
    pos: Vec2,
    vel: Vec2,
    radius: float,
    junk: SpaceJunk,
    *,
    reflect_velocity: bool = True,
    restitution: float = 0.55,
) -> tuple[Vec2, Vec2]:
    """Push circle out of convex junk; optionally damp/reflect velocity along normal."""
    verts = junk.world_vertices()
    if not circle_intersects_convex_polygon(pos, radius, verts):
        return pos, vel

    max_push = 0.0
    normal = Vec2(1.0, 0.0)
    count = len(verts)
    for i in range(count):
        a = verts[i]
        b = verts[(i + 1) % count]
        edge = b - a
        ln = edge.length()
        if ln <= 1e-9:
            continue
        n = Vec2(edge.y / ln, -edge.x / ln)
        if (junk.pos - a).dot(n) > 0.0:
            n = n * -1.0
        signed_dist = (pos - a).dot(n)
        need = radius - signed_dist + JUNK_SEPARATION_SLOP
        if need > max_push:
            max_push = need
            normal = n

    new_pos = pos + normal * max_push
    new_vel = vel
    if reflect_velocity:
        v_dot_n = vel.dot(normal)
        if v_dot_n < 0.0:
            new_vel = vel - normal * (2.0 * v_dot_n * restitution)
    return new_pos, new_vel


def apply_junk_separation(
    pos: Vec2,
    vel: Vec2,
    radius: float,
    junk_list: list[SpaceJunk],
    spatial: JunkSpatialGrid,
    *,
    reflect_velocity: bool = True,
    dt: float = 1.0 / 60.0,
) -> tuple[Vec2, Vec2]:
    """Up to JUNK_SEPARATION_PASSES iterations — returns corrected pos/vel."""
    if not junk_list:
        return pos, vel
    cur_pos = pos
    cur_vel = vel
    for _ in range(JUNK_SEPARATION_PASSES):
        hit = junk_contact_at(junk_list, spatial, cur_pos, cur_vel, radius, dt=dt)
        if hit is None:
            break
        probe = cur_pos
        if not circle_intersects_convex_polygon(cur_pos, radius, hit.world_vertices()):
            travel = cur_vel.length() * dt
            if travel > 1.0:
                probe = cur_pos - cur_vel.normalized() * min(travel, radius * 4.0)
        cur_pos, cur_vel = resolve_circle_against_junk(
            probe,
            cur_vel,
            radius,
            hit,
            reflect_velocity=reflect_velocity,
        )
    return cur_pos, cur_vel


def resolve_junk_bounce(ship: Ship, junk: SpaceJunk) -> None:
    """Push ship off junk and reflect velocity — no hull damage."""
    ship.pos, ship.vel = resolve_circle_against_junk(
        ship.pos,
        ship.vel,
        ship.radius,
        junk,
        reflect_velocity=True,
        restitution=0.88,
    )


def junk_avoidance_push(
    pos: Vec2,
    vel: Vec2,
    radius: float,
    junk_list: list[SpaceJunk],
    spatial: JunkSpatialGrid,
    *,
    avoid_radius: float,
    panic_gap: float,
    thrust: float,
) -> tuple[Vec2, float]:
    """Static obstacle steering — junk never moves (vel treated as zero)."""
    push = Vec2()
    urgency = 0.0
    if not junk_list:
        return push, urgency
    query_r = avoid_radius + radius + 48.0
    candidates = spatial.query_circle(pos, query_r) if spatial.populated else junk_list
    for junk in candidates:
        if junk.layer is not JunkLayer.STRUCTURAL:
            continue
        nearest, dist = nearest_point_on_polygon_boundary(pos, junk.world_vertices())
        gap = dist - radius
        if gap > avoid_radius:
            continue
        delta = pos - nearest
        if delta.length_sq() <= 1e-9:
            delta = pos - junk.pos
        if delta.length_sq() <= 1e-9:
            continue
        t = 1.0 - max(0.0, gap / avoid_radius)
        strength = t * t * (3.0 - 2.0 * t)
        closing = max(0.0, vel.dot(delta.normalized()))
        if closing > 0.0:
            strength *= 1.0 + min(3.0, closing / 50.0)
        if gap < panic_gap:
            strength = min(1.0, strength + 0.75)
        push += delta.normalized() * (thrust * strength)
        urgency = max(urgency, strength)
    return push, urgency
