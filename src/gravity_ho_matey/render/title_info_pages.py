"""Professional holo info pages for the nav station — mission, helm, combat, sector dossier."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass

from gravity_ho_matey.gameplay.progress import is_level_selectable
from gravity_ho_matey.levels.level_registry import LEVEL_LABELS, LEVEL_ORDER
from gravity_ho_matey.narrative.chart_briefing_copy import LEVEL_BRIEFING
from gravity_ho_matey.render import hud_primitives as hp
from gravity_ho_matey.render import palette
from gravity_ho_matey.render.menu_ui import draw_fitted_text, draw_holo_corners, draw_wrapped_text, measure_text
from gravity_ho_matey.render.title_deploy_list import TitleChromeLayout
from gravity_ho_matey.render.title_home_layout import compute_body_panel


@dataclass(frozen=True, slots=True)
class _KeyBind:
    keys: str
    action: str
    note: str = ""


@dataclass(frozen=True, slots=True)
class _ThreatCard:
    glyph: str
    title: str
    body: str
    severity: str  # safe | warn | lethal


_CAMPAIGN_ARC: tuple[tuple[str, str, str], ...] = (
    ("cove", "Smuggler's Cove", "Training chart · tag 3 of 4 beacons"),
    ("solar", "Singularity Crossing", "Vertical strip · all beacons · patrol skiffs"),
    ("drift", "The Drift", "Open arena · north gate · void squids"),
    ("rift", "Relay Hold", "Defend relay · 3 waves · extract south"),
    ("siege", "The Siege Line", "12-hostile roster · wing escorts · station"),
    ("brood_moon", "The Brood Moon", "Surface ops · optional Nursery Matriarch"),
)

_LEVEL_LOCK: dict[str, str] = {
    "cove": "",
    "solar": "Clear Cove",
    "drift": "Clear Solar",
    "rift": "Clear Drift",
    "siege": "Clear Rift",
    "brood_moon": "Clear Siege",
}


def _body_rect(chrome: TitleChromeLayout, *, screen_w: float) -> tuple[float, float, float, float]:
    panel = compute_body_panel(chrome, screen_w=screen_w)
    return panel.x, panel.y, panel.w, panel.h


def _draw_page_shell(
    canvas: tk.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    title: str,
    subtitle: str,
    accent: str,
    dim: str,
    frame: str,
    elapsed: float,
) -> float:
    """Outer panel + header band. Returns y below header for content."""
    hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill=palette.HUD_BG)
    draw_holo_corners(canvas, x, y, w, h, accent=accent, elapsed=elapsed)
    header_h = 52.0
    canvas.create_rectangle(x + 1, y + 1, x + w - 1, y + header_h, fill="#0a1420", outline="")
    canvas.create_line(x + 12, y + header_h, x + w - 12, y + header_h, fill=frame, width=1)
    hp.draw_panel_title(canvas, x + 16, y + 12, title, color=dim)
    draw_fitted_text(
        canvas,
        x + 16,
        y + 28,
        subtitle,
        max_width=w - 32,
        color=accent,
        font=hp.FONT_BODY,
    )
    return y + header_h + 10.0


def _draw_sub_card(
    canvas: tk.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    label: str,
    accent: str,
    dim: str,
    frame: str,
) -> tuple[float, float, float, float]:
    """Inset card; returns inner content box."""
    hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill="#080e18")
    hp.draw_panel_title(canvas, x + 10, y + 8, label, color=dim)
    return x + 12.0, y + 24.0, w - 24.0, h - 32.0


def _draw_key_badge(
    canvas: tk.Canvas,
    x: float,
    y: float,
    label: str,
    *,
    accent: str,
    dim: str,
) -> float:
    font = hp.FONT_BODY_BOLD
    pad_x = 8.0
    badge_h = 20.0
    badge_w = measure_text(label, font) + pad_x * 2
    hp.draw_panel(canvas, x, y, badge_w, badge_h, frame=dim, accent=accent, fill="#0c1828")
    draw_fitted_text(
        canvas,
        x + badge_w * 0.5,
        y + badge_h * 0.5,
        label,
        max_width=badge_w - 4,
        color=accent,
        font=font,
        anchor="center",
    )
    return badge_w


def _draw_key_bind_row(
    canvas: tk.Canvas,
    x: float,
    y: float,
    w: float,
    bind: _KeyBind,
    *,
    accent: str,
    dim: str,
) -> float:
    badge_w = _draw_key_badge(canvas, x, y, bind.keys, accent=accent, dim=dim)
    action_x = x + max(108.0, badge_w + 12.0)
    draw_fitted_text(
        canvas,
        action_x,
        y + 2,
        bind.action,
        max_width=w - (action_x - x),
        color=palette.TEXT,
        font=hp.FONT_BODY_BOLD,
    )
    if bind.note:
        draw_fitted_text(
            canvas,
            action_x,
            y + 16,
            bind.note,
            max_width=w - (action_x - x),
            color=dim,
            font=hp.FONT_SMALL,
        )
        return 34.0
    return 24.0


def _severity_color(severity: str) -> str:
    if severity == "lethal":
        return palette.HUD_WARN
    if severity == "warn":
        return palette.BOSS_SCRAPE_WARN
    return palette.TEXT


def _draw_threat_card(
    canvas: tk.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    card: _ThreatCard,
    *,
    accent: str,
    dim: str,
    frame: str,
) -> None:
    color = _severity_color(card.severity)
    hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill="#080e18")
    canvas.create_rectangle(x + 1, y + 1, x + 4, y + h - 1, fill=color, outline="")
    canvas.create_text(x + 14, y + 12, anchor="w", text=card.glyph, fill=color, font=hp.FONT_DISPLAY)
    draw_fitted_text(
        canvas,
        x + 38,
        y + 8,
        card.title,
        max_width=w - 46,
        color=accent,
        font=hp.FONT_BODY_BOLD,
    )
    draw_wrapped_text(
        canvas,
        x + 12,
        y + 28,
        card.body,
        max_width=w - 20,
        line_height=14.0,
        color=color,
        font=hp.FONT_BODY,
        max_lines=3,
    )


def _draw_bullet_list(
    canvas: tk.Canvas,
    x: float,
    y: float,
    w: float,
    bullets: tuple[str, ...],
    *,
    accent: str,
    dim: str,
) -> float:
    ry = y
    for bullet in bullets:
        canvas.create_text(x, ry + 6, anchor="w", text="◈", fill=accent, font=hp.FONT_SMALL)
        used = draw_wrapped_text(
            canvas,
            x + 14,
            ry,
            bullet,
            max_width=w - 16,
            line_height=14.0,
            color=dim,
            font=hp.FONT_BODY,
            max_lines=2,
        )
        ry += max(18.0, used + 4.0)
    return ry


def draw_mission_page(
    canvas: tk.Canvas,
    chrome: TitleChromeLayout,
    *,
    screen_w: float,
    accent: str,
    dim: str,
    frame: str,
    elapsed: float,
) -> None:
    x, y, w, h = _body_rect(chrome, screen_w=screen_w)
    content_y = _draw_page_shell(
        canvas,
        x,
        y,
        w,
        h,
        title="MISSION DIRECTIVE",
        subtitle="Chart cursed sectors · loot patrol wrecks · clear the campaign in one run.",
        accent=accent,
        dim=dim,
        frame=frame,
        elapsed=elapsed,
    )
    pad = 14.0
    col_gap = 12.0
    col_w = (w - pad * 2 - col_gap) * 0.5
    left_x = x + pad
    right_x = left_x + col_w + col_gap
    card_h = h - (content_y - y) - pad - 58.0
    ix, iy, iw, ih = _draw_sub_card(
        canvas,
        left_x,
        content_y,
        col_w,
        card_h,
        label="YOUR CONTRACT",
        accent=accent,
        dim=dim,
        frame=frame,
    )
    _draw_bullet_list(
        canvas,
        ix,
        iy,
        iw,
        (
            "Tag nav beacons to unlock exit gates — rules vary by sector.",
            "Destroy patrol skiffs and bosses for jewels and power-up fittings.",
            "Fittings and treasury jewels persist across the whole campaign.",
            "Review the holo chart briefing before every launch.",
            "Trade at the Holo Bazaar between sectors (B key).",
        ),
        accent=accent,
        dim=palette.TEXT,
    )
    _draw_sub_card(
        canvas,
        right_x,
        content_y,
        col_w,
        card_h,
        label="CAMPAIGN ARC · 6 CHARTS",
        accent=accent,
        dim=dim,
        frame=frame,
    )
    row_h = min(52.0, (card_h - 36.0) / max(1, len(_CAMPAIGN_ARC)))
    for i, (level_id, name, blurb) in enumerate(_CAMPAIGN_ARC):
        ry = content_y + 28.0 + i * row_h
        num_color = accent if is_level_selectable(level_id) else dim
        canvas.create_text(right_x + 16, ry + 10, anchor="w", text=f"{i + 1:02d}", fill=num_color, font=hp.FONT_DISPLAY)
        draw_fitted_text(
            canvas,
            right_x + 48,
            ry + 4,
            name,
            max_width=col_w - 58,
            color=palette.TEXT if is_level_selectable(level_id) else dim,
            font=hp.FONT_BODY_BOLD,
        )
        draw_fitted_text(
            canvas,
            right_x + 48,
            ry + 20,
            blurb,
            max_width=col_w - 58,
            color=dim,
            font=hp.FONT_SMALL,
        )
        if i + 1 < len(_CAMPAIGN_ARC):
            canvas.create_line(right_x + 12, ry + row_h - 2, right_x + col_w - 12, ry + row_h - 2, fill=frame, width=1)

    strip_y = y + h - 48.0
    hp.draw_panel(canvas, x + pad, strip_y, w - pad * 2, 36.0, frame=frame, accent=accent, fill="#0a1828")
    draw_fitted_text(
        canvas,
        x + pad + 12,
        strip_y + 10,
        "WIN = clear sector exit  ·  LOSE = three lives gone  ·  Enter on Select Level to deploy",
        max_width=w - pad * 2 - 24,
        color=palette.HUD_LOOT_NEW,
        font=hp.FONT_BODY_BOLD,
    )


def draw_helm_page(
    canvas: tk.Canvas,
    chrome: TitleChromeLayout,
    *,
    screen_w: float,
    accent: str,
    dim: str,
    frame: str,
    elapsed: float,
) -> None:
    x, y, w, h = _body_rect(chrome, screen_w=screen_w)
    content_y = _draw_page_shell(
        canvas,
        x,
        y,
        w,
        h,
        title="HELM & NAV STATION",
        subtitle="Flight controls in-chart · tab rail switches these briefing pages.",
        accent=accent,
        dim=dim,
        frame=frame,
        elapsed=elapsed,
    )
    pad = 14.0
    gap = 10.0
    col_w = (w - pad * 2 - gap * 2) / 3.0
    card_h = h - (content_y - y) - pad - 44.0
    groups: tuple[tuple[str, tuple[_KeyBind, ...]], ...] = (
        (
            "FLIGHT",
            (
                _KeyBind("A / D", "Rotate sail"),
                _KeyBind("← / →", "Rotate sail"),
                _KeyBind("W / ↑", "Main thrusters"),
                _KeyBind("Shift", "Reactor burst", "Tap for slingshot boost · drains boost meter"),
                _KeyBind("V", "Tactical / chase camera"),
            ),
        ),
        (
            "COMBAT",
            (
                _KeyBind("Space", "Fire cannon"),
                _KeyBind("Mouse", "Aim via ship facing"),
                _KeyBind("R", "Restart current chart"),
                _KeyBind("Esc", "Abort to nav station"),
            ),
        ),
        (
            "MISSION & UI",
            (
                _KeyBind("E (hold)", "Land / ascend", "Brood Moon surface & orbital"),
                _KeyBind("B", "Holo Bazaar overlay"),
                _KeyBind("Tab", "Next briefing page"),
                _KeyBind("Enter", "Launch selected chart"),
                _KeyBind("1 – 6", "Quick-deploy chart"),
            ),
        ),
    )
    for gi, (label, binds) in enumerate(groups):
        cx = x + pad + gi * (col_w + gap)
        ix, iy, iw, _ih = _draw_sub_card(
            canvas, cx, content_y, col_w, card_h, label=label, accent=accent, dim=dim, frame=frame,
        )
        ry = iy
        for bind in binds:
            ry += _draw_key_bind_row(canvas, ix, ry, iw, bind, accent=accent, dim=dim)

    tip_y = y + h - 38.0
    draw_fitted_text(
        canvas,
        x + pad,
        tip_y,
        "Gravity wells curve shots and thrust — burst through gaps, don't fight the maw.",
        max_width=w - pad * 2,
        color=dim,
        font=hp.FONT_SMALL,
    )


def draw_combat_page(
    canvas: tk.Canvas,
    chrome: TitleChromeLayout,
    *,
    screen_w: float,
    accent: str,
    dim: str,
    frame: str,
    elapsed: float,
) -> None:
    x, y, w, h = _body_rect(chrome, screen_w=screen_w)
    content_y = _draw_page_shell(
        canvas,
        x,
        y,
        w,
        h,
        title="COMBAT & SURVIVAL",
        subtitle="Three lives · three hull chunks per life · chart radiation on bounded sectors.",
        accent=accent,
        dim=dim,
        frame=frame,
        elapsed=elapsed,
    )
    pad = 14.0
    gap = 10.0
    cols = 3
    rows = 2
    legend_h = 32.0
    grid_h = h - (content_y - y) - pad - legend_h - 4.0
    card_w = (w - pad * 2 - gap * (cols - 1)) / cols
    card_h = (grid_h - gap * (rows - 1)) / rows
    cards: tuple[_ThreatCard, ...] = (
        _ThreatCard("♥", "Campaign lives", "Three lives for the full run. Zero lives ends the campaign.", "safe"),
        _ThreatCard("▣", "Hull chunks", "Three chunks per life. A chunk lost respawns you at sector start.", "warn"),
        _ThreatCard("●", "Singularity maw", "Black hole contact destroys the ship — instant life lost.", "lethal"),
        _ThreatCard("×", "Patrol skiff", "Ram or heavy fire costs one hull chunk.", "warn"),
        _ThreatCard("◉", "Void squid", "Tentacles cling — one chunk every two seconds until you boost free.", "warn"),
        _ThreatCard("⬡", "Asteroid impact", "Direct rock contact chips one hull chunk.", "warn"),
    )
    for i, card in enumerate(cards):
        col = i % cols
        row = i // cols
        cx = x + pad + col * (card_w + gap)
        cy = content_y + row * (card_h + gap)
        _draw_threat_card(canvas, cx, cy, card_w, card_h, card, accent=accent, dim=dim, frame=frame)

    legend_y = content_y + rows * (card_h + gap) + 2.0
    hp.draw_panel(canvas, x + pad, legend_y, w - pad * 2, 28.0, frame=frame, accent=accent, fill="#0a1828")
    draw_fitted_text(
        canvas,
        x + pad + 12,
        legend_y + 8,
        "Open drift sectors: 5s off-chart radiation banks exposure — chip damage, no respawn.",
        max_width=w - pad * 2 - 24,
        color=palette.HUD_WARN,
        font=hp.FONT_SMALL,
    )


def draw_sector_dossier(
    canvas: tk.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    level_id: str,
    *,
    accent: str,
    dim: str,
    frame: str,
    elapsed: float,
) -> None:
    """Right-hand preview pane on the deploy page."""
    label = LEVEL_LABELS.get(level_id, level_id)
    title = label.split(" — ", 1)[-1] if " — " in label else label
    unlocked = is_level_selectable(level_id)
    hp.draw_panel(canvas, x, y, w, h, frame=frame, accent=accent, fill="#080e18")
    draw_holo_corners(canvas, x, y, w, h, accent=accent, elapsed=elapsed)
    hp.draw_panel_title(canvas, x + 12, y + 10, "SECTOR DOSSIER", color=dim)
    status = "READY TO DEPLOY" if unlocked else f"LOCKED — {_LEVEL_LOCK.get(level_id, 'Clear prior chart')}"
    status_color = palette.GATE_OPEN if unlocked else palette.HUD_WARN
    draw_fitted_text(
        canvas,
        x + 12,
        y + 24,
        status,
        max_width=w - 24,
        color=status_color,
        font=hp.FONT_SMALL,
    )
    draw_fitted_text(
        canvas,
        x + 12,
        y + 44,
        title.upper(),
        max_width=w - 24,
        color=accent,
        font=hp.FONT_DISPLAY,
    )
    canvas.create_line(x + 12, y + 68, x + w - 12, y + 68, fill=frame, width=1)
    rows = LEVEL_BRIEFING.get(level_id, LEVEL_BRIEFING["cove"])
    ry = y + 78.0
    for section, line in rows:
        if section:
            hp.draw_panel_title(canvas, x + 12, ry, section, color=dim)
            ry += 12
        if line:
            used = draw_wrapped_text(
                canvas,
                x + 12,
                ry,
                line,
                max_width=w - 24,
                line_height=13.0,
                color=palette.TEXT if section else dim,
                font=hp.FONT_BODY if section else hp.FONT_SMALL,
                max_lines=2,
            )
            ry += used + 4
        if ry > y + h - 36.0:
            break
    draw_fitted_text(
        canvas,
        x + 12,
        y + h - 22,
        "Enter to launch · holo briefing repeats this before play",
        max_width=w - 24,
        color=dim,
        font=hp.FONT_SMALL,
    )
