from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.entities import Asteroid


class TractorPhase(Enum):
    IDLE = auto()
    ACQUIRING = auto()
    PULLING = auto()
    TOSSING = auto()
    COOLDOWN = auto()


ACQUIRE_TIME = 0.3
PULL_TIME = 1.4
COOLDOWN_TIME = 8.0
TRACTOR_RANGE = 480.0
GRAB_RADIUS = 95.0
PULL_ACCEL = 340.0
TOSS_SPEED_MIN = 185.0
TOSS_SPEED_MAX = 235.0


@dataclass(slots=True)
class TractorBeamState:
    phase: TractorPhase = TractorPhase.IDLE
    phase_timer: float = 0.0
    cooldown_remaining: float = 0.0
    target_asteroid: Asteroid | None = None
    aim_pos: Vec2 = field(default_factory=Vec2)
    tossed_flash: float = 0.0

    def tick_cooldown(self, dt: float) -> None:
        if self.cooldown_remaining > 0.0:
            self.cooldown_remaining = max(0.0, self.cooldown_remaining - dt)
        if self.tossed_flash > 0.0:
            self.tossed_flash = max(0.0, self.tossed_flash - dt)

    def reset_cycle(self) -> None:
        self.phase = TractorPhase.COOLDOWN
        self.phase_timer = 0.0
        self.cooldown_remaining = COOLDOWN_TIME
        self.target_asteroid = None

    def begin_acquire(self, asteroid: Asteroid, aim: Vec2) -> None:
        self.phase = TractorPhase.ACQUIRING
        self.phase_timer = 0.0
        self.target_asteroid = asteroid
        self.aim_pos = Vec2(aim.x, aim.y)

    def advance(
        self,
        dt: float,
        station_pos: Vec2,
        asteroids: list[Asteroid],
    ) -> bool:
        """Returns True when a toss impulse was applied this tick."""
        self.phase_timer += dt
        if self.phase is TractorPhase.COOLDOWN:
            if self.cooldown_remaining <= 0.0:
                self.phase = TractorPhase.IDLE
            return False

        target = self.target_asteroid
        if target is None or target not in asteroids:
            self.reset_cycle()
            return False

        if self.phase is TractorPhase.ACQUIRING:
            if self.phase_timer >= ACQUIRE_TIME:
                self.phase = TractorPhase.PULLING
                self.phase_timer = 0.0
            return False

        if self.phase is TractorPhase.PULLING:
            offset = station_pos - target.pos
            dist = offset.length()
            if dist > 1e-6:
                pull = offset.normalized() * PULL_ACCEL * dt
                target.vel = target.vel + pull
            if dist <= GRAB_RADIUS or self.phase_timer >= PULL_TIME:
                self.phase = TractorPhase.TOSSING
                self.phase_timer = 0.0
            return False

        if self.phase is TractorPhase.TOSSING:
            to_aim = self.aim_pos - target.pos
            if to_aim.length_sq() > 1.0:
                speed = TOSS_SPEED_MIN + (TOSS_SPEED_MAX - TOSS_SPEED_MIN) * min(
                    1.0, target.mass / 4.0
                )
                target.vel = to_aim.normalized() * speed
            self.tossed_flash = 0.35
            self.reset_cycle()
            return True

        return False


def pick_tractor_asteroid(station_pos: Vec2, asteroids: list[Asteroid], *, exclusion_radius: float) -> Asteroid | None:
    best: Asteroid | None = None
    best_score = -1.0
    for asteroid in asteroids:
        offset = asteroid.pos - station_pos
        dist = offset.length()
        rock_r = asteroid.approximate_radius()
        if dist - rock_r > TRACTOR_RANGE:
            continue
        if dist < exclusion_radius + rock_r:
            continue
        score = rock_r * 2.2 + (TRACTOR_RANGE - dist) * 0.15
        if score > best_score:
            best = asteroid
            best_score = score
    return best


def pick_toss_target(
    station_pos: Vec2,
    player_pos: Vec2,
    allies: list,
    *,
    player_bias: float = 1.35,
) -> Vec2:
    best = player_pos
    best_score = (player_pos - station_pos).length() / player_bias
    for ally in allies:
        if not getattr(ally, "alive", True):
            continue
        pos = getattr(ally, "pos", None)
        if pos is None:
            continue
        score = (pos - station_pos).length()
        if score < best_score:
            best = pos
            best_score = score
    lead = (best - station_pos).normalized() * 48.0 if (best - station_pos).length_sq() > 1.0 else Vec2()
    return best + lead
