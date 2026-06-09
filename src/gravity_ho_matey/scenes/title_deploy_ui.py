"""Pointer + wheel handlers for the title screen deploy (level pick) list."""

from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.render.title_deploy_list import (
    DeployListLayout,
    DeploySplitLayout,
    clamp_scroll,
    deploy_split_contains,
    panel_list_contains,
    scroll_from_drag_delta,
    scroll_wheel_delta,
    scrollbar_geometry,
    scroll_at_track_y,
    viewport_contains,
)

_DRAG_THRESHOLD_PX = 4.0


@dataclass(slots=True)
class DeployListUiState:
    pointer_down: bool = False
    dragging: bool = False
    thumb_dragging: bool = False
    down_x: float = 0.0
    down_y: float = 0.0
    down_scroll: float = 0.0
    down_hit: str | None = None
    drag_y: float = 0.0
    moved: bool = False


def deploy_list_reset(state: DeployListUiState) -> None:
    state.pointer_down = False
    state.dragging = False
    state.thumb_dragging = False
    state.down_hit = None
    state.moved = False


def deploy_list_wheel(
    scroll: float,
    layout: DeployListLayout,
    x: float,
    y: float,
    delta: int,
    *,
    split: DeploySplitLayout | None = None,
) -> float | None:
    """Return updated scroll when wheel applies over the deploy page."""
    if delta == 0 or layout.max_scroll <= 0.0:
        return None
    if split is not None:
        if not deploy_split_contains(split, x, y):
            return None
    elif not panel_list_contains(layout, x, y):
        return None
    return scroll_wheel_delta(scroll, layout, delta)


def deploy_list_pointer_down(
    state: DeployListUiState,
    x: float,
    y: float,
    hit: str | None,
    *,
    layout: DeployListLayout,
    scroll: float,
) -> None:
    state.pointer_down = True
    state.dragging = False
    state.thumb_dragging = False
    state.moved = False
    state.down_x = x
    state.down_y = y
    state.down_scroll = scroll
    state.down_hit = hit
    state.drag_y = y
    if hit == "deploy_scroll_thumb":
        state.thumb_dragging = True
        return
    if hit == "deploy_scroll_track":
        return
    if panel_list_contains(layout, x, y) or viewport_contains(layout, x, y):
        state.dragging = True


def deploy_list_pointer_motion(
    state: DeployListUiState,
    x: float,
    y: float,
    *,
    layout: DeployListLayout,
    scroll: float,
) -> float | None:
    if not state.pointer_down:
        return None
    if abs(y - state.down_y) > _DRAG_THRESHOLD_PX or abs(x - state.down_x) > _DRAG_THRESHOLD_PX:
        state.moved = True
    if state.thumb_dragging:
        track_x, track_y, track_h, _thumb_y, thumb_h = scrollbar_geometry(layout, scroll)
        _ = track_x
        return scroll_at_track_y(layout, track_y, track_h, thumb_h, y)
    if not state.dragging:
        return None
    return scroll_from_drag_delta(state.down_scroll, layout, y - state.down_y)


def deploy_list_pointer_up(state: DeployListUiState) -> tuple[str | None, bool]:
    """Return (pending_hit, consumed_as_drag)."""
    hit = state.down_hit
    dragged = state.moved and (state.dragging or state.thumb_dragging)
    deploy_list_reset(state)
    if dragged:
        return None, True
    return hit, False


def deploy_list_track_click(
    layout: DeployListLayout,
    x: float,
    y: float,
    scroll: float,
) -> float | None:
    track_x, track_y, track_h, _thumb_y, thumb_h = scrollbar_geometry(layout, scroll)
    if not (track_x <= x <= track_x + 8.0 and track_y <= y <= track_y + track_h):
        return None
    return scroll_at_track_y(layout, track_y, track_h, thumb_h, y)
