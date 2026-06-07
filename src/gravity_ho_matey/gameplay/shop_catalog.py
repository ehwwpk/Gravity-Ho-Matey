from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.gameplay.powerup_kinds import POWERUP_HUD_TAGS, POWERUP_LABELS, PowerUpKind
from gravity_ho_matey.gameplay.drone_config import DRONE_WINGMAN_SHOP_PRICE
from gravity_ho_matey.gameplay.upgrade_config import UPGRADE_MAX_STACKS


@dataclass(frozen=True, slots=True)
class ShopItem:
    kind: PowerUpKind
    base_price: int
    tag: str
    label: str
    max_stacks: int | None = UPGRADE_MAX_STACKS


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
        max_stacks=None,
    ),
    ShopItem(
        PowerUpKind.RUBBER_HULL,
        16,
        POWERUP_HUD_TAGS[PowerUpKind.RUBBER_HULL],
        POWERUP_LABELS[PowerUpKind.RUBBER_HULL],
        max_stacks=None,
    ),
    ShopItem(
        PowerUpKind.DRONE_WINGMAN,
        DRONE_WINGMAN_SHOP_PRICE,
        POWERUP_HUD_TAGS[PowerUpKind.DRONE_WINGMAN],
        POWERUP_LABELS[PowerUpKind.DRONE_WINGMAN],
        max_stacks=None,
    ),
)

_SHOP_BY_KIND = {item.kind: item for item in SHOP_CATALOG}


def shop_item_for(kind: PowerUpKind) -> ShopItem | None:
    return _SHOP_BY_KIND.get(kind)


def shop_hit_id(kind: PowerUpKind) -> str:
    return f"shop_{kind.name.lower()}"


def shop_price_for(
    kind: PowerUpKind,
    *,
    stacks: int,
    rubber_hull_purchases: int,
) -> int | None:
    """Next purchase price — doubles per tier already owned (or per rubber hull bought)."""
    item = shop_item_for(kind)
    if item is None:
        return None
    if kind is PowerUpKind.RUBBER_HULL:
        return item.base_price * (2**rubber_hull_purchases)
    if kind is PowerUpKind.DRONE_WINGMAN:
        return item.base_price
    return item.base_price * (2**stacks)


def shop_at_max_stacks(kind: PowerUpKind, stacks: int) -> bool:
    item = shop_item_for(kind)
    if item is None or item.max_stacks is None:
        return False
    return stacks >= item.max_stacks
