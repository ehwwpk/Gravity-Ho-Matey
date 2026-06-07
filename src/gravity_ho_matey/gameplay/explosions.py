from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto

from gravity_ho_matey.core.vector import Vec2


class ExplosionKind(Enum):
    PROJECTILE_IMPACT = auto()
    ENEMY_DESTROYED = auto()
    SHIP_STRUCK = auto()
    SHIP_DESTROYED = auto()
    ASTEROID_DESTROYED = auto()
    ASTEROID_BREAKUP = auto()


@dataclass(slots=True)
class ExplosionParticle:
    pos: Vec2
    vel: Vec2
    life: float
    max_life: float
    size: float
    particle_type: str  # spark | ember | smoke


@dataclass(slots=True)
class Explosion:
    kind: ExplosionKind
    pos: Vec2
    particles: list[ExplosionParticle] = field(default_factory=list)
    ring_radius: float = 0.0
    ring_max: float = 24.0
    ring_life: float = 0.22
    ring_age: float = 0.0
    flash_life: float = 0.12
    flash_age: float = 0.0

    @property
    def alive(self) -> bool:
        if self.particles:
            return True
        if self.ring_age < self.ring_life:
            return True
        if self.flash_age < self.flash_life:
            return True
        return False


_PRESETS: dict[ExplosionKind, tuple[int, float, float]] = {
    ExplosionKind.PROJECTILE_IMPACT: (10, 14.0, 0.16),
    ExplosionKind.ENEMY_DESTROYED: (24, 32.0, 0.28),
    ExplosionKind.SHIP_STRUCK: (20, 28.0, 0.24),
    ExplosionKind.SHIP_DESTROYED: (34, 52.0, 0.38),
    ExplosionKind.ASTEROID_DESTROYED: (14, 20.0, 0.2),
    ExplosionKind.ASTEROID_BREAKUP: (22, 38.0, 0.3),
}


def spawn_explosion(kind: ExplosionKind, pos: Vec2, *, scale: float = 1.0) -> Explosion:
    count, ring_max, ring_life = _PRESETS[kind]
    base_scale = {
        ExplosionKind.PROJECTILE_IMPACT: 0.55,
        ExplosionKind.ENEMY_DESTROYED: 1.0,
        ExplosionKind.SHIP_STRUCK: 0.9,
        ExplosionKind.SHIP_DESTROYED: 1.35,
        ExplosionKind.ASTEROID_DESTROYED: 0.75,
        ExplosionKind.ASTEROID_BREAKUP: 1.05,
    }[kind]
    scale = max(0.35, min(1.8, scale * base_scale))

    explosion = Explosion(
        kind=kind,
        pos=Vec2(pos.x, pos.y),
        ring_max=ring_max * scale,
        ring_life=ring_life,
        flash_life=0.08 + ring_life * 0.35,
    )
    explosion.particles = _build_particles(pos, max(4, int(count * scale)), scale)
    return explosion


def _build_particles(origin: Vec2, count: int, scale: float) -> list[ExplosionParticle]:
    particles: list[ExplosionParticle] = []
    for i in range(count):
        angle = random.uniform(0.0, math.tau)
        speed = random.uniform(70.0, 240.0) * scale
        if i % 3 == 0:
            particle_type = "spark"
            max_life = random.uniform(0.12, 0.28)
            size = random.uniform(2.0, 4.5) * scale
            speed *= 1.25
        elif i % 3 == 1:
            particle_type = "ember"
            max_life = random.uniform(0.25, 0.55)
            size = random.uniform(3.0, 7.0) * scale
        else:
            particle_type = "smoke"
            max_life = random.uniform(0.35, 0.75)
            size = random.uniform(5.0, 11.0) * scale
            speed *= 0.55

        vel = Vec2(math.cos(angle) * speed, math.sin(angle) * speed)
        particles.append(
            ExplosionParticle(
                pos=Vec2(origin.x, origin.y),
                vel=vel,
                life=max_life,
                max_life=max_life,
                size=size,
                particle_type=particle_type,
            )
        )
    return particles


def update_explosion(explosion: Explosion, dt: float) -> None:
    explosion.ring_age += dt
    explosion.flash_age += dt
    explosion.ring_radius = min(
        explosion.ring_max,
        explosion.ring_radius + dt * explosion.ring_max * 4.5,
    )

    drag = 0.965
    gravity = 28.0
    kept: list[ExplosionParticle] = []
    for particle in explosion.particles:
        particle.life -= dt
        if particle.life <= 0.0:
            continue
        particle.vel = Vec2(particle.vel.x * drag, particle.vel.y * drag + gravity * dt * 0.15)
        particle.pos = particle.pos + particle.vel * dt
        kept.append(particle)
    explosion.particles = kept


@dataclass(slots=True)
class ExplosionSystem:
    active: list[Explosion] = field(default_factory=list)

    def spawn(self, kind: ExplosionKind, pos: Vec2, *, scale: float = 1.0) -> None:
        self.active.append(spawn_explosion(kind, pos, scale=scale))

    def update(self, dt: float) -> None:
        for explosion in self.active:
            update_explosion(explosion, dt)
        self.active = [explosion for explosion in self.active if explosion.alive]
