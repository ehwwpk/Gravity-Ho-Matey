"""Layout math for the title screen welcome / briefing body zones."""

from __future__ import annotations

from dataclasses import dataclass

from gravity_ho_matey.render.title_deploy_list import TitleChromeLayout

BODY_MARGIN = 16.0
WELCOME_LEFT_FRAC = 0.38
HANGAR_DECK_FRAC = 0.84
SHIP_HANGAR_X_FRAC = 0.50
SHIP_DECK_LIFT = 18.0
CODEX_PODIUM_Y_FRAC = 0.36
CODEX_INFO_H_FRAC = 0.30
CODEX_NAV_W = 28.0
CODEX_NAV_H = 30.0


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


def compute_codex_layout(layout: WelcomeHomeLayout) -> CodexLayout:
    pad = 12.0
    hy = layout.panel.y + pad
    hx = layout.hangar_x
    hw = layout.hangar_w
    hh = layout.hangar_h
    deck_y = layout.deck_y
    info_h = max(88.0, hh * CODEX_INFO_H_FRAC)
    info_y = deck_y - info_h - 8.0
    podium_cx = hx + hw * 0.5
    podium_cy = hy + hh * CODEX_PODIUM_Y_FRAC
    nav_y = podium_cy - CODEX_NAV_H * 0.5
    return CodexLayout(
        viewport_x=hx,
        viewport_y=hy,
        viewport_w=hw,
        viewport_h=hh,
        podium_cx=podium_cx,
        podium_cy=podium_cy,
        deck_y=deck_y,
        info_x=hx + 10.0,
        info_y=info_y,
        info_w=max(120.0, hw - 20.0),
        info_h=info_h,
        dots_y=info_y - 10.0,
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
