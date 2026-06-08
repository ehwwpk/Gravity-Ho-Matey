from __future__ import annotations

import math
import random

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_mass import compute_mass
from gravity_ho_matey.gameplay.asteroid_shape import generate_asteroid_verts
from gravity_ho_matey.gameplay.asteroid_tiers import AsteroidTier, roll_hits_max, tier_for_spawn
from gravity_ho_matey.gameplay.entities import Asteroid, GravityWell
from gravity_ho_matey.gameplay.gravity import gravity_acceleration_at

_DRIFT_SPEED: dict[str, tuple[float, float]] = {
    "slow": (8.0, 22.0),
    "medium": (22.0, 50.0),
    "fast": (50.0, 95.0),
}

_RING_SPEED = (32.0, 58.0)
_SHOWER_SPEED = (115.0, 195.0)


def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def _random_unit(rng: random.Random) -> Vec2:
    angle = rng.random() * math.tau
    return Vec2(math.cos(angle), math.sin(angle))


def _speed_for_kind(rng: random.Random, drift_kind: str) -> float:
    if drift_kind == "shower":
        lo, hi = _SHOWER_SPEED
    elif drift_kind == "ring":
        lo, hi = _RING_SPEED
    else:
        lo, hi = _DRIFT_SPEED.get(drift_kind, _DRIFT_SPEED["medium"])
    return lo + rng.random() * (hi - lo)


def make_asteroid(
    center: Vec2,
    *,
    seed: int,
    size_class: str = "rock",
    drift_kind: str = "medium",
    velocity: Vec2 | None = None,
    ring_anchor: Vec2 | None = None,
    ring_radius: float = 0.0,
    ring_orbit_radius: float = 0.0,
    ring_phase: float = 0.0,
    ring_sign: float = 1.0,
    tier_override: AsteroidTier | None = None,
) -> Asteroid:
    rng = _rng(seed)
    local_verts = generate_asteroid_verts(seed, size_class)
    if velocity is None:
        direction = _random_unit(rng)
        speed = _speed_for_kind(rng, drift_kind)
        velocity = direction * speed
    spin = (rng.random() - 0.5) * (0.6 if size_class == "pebble" else 0.35)
    radius_hint = max((v.length() for v in local_verts), default=20.0)
    tier = tier_override if tier_override is not None else tier_for_spawn(size_class, radius_hint)
    hits_max = roll_hits_max(tier, rng)
    asteroid = Asteroid(
        pos=Vec2(center.x, center.y),
        vel=velocity,
        angle=rng.random() * math.tau,
        spin=spin,
        local_verts=local_verts,
        size_class=size_class,
        drift_kind=drift_kind,
        seed=seed,
        ring_anchor=Vec2(ring_anchor.x, ring_anchor.y) if ring_anchor is not None else None,
        ring_radius=ring_radius,
        ring_orbit_radius=ring_orbit_radius,
        ring_phase=ring_phase,
        ring_sign=ring_sign,
        tier=tier,
        hits_max=hits_max,
        hits_remaining=hits_max,
        generation=0,
    )
    asteroid.mass = compute_mass(local_verts, radius_hint=asteroid.approximate_radius())
    return asteroid


def spawn_fragment(
    center: Vec2,
    *,
    seed: int,
    local_verts: tuple[Vec2, ...],
    size_class: str,
    velocity: Vec2,
    parent: Asteroid,
) -> Asteroid:
    rng = _rng(seed)
    spin = (rng.random() - 0.5) * 0.55
    hits_max = roll_hits_max(AsteroidTier.SMALL, rng)
    return Asteroid(
        pos=Vec2(center.x, center.y),
        vel=velocity,
        angle=parent.angle + (rng.random() - 0.5) * 0.35,
        spin=spin,
        local_verts=local_verts,
        size_class=size_class,
        drift_kind="medium",
        seed=seed,
        ring_anchor=None,
        ring_radius=0.0,
        ring_sign=1.0,
        tier=AsteroidTier.SMALL,
        hits_max=hits_max,
        hits_remaining=hits_max,
        mass=0.0,
        generation=parent.generation + 1,
        free_bounds=False,
    )


def make_ring_cluster(
    anchor: Vec2,
    *,
    radius: float,
    count: int,
    base_seed: int,
    size_class: str = "rock",
    clockwise: bool = True,
) -> list[Asteroid]:
    sign = -1.0 if clockwise else 1.0
    rng = _rng(base_seed)
    speed = _speed_for_kind(rng, "ring")
    asteroids: list[Asteroid] = []
    for i in range(count):
        angle = (math.tau * i / count) + rng.uniform(-0.08, 0.08)
        orbit_r = radius + rng.uniform(-12.0, 12.0)
        offset = Vec2(math.cos(angle), math.sin(angle)) * orbit_r
        pos = anchor + offset
        radial = offset.normalized() if offset.length_sq() > 1e-6 else Vec2(1.0, 0.0)
        tangent = radial.rotated(math.pi / 2.0 * sign)
        seed = base_seed * 1000 + i + 1
        asteroids.append(
            make_asteroid(
                pos,
                seed=seed,
                size_class=size_class,
                drift_kind="ring",
                velocity=tangent * (speed + rng.uniform(-6.0, 6.0)),
                ring_anchor=anchor,
                ring_radius=radius,
                ring_orbit_radius=orbit_r,
                ring_phase=angle,
                ring_sign=sign,
            )
        )
    return asteroids


def make_mixed_belt_ring(
    anchor: Vec2,
    *,
    radius: float,
    count: int,
    base_seed: int,
    size_mix: tuple[str, ...],
    clockwise: bool = True,
    radial_jitter: float = 6.0,
) -> list[Asteroid]:
    """Dense debris ring with mixed size classes on one orbit."""
    sign = -1.0 if clockwise else 1.0
    rng = _rng(base_seed)
    speed = _speed_for_kind(rng, "ring")
    mix = size_mix if size_mix else ("rock",)
    asteroids: list[Asteroid] = []
    for i in range(count):
        angle = (math.tau * i / count) + rng.uniform(-0.06, 0.06)
        orbit_r = radius + rng.uniform(-radial_jitter, radial_jitter)
        offset = Vec2(math.cos(angle), math.sin(angle)) * orbit_r
        pos = anchor + offset
        radial = offset.normalized() if offset.length_sq() > 1e-6 else Vec2(1.0, 0.0)
        tangent = radial.rotated(math.pi / 2.0 * sign)
        seed = base_seed * 1000 + i + 1
        size_class = mix[i % len(mix)]
        asteroids.append(
            make_asteroid(
                pos,
                seed=seed,
                size_class=size_class,
                drift_kind="ring",
                velocity=tangent * (speed + rng.uniform(-5.0, 5.0)),
                ring_anchor=anchor,
                ring_radius=radius,
                ring_orbit_radius=orbit_r,
                ring_phase=angle,
                ring_sign=sign,
            )
        )
    return asteroids


def integrate_ring_asteroid_kinematic(asteroid: Asteroid, dt: float) -> None:
    """O(1) belt orbit — no gravity, no wall bounce."""
    anchor = asteroid.ring_anchor
    if anchor is None:
        return
    orbit_r = asteroid.ring_orbit_radius if asteroid.ring_orbit_radius > 0.0 else asteroid.ring_radius
    orbit_r = max(orbit_r, 1.0)
    speed = asteroid.vel.length()
    if speed < _RING_SPEED[0]:
        speed = _RING_SPEED[0] + (orbit_r % 17.0) * 0.05
    angular = (speed / orbit_r) * asteroid.ring_sign
    asteroid.ring_phase = (asteroid.ring_phase + angular * dt) % math.tau
    offset = Vec2(math.cos(asteroid.ring_phase), math.sin(asteroid.ring_phase)) * orbit_r
    asteroid.pos = anchor + offset
    radial = offset.normalized()
    tangent = radial.rotated(math.pi / 2.0 * asteroid.ring_sign)
    asteroid.vel = tangent * speed
    asteroid.angle += asteroid.spin * dt


def make_shower_cluster(
    origin: Vec2,
    *,
    count: int,
    base_seed: int,
    direction: Vec2,
    size_class: str = "pebble",
    spread: float = 70.0,
) -> list[Asteroid]:
    rng = _rng(base_seed)
    base_speed = _speed_for_kind(rng, "shower")
    flow = direction.normalized() if direction.length_sq() > 1e-6 else Vec2(1.0, 0.0)
    base_vel = flow * base_speed
    asteroids: list[Asteroid] = []
    for i in range(count):
        jitter = Vec2(rng.uniform(-spread, spread), rng.uniform(-spread, spread))
        pos = origin + jitter
        vel_jitter = Vec2(rng.uniform(-18.0, 18.0), rng.uniform(-18.0, 18.0))
        seed = base_seed * 1000 + i + 7
        asteroids.append(
            make_asteroid(
                pos,
                seed=seed,
                size_class=size_class,
                drift_kind="shower",
                velocity=base_vel + vel_jitter,
            )
        )
    return asteroids


def integrate_asteroid(
    asteroid: Asteroid,
    dt: float,
    wells: list[GravityWell],
    *,
    gravity_scale: float,
    world_width: float,
    world_height: float,
    wall_bounce: bool = True,
) -> None:
    if asteroid.drift_kind == "ring" and asteroid.ring_anchor is not None:
        offset = asteroid.pos - asteroid.ring_anchor
        dist = offset.length()
        if dist > 1e-6:
            radial = offset / dist
            tangent = radial.rotated(math.pi / 2.0 * asteroid.ring_sign)
            speed = max(asteroid.vel.length(), _RING_SPEED[0])
            asteroid.vel = tangent * speed
            if asteroid.ring_radius > 0.0:
                asteroid.vel = asteroid.vel + radial * ((asteroid.ring_radius - dist) * 1.6)

    if wells and not asteroid.free_bounds:
        accel = gravity_acceleration_at(asteroid.pos, wells) * gravity_scale * 0.1
        asteroid.vel = asteroid.vel + accel * dt

    asteroid.pos = asteroid.pos + asteroid.vel * dt
    asteroid.angle += asteroid.spin * dt

    if asteroid.free_bounds or not wall_bounce:
        return

    radius = asteroid.approximate_radius()
    margin = 8.0
    left = margin + radius
    right = world_width - margin - radius
    top = margin + radius
    bottom = world_height - margin - radius
    restitution = 0.82
    if asteroid.pos.x < left:
        asteroid.pos = Vec2(left, asteroid.pos.y)
        asteroid.vel = Vec2(abs(asteroid.vel.x) * restitution, asteroid.vel.y)
    elif asteroid.pos.x > right:
        asteroid.pos = Vec2(right, asteroid.pos.y)
        asteroid.vel = Vec2(-abs(asteroid.vel.x) * restitution, asteroid.vel.y)
    if asteroid.pos.y < top:
        asteroid.pos = Vec2(asteroid.pos.x, top)
        asteroid.vel = Vec2(asteroid.vel.x, abs(asteroid.vel.y) * restitution)
    elif asteroid.pos.y > bottom:
        asteroid.pos = Vec2(asteroid.pos.x, bottom)
        asteroid.vel = Vec2(asteroid.vel.x, -abs(asteroid.vel.y) * restitution)
