from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SpawnDirector:
    max_alive: int = 5
    global_cooldown: float = 2.5
    archetype_cooldown: float = 4.0
    _global_timer: float = field(default=0.0, init=False)
    _archetype_timer: float = field(default=0.0, init=False)

    def tick(self, dt: float) -> None:
        self._global_timer = max(0.0, self._global_timer - dt)
        self._archetype_timer = max(0.0, self._archetype_timer - dt)

    def can_spawn(self, alive_count: int) -> bool:
        if alive_count >= self.max_alive:
            return False
        if self._global_timer > 0.0:
            return False
        if self._archetype_timer > 0.0:
            return False
        return True

    def record_spawn(self) -> None:
        self._global_timer = self.global_cooldown
        self._archetype_timer = self.archetype_cooldown
