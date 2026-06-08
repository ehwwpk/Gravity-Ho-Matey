from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from gravity_ho_matey.core.vector import Vec2


class PodPhase(Enum):
    FLYING = auto()
    HATCHING = auto()


@dataclass(slots=True)
class SquidPod:
    pos: Vec2
    vel: Vec2
    target: Vec2
    phase: PodPhase = PodPhase.FLYING
    hatch_timer: float = 0.0
    hatch_duration: float = 1.15
    wobble: float = 0.0
    alive: bool = True

    def hit_radius(self) -> float:
        return 16.0 if self.phase is PodPhase.HATCHING else 10.0

    def tick(self, dt: float) -> bool:
        """Returns True when hatch completes and caller should spawn squid."""
        self.wobble += dt * 7.5
        if self.phase is PodPhase.FLYING:
            self.pos = self.pos + self.vel * dt
            if (self.pos - self.target).length() <= 38.0 or self.hatch_timer > 2.4:
                self.phase = PodPhase.HATCHING
                self.hatch_timer = 0.0
                self.vel = Vec2()
            else:
                self.hatch_timer += dt
            return False
        self.hatch_timer += dt
        if self.hatch_timer >= self.hatch_duration:
            self.alive = False
            return True
        return False
