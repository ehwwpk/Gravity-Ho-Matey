"""Layout math for the paginated title screen deploy (level pick) list."""

from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.levels.level_registry import LEVEL_ORDER

DEPLOY_ROW_H = 64.0
DEPLOY_ROW_GAP = 8.0
DEPLOY_ROW_PITCH = DEPLOY_ROW_H + DEPLOY_ROW_GAP
DEPLOY_PREVIEW_FRAC = 0.40
DEPLOY_SPLIT_GAP = 12.0


@dataclass(frozen=True, slots=True)
class TitleChromeLayout:
    """Fixed vertical zones — body must not overlap shop, tab rail, or footer."""

    body_top: float
    body_bottom: float
    shop_y: float
    shop_h: float
    rail_y: float
    rail_h: float
    footer_y: float
    footer_h: float


@dataclass(frozen=True, slots=True)
class DeployPreviewLayout:
    x: float
    y: float
    w: float
    h: float


@dataclass(frozen=True, slots=True)
class DeploySplitLayout:
    list: DeployListLayout
    preview: DeployPreviewLayout


@dataclass(frozen=True, slots=True)
class DeployListLayout:
    panel_x: float
    panel_y: float
    panel_w: float
    panel_h: float
    viewport_x: float
    viewport_y: float
    viewport_w: float
    viewport_h: float
    row_pitch: float
    row_h: float
    content_h: float
    max_scroll: float
    level_count: int


def title_chrome_layout(
    *,
    screen_h: float,
    top_bar_h: float,
    footer_h: float,
    rail_h: float,
    shop_h: float,
    margin_gap: float = 6.0,
    body_pad: float = 8.0,
) -> TitleChromeLayout:
    footer_y = screen_h - footer_h
    rail_y = footer_y - margin_gap - rail_h
    if shop_h > 0.0:
        shop_y = rail_y - margin_gap - shop_h
        body_bottom = shop_y - body_pad
    else:
        shop_y = rail_y
        body_bottom = rail_y - body_pad
    body_top = top_bar_h + body_pad
    return TitleChromeLayout(
        body_top=body_top,
        body_bottom=body_bottom,
        shop_y=shop_y,
        shop_h=shop_h,
        rail_y=rail_y,
        rail_h=rail_h,
        footer_y=footer_y,
        footer_h=footer_h,
    )


def compute_deploy_split_layout(
    chrome: TitleChromeLayout,
    *,
    screen_w: float,
    margin: float = 16.0,
    header_h: float = 36.0,
    footer_hint_h: float = 22.0,
) -> DeploySplitLayout:
    """Full-width deploy panel — scroll list left, sector dossier right."""
    body_h = max(120.0, chrome.body_bottom - chrome.body_top)
    panel_w = screen_w - margin * 2.0
    panel_x = margin
    panel_y = chrome.body_top
    panel_h = body_h
    preview_w = max(280.0, panel_w * DEPLOY_PREVIEW_FRAC)
    list_w = panel_w - preview_w - DEPLOY_SPLIT_GAP
    list = compute_deploy_list_layout(
        chrome,
        screen_w=screen_w,
        panel_w=list_w,
        panel_x=panel_x,
        panel_y=panel_y,
        panel_h=panel_h,
        header_h=header_h,
        footer_hint_h=footer_hint_h,
    )
    preview = DeployPreviewLayout(
        x=panel_x + list_w + DEPLOY_SPLIT_GAP,
        y=panel_y,
        w=preview_w,
        h=panel_h,
    )
    return DeploySplitLayout(list=list, preview=preview)


def compute_deploy_list_layout(
    chrome: TitleChromeLayout,
    *,
    screen_w: float,
    panel_w: float = 820.0,
    panel_x: float | None = None,
    panel_y: float | None = None,
    panel_h: float | None = None,
    header_h: float = 36.0,
    footer_hint_h: float = 22.0,
) -> DeployListLayout:
    body_h = max(120.0, chrome.body_bottom - chrome.body_top)
    resolved_h = panel_h if panel_h is not None else body_h
    resolved_x = panel_x if panel_x is not None else (screen_w - panel_w) / 2.0
    resolved_y = panel_y if panel_y is not None else chrome.body_top
    panel_h = resolved_h
    panel_x = resolved_x
    panel_y = resolved_y
    viewport_x = panel_x + 12.0
    viewport_y = panel_y + header_h
    viewport_w = panel_w - 24.0
    viewport_h = max(80.0, panel_h - header_h - footer_hint_h)
    count = len(LEVEL_ORDER)
    content_h = count * DEPLOY_ROW_PITCH - DEPLOY_ROW_GAP if count else 0.0
    max_scroll = max(0.0, content_h - viewport_h)
    return DeployListLayout(
        panel_x=panel_x,
        panel_y=panel_y,
        panel_w=panel_w,
        panel_h=panel_h,
        viewport_x=viewport_x,
        viewport_y=viewport_y,
        viewport_w=viewport_w,
        viewport_h=viewport_h,
        row_pitch=DEPLOY_ROW_PITCH,
        row_h=DEPLOY_ROW_H,
        content_h=content_h,
        max_scroll=max_scroll,
        level_count=count,
    )


def clamp_scroll(scroll: float, layout: DeployListLayout) -> float:
    return max(0.0, min(layout.max_scroll, scroll))


def row_screen_y(layout: DeployListLayout, index: int, scroll: float) -> float:
    return layout.viewport_y + index * layout.row_pitch - scroll


def row_visible(layout: DeployListLayout, index: int, scroll: float) -> bool:
    ry = row_screen_y(layout, index, scroll)
    return ry + layout.row_h > layout.viewport_y and ry < layout.viewport_y + layout.viewport_h


def scroll_to_show_index(scroll: float, layout: DeployListLayout, index: int) -> float:
    if layout.level_count <= 0:
        return 0.0
    idx = max(0, min(layout.level_count - 1, index))
    row_top = idx * layout.row_pitch
    row_bottom = row_top + layout.row_h
    if row_top < scroll:
        return clamp_scroll(row_top, layout)
    if row_bottom > scroll + layout.viewport_h:
        return clamp_scroll(row_bottom - layout.viewport_h, layout)
    return scroll


def scroll_wheel_delta(scroll: float, layout: DeployListLayout, delta: int, *, step: float = 28.0) -> float:
    if delta == 0 or layout.max_scroll <= 0.0:
        return scroll
    direction = 1.0 if delta > 0 else -1.0
    return clamp_scroll(scroll + direction * step, layout)


def viewport_contains(layout: DeployListLayout, x: float, y: float) -> bool:
    return (
        layout.viewport_x <= x <= layout.viewport_x + layout.viewport_w
        and layout.viewport_y <= y <= layout.viewport_y + layout.viewport_h
    )


def visible_row_hit_rect(
    layout: DeployListLayout, index: int, scroll: float
) -> tuple[float, float, float, float] | None:
    """Row hit box clipped to the scroll viewport (ignores masked bleed)."""
    if not row_visible(layout, index, scroll):
        return None
    ry = row_screen_y(layout, index, scroll)
    clip_top = max(ry, layout.viewport_y)
    clip_bottom = min(ry + layout.row_h, layout.viewport_y + layout.viewport_h)
    if clip_bottom <= clip_top:
        return None
    return layout.viewport_x, clip_top, layout.viewport_w, clip_bottom - clip_top
