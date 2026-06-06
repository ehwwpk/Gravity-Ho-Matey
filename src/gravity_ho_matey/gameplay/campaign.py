from __future__ import annotations

from dataclasses import dataclass, field

from gravity_ho_matey.gameplay.entities import Ship
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.ship_modifiers import apply_powerups_to_ship

MAX_LIVES = 3


@dataclass(slots=True)
class CampaignState:
    lives: int = MAX_LIVES
    powerups: set[PowerUpKind] = field(default_factory=set)

    @classmethod
    def new(cls) -> CampaignState:
        return cls(lives=MAX_LIVES)

    def collect_powerup(self, kind: PowerUpKind, ship: Ship) -> None:
        self.powerups.add(kind)
        apply_powerups_to_ship(ship, self.powerups)

    def lose_life(self) -> bool:
        """Spend one life. Returns True if the campaign continues."""
        self.lives = max(0, self.lives - 1)
        return self.lives > 0

    @property
    def game_over(self) -> bool:
        return self.lives <= 0
