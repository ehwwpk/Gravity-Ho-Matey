from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.core.vector import Vec2


@dataclass(slots=True)
class EggPodObjective:
    """Ground egg sac on the Brood Moon surface — shoot to rupture before hatch."""

    pos: Vec2
    radius: float = 20.0
    hits_max: int = 3
    hits_remaining: int = 3
    alive: bool = True
    alarm: bool = False
    pod_id: int = 0
    pulse: float = 0.0

    def apply_shot(self) -> bool:
        self.hits_remaining = max(0, self.hits_remaining - 1)
        if self.hits_remaining <= 0:
            self.alive = False
            return True
        return False

    def tick(self, dt: float) -> None:
        self.pulse += dt * 4.2
