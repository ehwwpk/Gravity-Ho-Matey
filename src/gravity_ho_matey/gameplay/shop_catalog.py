from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from gravity_ho_matey.gameplay.powerup_kinds import POWERUP_HUD_TAGS, POWERUP_LABELS, PowerUpKind
from gravity_ho_matey.gameplay.drone_config import DRONE_WINGMAN_SHOP_PRICE
from gravity_ho_matey.gameplay.upgrade_config import (
    DRONE_ARMOR_PRICE,
    DRONE_REPAIR_PRICE,
    HULL_REINFORCE_BASE_PRICE,
    HULL_REINFORCE_COST_MULTIPLIER,
    HULL_REINFORCE_MAX_PURCHASES,
    UPGRADE_MAX_STACKS,
)
from gravity_ho_matey.gameplay.weapon_config import WEAPON_ADVANCED_PRICE, WEAPON_DOCTRINE_PRICE
from gravity_ho_matey.gameplay.weapon_kinds import is_weapon_advanced_powerup, is_weapon_powerup

if TYPE_CHECKING:
    from gravity_ho_matey.gameplay.campaign import CampaignState


@dataclass(frozen=True, slots=True)
class ShopItem:
    kind: PowerUpKind
    base_price: int
    tag: str
    label: str
    max_stacks: int | None = UPGRADE_MAX_STACKS


WEAPON_DOCTRINE_CATALOG: tuple[ShopItem, ...] = (
    ShopItem(
        PowerUpKind.WEAPON_LASER,
        WEAPON_DOCTRINE_PRICE,
        POWERUP_HUD_TAGS[PowerUpKind.WEAPON_LASER],
        POWERUP_LABELS[PowerUpKind.WEAPON_LASER],
        max_stacks=1,
    ),
    ShopItem(
        PowerUpKind.WEAPON_SHOTGUN,
        WEAPON_DOCTRINE_PRICE,
        POWERUP_HUD_TAGS[PowerUpKind.WEAPON_SHOTGUN],
        POWERUP_LABELS[PowerUpKind.WEAPON_SHOTGUN],
        max_stacks=1,
    ),
    ShopItem(
        PowerUpKind.WEAPON_EXPLOSIVE,
        WEAPON_DOCTRINE_PRICE,
        POWERUP_HUD_TAGS[PowerUpKind.WEAPON_EXPLOSIVE],
        POWERUP_LABELS[PowerUpKind.WEAPON_EXPLOSIVE],
        max_stacks=1,
    ),
)

SHOP_CATALOG: tuple[ShopItem, ...] = (
    ShopItem(
        PowerUpKind.THRUST_BOOST,
        12,
        POWERUP_HUD_TAGS[PowerUpKind.THRUST_BOOST],
        POWERUP_LABELS[PowerUpKind.THRUST_BOOST],
        max_stacks=UPGRADE_MAX_STACKS,
    ),
    ShopItem(
        PowerUpKind.BOOST_TAP,
        12,
        POWERUP_HUD_TAGS[PowerUpKind.BOOST_TAP],
        POWERUP_LABELS[PowerUpKind.BOOST_TAP],
        max_stacks=UPGRADE_MAX_STACKS,
    ),
    ShopItem(
        PowerUpKind.RAPID_FIRE,
        14,
        POWERUP_HUD_TAGS[PowerUpKind.RAPID_FIRE],
        POWERUP_LABELS[PowerUpKind.RAPID_FIRE],
        max_stacks=1,
    ),
    ShopItem(
        PowerUpKind.RUBBER_HULL,
        16,
        POWERUP_HUD_TAGS[PowerUpKind.RUBBER_HULL],
        POWERUP_LABELS[PowerUpKind.RUBBER_HULL],
        max_stacks=None,
    ),
    ShopItem(
        PowerUpKind.HULL_REINFORCE,
        HULL_REINFORCE_BASE_PRICE,
        POWERUP_HUD_TAGS[PowerUpKind.HULL_REINFORCE],
        POWERUP_LABELS[PowerUpKind.HULL_REINFORCE],
        max_stacks=HULL_REINFORCE_MAX_PURCHASES,
    ),
    ShopItem(
        PowerUpKind.DRONE_WINGMAN,
        DRONE_WINGMAN_SHOP_PRICE,
        POWERUP_HUD_TAGS[PowerUpKind.DRONE_WINGMAN],
        POWERUP_LABELS[PowerUpKind.DRONE_WINGMAN],
        max_stacks=None,
    ),
)

DRONE_UPGRADE_CATALOG: tuple[ShopItem, ...] = (
    ShopItem(
        PowerUpKind.DRONE_REPAIR,
        DRONE_REPAIR_PRICE,
        POWERUP_HUD_TAGS[PowerUpKind.DRONE_REPAIR],
        POWERUP_LABELS[PowerUpKind.DRONE_REPAIR],
        max_stacks=None,
    ),
    ShopItem(
        PowerUpKind.DRONE_ARMOR,
        DRONE_ARMOR_PRICE,
        POWERUP_HUD_TAGS[PowerUpKind.DRONE_ARMOR],
        POWERUP_LABELS[PowerUpKind.DRONE_ARMOR],
        max_stacks=1,
    ),
)

WEAPON_ADVANCED_CATALOG: tuple[ShopItem, ...] = (
    ShopItem(
        PowerUpKind.WEAPON_ADV_LASER,
        WEAPON_ADVANCED_PRICE,
        POWERUP_HUD_TAGS[PowerUpKind.WEAPON_ADV_LASER],
        POWERUP_LABELS[PowerUpKind.WEAPON_ADV_LASER],
        max_stacks=1,
    ),
    ShopItem(
        PowerUpKind.WEAPON_ADV_SHOTGUN,
        WEAPON_ADVANCED_PRICE,
        POWERUP_HUD_TAGS[PowerUpKind.WEAPON_ADV_SHOTGUN],
        POWERUP_LABELS[PowerUpKind.WEAPON_ADV_SHOTGUN],
        max_stacks=1,
    ),
    ShopItem(
        PowerUpKind.WEAPON_ADV_EXPLOSIVE,
        WEAPON_ADVANCED_PRICE,
        POWERUP_HUD_TAGS[PowerUpKind.WEAPON_ADV_EXPLOSIVE],
        POWERUP_LABELS[PowerUpKind.WEAPON_ADV_EXPLOSIVE],
        max_stacks=1,
    ),
)

_SHOP_BY_KIND = {
    item.kind: item
    for item in (*WEAPON_DOCTRINE_CATALOG, *WEAPON_ADVANCED_CATALOG, *SHOP_CATALOG, *DRONE_UPGRADE_CATALOG)
}


def shop_weapon_doctrine_catalog() -> tuple[ShopItem, ...]:
    return WEAPON_DOCTRINE_CATALOG


def shop_visible_catalog(campaign: CampaignState) -> tuple[ShopItem, ...]:
    items = list(SHOP_CATALOG)
    if campaign.has_drone_contract:
        items.extend(DRONE_UPGRADE_CATALOG)
    return tuple(items)


def shop_item_for(kind: PowerUpKind) -> ShopItem | None:
    return _SHOP_BY_KIND.get(kind)


def shop_hit_id(kind: PowerUpKind) -> str:
    return f"shop_{kind.name.lower()}"


def shop_kind_from_hit(hit: str) -> PowerUpKind | None:
    if not hit.startswith("shop_"):
        return None
    suffix = hit.removeprefix("shop_").upper()
    try:
        return PowerUpKind[suffix]
    except KeyError:
        return None


def shop_price_for(
    kind: PowerUpKind,
    *,
    stacks: int,
    rubber_hull_purchases: int,
    hull_reinforce_purchases: int = 0,
) -> int | None:
    """Next purchase price — doubles per tier (or triple for hull reinforce)."""
    item = shop_item_for(kind)
    if item is None:
        return None
    if kind is PowerUpKind.RUBBER_HULL:
        return item.base_price * (2**rubber_hull_purchases)
    if kind is PowerUpKind.HULL_REINFORCE:
        return item.base_price * (HULL_REINFORCE_COST_MULTIPLIER**hull_reinforce_purchases)
    if kind in (
        PowerUpKind.DRONE_WINGMAN,
        PowerUpKind.DRONE_REPAIR,
        PowerUpKind.DRONE_ARMOR,
        PowerUpKind.RAPID_FIRE,
    ) or is_weapon_powerup(kind) or is_weapon_advanced_powerup(kind):
        return item.base_price
    return item.base_price * (2**stacks)


def shop_at_max_stacks(kind: PowerUpKind, stacks: int) -> bool:
    item = shop_item_for(kind)
    if item is None or item.max_stacks is None:
        return False
    if kind is PowerUpKind.HULL_REINFORCE:
        return stacks >= HULL_REINFORCE_MAX_PURCHASES
    if kind is PowerUpKind.DRONE_ARMOR:
        return stacks >= 1
    if is_weapon_powerup(kind) or is_weapon_advanced_powerup(kind):
        return stacks >= 1
    return stacks >= item.max_stacks
