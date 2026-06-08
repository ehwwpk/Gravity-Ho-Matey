"""Draw the welcome hangar field codex — turntable preview + info card."""

from __future__ import annotations

import math
import tkinter as tk

from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.camera import CameraMode
from gravity_ho_matey.render.lighting import LightRig
from gravity_ho_matey.render.menu_ui import draw_fitted_text, draw_menu_button, draw_wrapped_text
from gravity_ho_matey.render.title_codex import CODEX_ENTRIES, CodexEntry
from gravity_ho_matey.render.title_codex_tactical import draw_codex_tactical_preview
from gravity_ho_matey.render.title_home_layout import CodexLayout


def turntable_scale_x(yaw: float) -> float:
    return 0.72 + 0.28 * abs(math.cos(yaw))


def _rig_for_entry(entry: CodexEntry) -> LightRig:
    return LightRig.for_play(theme=entry.theme, camera_mode=CameraMode.TACTICAL)


def _threat_color(threat: str) -> str:
    key = threat.upper()
    if key in ("APEX", "BRUTAL", "LETHAL", "NASTY"):
        return palette.BOSS_SCRAPE_WARN
    if key in ("MEAN", "HEAVY"):
        return palette.HUD_ACCENT
    if key in ("CREW", "ALLY", "SAFE"):
        return palette.HUD_LOOT_NEW
    return palette.HUD_DIM


def draw_codex_pedestal(
    canvas: tk.Canvas,
    layout: CodexLayout,
    entry: CodexEntry,
    *,
    index: int,
    accent: str,
    dim: str,
    frame: str,
    elapsed: float,
    yaw: float,
    hover_id: str | None,
    hits,
) -> None:
    pulse = 0.5 + 0.5 * math.sin(elapsed * 2.8)
    cx, cy = layout.podium_cx, layout.podium_cy
    ring_rx = min(102.0, layout.viewport_w * 0.30)
    ring_ry = 16.0
    deck_y = layout.deck_y

    canvas.create_oval(
        cx - ring_rx,
        deck_y - ring_ry * 0.4,
        cx + ring_rx,
        deck_y + ring_ry,
        fill="#101c28",
        outline=accent if pulse > 0.52 else dim,
        width=2,
    )
    canvas.create_oval(
        cx - ring_rx * 0.58,
        deck_y - ring_ry * 0.22,
        cx + ring_rx * 0.58,
        deck_y + ring_ry * 0.52,
        fill="",
        outline=palette.HUD_LOOT_NEW,
        width=1,
        dash=(4, 6),
    )

    holo_r = ring_rx * 0.68
    for i, frac in enumerate((0.62, 0.82)):
        canvas.create_oval(
            cx - holo_r * frac,
            cy - holo_r * frac * 0.34,
            cx + holo_r * frac,
            cy + holo_r * frac * 0.34,
            fill="",
            outline=accent if i else dim,
            width=1,
            dash=(4, 7),
        )

    rig = _rig_for_entry(entry)
    preview_cy = cy + math.sin(yaw) * 1.5
    draw_codex_tactical_preview(
        canvas,
        entry,
        cx,
        preview_cy,
        rig=rig,
        elapsed=elapsed,
        yaw=yaw,
    )

    _draw_info_card(canvas, layout, entry, accent=accent, dim=dim, frame=frame)
    _draw_codex_dots(canvas, layout, index, accent=accent, dim=dim)
    _draw_codex_nav(canvas, layout, accent=accent, dim=dim, frame=frame, hover_id=hover_id, hits=hits)


def _draw_info_card(
    canvas: tk.Canvas,
    layout: CodexLayout,
    entry: CodexEntry,
    *,
    accent: str,
    dim: str,
    frame: str,
) -> None:
    ix, iy, iw, ih = layout.info_x, layout.info_y, layout.info_w, layout.info_h
    hp.draw_panel(canvas, ix, iy, iw, ih, frame=frame, accent=accent, fill="#0a1420")

    title_y = iy + 10
    draw_fitted_text(
        canvas,
        ix + 10,
        title_y,
        entry.title,
        max_width=iw * 0.58,
        color=accent,
        font=hp.FONT_BODY_BOLD,
    )
    draw_fitted_text(
        canvas,
        ix + iw - 10,
        title_y,
        entry.tag,
        max_width=iw * 0.34,
        color=dim,
        font=hp.FONT_SMALL,
        anchor="e",
    )

    meta_y = iy + 28
    draw_fitted_text(
        canvas,
        ix + 10,
        meta_y,
        f"RATING · {entry.threat}",
        max_width=iw - 20,
        color=_threat_color(entry.threat),
        font=hp.FONT_SMALL,
    )

    body_top = iy + 44
    body_h = max(28.0, ih - 50)
    max_lines = max(2, int(body_h // 13))
    draw_wrapped_text(
        canvas,
        ix + 10,
        body_top,
        entry.blurb,
        max_width=iw - 20,
        line_height=13.0,
        color=palette.TEXT,
        font=hp.FONT_SMALL,
        max_lines=max_lines,
    )


def _draw_codex_dots(
    canvas: tk.Canvas,
    layout: CodexLayout,
    index: int,
    *,
    accent: str,
    dim: str,
) -> None:
    count = len(CODEX_ENTRIES)
    spacing = min(11.0, (layout.viewport_w - 40.0) / max(1, count - 1))
    total_w = (count - 1) * spacing
    start_x = layout.podium_cx - total_w * 0.5
    y = layout.dots_y
    for i in range(count):
        x = start_x + i * spacing
        r = 3.5 if i == index else 2.0
        fill = accent if i == index else dim
        canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline="")


def _draw_codex_nav(
    canvas: tk.Canvas,
    layout: CodexLayout,
    *,
    accent: str,
    dim: str,
    frame: str,
    hover_id: str | None,
    hits,
) -> None:
    hits.add("codex_body", layout.viewport_x, layout.viewport_y, layout.viewport_w, layout.viewport_h)
    hits.add("codex_prev", layout.prev_x, layout.prev_y, layout.prev_w, layout.prev_h)
    hits.add("codex_next", layout.next_x, layout.next_y, layout.next_w, layout.next_h)

    draw_menu_button(
        canvas,
        layout.prev_x,
        layout.prev_y,
        layout.prev_w,
        layout.prev_h,
        "◀",
        accent=accent,
        dim=dim,
        frame=frame,
        hover=hover_id == "codex_prev",
    )
    draw_menu_button(
        canvas,
        layout.next_x,
        layout.next_y,
        layout.next_w,
        layout.next_h,
        "▶",
        accent=accent,
        dim=dim,
        frame=frame,
        hover=hover_id == "codex_next",
    )


def draw_codex_preview(
    canvas: tk.Canvas,
    entry: CodexEntry,
    cx: float,
    cy: float,
    *,
    elapsed: float,
    yaw: float,
) -> None:
    """Test helper — draw preview only."""
    draw_codex_tactical_preview(
        canvas,
        entry,
        cx,
        cy,
        rig=_rig_for_entry(entry),
        elapsed=elapsed,
        yaw=yaw,
    )
