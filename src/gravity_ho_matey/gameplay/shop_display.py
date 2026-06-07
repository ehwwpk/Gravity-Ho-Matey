from __future__ import annotations

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.shop_catalog import shop_at_max_stacks, shop_item_for
from gravity_ho_matey.gameplay.upgrade_config import (
    HULL_REINFORCE_MAX_PURCHASES,
    RUBBER_HULL_BOUNCE_CHARGES,
)
from gravity_ho_matey.gameplay.weapon_kinds import (
    WEAPON_TRACK_SHORT,
    is_weapon_powerup,
    weapon_track_from_kind,
)


def shop_owned_status(campaign: CampaignState, kind: PowerUpKind) -> str:
    if is_weapon_powerup(kind):
        track = weapon_track_from_kind(kind)
        if campaign.weapon_track is track:
            return f"ACTIVE DOCTRINE · {WEAPON_TRACK_SHORT[track]}"
        if campaign.weapon_track is not None:
            active = WEAPON_TRACK_SHORT[campaign.weapon_track]
            return f"Locked — {active} installed"
        return "Pick one weapon path for this campaign"
    if kind is PowerUpKind.RAPID_FIRE:
        if campaign.powerup_stacks.get(PowerUpKind.RAPID_FIRE, 0):
            return "INSTALLED · modest fire-rate boost"
        return "One-time bolt cycle upgrade"
    if kind is PowerUpKind.DRONE_WINGMAN:
        if campaign.drone_wingman_pending:
            return "Purchased — deploys next sector"
        if campaign.drone_wingman_hp > 0:
            return f"ACTIVE · {campaign.drone_wingman_hp}/{campaign.drone_hits_max} HP"
        return "One escort contract per campaign life"
    if kind is PowerUpKind.DRONE_REPAIR:
        if not campaign.has_drone_contract:
            return "Requires active drone"
        if campaign.drone_wingman_pending:
            return "Deploys full HP next sector"
        if campaign.drone_wingman_hp <= 0:
            return "Drone destroyed — buy new contract"
        if campaign.drone_wingman_hp >= campaign.drone_hits_max:
            return "Escort at full HP"
        return f"Restore to {campaign.drone_hits_max}/{campaign.drone_hits_max} HP"
    if kind is PowerUpKind.DRONE_ARMOR:
        if campaign.drone_armored:
            return f"INSTALLED · {campaign.drone_hits_max} HP cap"
        return "Upgrade escort to 8 HP max (+3)"
    if kind is PowerUpKind.HULL_REINFORCE:
        max_h = campaign.max_hull_chunks_per_life
        return f"Life cap {max_h} chunks · {campaign.hull_reinforce_purchases}/{HULL_REINFORCE_MAX_PURCHASES} buys"
    if kind is PowerUpKind.RUBBER_HULL:
        if campaign.rubber_hull_charges > 0:
            return f"ACTIVE · {campaign.rubber_hull_charges}/{RUBBER_HULL_BOUNCE_CHARGES} bounces"
        return f"Coats worn — next buy grants {RUBBER_HULL_BOUNCE_CHARGES} bounces"
    stacks = campaign.powerup_stacks.get(kind, 0)
    item = shop_item_for(kind)
    if item is not None and item.max_stacks is not None and kind is not PowerUpKind.HULL_REINFORCE:
        return f"Tier {stacks}/{item.max_stacks}"
    if stacks:
        return f"Owned ×{stacks}"
    return "Not installed"


def shop_button_label(campaign: CampaignState, kind: PowerUpKind) -> str:
    if not campaign.can_purchase(kind):
        if is_weapon_powerup(kind):
            if campaign.weapon_track is not None:
                if weapon_track_from_kind(kind) is campaign.weapon_track:
                    return "ACTIVE"
                return "LOCKED"
        if kind is PowerUpKind.RAPID_FIRE and campaign.powerup_stacks.get(PowerUpKind.RAPID_FIRE, 0):
            return "INSTALLED"
        if kind is PowerUpKind.DRONE_WINGMAN and campaign.has_drone_contract:
            return "ACTIVE" if campaign.drone_wingman_hp > 0 else "DEPLOYING"
        if kind is PowerUpKind.DRONE_REPAIR:
            if campaign.drone_wingman_hp >= campaign.drone_hits_max and campaign.drone_wingman_hp > 0:
                return "FULL"
            if campaign.drone_wingman_hp <= 0 and not campaign.drone_wingman_pending:
                return "NO DRONE"
        if kind is PowerUpKind.DRONE_ARMOR and campaign.drone_armored:
            return "ARMORED"
        if kind is PowerUpKind.RUBBER_HULL and campaign.rubber_hull_charges > 0:
            return "ACTIVE"
        if kind is PowerUpKind.HULL_REINFORCE:
            if campaign.hull_reinforce_purchases >= HULL_REINFORCE_MAX_PURCHASES:
                return "MAX TIER"
        item = shop_item_for(kind)
        stack_count = (
            campaign.hull_reinforce_purchases
            if kind is PowerUpKind.HULL_REINFORCE
            else campaign.powerup_stacks.get(kind, 0)
        )
        if item is not None and shop_at_max_stacks(kind, stack_count):
            return "MAX TIER"
        return "NEED ★"
    return "PURCHASE"
