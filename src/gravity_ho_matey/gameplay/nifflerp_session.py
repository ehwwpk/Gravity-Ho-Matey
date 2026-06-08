from __future__ import annotations

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.nifflerp import Nifflerp
from gravity_ho_matey.gameplay.nifflerp_config import NIFFLERP_HITS_MAX
from gravity_ho_matey.gameplay.world import GameWorld


def deploy_nifflerp(world: GameWorld, campaign: CampaignState) -> None:
    """Spawn jewel retriever when the holo contract is active."""
    if world.nifflerp is not None:
        return
    if not campaign.has_nifflerp_contract:
        return
    if campaign.nifflerp_pending:
        world.nifflerp = Nifflerp.spawn_beside_player(world.ship, hits_max=NIFFLERP_HITS_MAX)
        campaign.nifflerp_hp = world.nifflerp.hits_remaining
        campaign.nifflerp_pending = False
        return
    if campaign.nifflerp_hp > 0:
        world.nifflerp = Nifflerp.spawn_beside_player(
            world.ship,
            hits_remaining=campaign.nifflerp_hp,
            hits_max=NIFFLERP_HITS_MAX,
        )


def sync_nifflerp_to_campaign(world: GameWorld, campaign: CampaignState) -> None:
    buddy = world.nifflerp
    if buddy is None or not buddy.alive:
        campaign.nifflerp_hp = 0
        world.nifflerp = None
    else:
        campaign.nifflerp_hp = buddy.hits_remaining
