"""Visual layers for the title screen welcome hangar and backdrop."""

from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.gameplay.campaign import CampaignState
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.menu_ui import draw_holo_corners
from gravity_ho_matey.render.starfield_viz import draw_layered_starfield
from gravity_ho_matey.render.title_home_layout import WelcomeHomeLayout
from gravity_ho_matey.render.title_codex import CODEX_ENTRIES


def draw_title_starfield(
    canvas: tk.Canvas,
    width: float,
    height: float,
    *,
    elapsed: float,
    body_top: float = 0.0,
    body_bottom: float | None = None,
) -> None:
    """Layered parallax stars — denser in the hangar band."""
    bottom = height if body_bottom is None else body_bottom
    draw_layered_starfield(
        canvas,
        x=0.0,
        y=body_top,
        width=width,
        height=max(1.0, bottom - body_top),
        elapsed=elapsed,
        theme="cove",
    )


def draw_hangar_bay(
    canvas: tk.Canvas,
    layout: WelcomeHomeLayout,
    *,
    accent: str,
    dim: str,
    frame: str,
    elapsed: float,
    codex_index: int = 0,
) -> None:
    """Open hangar zone — deck bands and ambient glow (codex draws the centerpiece)."""
    hx = layout.hangar_x
    hy = layout.panel.y + 12.0
    hw = layout.hangar_w
    hh = layout.hangar_h
    pulse = 0.5 + 0.5 * math.sin(elapsed * 2.4)

    canvas.create_rectangle(hx, hy, hx + hw, hy + hh, fill="#0c1620", outline="")
    for i, color in enumerate(("#081018", "#0e1c28", "#142636")):
        band_h = hh * (0.35 + i * 0.22)
        canvas.create_rectangle(
            hx,
            hy + hh - band_h,
            hx + hw,
            hy + hh,
            fill=color,
            outline="",
        )

    deck_y = layout.deck_y
    canvas.create_line(hx + 8, deck_y, hx + hw - 8, deck_y, fill=accent, width=2)
    canvas.create_line(hx + 8, deck_y + 1, hx + hw - 8, deck_y + 1, fill=frame, width=1)

    canvas.create_line(layout.divider_x, hy, layout.divider_x, hy + hh, fill=frame, width=1)
    draw_holo_corners(canvas, hx, hy, hw, hh, accent=accent, elapsed=elapsed)

    count = len(CODEX_ENTRIES)
    label = f"FIELD CODEX · {codex_index + 1}/{count}"
    canvas.create_text(
        hx + hw - 12,
        hy + 14,
        anchor="e",
        text=label,
        fill=dim,
        font=hp.FONT_SMALL,
    )
    canvas.create_text(
        hx + 12,
        hy + 14,
        anchor="w",
        text="TACTICAL PREVIEW · WHEEL ◀ ▶",
        fill=accent if pulse > 0.5 else dim,
        font=hp.FONT_SMALL,
    )


def draw_campaign_status_chip(
    canvas: tk.Canvas,
    x: float,
    y: float,
    *,
    campaign: CampaignState,
    accent: str,
    dim: str,
    frame: str,
) -> None:
    w = 200.0
    h = 34.0
    hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
    hp.draw_panel_title(canvas, x + 10, y + 6, "TREASURY", color=dim)
    canvas.create_text(
        x + w - 10,
        y + 22,
        anchor="e",
        text=f"{campaign.jewels} JEWELS",
        fill=palette.HUD_LOOT_NEW,
        font=hp.FONT_BODY_BOLD,
    )
