from __future__ import annotations

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.ship_modifiers import apply_powerups_to_ship
from gravity_ho_matey.gameplay.world import GameWorld


def wire_world_for_campaign(world: GameWorld, campaign: CampaignState) -> None:
    """Apply carried campaign bonuses and route pickup collection back to campaign."""
    apply_powerups_to_ship(world.ship, campaign.powerups)

    def on_powerup_collected(kind: PowerUpKind) -> None:
        campaign.collect_powerup(kind, world.ship)

    world.on_powerup_collected = on_powerup_collected
