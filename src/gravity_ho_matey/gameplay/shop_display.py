from __future__ import annotations

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.shop_catalog import shop_at_max_stacks, shop_item_for
from gravity_ho_matey.gameplay.drone_config import DRONE_WINGMAN_HITS_MAX
from gravity_ho_matey.gameplay.upgrade_config import RUBBER_HULL_BOUNCE_CHARGES, UPGRADE_MAX_STACKS


def shop_owned_status(campaign: CampaignState, kind: PowerUpKind) -> str:
    if kind is PowerUpKind.DRONE_WINGMAN:
        if campaign.drone_wingman_pending:
            return "Purchased — deploys next sector"
        if campaign.drone_wingman_hp > 0:
            return f"ACTIVE · {campaign.drone_wingman_hp}/{DRONE_WINGMAN_HITS_MAX} HP"
        return "One escort contract per campaign life"
    if kind is PowerUpKind.RUBBER_HULL:
        if campaign.rubber_hull_charges > 0:
            return f"ACTIVE · {campaign.rubber_hull_charges}/{RUBBER_HULL_BOUNCE_CHARGES} bounces"
        return f"Coats worn — next buy grants {RUBBER_HULL_BOUNCE_CHARGES} bounces"
    stacks = campaign.powerup_stacks.get(kind, 0)
    item = shop_item_for(kind)
    if item is not None and item.max_stacks is not None:
        return f"Tier {stacks}/{item.max_stacks}"
    if stacks:
        return f"Owned ×{stacks}"
    return "Not installed"


def shop_button_label(campaign: CampaignState, kind: PowerUpKind) -> str:
    if not campaign.can_purchase(kind):
        if kind is PowerUpKind.DRONE_WINGMAN and campaign.has_drone_contract:
            return "ACTIVE" if campaign.drone_wingman_hp > 0 else "DEPLOYING"
        if kind is PowerUpKind.RUBBER_HULL and campaign.rubber_hull_charges > 0:
            return "ACTIVE"
        item = shop_item_for(kind)
        if item is not None and shop_at_max_stacks(kind, campaign.powerup_stacks.get(kind, 0)):
            return "MAX TIER"
        return "NEED ★"
    return "PURCHASE"
