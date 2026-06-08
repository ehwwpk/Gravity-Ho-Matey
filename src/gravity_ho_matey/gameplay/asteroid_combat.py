from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.asteroid_mass import (
    compute_mass,
    explosion_scale_for_mass,
    scale_local_verts,
    size_class_for_scale,
)
from gravity_ho_matey.gameplay.asteroid_motion import spawn_fragment
from gravity_ho_matey.gameplay.asteroid_tiers import (
    MAX_ASTEROIDS,
    can_split,
    fragment_count,
)
from gravity_ho_matey.gameplay.entities import Asteroid
from gravity_ho_matey.gameplay.explosions import ExplosionKind


@dataclass(slots=True)
class AsteroidCombatFx:
    kind: ExplosionKind
    pos: Vec2
    scale: float = 1.0


@dataclass(slots=True)
class AsteroidCombatResult:
    projectile_consumed: bool = True
    asteroids_removed: list[Asteroid] = field(default_factory=list)
    asteroids_added: list[Asteroid] = field(default_factory=list)
    fx: list[AsteroidCombatFx] = field(default_factory=list)
    snapshots_dirty: bool = False


def apply_projectile_hit(
    asteroid: Asteroid,
    impact_pos: Vec2,
    projectile_vel: Vec2,
    *,
    world_asteroid_count: int,
    max_asteroids: int = MAX_ASTEROIDS,
) -> AsteroidCombatResult:
    """Resolve one projectile strike against an asteroid (player or hostile)."""
    result = AsteroidCombatResult()

    if asteroid.hits_remaining <= 0:
        result.fx.append(
            AsteroidCombatFx(
                ExplosionKind.PROJECTILE_IMPACT,
                Vec2(impact_pos.x, impact_pos.y),
                scale=0.55,
            )
        )
        return result

    asteroid.hits_remaining -= 1

    if asteroid.hits_remaining > 0:
        result.fx.append(
            AsteroidCombatFx(
                ExplosionKind.PROJECTILE_IMPACT,
                Vec2(impact_pos.x, impact_pos.y),
                scale=0.55,
            )
        )
        return result

    if not can_split(asteroid.tier, asteroid.generation):
        result.fx.append(
            AsteroidCombatFx(
                ExplosionKind.ASTEROID_DESTROYED,
                Vec2(asteroid.pos.x, asteroid.pos.y),
                scale=explosion_scale_for_mass(asteroid.mass),
            )
        )
        result.asteroids_removed.append(asteroid)
        result.snapshots_dirty = True
        return result

    return _resolve_large_breakup(
        asteroid,
        impact_pos,
        projectile_vel,
        world_asteroid_count=world_asteroid_count,
        max_asteroids=max_asteroids,
    )


def apply_friendly_projectile_hit(
    asteroid: Asteroid,
    impact_pos: Vec2,
    projectile_vel: Vec2,
    *,
    world_asteroid_count: int,
    max_asteroids: int = MAX_ASTEROIDS,
) -> AsteroidCombatResult:
    return apply_projectile_hit(
        asteroid,
        impact_pos,
        projectile_vel,
        world_asteroid_count=world_asteroid_count,
        max_asteroids=max_asteroids,
    )


def _resolve_large_breakup(
    parent: Asteroid,
    impact_pos: Vec2,
    projectile_vel: Vec2,
    *,
    world_asteroid_count: int,
    max_asteroids: int,
) -> AsteroidCombatResult:
    result = AsteroidCombatResult()
    result.asteroids_removed.append(parent)
    result.snapshots_dirty = True

    full_fragment_budget = parent.mass * 0.5

    rng = random.Random(parent.seed ^ 0xB1EA001)
    desired = fragment_count(rng, parent.tier)
    slots = max(0, max_asteroids - world_asteroid_count)
    n_fragments = min(desired, slots)

    if n_fragments <= 0:
        vapor_mass = parent.mass
        fragment_mass_budget = 0.0
    else:
        each_mass = full_fragment_budget / desired
        fragment_mass_budget = each_mass * n_fragments
        vapor_mass = parent.mass - fragment_mass_budget

    result.fx.append(
        AsteroidCombatFx(
            ExplosionKind.ASTEROID_BREAKUP,
            Vec2(parent.pos.x, parent.pos.y),
            scale=explosion_scale_for_mass(vapor_mass),
        )
    )

    if n_fragments <= 0:
        return result

    each_mass = fragment_mass_budget / n_fragments
    mass_scale = math.sqrt(max(each_mass / max(parent.mass, 1e-6), 1e-6))
    child_verts = scale_local_verts(parent.local_verts, mass_scale)
    child_size_class = size_class_for_scale(mass_scale)
    parent_radius = parent.approximate_radius()
    impulse_base = 45.0 + parent_radius * 0.55
    max_jitter = parent_radius * 0.07

    impact_dir = projectile_vel.normalized() if projectile_vel.length_sq() > 1e-6 else Vec2(1.0, 0.0)
    step = math.tau / n_fragments

    for i in range(n_fragments):
        child_seed = parent.seed * 1000 + i + 17
        child_rng = random.Random(child_seed)
        angle = step * i + child_rng.uniform(-0.25, 0.25)
        dir_vec = Vec2(math.cos(angle), math.sin(angle))
        blend = dir_vec * 0.65 + impact_dir * 0.35
        outward = blend.normalized() if blend.length_sq() > 1e-6 else dir_vec

        jitter = max_jitter * child_rng.uniform(0.0, 1.0)
        spawn_pos = parent.pos + outward * jitter
        impulse = impulse_base + child_rng.uniform(-12.0, 18.0)
        tangential = outward.rotated(math.pi / 2.0) * child_rng.uniform(-22.0, 22.0)
        child_vel = parent.vel + outward * impulse + tangential

        child = spawn_fragment(
            spawn_pos,
            seed=child_seed,
            local_verts=child_verts,
            size_class=child_size_class,
            velocity=child_vel,
            parent=parent,
        )
        child.mass = compute_mass(child.local_verts, radius_hint=child.approximate_radius())
        result.asteroids_added.append(child)

    return result
