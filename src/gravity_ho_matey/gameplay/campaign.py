from __future__ import annotations

from dataclasses import dataclass, field

from gravity_ho_matey.gameplay.damage import (
    DamageEvent,
    DamageResult,
    DamageSeverity,
    damage_spec_for,
    default_reason,
)
from gravity_ho_matey.gameplay.entities import Ship
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.ship_modifiers import apply_powerups_to_ship

MAX_LIVES = 3
CHUNKS_PER_LIFE = 3


@dataclass(slots=True)
class CampaignState:
    lives: int = MAX_LIVES
    hull_chunks: int = CHUNKS_PER_LIFE
    powerups: set[PowerUpKind] = field(default_factory=set)

    @classmethod
    def new(cls) -> CampaignState:
        return cls(lives=MAX_LIVES, hull_chunks=CHUNKS_PER_LIFE)

    def collect_powerup(self, kind: PowerUpKind, ship: Ship) -> None:
        self.powerups.add(kind)
        apply_powerups_to_ship(ship, self.powerups)

    def lose_life(self) -> bool:
        """Spend one life. Returns True if the campaign continues."""
        self.lives = max(0, self.lives - 1)
        return self.lives > 0

    def apply_damage(self, event: DamageEvent, *, level_theme: str = "cove") -> DamageResult:
        """Resolve hull chip or lethal damage. Mutates lives and hull_chunks."""
        if self.game_over:
            return DamageResult(
                life_lost=True,
                campaign_over=True,
                hull_chunks=0,
                lives=0,
                reason=event.reason or default_reason(event.source, level_theme),
                chipped=False,
            )

        spec = damage_spec_for(event.source)
        reason = event.reason or default_reason(event.source, level_theme)

        if spec.severity is DamageSeverity.LETHAL:
            still_alive = self.lose_life()
            self.hull_chunks = 0
            return DamageResult(
                life_lost=True,
                campaign_over=not still_alive,
                hull_chunks=0,
                lives=self.lives,
                reason=reason,
                chipped=False,
            )

        self.hull_chunks = max(0, self.hull_chunks - spec.chunks)
        if self.hull_chunks <= 0:
            still_alive = self.lose_life()
            self.hull_chunks = 0
            return DamageResult(
                life_lost=True,
                campaign_over=not still_alive,
                hull_chunks=0,
                lives=self.lives,
                reason=reason,
                chipped=True,
            )

        return DamageResult(
            life_lost=False,
            campaign_over=False,
            hull_chunks=self.hull_chunks,
            lives=self.lives,
            reason=reason,
            chipped=True,
        )

    @property
    def game_over(self) -> bool:
        return self.lives <= 0
