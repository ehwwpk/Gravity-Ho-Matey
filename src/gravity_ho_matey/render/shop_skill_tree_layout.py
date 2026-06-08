from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gravity_ho_matey.gameplay.powerup_kinds import PowerUpKind
from gravity_ho_matey.gameplay.shop_catalog import shop_item_for, shop_weapon_doctrine_catalog
from gravity_ho_matey.gameplay.weapon_kinds import WeaponTrack

if TYPE_CHECKING:
    from gravity_ho_matey.gameplay.campaign import CampaignState
    from gravity_ho_matey.render.shop_tree_view import ShopTreeView


@dataclass(frozen=True, slots=True)
class SkillTreeBranch:
    branch_id: str
    label: str
    label_angle_deg: float
    label_radius: float


@dataclass(frozen=True, slots=True)
class SkillTreeNode:
    kind: PowerUpKind
    angle_deg: float
    radius: float
    branch_id: str
    chain_index: int = 0


@dataclass(frozen=True, slots=True)
class SkillTreeViewport:
    """Maps tree-local coordinates (hub at origin) onto the shop panel."""

    screen_cx: float
    screen_cy: float
    scale: float


BRANCHES: tuple[SkillTreeBranch, ...] = (
    SkillTreeBranch("weapons", "WEAPON DOCTRINE", -90.0, 52.0),
    SkillTreeBranch("drive", "DRIVE", 8.0, 52.0),
    SkillTreeBranch("hull", "HULL", 178.0, 52.0),
    SkillTreeBranch("escort", "ESCORT", 72.0, 52.0),
)

# Four quadrants, staggered tiers — wide fan so node cards never stack.
_WEAPON_NODES: tuple[SkillTreeNode, ...] = (
    SkillTreeNode(PowerUpKind.WEAPON_LASER, -132.0, 178.0, "weapons", 0),
    SkillTreeNode(PowerUpKind.WEAPON_SHOTGUN, -90.0, 272.0, "weapons", 1),
    SkillTreeNode(PowerUpKind.WEAPON_EXPLOSIVE, -48.0, 178.0, "weapons", 2),
)

_DRIVE_NODES: tuple[SkillTreeNode, ...] = (
    SkillTreeNode(PowerUpKind.THRUST_BOOST, 4.0, 178.0, "drive", 0),
    SkillTreeNode(PowerUpKind.BOOST_TAP, 22.0, 272.0, "drive", 1),
    SkillTreeNode(PowerUpKind.RAPID_FIRE, 38.0, 358.0, "drive", 2),
)

_HULL_NODES: tuple[SkillTreeNode, ...] = (
    SkillTreeNode(PowerUpKind.RUBBER_HULL, 178.0, 178.0, "hull", 0),
    SkillTreeNode(PowerUpKind.HULL_REINFORCE, 198.0, 272.0, "hull", 1),
)

_ESCORT_BASE: tuple[SkillTreeNode, ...] = (
    SkillTreeNode(PowerUpKind.DRONE_WINGMAN, 58.0, 178.0, "escort", 0),
    SkillTreeNode(PowerUpKind.NIFFLERP, 106.0, 178.0, "escort", 0),
)

_ESCORT_UPGRADES: tuple[SkillTreeNode, ...] = (
    SkillTreeNode(PowerUpKind.DRONE_REPAIR, 74.0, 272.0, "escort", 1),
    SkillTreeNode(PowerUpKind.DRONE_ARMOR, 90.0, 358.0, "escort", 2),
)

NODE_W = 104.0
NODE_H = 68.0
HUB_R = 40.0

_WEAPON_ADV_BY_TRACK: dict[WeaponTrack, SkillTreeNode] = {
    WeaponTrack.LASER: SkillTreeNode(PowerUpKind.WEAPON_ADV_LASER, -132.0, 358.0, "weapons", 3),
    WeaponTrack.SHOTGUN: SkillTreeNode(PowerUpKind.WEAPON_ADV_SHOTGUN, -90.0, 358.0, "weapons", 3),
    WeaponTrack.EXPLOSIVE: SkillTreeNode(PowerUpKind.WEAPON_ADV_EXPLOSIVE, -48.0, 358.0, "weapons", 3),
}


SHOP_OPEN_ANIM_SECONDS = 0.42


def shop_open_anim_at(open_since: float | None, now: float) -> float:
    if open_since is None:
        return 1.0
    return min(1.0, max(0.0, (now - open_since) / SHOP_OPEN_ANIM_SECONDS))


def skill_tree_nodes(campaign: CampaignState) -> tuple[SkillTreeNode, ...]:
    nodes: list[SkillTreeNode] = [
        *_WEAPON_NODES,
        *_DRIVE_NODES,
        *_HULL_NODES,
        *_ESCORT_BASE,
    ]
    if campaign.weapon_track is not None and not campaign.weapon_advanced:
        nodes.append(_WEAPON_ADV_BY_TRACK[campaign.weapon_track])
    if campaign.has_drone_contract:
        nodes.extend(_ESCORT_UPGRADES)
    return tuple(nodes)


def node_tree_xy(node: SkillTreeNode) -> tuple[float, float]:
    rad = math.radians(node.angle_deg)
    return math.cos(rad) * node.radius, math.sin(rad) * node.radius


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def tree_content_rect(
    nodes: tuple[SkillTreeNode, ...],
    *,
    node_w: float = NODE_W,
    node_h: float = NODE_H,
    hub_r: float = HUB_R,
) -> tuple[float, float, float, float]:
    """Axis-aligned bounds in tree-local space (x0, y0, x1, y1)."""
    half_w = node_w * 0.5
    half_h = node_h * 0.5
    min_x = -hub_r
    min_y = -hub_r
    max_x = hub_r
    max_y = hub_r
    for node in nodes:
        tx, ty = node_tree_xy(node)
        min_x = min(min_x, tx - half_w)
        min_y = min(min_y, ty - half_h)
        max_x = max(max_x, tx + half_w)
        max_y = max(max_y, ty + half_h)
    return min_x, min_y, max_x, max_y


def compute_fit_viewport(
    nodes: tuple[SkillTreeNode, ...],
    *,
    left: float,
    top: float,
    width: float,
    height: float,
    open_anim: float = 1.0,
    padding: float = 22.0,
    fill: float = 0.80,
) -> SkillTreeViewport:
    """Fit the full tree inside the panel; gentle zoom-in when the deck opens."""
    if width <= 0.0 or height <= 0.0:
        return SkillTreeViewport(left + width * 0.5, top + height * 0.5, 1.0)

    min_x, min_y, max_x, max_y = tree_content_rect(nodes)
    bbox_w = max(1.0, max_x - min_x)
    bbox_h = max(1.0, max_y - min_y)
    bbox_cx = (min_x + max_x) * 0.5
    bbox_cy = (min_y + max_y) * 0.5

    avail_w = max(1.0, width - padding * 2.0)
    avail_h = max(1.0, height - padding * 2.0)
    fit_scale = min(avail_w / bbox_w, avail_h / bbox_h) * fill
    fit_scale = max(0.56, min(1.08, fit_scale))

    eased = ease_out_cubic(open_anim)
    scale = fit_scale * (0.84 + 0.16 * eased)

    screen_cx = left + width * 0.5 - bbox_cx * scale
    screen_cy = top + height * 0.5 - bbox_cy * scale
    return SkillTreeViewport(screen_cx, screen_cy, scale)


def compute_viewport(
    nodes: tuple[SkillTreeNode, ...],
    *,
    left: float,
    top: float,
    width: float,
    height: float,
    open_anim: float = 1.0,
    padding: float = 18.0,
    fill: float = 0.86,
    view: ShopTreeView | None = None,
) -> SkillTreeViewport:
    from gravity_ho_matey.render.shop_tree_view import ShopTreeView, apply_shop_tree_view

    fit = compute_fit_viewport(
        nodes,
        left=left,
        top=top,
        width=width,
        height=height,
        open_anim=open_anim,
        padding=padding,
        fill=fill,
    )
    if view is None:
        view = ShopTreeView()
    return apply_shop_tree_view(fit, view)


def shop_tree_rect(
    panel_x: float,
    panel_y: float,
    panel_w: float,
    panel_h: float,
    *,
    header_h: float = 48.0,
    footer_h: float = 44.0,
) -> tuple[float, float, float, float]:
    """Usable tree canvas inside the holo shop panel."""
    tree_top = panel_y + header_h + 10.0
    tree_bottom = panel_y + panel_h - footer_h
    inset = 12.0
    return (
        panel_x + inset,
        tree_top,
        panel_w - inset * 2.0,
        max(1.0, tree_bottom - tree_top),
    )


def node_screen_center(viewport: SkillTreeViewport, node: SkillTreeNode) -> tuple[float, float]:
    tx, ty = node_tree_xy(node)
    return viewport.screen_cx + tx * viewport.scale, viewport.screen_cy + ty * viewport.scale


def node_center(cx: float, cy: float, node: SkillTreeNode) -> tuple[float, float]:
    """Legacy helper — prefer viewport-based placement in new code."""
    _ = cx, cy
    return node_tree_xy(node)


def node_bounds(viewport: SkillTreeViewport, node: SkillTreeNode) -> tuple[float, float, float, float]:
    nx, ny = node_screen_center(viewport, node)
    w = NODE_W * viewport.scale
    h = NODE_H * viewport.scale
    return nx - w * 0.5, ny - h * 0.5, w, h


def branch_label_position(viewport: SkillTreeViewport, branch: SkillTreeBranch) -> tuple[float, float]:
    rad = math.radians(branch.label_angle_deg)
    tx = math.cos(rad) * branch.label_radius
    ty = math.sin(rad) * branch.label_radius
    return viewport.screen_cx + tx * viewport.scale, viewport.screen_cy + ty * viewport.scale


def hub_screen_center(viewport: SkillTreeViewport) -> tuple[float, float]:
    return viewport.screen_cx, viewport.screen_cy


def hub_screen_radius(viewport: SkillTreeViewport) -> float:
    return HUB_R * viewport.scale


def nodes_overlap(
    viewport: SkillTreeViewport,
    nodes: tuple[SkillTreeNode, ...],
    *,
    gap: float = 6.0,
) -> bool:
    boxes = [node_bounds(viewport, n) for n in nodes]
    for i, ax in enumerate(boxes):
        ax0, ay0, aw, ah = ax
        ax1, ay1 = ax0 + aw, ay0 + ah
        for bx in boxes[i + 1 :]:
            bx0, by0, bw, bh = bx
            bx1, by1 = bx0 + bw, by0 + bh
            if ax0 < bx1 + gap and ax1 + gap > bx0 and ay0 < by1 + gap and ay1 + gap > by0:
                return True
    return False


def nodes_in_branch(nodes: tuple[SkillTreeNode, ...], branch_id: str) -> tuple[SkillTreeNode, ...]:
    return tuple(sorted((n for n in nodes if n.branch_id == branch_id), key=lambda n: n.chain_index))


def weapon_advanced_node_for_track(track: WeaponTrack) -> SkillTreeNode:
    return _WEAPON_ADV_BY_TRACK[track]


def doctrine_items() -> tuple:
    return shop_weapon_doctrine_catalog()


def item_for_node(node: SkillTreeNode):
    return shop_item_for(node.kind)

