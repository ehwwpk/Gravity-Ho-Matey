from __future__ import annotations

from collections.abc import Callable

from gravity_ho_matey.core.vector import Vec2
from gravity_ho_matey.gameplay.campaign import CHUNKS_PER_LIFE, CampaignState
from gravity_ho_matey.gameplay.entities import GameStatus
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.ship_modifiers import apply_powerups_to_ship
from gravity_ho_matey.gameplay.world import GameWorld

INVULN_SECONDS = 1.0
LOOT_TOAST_SECONDS = 2.8

PowerUpHudCallback = Callable[[PowerUpKind, bool], None]


def capture_level_spawn(world: GameWorld) -> None:
    world.spawn_pos = Vec2(world.ship.pos.x, world.ship.pos.y)
    world.spawn_angle = world.ship.angle


def ensure_active_life_hull(campaign: CampaignState) -> None:
    """Refill hull when starting a fresh life; keep partial hull between levels."""
    if campaign.lives > 0 and campaign.hull_chunks <= 0:
        campaign.hull_chunks = CHUNKS_PER_LIFE


def wire_world_for_campaign(
    world: GameWorld,
    campaign: CampaignState,
    *,
    on_powerup_collected_hud: PowerUpHudCallback | None = None,
) -> None:
    """Apply carried campaign bonuses and route pickup collection back to campaign."""
    apply_powerups_to_ship(world.ship, campaign.powerups)

    def on_powerup_collected(kind: PowerUpKind) -> None:
        is_new = kind not in campaign.powerups
        campaign.collect_powerup(kind, world.ship)
        if on_powerup_collected_hud is not None:
            on_powerup_collected_hud(kind, is_new)

    world.on_powerup_collected = on_powerup_collected


def respawn_ship_at_spawn(world: GameWorld) -> None:
    world.ship.pos = Vec2(world.spawn_pos.x, world.spawn_pos.y)
    world.ship.vel = Vec2()
    world.ship.angle = world.spawn_angle
    world.ship.cooldown = 0.0
    world.invuln_remaining = INVULN_SECONDS
    world.last_damage = None
    world.status = GameStatus.RUNNING
