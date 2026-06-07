from __future__ import annotations

from collections import Counter
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
from gravity_ho_matey.gameplay.powerup_stacks import PowerUpStacks, active_powerup_kinds
from gravity_ho_matey.gameplay.shop_catalog import (
    shop_at_max_stacks,
    shop_price_for,
)
from gravity_ho_matey.gameplay.ship_modifiers import apply_powerups_to_ship
from gravity_ho_matey.gameplay.upgrade_config import (
    HULL_REINFORCE_BONUS,
    HULL_REINFORCE_MAX_PURCHASES,
    RUBBER_HULL_BOUNCE_CHARGES,
)
from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack, is_weapon_advanced_powerup, is_weapon_powerup, weapon_track_from_kind
from gravity_ho_matey.settings import DEV_START_JEWELS

MAX_LIVES = 3
CHUNKS_PER_LIFE = 3


@dataclass(slots=True)
class CampaignState:
    lives: int = MAX_LIVES
    hull_chunks: int = CHUNKS_PER_LIFE
    jewels: int = 0
    powerup_stacks: PowerUpStacks = field(default_factory=Counter)
    rubber_hull_charges: int = 0
    rubber_hull_purchases: int = 0
    hull_reinforce_purchases: int = 0
    drone_armored: bool = False
    drone_wingman_hp: int = 0
    drone_wingman_pending: bool = False
    weapon_track: WeaponTrack | None = None
    weapon_advanced: bool = False

    @classmethod
    def new(cls) -> CampaignState:
        return cls(lives=MAX_LIVES, hull_chunks=CHUNKS_PER_LIFE, jewels=DEV_START_JEWELS)

    @property
    def has_drone_contract(self) -> bool:
        return self.drone_wingman_hp > 0 or self.drone_wingman_pending

    @property
    def max_hull_chunks_per_life(self) -> int:
        return CHUNKS_PER_LIFE + HULL_REINFORCE_BONUS * self.hull_reinforce_purchases

    @property
    def drone_hits_max(self) -> int:
        from gravity_ho_matey.gameplay.drone_config import DRONE_ARMORED_HITS_MAX, DRONE_WINGMAN_HITS_MAX

        return DRONE_ARMORED_HITS_MAX if self.drone_armored else DRONE_WINGMAN_HITS_MAX

    @property
    def powerups(self) -> set[PowerUpKind]:
        """Unique upgrade kinds carried — use powerup_stacks for stack depth."""
        return active_powerup_kinds(self.powerup_stacks)

    def add_jewels(self, amount: int) -> None:
        if amount > 0:
            self.jewels += amount

    def upgrade_price(self, kind: PowerUpKind) -> int | None:
        return shop_price_for(
            kind,
            stacks=self.powerup_stacks.get(kind, 0),
            rubber_hull_purchases=self.rubber_hull_purchases,
            hull_reinforce_purchases=self.hull_reinforce_purchases,
        )

    def can_purchase(self, kind: PowerUpKind) -> bool:
        price = self.upgrade_price(kind)
        if price is None or self.jewels < price:
            return False
        if kind is PowerUpKind.RUBBER_HULL:
            return self.rubber_hull_charges <= 0
        if kind is PowerUpKind.DRONE_WINGMAN:
            return not self.has_drone_contract
        if kind is PowerUpKind.HULL_REINFORCE:
            return self.hull_reinforce_purchases < HULL_REINFORCE_MAX_PURCHASES
        if kind is PowerUpKind.DRONE_REPAIR:
            if not self.has_drone_contract or self.drone_wingman_pending:
                return False
            return 0 < self.drone_wingman_hp < self.drone_hits_max
        if kind is PowerUpKind.DRONE_ARMOR:
            return self.has_drone_contract and not self.drone_armored
        if is_weapon_powerup(kind):
            return self.weapon_track is None
        if is_weapon_advanced_powerup(kind):
            track = weapon_track_from_kind(kind)
            return (
                track is not None
                and self.weapon_track is track
                and not self.weapon_advanced
            )
        stack_count = (
            self.hull_reinforce_purchases
            if kind is PowerUpKind.HULL_REINFORCE
            else self.powerup_stacks.get(kind, 0)
        )
        if shop_at_max_stacks(kind, stack_count):
            return False
        return True

    def can_afford(self, kind: PowerUpKind) -> bool:
        return self.can_purchase(kind)

    def try_purchase(self, kind: PowerUpKind, ship: Ship | None = None) -> bool:
        if not self.can_purchase(kind):
            return False
        price = self.upgrade_price(kind)
        assert price is not None
        self.jewels -= price
        if kind is PowerUpKind.RUBBER_HULL:
            self.rubber_hull_charges = RUBBER_HULL_BOUNCE_CHARGES
            self.rubber_hull_purchases += 1
        elif kind is PowerUpKind.DRONE_WINGMAN:
            self.drone_wingman_pending = True
        elif kind is PowerUpKind.HULL_REINFORCE:
            self.hull_reinforce_purchases += 1
            self.hull_chunks = min(
                self.max_hull_chunks_per_life,
                self.hull_chunks + HULL_REINFORCE_BONUS,
            )
        elif kind is PowerUpKind.DRONE_REPAIR:
            self.drone_wingman_hp = self.drone_hits_max
        elif kind is PowerUpKind.DRONE_ARMOR:
            self.drone_armored = True
            if self.drone_wingman_hp > 0:
                self.drone_wingman_hp = self.drone_hits_max
        elif is_weapon_powerup(kind):
            track = weapon_track_from_kind(kind)
            assert track is not None
            self.weapon_track = track
        elif is_weapon_advanced_powerup(kind):
            track = weapon_track_from_kind(kind)
            assert track is not None
            self.weapon_track = track
            self.weapon_advanced = True
        else:
            self.powerup_stacks[kind] += 1
            if ship is not None:
                apply_powerups_to_ship(ship, self.powerup_stacks)
        return True

    def try_consume_rubber_hull_bounce(self) -> bool:
        """Spend one rubber-hull charge on an asteroid bump. Returns True if absorbed."""
        if self.rubber_hull_charges <= 0:
            return False
        self.rubber_hull_charges -= 1
        return True

    def collect_powerup(self, kind: PowerUpKind, ship: Ship) -> None:
        if kind is PowerUpKind.RUBBER_HULL:
            if self.rubber_hull_charges <= 0:
                self.rubber_hull_charges = RUBBER_HULL_BOUNCE_CHARGES
            return
        if shop_at_max_stacks(kind, self.powerup_stacks.get(kind, 0)):
            return
        self.powerup_stacks[kind] += 1
        apply_powerups_to_ship(ship, self.powerup_stacks)

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
