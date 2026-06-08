"""Layout math for the title screen welcome / briefing body zones."""

from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.render.title_codex import CODEX_ENTRIES, CodexEntry
from gravity_ho_matey.render.title_deploy_list import TitleChromeLayout

BODY_MARGIN = 16.0
WELCOME_LEFT_FRAC = 0.42
HANGAR_DECK_FRAC = 0.92
HANGAR_HEADER_H = 28.0
HANGAR_DECK_BAND_H = 22.0
CODEX_DOTS_GAP = 8.0
CODEX_INFO_PAD = 10.0
CODEX_INFO_TITLE_H = 28.0
CODEX_INFO_META_H = 16.0
CODEX_INFO_BODY_LINE_H = 13.0
CODEX_INFO_MIN_H = 68.0
CODEX_INFO_MAX_LINES = 3
CODEX_NAV_W = 28.0
CODEX_NAV_H = 30.0
SHIP_HANGAR_X_FRAC = 0.50
SHIP_DECK_LIFT = 18.0

WELCOME_BTN_H = 44.0
WELCOME_PITCH_LINE_H = 14.0
WELCOME_PITCH_LINES = 2
WELCOME_BLOCK_GAP = 14.0


@dataclass(frozen=True, slots=True)
class BodyPanelLayout:
    x: float
    y: float
    w: float
    h: float


@dataclass(frozen=True, slots=True)
class CodexLayout:
    viewport_x: float
    viewport_y: float
    viewport_w: float
    viewport_h: float
    header_bottom: float
    preview_top: float
    preview_bottom: float
    podium_cx: float
    podium_cy: float
    deck_y: float
    info_x: float
    info_y: float
    info_w: float
    info_h: float
    dots_y: float
    prev_x: float
    prev_y: float
    prev_w: float
    prev_h: float
    next_x: float
    next_y: float
    next_w: float
    next_h: float


@dataclass(frozen=True, slots=True)
class WelcomeLeftLayout:
    x: float
    w: float
    pitch_y: float
    btn_x: float
    btn_y: float
    btn_w: float
    btn_h: float


@dataclass(frozen=True, slots=True)
class WelcomeHomeLayout:
    panel: BodyPanelLayout
    left_x: float
    left_w: float
    hangar_x: float
    hangar_w: float
    hangar_h: float
    divider_x: float
    deck_y: float
    ship_x: float
    ship_y: float


def estimate_codex_info_height(
    blurb: str,
    info_w: float,
    *,
    min_h: float = CODEX_INFO_MIN_H,
    max_lines: int = CODEX_INFO_MAX_LINES,
) -> float:
    chars_per_line = max(20, int(info_w / 6.5))
    lines = min(max_lines, max(1, (len(blurb) + chars_per_line - 1) // chars_per_line))
    body_h = lines * CODEX_INFO_BODY_LINE_H
    return max(min_h, CODEX_INFO_TITLE_H + CODEX_INFO_META_H + body_h + CODEX_INFO_PAD)


def max_codex_info_height(info_w: float) -> float:
    return max(estimate_codex_info_height(entry.blurb, info_w) for entry in CODEX_ENTRIES)


def compute_body_panel(
    chrome: TitleChromeLayout,
    *,
    screen_w: float,
    margin: float = BODY_MARGIN,
) -> BodyPanelLayout:
    w = screen_w - margin * 2.0
    h = max(120.0, chrome.body_bottom - chrome.body_top)
    return BodyPanelLayout(x=margin, y=chrome.body_top, w=w, h=h)


def compute_welcome_home_layout(
    chrome: TitleChromeLayout,
    *,
    screen_w: float,
    margin: float = BODY_MARGIN,
) -> WelcomeHomeLayout:
    panel = compute_body_panel(chrome, screen_w=screen_w, margin=margin)
    pad = 12.0
    inner_x = panel.x + pad
    inner_w = panel.w - pad * 2.0
    inner_h = panel.h - pad * 2.0
    left_w = max(220.0, inner_w * WELCOME_LEFT_FRAC)
    hangar_x = inner_x + left_w + 10.0
    hangar_w = max(180.0, inner_x + inner_w - hangar_x)
    deck_y = panel.y + pad + inner_h * HANGAR_DECK_FRAC
    return WelcomeHomeLayout(
        panel=panel,
        left_x=inner_x,
        left_w=left_w,
        hangar_x=hangar_x,
        hangar_w=hangar_w,
        hangar_h=inner_h,
        divider_x=inner_x + left_w + 4.0,
        deck_y=deck_y,
        ship_x=hangar_x + hangar_w * SHIP_HANGAR_X_FRAC,
        ship_y=deck_y - SHIP_DECK_LIFT,
    )


def compute_welcome_left_layout(
    panel: BodyPanelLayout,
    left_x: float,
    left_w: float,
) -> WelcomeLeftLayout:
    """Vertically balanced hero block — pitch + deploy CTA, no dead middle gap."""
    pitch_block_h = WELCOME_PITCH_LINE_H * WELCOME_PITCH_LINES
    block_h = pitch_block_h + WELCOME_BLOCK_GAP + WELCOME_BTN_H
    inset = 16.0
    available_top = panel.y + inset
    available_h = max(block_h, panel.h - inset * 2.0)
    block_top = available_top + max(0.0, (available_h - block_h) * 0.34)
    btn_w = left_w - 4.0
    btn_y = block_top + pitch_block_h + WELCOME_BLOCK_GAP
    return WelcomeLeftLayout(
        x=left_x,
        w=left_w,
        pitch_y=block_top,
        btn_x=left_x,
        btn_y=btn_y,
        btn_w=btn_w,
        btn_h=WELCOME_BTN_H,
    )


def compute_codex_layout(
    layout: WelcomeHomeLayout,
    entry: CodexEntry | None = None,
) -> CodexLayout:
    pad = 12.0
    hy = layout.panel.y + pad
    hx = layout.hangar_x
    hw = layout.hangar_w
    hh = layout.hangar_h
    header_bottom = hy + HANGAR_HEADER_H
    deck_y = layout.deck_y
    info_w = max(120.0, hw - 20.0)
    blurb = entry.blurb if entry is not None else max(CODEX_ENTRIES, key=lambda e: len(e.blurb)).blurb
    info_h = estimate_codex_info_height(blurb, info_w)
    info_y = deck_y - info_h - CODEX_DOTS_GAP
    dots_y = info_y - CODEX_DOTS_GAP
    preview_top = header_bottom
    preview_bottom = max(preview_top + 48.0, dots_y - 6.0)
    podium_cx = hx + hw * 0.5
    podium_cy = preview_top + (preview_bottom - preview_top) * 0.52
    nav_y = podium_cy - CODEX_NAV_H * 0.5
    return CodexLayout(
        viewport_x=hx,
        viewport_y=hy,
        viewport_w=hw,
        viewport_h=hh,
        header_bottom=header_bottom,
        preview_top=preview_top,
        preview_bottom=preview_bottom,
        podium_cx=podium_cx,
        podium_cy=podium_cy,
        deck_y=deck_y,
        info_x=hx + 10.0,
        info_y=info_y,
        info_w=info_w,
        info_h=info_h,
        dots_y=dots_y,
        prev_x=hx + 8.0,
        prev_y=nav_y,
        prev_w=CODEX_NAV_W,
        prev_h=CODEX_NAV_H,
        next_x=hx + hw - CODEX_NAV_W - 8.0,
        next_y=nav_y,
        next_w=CODEX_NAV_W,
        next_h=CODEX_NAV_H,
    )


def codex_viewport_contains(layout: CodexLayout, x: float, y: float) -> bool:
    return (
        layout.viewport_x <= x <= layout.viewport_x + layout.viewport_w
        and layout.viewport_y <= y <= layout.viewport_y + layout.viewport_h
    )
