from __future__ import annotations

from dataclasses import dataclass, field

from gravity_ho_matey.gameplay.shop_catalog import shop_kind_from_hit
from gravity_ho_matey.render.shop_tree_view import (
    KEY_ZOOM_FACTOR,
    WHEEL_ZOOM_FACTOR,
    ShopTreeView,
)

_SHOP_ZOOM_HITS = frozenset({"shop_zoom_in", "shop_zoom_out", "shop_zoom_fit"})
_SHOP_CHROME_HITS = frozenset({"shop_close", "shop_zoom_in", "shop_zoom_out", "shop_zoom_fit"})


@dataclass(slots=True)
class ShopUiState:
    view: ShopTreeView = field(default_factory=ShopTreeView)
    dragging: bool = False
    drag_x: float = 0.0
    drag_y: float = 0.0


def shop_open_reset(state: ShopUiState) -> None:
    state.view.reset()
    state.dragging = False


def shop_on_open(state: ShopUiState, *, opening: bool) -> None:
    if opening:
        shop_open_reset(state)


def shop_on_pointer_down(state: ShopUiState, x: float, y: float, hit: str | None, *, shop_open: bool) -> None:
    if not shop_open:
        return
    if hit in _SHOP_CHROME_HITS:
        return
    if hit is not None and hit.startswith("shop_") and hit != "shop_tree_pan":
        return
    state.dragging = True
    state.drag_x = x
    state.drag_y = y


def shop_on_pointer_motion(state: ShopUiState, x: float, y: float, *, shop_open: bool) -> None:
    if not shop_open or not state.dragging:
        return
    state.view.pan_by(x - state.drag_x, y - state.drag_y)
    state.drag_x = x
    state.drag_y = y


def shop_on_pointer_up(state: ShopUiState) -> None:
    state.dragging = False


def shop_on_wheel(
    state: ShopUiState,
    x: float,
    y: float,
    delta: int,
    *,
    shop_open: bool,
    fit_viewport,
) -> None:
    if not shop_open or delta == 0:
        return
    factor = WHEEL_ZOOM_FACTOR if delta > 0 else 1.0 / WHEEL_ZOOM_FACTOR
    state.view.zoom_by(factor, mx=x, my=y, fit=fit_viewport)


def shop_on_key(state: ShopUiState, key: str, *, shop_open: bool, fit_viewport, pointer: tuple[float, float]) -> bool:
    """Return True if the key was consumed."""
    if not shop_open:
        return False
    lowered = key.lower()
    mx, my = pointer
    if lowered in ("equal", "plus", "kp_add"):
        state.view.zoom_by(KEY_ZOOM_FACTOR, mx=mx, my=my, fit=fit_viewport)
        return True
    if lowered in ("minus", "underscore", "kp_subtract"):
        state.view.zoom_by(1.0 / KEY_ZOOM_FACTOR, mx=mx, my=my, fit=fit_viewport)
        return True
    if lowered == "0":
        state.view.fit_all()
        return True
    if lowered == "home":
        state.view.reset()
        return True
    return False


def shop_handle_pointer_click(
    hit: str | None,
    state: ShopUiState,
    *,
    shop_open: bool,
    fit_viewport,
    pointer: tuple[float, float],
    on_purchase,
) -> bool:
    """Handle shop chrome clicks. Return True if handled (no further action)."""
    if not shop_open or hit is None:
        return False
    mx, my = pointer
    if hit == "shop_zoom_in":
        state.view.zoom_by(KEY_ZOOM_FACTOR, mx=mx, my=my, fit=fit_viewport)
        return True
    if hit == "shop_zoom_out":
        state.view.zoom_by(1.0 / KEY_ZOOM_FACTOR, mx=mx, my=my, fit=fit_viewport)
        return True
    if hit == "shop_zoom_fit":
        state.view.fit_all()
        return True
    if hit.startswith("shop_"):
        kind = shop_kind_from_hit(hit)
        if kind is not None:
            on_purchase(kind)
            return True
        return False
    return False


def shop_fit_viewport_for(state: ShopUiState, campaign, *, vw: int = 960, vh: int = 640):
    from gravity_ho_matey.render.holo_shop_overlay import HoloShopOverlay
    from gravity_ho_matey.render.shop_skill_tree_layout import compute_fit_viewport, skill_tree_nodes

    px, py, pw, ph = HoloShopOverlay.panel_rect(vw, vh)
    tree_left, tree_top, tree_w, tree_h = HoloShopOverlay.tree_content_rect(px, py, pw, ph)
    nodes = skill_tree_nodes(campaign)
    return compute_fit_viewport(
        nodes,
        left=tree_left,
        top=tree_top,
        width=tree_w,
        height=tree_h,
        open_anim=1.0,
    )
